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

@analytics_router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    all_events = db.query(Analytics).all()
    
    unique_screens = len(set([e.screen_id for e in all_events]))
    unique_users = len(set([e.user_id for e in all_events if e.user_id]))
    
    screen_views = {}
    for e in all_events:
        if e.event_type == "view":
            screen_views[e.screen_id] = screen_views.get(e.screen_id, 0) + 1
    
    top_screens = [{"screen_id": k, "views": v} for k, v in screen_views.items()]
    
    return {
        "total_events": len(all_events),
        "unique_screens": unique_screens,
        "unique_users": unique_users,
        "top_screens": top_screens,
        "daily_stats": []
    }

app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])


ab_testing_router = APIRouter()

class ABTestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    screen_id: int
    variants: dict
    traffic_allocation: float = 0.5
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ABTestUpdate(BaseModel):
    description: Optional[str] = None
    traffic_allocation: Optional[float] = None
    is_active: Optional[bool] = None

@ab_testing_router.post("/")
def create_ab_test(test: ABTestCreate, db: Session = Depends(get_db)):
    screen = db.query(Screen).filter(Screen.id == test.screen_id).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    existing = db.query(ABTest).filter(ABTest.name == test.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="A/B test with this name already exists")
    
    db_test = ABTest(**test.model_dump())
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

@ab_testing_router.get("/{test_id}")
def get_ab_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return test

@ab_testing_router.get("/")
def get_ab_tests(is_active: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(ABTest)
    if is_active is not None:
        query = query.filter(ABTest.is_active == is_active)
    return query.all()

@ab_testing_router.put("/{test_id}")
def update_ab_test(test_id: int, test: ABTestUpdate, db: Session = Depends(get_db)):
    db_test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    update_data = test.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_test, key, value)
    
    db.commit()
    db.refresh(db_test)
    return db_test

@ab_testing_router.post("/{test_id}/activate")
def activate_ab_test(test_id: int, db: Session = Depends(get_db)):
    db_test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    db_test.is_active = True
    db.commit()
    db.refresh(db_test)
    return db_test

@ab_testing_router.post("/{test_id}/deactivate")
def deactivate_ab_test(test_id: int, db: Session = Depends(get_db)):
    db_test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    db_test.is_active = False
    db.commit()
    db.refresh(db_test)
    return db_test

@ab_testing_router.delete("/{test_id}")
def delete_ab_test(test_id: int, db: Session = Depends(get_db)):
    db_test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    db.delete(db_test)
    db.commit()
    return {"message": "A/B test deleted successfully"}

@ab_testing_router.get("/screen/{screen_identifier}/variant")
def get_screen_variant(screen_identifier: int, user_id: Optional[str] = None, session_id: Optional[str] = None, db: Session = Depends(get_db)):
    screen = db.query(Screen).filter(Screen.id == screen_identifier).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    active_test = db.query(ABTest).filter(
        ABTest.screen_id == screen_identifier,
        ABTest.is_active == True
    ).first()
    
    if not active_test:
        return {
            "variant": "control",
            "config": screen.config,
            "test_id": None
        }
    
    seed = f"{user_id or session_id or ''}{active_test.id}"
    variant_hash = hash(seed) % 100
    
    if variant_hash < active_test.traffic_allocation * 100:
        variant_keys = list(active_test.variants.keys())
        variant_index = hash(seed + "variant") % len(variant_keys)
        variant_name = variant_keys[variant_index]
        return {
            "variant": variant_name,
            "config": active_test.variants[variant_name],
            "test_id": active_test.id
        }
    else:
        return {
            "variant": "control",
            "config": screen.config,
            "test_id": active_test.id
        }

app.include_router(ab_testing_router, prefix="/api/ab-testing", tags=["ab-testing"])


templates_router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: dict
    category: str = "general"
    is_public: bool = True
    parent_id: Optional[int] = None

class TemplateUpdate(BaseModel):
    description: Optional[str] = None
    config: Optional[dict] = None
    is_public: Optional[bool] = None

@templates_router.post("/")
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    existing = db.query(Template).filter(Template.name == template.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    db_template = Template(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@templates_router.get("/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@templates_router.get("/")
def get_templates(category: Optional[str] = None, is_public: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(Template)
    if category:
        query = query.filter(Template.category == category)
    if is_public is not None:
        query = query.filter(Template.is_public == is_public)
    return query.all()

@templates_router.put("/{template_id}")
def update_template(template_id: int, template: TemplateUpdate, db: Session = Depends(get_db)):
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = template.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_template, key, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template

@templates_router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    children = db.query(Template).filter(Template.parent_id == template_id).first()
    if children:
        raise HTTPException(status_code=400, detail="Cannot delete template with children")
    
    db.delete(db_template)
    db.commit()
    return {"message": "Template deleted successfully"}

@templates_router.post("/{template_id}/inherit")
def inherit_template(template_id: int, new_name: str, db: Session = Depends(get_db)):
    parent = db.query(Template).filter(Template.id == template_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Template not found")
    
    new_template = Template(
        name=new_name,
        description=parent.description,
        config=parent.config,
        category=parent.category,
        is_public=False,
        parent_id=parent.id
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template

@templates_router.get("/categories/list")
def get_template_categories(db: Session = Depends(get_db)):
    templates = db.query(Template).all()
    categories = list(set([t.category for t in templates]))
    return categories

app.include_router(templates_router, prefix="/api/templates", tags=["templates"])


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_screen_data():
    """Sample screen data for testing"""
    return {
        "name": "test_screen",
        "title": "Test Screen",
        "description": "A test screen",
        "config": {
            "components": [
                {
                    "id": "header",
                    "type": "Text",
                    "props": {
                        "content": "Hello World",
                        "variant": "h1"
                    }
                }
            ]
        },
        "platform": "web",
        "locale": "ru"
    }


@pytest.fixture
def sample_component_data():
    """Sample component data for testing"""
    return {
        "name": "TestButton",
        "type": "button",
        "category": "basic",
        "config": {
            "defaultProps": {
                "text": "Click me",
                "variant": "primary"
            }
        },
        "props_schema": {
            "text": {"type": "string", "required": True},
            "variant": {"type": "enum", "values": ["primary", "secondary"]}
        }
    }


@pytest.fixture
def sample_analytics_data():
    """Sample analytics event data"""
    return {
        "screen_id": 1,
        "component_id": "button_1",
        "event_type": "click",
        "user_id": "user_123",
        "session_id": "session_456",
        "platform": "web",
        "locale": "ru",
        "data": {"extra": "info"}
    }


