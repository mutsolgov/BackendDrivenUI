from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Screen(Base):
    __tablename__ = "screens"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    config = Column(JSON)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    platform = Column(String, default="web")
    locale = Column(String, default="ru")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    analytics = relationship("Analytics", back_populates="screen")
    ab_tests = relationship("ABTest", back_populates="screen")


class Component(Base):
    __tablename__ = "components"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)
    config = Column(JSON)
    props_schema = Column(JSON)
    is_system = Column(Boolean, default=False)
    category = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    screen_id = Column(Integer, ForeignKey("screens.id"))
    component_id = Column(String)
    event_type = Column(String)
    user_id = Column(String)
    session_id = Column(String)
    platform = Column(String)
    locale = Column(String)
    data = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    screen = relationship("Screen", back_populates="analytics")


class ABTest(Base):
    __tablename__ = "ab_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    screen_id = Column(Integer, ForeignKey("screens.id"))
    variants = Column(JSON)
    traffic_allocation = Column(Float, default=0.5)
    is_active = Column(Boolean, default=False)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    screen = relationship("Screen", back_populates="ab_tests")


