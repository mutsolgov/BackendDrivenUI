from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Template as TemplateModel
from schemas import Template, TemplateCreate, TemplateUpdate
from cache import cache

router = APIRouter()


@router.get("/", response_model=List[Template])
async def get_templates(
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    cache_key = f"templates:{category}:{is_public}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return [Template(**tmpl) for tmpl in cached_result]
    
    query = db.query(TemplateModel)
    
    if category:
        query = query.filter(TemplateModel.category == category)
    if is_public is not None:
        query = query.filter(TemplateModel.is_public == is_public)
    
    templates = query.all()
    result = [Template.from_orm(template) for template in templates]
    
    await cache.set(cache_key, [tmpl.dict() for tmpl in result])
    return result


@router.get("/{template_id}", response_model=Template)
async def get_template(template_id: int, db: Session = Depends(get_db)):
    cache_key = f"template:{template_id}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return Template(**cached_result)
    
    template = db.query(TemplateModel).filter(TemplateModel.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    result = Template.from_orm(template)
    await cache.set(cache_key, result.dict())
    return result


@router.post("/", response_model=Template)
async def create_template(
    template: TemplateCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing_template = db.query(TemplateModel).filter(TemplateModel.name == template.name).first()
    if existing_template:
        raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    if template.parent_id:
        parent_template = db.query(TemplateModel).filter(TemplateModel.id == template.parent_id).first()
        if not parent_template:
            raise HTTPException(status_code=404, detail="Parent template not found")
    
    db_template = TemplateModel(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    background_tasks.add_task(invalidate_template_cache)
    
    return Template.from_orm(db_template)


@router.put("/{template_id}", response_model=Template)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_template = db.query(TemplateModel).filter(TemplateModel.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = template_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    
    background_tasks.add_task(invalidate_template_cache)
    
    return Template.from_orm(db_template)


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_template = db.query(TemplateModel).filter(TemplateModel.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    children = db.query(TemplateModel).filter(TemplateModel.parent_id == template_id).all()
    if children:
        raise HTTPException(status_code=400, detail="Cannot delete template with children")
    
    db.delete(db_template)
    db.commit()
    
    background_tasks.add_task(invalidate_template_cache)
    
    return {"message": "Template deleted successfully"}

