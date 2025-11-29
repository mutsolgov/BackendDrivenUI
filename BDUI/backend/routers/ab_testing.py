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


