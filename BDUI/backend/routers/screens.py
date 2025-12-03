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

