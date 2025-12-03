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

