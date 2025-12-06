"""
Pytest configuration and fixtures for BDUI backend tests
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON
from datetime import datetime

class Screen(Base):
    __tablename__ = "screens"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    config = Column(JSON)
    platform = Column(String, default="web")
    locale = Column(String, default="ru")
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Component(Base):
    __tablename__ = "components"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)
    config = Column(JSON)
    props_schema = Column(JSON, default={})
    category = Column(String, default="basic")
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, index=True)
    screen_id = Column(Integer)
    component_id = Column(String, nullable=True)
    event_type = Column(String)
    user_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    platform = Column(String, default="web")
    locale = Column(String, default="ru")
    data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ABTest(Base):
    __tablename__ = "ab_tests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    screen_id = Column(Integer)
    variants = Column(JSON)
    traffic_allocation = Column(Float, default=0.5)
    is_active = Column(Boolean, default=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    config = Column(JSON)
    category = Column(String, default="general")
    is_public = Column(Boolean, default=True)
    parent_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Database dependency for tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

import time

class MockCache:
    def __init__(self):
        self.storage = {}
        self.ttls = {}
        self.set_times = {}
    
    async def get(self, key):
        if key in self.storage:
            if key in self.ttls:
                elapsed = time.time() - self.set_times[key]
                if elapsed > self.ttls[key]:
                    await self.delete(key)
                    return None
            return self.storage[key]
        return None
    
    async def set(self, key, value, ttl=3600):
        self.storage[key] = value
        self.ttls[key] = ttl
        self.set_times[key] = time.time()
    
    async def delete(self, key):
        if key in self.storage:
            del self.storage[key]
        if key in self.ttls:
            del self.ttls[key]
        if key in self.set_times:
            del self.set_times[key]
    
    async def invalidate_pattern(self, pattern):
        keys_to_delete = [k for k in self.storage.keys() if pattern in k]
        for key in keys_to_delete:
            await self.delete(key)

mock_cache = MockCache()
sys.modules['cache'] = type(sys)('cache')
sys.modules['cache'].cache = mock_cache

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel

class ScreenCreate(BaseModel):
    name: str
    title: str
    description: Optional[str] = None
    config: dict
    platform: str = "web"
    locale: str = "ru"

class ScreenUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None
    platform: Optional[str] = None
    locale: Optional[str] = None
    is_active: Optional[bool] = None

screens_router = APIRouter()

@screens_router.post("/")
def create_screen(screen: ScreenCreate, db: Session = Depends(get_db)):
    existing = db.query(Screen).filter(Screen.name == screen.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Screen with this name already exists")
    
    db_screen = Screen(**screen.model_dump())
    db.add(db_screen)
    db.commit()
    db.refresh(db_screen)
    return db_screen

@screens_router.get("/{screen_id}")
def get_screen(screen_id: int, db: Session = Depends(get_db)):
    screen = db.query(Screen).filter(Screen.id == screen_id).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    return screen

@screens_router.get("/")
def get_screens(platform: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Screen)
    if platform:
        query = query.filter(Screen.platform == platform)
    return query.all()

@screens_router.get("/by-name/{name}")
def get_screen_by_name(name: str, db: Session = Depends(get_db)):
    screen = db.query(Screen).filter(Screen.name == name).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    return screen

@screens_router.put("/{screen_id}")
def update_screen(screen_id: int, screen: ScreenUpdate, db: Session = Depends(get_db)):
    db_screen = db.query(Screen).filter(Screen.id == screen_id).first()
    if not db_screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    update_data = screen.model_dump(exclude_unset=True)
    if 'config' in update_data and update_data['config'] != db_screen.config:
        db_screen.version += 1
    
    for key, value in update_data.items():
        setattr(db_screen, key, value)
    
    db.commit()
    db.refresh(db_screen)
    return db_screen

@screens_router.delete("/{screen_id}")
def delete_screen(screen_id: int, db: Session = Depends(get_db)):
    db_screen = db.query(Screen).filter(Screen.id == screen_id).first()
    if not db_screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    db.delete(db_screen)
    db.commit()
    return {"message": "Screen deleted successfully"}

@screens_router.post("/{screen_id}/duplicate")
def duplicate_screen(screen_id: int, new_name: str, db: Session = Depends(get_db)):
    original = db.query(Screen).filter(Screen.id == screen_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    new_screen = Screen(
        name=new_name,
        title=f"{original.title} (Copy)",
        description=original.description,
        config=original.config,
        platform=original.platform,
        locale=original.locale,
        is_active=False
    )
    db.add(new_screen)
    db.commit()
    db.refresh(new_screen)
    return new_screen

app.include_router(screens_router, prefix="/api/screens", tags=["screens"])


components_router = APIRouter()

class ComponentCreate(BaseModel):
    name: str
    type: str
    category: str = "basic"
    config: dict
    props_schema: dict = {}

class ComponentUpdate(BaseModel):
    config: Optional[dict] = None
    props_schema: Optional[dict] = None
    category: Optional[str] = None

@components_router.post("/")
def create_component(component: ComponentCreate, db: Session = Depends(get_db)):
    existing = db.query(Component).filter(Component.name == component.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Component with this name already exists")
    
    db_component = Component(**component.model_dump())
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    return db_component

@components_router.get("/{component_id}")
def get_component(component_id: int, db: Session = Depends(get_db)):
    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return component

@components_router.get("/")
def get_components(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Component)
    if category:
        query = query.filter(Component.category == category)
    return query.all()

@components_router.put("/{component_id}")
def update_component(component_id: int, component: ComponentUpdate, db: Session = Depends(get_db)):
    db_component = db.query(Component).filter(Component.id == component_id).first()
    if not db_component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    update_data = component.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_component, key, value)
    
    db.commit()
    db.refresh(db_component)
    return db_component

@components_router.delete("/{component_id}")
def delete_component(component_id: int, db: Session = Depends(get_db)):
    db_component = db.query(Component).filter(Component.id == component_id).first()
    if not db_component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    if db_component.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system component")
    
    db.delete(db_component)
    db.commit()
    return {"message": "Component deleted successfully"}

@components_router.get("/categories/list")
def get_component_categories(db: Session = Depends(get_db)):
    components = db.query(Component).all()
    categories = list(set([c.category for c in components]))
    return categories

app.include_router(components_router, prefix="/api/components", tags=["components"])


analytics_router = APIRouter()

class AnalyticsEventCreate(BaseModel):
    screen_id: int
    component_id: Optional[str] = None
    event_type: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    platform: str = "web"
    locale: str = "ru"
    data: Optional[dict] = None

@analytics_router.post("/track")
def track_event(event: AnalyticsEventCreate, db: Session = Depends(get_db)):
    db_event = Analytics(**event.model_dump())
    db.add(db_event)
    db.commit()
    return {"message": "Event tracked successfully"}

@analytics_router.get("/events")
def get_events(
    screen_id: Optional[int] = None,
    event_type: Optional[str] = None,
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Analytics)
    if screen_id:
        query = query.filter(Analytics.screen_id == screen_id)
    if event_type:
        query = query.filter(Analytics.event_type == event_type)
    if platform:
        query = query.filter(Analytics.platform == platform)
    return query.all()

@analytics_router.get("/events/count")
def get_events_count(screen_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Analytics)
    if screen_id:
        query = query.filter(Analytics.screen_id == screen_id)
    return {"total": query.count()}

@analytics_router.get("/stats/{screen_id}")
def get_screen_stats(screen_id: int, db: Session = Depends(get_db)):
    events = db.query(Analytics).filter(Analytics.screen_id == screen_id).all()
    
    views = [e for e in events if e.event_type == "view"]
    unique_users = len(set([e.user_id for e in events if e.user_id]))
    
    component_clicks = {}
    for e in events:
        if e.component_id and e.event_type == "click":
            component_clicks[e.component_id] = component_clicks.get(e.component_id, 0) + 1
    
    most_used = [{"component_id": k, "clicks": v} for k, v in component_clicks.items()]
    
    platform_breakdown = {}
    for e in events:
        platform_breakdown[e.platform] = platform_breakdown.get(e.platform, 0) + 1
    
    locale_breakdown = {}
    for e in events:
        locale_breakdown[e.locale] = locale_breakdown.get(e.locale, 0) + 1
    
    return {
        "total_views": len(views),
        "unique_users": unique_users,
        "avg_session_duration": 0,
        "most_used_components": most_used,
        "platform_breakdown": platform_breakdown,
        "locale_breakdown": locale_breakdown
    }

