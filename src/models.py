import uuid
from pydantic import BaseModel, Field
from datetime import datetime, time
from typing import Optional, List, Dict


class KeyboardInput(BaseModel):
    timestamp: datetime = Field(...)
    key_value: str = Field(...)


class MouseInput(BaseModel):
    timestamp: datetime = Field(...)
    x: int = Field(...)
    y: int = Field(...)
    right_click: bool = Field(...)
    left_click: bool = Field(...)
    scroll: int = Field(...)


class ApplicationData(BaseModel):
    timestamp: datetime = Field(...)
    focused_app: str = Field(...)
    visible_apps: list = Field(...)


class ClickCount(BaseModel):
    left_click: int = Field(...)
    right_click: int = Field(...)
    
class KeypressCount(BaseModel):
    total: int = Field(...)
    


class Settings(BaseModel):
    timestamp: datetime = Field(...)
    daily_clicking_limit: int = Field(...)
    extra_clicking_limit: Optional[Dict[str, int]] = None
    daily_typing_limit: int = Field(...)
    extra_typing_limit: Optional[Dict[str, int]] = None
    inactivity_limit: time = Field(...)
