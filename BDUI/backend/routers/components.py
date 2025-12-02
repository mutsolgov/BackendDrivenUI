from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Component as ComponentModel
from schemas import Component, ComponentCreate, ComponentUpdate
from cache import cache

router = APIRouter()


@router.get("/", response_model=List[Component])
async def get_components(
    category: Optional[str] = None,
    component_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    cache_key = f"components:{category}:{component_type}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return [Component(**comp) for comp in cached_result]
    
    query = db.query(ComponentModel)
    
    if category:
        query = query.filter(ComponentModel.category == category)
    if component_type:
        query = query.filter(ComponentModel.type == component_type)
    
    components = query.all()
    result = [Component.from_orm(component) for component in components]
    
    await cache.set(cache_key, [comp.dict() for comp in result])
    return result


@router.get("/{component_id}", response_model=Component)
async def get_component(component_id: int, db: Session = Depends(get_db)):
    cache_key = f"component:{component_id}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return Component(**cached_result)
    
    component = db.query(ComponentModel).filter(ComponentModel.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    result = Component.from_orm(component)
    await cache.set(cache_key, result.dict())
    return result


@router.post("/", response_model=Component)
async def create_component(
    component: ComponentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing_component = db.query(ComponentModel).filter(ComponentModel.name == component.name).first()
    if existing_component:
        raise HTTPException(status_code=400, detail="Component already exists")
    
    db_component = ComponentModel(**component.dict())
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    
    background_tasks.add_task(invalidate_component_cache)
    
    return Component.from_orm(db_component)



