from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from database import get_db
from models import Analytics as AnalyticsModel, Screen as ScreenModel
from schemas import Analytics, AnalyticsEvent, AnalyticsStats
from cache import cache

def count_all_components(components):
    """
    Рекурсивно подсчитывает все компоненты в экране, включая вложенные
    """
    total_count = 0
    for component in components:
        total_count += 1  # Считаем сам компонент
        
        # Если у компонента есть дочерние компоненты, считаем их тоже
        if 'children' in component and component['children']:
            total_count += count_all_components(component['children'])
    
    return total_count

router = APIRouter()


@router.post("/track")
async def track_event(
    event: AnalyticsEvent,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_analytics = AnalyticsModel(**event.dict())
    db.add(db_analytics)
    db.commit()
    
    background_tasks.add_task(invalidate_analytics_cache)
    
    return {"message": "Event tracked successfully"}


@router.get("/events", response_model=List[Analytics])
async def get_analytics_events(
    screen_id: Optional[int] = None,
    event_type: Optional[str] = None,
    platform: Optional[str] = None,
    locale: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(AnalyticsModel)
    
    if screen_id:
        query = query.filter(AnalyticsModel.screen_id == screen_id)
    if event_type:
        query = query.filter(AnalyticsModel.event_type == event_type)
    if platform:
        query = query.filter(AnalyticsModel.platform == platform)
    if locale:
        query = query.filter(AnalyticsModel.locale == locale)
    
    events = query.order_by(desc(AnalyticsModel.timestamp)).offset(offset).limit(limit).all()
    
    return [Analytics.from_orm(event) for event in events]


@router.get("/events/count")
async def get_analytics_events_count(
    screen_id: Optional[int] = None,
    event_type: Optional[str] = None,
    platform: Optional[str] = None,
    locale: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AnalyticsModel)
    
    if screen_id:
        query = query.filter(AnalyticsModel.screen_id == screen_id)
    if event_type:
        query = query.filter(AnalyticsModel.event_type == event_type)
    if platform:
        query = query.filter(AnalyticsModel.platform == platform)
    if locale:
        query = query.filter(AnalyticsModel.locale == locale)
    
    total_count = query.count()
    return {"total": total_count}


@router.get("/stats/{screen_id}", response_model=AnalyticsStats)
async def get_screen_stats(
    screen_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    cache_key = f"stats:{screen_id}:{days}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        # Добавляем active_components_count для старых кэшированных данных
        if 'active_components_count' not in cached_result:
            # Получаем общее количество компонентов в экране (включая вложенные)
            screen = db.query(ScreenModel).filter(ScreenModel.id == screen_id).first()
            total_components_count = 0
            if screen and screen.config:
                try:
                    config_data = screen.config if isinstance(screen.config, dict) else json.loads(screen.config)
                    components = config_data.get('components', [])
                    total_components_count = count_all_components(components)
                except:
                    total_components_count = 0
            cached_result['active_components_count'] = total_components_count
        return AnalyticsStats(**cached_result)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(AnalyticsModel).filter(
        AnalyticsModel.screen_id == screen_id,
        AnalyticsModel.timestamp >= start_date
    )
    
    total_views = query.filter(AnalyticsModel.event_type == "view").count()
    
    unique_users = query.filter(AnalyticsModel.user_id.isnot(None)).with_entities(AnalyticsModel.user_id).distinct().count()
    
    session_durations = db.query(
        AnalyticsModel.session_id,
        func.max(AnalyticsModel.timestamp) - func.min(AnalyticsModel.timestamp)
    ).filter(
        AnalyticsModel.screen_id == screen_id,
        AnalyticsModel.timestamp >= start_date
    ).group_by(AnalyticsModel.session_id).all()
    
    avg_session_duration = 0
    if session_durations:
        total_duration = sum([duration[1].total_seconds() for duration in session_durations if duration[1]])
        avg_session_duration = total_duration / len(session_durations)
    
    # Получаем все активные компоненты (без ограничения)
    active_components = db.query(
        AnalyticsModel.component_id,
        func.count(AnalyticsModel.id).label('count')
    ).filter(
        AnalyticsModel.screen_id == screen_id,
        AnalyticsModel.timestamp >= start_date,
        AnalyticsModel.component_id.isnot(None)
    ).group_by(AnalyticsModel.component_id).order_by(desc('count')).all()
    
    # Ограничиваем до 10 только для отображения в деталях
    most_used_components = active_components[:10]
    
    platform_breakdown = dict(db.query(
        AnalyticsModel.platform,
        func.count(AnalyticsModel.id)
    ).filter(
        AnalyticsModel.screen_id == screen_id,
        AnalyticsModel.timestamp >= start_date
    ).group_by(AnalyticsModel.platform).all())
    
    locale_breakdown = dict(db.query(
        AnalyticsModel.locale,
        func.count(AnalyticsModel.id)
    ).filter(
        AnalyticsModel.screen_id == screen_id,
        AnalyticsModel.timestamp >= start_date
    ).group_by(AnalyticsModel.locale).all())
    
    # Получаем общее количество компонентов в экране (включая вложенные)
    screen = db.query(ScreenModel).filter(ScreenModel.id == screen_id).first()
    total_components_count = 0
    if screen and screen.config:
        try:
            config_data = screen.config if isinstance(screen.config, dict) else json.loads(screen.config)
            components = config_data.get('components', [])
            total_components_count = count_all_components(components)
        except:
            total_components_count = 0
    
    stats = AnalyticsStats(
        total_views=total_views,
        unique_users=unique_users,
        avg_session_duration=avg_session_duration,
        most_used_components=[
            {"component_id": comp[0], "count": comp[1]} 
            for comp in most_used_components
        ],
        active_components_count=total_components_count,  # Общее количество компонентов в экране (включая вложенные)
        platform_breakdown=platform_breakdown,
        locale_breakdown=locale_breakdown
    )
    
    await cache.set(cache_key, stats.dict(), ttl=300)
    return stats


@router.get("/overview")
async def get_analytics_overview(days: int = 7, db: Session = Depends(get_db)):
    cache_key = f"analytics_overview:{days}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    total_events = db.query(AnalyticsModel).filter(
        AnalyticsModel.timestamp >= start_date
    ).count()
    
    # Считаем активные экраны из таблицы screens, а не из аналитики
    unique_screens = db.query(ScreenModel).filter(
        ScreenModel.is_active == True
    ).count()
    
    unique_users = db.query(AnalyticsModel.user_id).filter(
        AnalyticsModel.timestamp >= start_date,
        AnalyticsModel.user_id.isnot(None)
    ).distinct().count()
    
    top_screens = db.query(
        ScreenModel.name,
        ScreenModel.title,
        func.count(AnalyticsModel.id).label('views')
    ).join(
        AnalyticsModel, ScreenModel.id == AnalyticsModel.screen_id
    ).filter(
        AnalyticsModel.timestamp >= start_date,
        AnalyticsModel.event_type == "view"
    ).group_by(
        ScreenModel.id, ScreenModel.name, ScreenModel.title
    ).order_by(desc('views')).limit(10).all()
    
    daily_stats = db.query(
        func.date(AnalyticsModel.timestamp).label('date'),
        func.count(AnalyticsModel.id).label('events'),
        func.count(func.distinct(AnalyticsModel.user_id)).label('unique_users')
    ).filter(
        AnalyticsModel.timestamp >= start_date
    ).group_by(func.date(AnalyticsModel.timestamp)).order_by('date').all()
    
    result = {
        "total_events": total_events,
        "unique_screens": unique_screens,  # Количество активных экранов в системе
        "unique_users": unique_users,
        "top_screens": [
            {"name": screen[0], "title": screen[1], "views": screen[2]}
            for screen in top_screens
        ],
        "daily_stats": [
            {
                "date": stat[0].isoformat(),
                "events": stat[1],
                "unique_users": stat[2]
            }
            for stat in daily_stats
        ]
    }
    
    await cache.set(cache_key, result, ttl=300)
    return result


async def invalidate_analytics_cache():
    await cache.invalidate_pattern("stats:*")
    await cache.invalidate_pattern("analytics_overview:*")





