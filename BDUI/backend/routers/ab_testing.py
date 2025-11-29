from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import hashlib
import random
from database import get_db
from models import ABTest as ABTestModel, Screen as ScreenModel
from schemas import ABTest, ABTestCreate, ABTestUpdate
from cache import cache

router = APIRouter()


@router.get("/", response_model=List[ABTest])
async def get_ab_tests(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ABTestModel)
    
    if is_active is not None:
        query = query.filter(ABTestModel.is_active == is_active)
    
    tests = query.all()
    return [ABTest.from_orm(test) for test in tests]


@router.get("/{test_id}", response_model=ABTest)
async def get_ab_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(ABTestModel).filter(ABTestModel.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    return ABTest.from_orm(test)


@router.post("/", response_model=ABTest)
async def create_ab_test(
    ab_test: ABTestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    screen = db.query(ScreenModel).filter(ScreenModel.id == ab_test.screen_id).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    existing_test = db.query(ABTestModel).filter(ABTestModel.name == ab_test.name).first()
    if existing_test:
        raise HTTPException(status_code=400, detail="A/B test with this name already exists")
    
    db_test = ABTestModel(**ab_test.dict())
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    
    background_tasks.add_task(invalidate_ab_test_cache)
    
    return ABTest.from_orm(db_test)


@router.put("/{test_id}", response_model=ABTest)
async def update_ab_test(
    test_id: int,
    test_update: ABTestUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_test = db.query(ABTestModel).filter(ABTestModel.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    update_data = test_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_test, field, value)
    
    db.commit()
    db.refresh(db_test)
    
    background_tasks.add_task(invalidate_ab_test_cache)
    
    return ABTest.from_orm(db_test)


@router.delete("/{test_id}")
async def delete_ab_test(
    test_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_test = db.query(ABTestModel).filter(ABTestModel.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    db.delete(db_test)
    db.commit()
    
    background_tasks.add_task(invalidate_ab_test_cache)
    
    return {"message": "A/B test deleted successfully"}


@router.post("/{test_id}/activate")
async def activate_ab_test(
    test_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_test = db.query(ABTestModel).filter(ABTestModel.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    db_test.is_active = True
    if not db_test.start_date:
        db_test.start_date = datetime.utcnow()
    
    db.commit()
    db.refresh(db_test)
    
    background_tasks.add_task(invalidate_ab_test_cache)
    
    return {"message": "A/B test activated successfully"}


@router.post("/{test_id}/deactivate")
async def deactivate_ab_test(
    test_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_test = db.query(ABTestModel).filter(ABTestModel.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    db_test.is_active = False
    if not db_test.end_date:
        db_test.end_date = datetime.utcnow()
    
    db.commit()
    db.refresh(db_test)
    
    background_tasks.add_task(invalidate_ab_test_cache)
    
    return {"message": "A/B test deactivated successfully"}


@router.get("/screen/{screen_identifier}/variant")
async def get_screen_variant(
    screen_identifier: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    platform: str = "web",
    locale: str = "ru",
    db: Session = Depends(get_db)
):
    # First, find the screen by identifier (could be ID or name)
    screen = None
    if screen_identifier.isdigit():
        # If identifier is numeric, treat as ID
        screen = db.query(ScreenModel).filter(ScreenModel.id == int(screen_identifier)).first()
    else:
        # Otherwise, treat as name - try exact match first
        screen = db.query(ScreenModel).filter(
            ScreenModel.name == screen_identifier,
            ScreenModel.platform == platform,
            ScreenModel.locale == locale,
            ScreenModel.is_active == True
        ).first()
        
        # If not found and locale is 'en', try with _en suffix
        if not screen and locale == 'en':
            screen = db.query(ScreenModel).filter(
                ScreenModel.name == f"{screen_identifier}_en",
                ScreenModel.platform == platform,
                ScreenModel.locale == locale,
                ScreenModel.is_active == True
            ).first()
        
        # If still not found, try fallback to Russian version
        if not screen:
            screen = db.query(ScreenModel).filter(
                ScreenModel.name == screen_identifier,
                ScreenModel.platform == platform,
                ScreenModel.locale == "ru",
                ScreenModel.is_active == True
            ).first()
    
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    cache_key = f"ab_variant:{screen.id}:{user_id}:{session_id}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    active_test = db.query(ABTestModel).filter(
        ABTestModel.screen_id == screen.id,
        ABTestModel.is_active == True
    ).first()
    
    if not active_test:
        result = {
            "variant": "control",
            "config": screen.config,
            "test_id": None
        }
    else:
        identifier = user_id or session_id or str(random.random())
        hash_value = int(hashlib.md5(f"{active_test.id}:{identifier}".encode()).hexdigest(), 16)
        
        if (hash_value % 100) / 100 < active_test.traffic_allocation:
            variant_keys = list(active_test.variants.keys())
            variant_index = hash_value % len(variant_keys)
            variant_key = variant_keys[variant_index]
            
            result = {
                "variant": variant_key,
                "config": active_test.variants[variant_key],
                "test_id": active_test.id
            }
        else:
            result = {
                "variant": "control",
                "config": screen.config,
                "test_id": active_test.id
            }
    
    await cache.set(cache_key, result, ttl=3600)
    return result


async def invalidate_ab_test_cache():
    await cache.invalidate_pattern("ab_variant:*")





