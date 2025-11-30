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



