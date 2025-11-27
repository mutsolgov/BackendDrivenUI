from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ComponentBase(BaseModel):
    name: str
    type: str
    config: Dict[str, Any]
    props_schema: Optional[Dict[str, Any]] = None
    category: Optional[str] = None


class ComponentCreate(ComponentBase):
    pass


class ComponentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    props_schema: Optional[Dict[str, Any]] = None
    category: Optional[str] = None


class Component(ComponentBase):
    id: int
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScreenBase(BaseModel):
    name: str
    title: str
    description: Optional[str] = None
    config: Dict[str, Any]
    platform: str = "web"
    locale: str = "ru"


class ScreenCreate(ScreenBase):
    pass


class ScreenUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    platform: Optional[str] = None
    locale: Optional[str] = None
    is_active: Optional[bool] = None


class Screen(ScreenBase):
    id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalyticsEvent(BaseModel):
    screen_id: int
    component_id: Optional[str] = None
    event_type: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    platform: str = "web"
    locale: str = "ru"
    data: Optional[Dict[str, Any]] = None


class Analytics(BaseModel):
    id: int
    screen_id: int
    component_id: Optional[str] = None
    event_type: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    platform: str
    locale: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ABTestBase(BaseModel):
    name: str
    description: Optional[str] = None
    screen_id: int
    variants: Dict[str, Any]
    traffic_allocation: float = 0.5


class ABTestCreate(ABTestBase):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ABTestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    variants: Optional[Dict[str, Any]] = None
    traffic_allocation: Optional[float] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ABTest(ABTestBase):
    id: int
    is_active: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]
    category: Optional[str] = None
    is_public: bool = True


class TemplateCreate(TemplateBase):
    parent_id: Optional[int] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None


class Template(TemplateBase):
    id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalyticsStats(BaseModel):
    total_views: int
    unique_users: int
    avg_session_duration: float
    most_used_components: List[Dict[str, Any]]
    active_components_count: Optional[int] = None  
    platform_breakdown: Dict[str, int]
    locale_breakdown: Dict[str, int]





