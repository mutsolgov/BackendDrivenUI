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

