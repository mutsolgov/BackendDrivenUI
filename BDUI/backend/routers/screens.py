from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database import get_db
from models import Screen as ScreenModel, Template as TemplateModel, PerformanceMetric
from schemas import Screen, ScreenCreate, ScreenUpdate
from cache import cache
from websocket_manager import manager
import hashlib
import json
import re
import time

router = APIRouter()


@router.get("/", response_model=List[Screen])
async def get_screens(
    platform: Optional[str] = None,
    locale: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    cache_key = f"screens:{platform}:{locale}:{is_active}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    query = db.query(ScreenModel)
    
    if platform:
        query = query.filter(ScreenModel.platform == platform)
    if locale:
        query = query.filter(ScreenModel.locale == locale)
    if is_active is not None:
        query = query.filter(ScreenModel.is_active == is_active)
    
    screens = query.all()
    result = [Screen.from_orm(screen) for screen in screens]
    
    await cache.set(cache_key, [screen.dict() for screen in result])
    return result


@router.get("/{screen_id}", response_model=Screen)
async def get_screen(screen_id: int, db: Session = Depends(get_db)):
    cache_key = f"screen:{screen_id}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return Screen(**cached_result)
    
    screen = db.query(ScreenModel).filter(ScreenModel.id == screen_id).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    result = Screen.from_orm(screen)
    await cache.set(cache_key, result.dict())
    return result


@router.get("/by-name/{screen_name}")
async def get_screen_by_name(
    screen_name: str,
    platform: str = "web",
    locale: str = "ru",
    db: Session = Depends(get_db)
):
    cache_key = f"screen_name:{screen_name}:{platform}:{locale}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Try to find screen with exact name and locale
    screen = db.query(ScreenModel).filter(
        ScreenModel.name == screen_name,
        ScreenModel.platform == platform,
        ScreenModel.locale == locale,
        ScreenModel.is_active == True
    ).first()
    
    # If not found and locale is 'en', try with _en suffix
    if not screen and locale == 'en':
        screen = db.query(ScreenModel).filter(
            ScreenModel.name == f"{screen_name}_en",
            ScreenModel.platform == platform,
            ScreenModel.locale == locale,
            ScreenModel.is_active == True
        ).first()
    
    # If still not found, try fallback to Russian version
    if not screen:
        screen = db.query(ScreenModel).filter(
            ScreenModel.name == screen_name,
            ScreenModel.platform == platform,
            ScreenModel.locale == "ru",
            ScreenModel.is_active == True
        ).first()
    
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    result = Screen.from_orm(screen).dict()
    await cache.set(cache_key, result)
    return result


@router.post("/", response_model=Screen)
async def create_screen(
    screen: ScreenCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing_screen = db.query(ScreenModel).filter(
        ScreenModel.name == screen.name,
        ScreenModel.platform == screen.platform,
        ScreenModel.locale == screen.locale
    ).first()
    
    if existing_screen:
        raise HTTPException(status_code=400, detail="Screen already exists")
    
    db_screen = ScreenModel(**screen.dict())
    db.add(db_screen)
    db.commit()
    db.refresh(db_screen)
    
    background_tasks.add_task(invalidate_screen_cache, db_screen.id)
    background_tasks.add_task(notify_screen_update, db_screen.id, Screen.from_orm(db_screen).dict())
    
    return Screen.from_orm(db_screen)


@router.put("/{screen_id}", response_model=Screen)
async def update_screen(
    screen_id: int,
    screen_update: ScreenUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Начинаем отсчет времени
    start_time = time.time() * 1000  # миллисекунды
    save_timestamp = screen_update.dict().get('metadata', {}).get('saveTimestamp', start_time)
    
    db_screen = db.query(ScreenModel).filter(ScreenModel.id == screen_id).first()
    if not db_screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    update_data = screen_update.dict(exclude_unset=True)
    
    if update_data.get('config') and update_data['config'] != db_screen.config:
        db_screen.version += 1
    
    for field, value in update_data.items():
        setattr(db_screen, field, value)
    
    # Замеряем время сохранения в БД
    db_start = time.time() * 1000
    db.commit()
    db.refresh(db_screen)
    db_time = time.time() * 1000 - db_start
    
    backend_time = time.time() * 1000 - start_time
    
    # Создаем метрики
    performance_data = {
        "save_timestamp": save_timestamp,
        "backend_processed_at": time.time() * 1000,
        "db_time": db_time,
        "backend_time": backend_time,
        "screen_id": screen_id
    }
    
    # Сохраняем метрики в БД (асинхронно)
    background_tasks.add_task(save_performance_metric, db, screen_id, "update", db_time, backend_time)
    background_tasks.add_task(invalidate_screen_cache, screen_id)
    background_tasks.add_task(notify_screen_update, screen_id, Screen.from_orm(db_screen).dict(), performance_data)
    
    return Screen.from_orm(db_screen)


@router.delete("/{screen_id}")
async def delete_screen(
    screen_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_screen = db.query(ScreenModel).filter(ScreenModel.id == screen_id).first()
    if not db_screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    db.delete(db_screen)
    db.commit()
    
    background_tasks.add_task(invalidate_screen_cache, screen_id)
    
    return {"message": "Screen deleted successfully"}


@router.post("/{screen_id}/duplicate", response_model=Screen)
async def duplicate_screen(
    screen_id: int,
    new_name: str,
    db: Session = Depends(get_db)
):
    original_screen = db.query(ScreenModel).filter(ScreenModel.id == screen_id).first()
    if not original_screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    existing_screen = db.query(ScreenModel).filter(
        ScreenModel.name == new_name,
        ScreenModel.platform == original_screen.platform,
        ScreenModel.locale == original_screen.locale
    ).first()
    
    if existing_screen:
        raise HTTPException(status_code=400, detail="Screen with this name already exists")
    
    new_screen = ScreenModel(
        name=new_name,
        title=f"{original_screen.title} (Copy)",
        description=original_screen.description,
        config=original_screen.config,
        platform=original_screen.platform,
        locale=original_screen.locale,
        is_active=False
    )
    
    db.add(new_screen)
    db.commit()
    db.refresh(new_screen)
    
    return Screen.from_orm(new_screen)


@router.post("/create-from-template", response_model=Screen)
async def create_screen_from_template(
    request_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Создает экран на основе шаблона с подстановкой переменных
    """
    # Извлекаем параметры из запроса
    template_id = request_data.get('template_id')
    screen_name = request_data.get('screen_name')
    screen_title = request_data.get('screen_title')
    template_variables = request_data.get('template_variables', {})
    platform = request_data.get('platform', 'web')
    locale = request_data.get('locale', 'ru')
    
    if not template_id or not screen_name:
        raise HTTPException(status_code=400, detail="template_id and screen_name are required")
    
    # Получаем шаблон
    template = db.query(TemplateModel).filter(TemplateModel.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Проверяем, не существует ли уже экран с таким именем
    existing_screen = db.query(ScreenModel).filter(
        ScreenModel.name == screen_name,
        ScreenModel.platform == platform,
        ScreenModel.locale == locale
    ).first()
    
    if existing_screen:
        raise HTTPException(status_code=400, detail="Screen with this name already exists")
    
    # Подставляем переменные в конфигурацию шаблона
    processed_config = substitute_template_variables(template.config, template_variables)
    
    # Создаем экран
    screen_title = screen_title or screen_name
    new_screen = ScreenModel(
        name=screen_name,
        title=screen_title,
        description=f"Created from template: {template.name}",
        config=processed_config,
        platform=platform,
        locale=locale,
        is_active=False  # По умолчанию неактивный, пользователь активирует вручную
    )
    
    db.add(new_screen)
    db.commit()
    db.refresh(new_screen)
    
    if background_tasks:
        background_tasks.add_task(invalidate_screen_cache, new_screen.id)
        background_tasks.add_task(notify_screen_update, new_screen.id, Screen.from_orm(new_screen).dict())
    
    return Screen.from_orm(new_screen)


def substitute_template_variables(config: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Рекурсивно подставляет переменные шаблона в конфигурацию
    """
    if isinstance(config, dict):
        result = {}
        for key, value in config.items():
            result[key] = substitute_template_variables(value, variables)
        return result
    elif isinstance(config, list):
        return [substitute_template_variables(item, variables) for item in config]
    elif isinstance(config, str):
        # Заменяем переменные в строке
        def replace_variable(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))
        
        return re.sub(r'\{\{(\w+)\}\}', replace_variable, config)
    else:
        return config


async def invalidate_screen_cache(screen_id: int):
    await cache.delete(f"screen:{screen_id}")
    await cache.invalidate_pattern("screens:*")
    await cache.invalidate_pattern("screen_name:*")
    # Также инвалидируем кэш аналитики, так как количество активных экранов может измениться
    await cache.invalidate_pattern("analytics_overview:*")

async def notify_screen_update(screen_id: int, screen_data: dict, performance_data: dict = None):
    """Уведомить всех клиентов об обновлении экрана с метриками производительности"""
    print(f"🚀 notify_screen_update called for screen {screen_id}")
    await manager.broadcast_screen_update(str(screen_id), screen_data, performance_data)

def save_performance_metric(db: Session, screen_id: int, operation_type: str, db_time: float, backend_time: float):
    """Сохранить метрику производительности в БД"""
    try:
        metric = PerformanceMetric(
            screen_id=screen_id,
            operation_type=operation_type,
            total_time=backend_time,
            db_time=db_time,
            backend_time=backend_time,
            websocket_time=0.0,  # Будет обновлено позже
            client_time=0.0  # Будет обновлено позже
        )
        db.add(metric)
        db.commit()
        print(f"✅ Performance metric saved: {operation_type} on screen {screen_id} - {backend_time:.2f}ms")
    except Exception as e:
        print(f"❌ Error saving performance metric: {e}")
        db.rollback()





