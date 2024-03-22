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
    middle_click: bool = Field(...)
    scroll: int = Field(...)


class ApplicationData(BaseModel):
    timestamp: datetime = Field(...)
    focused_app: str = Field(...)
    visible_apps: list = Field(...)


class ClickCount(BaseModel):
    right: int = Field(...)
    left: int = Field(...)
    middle: int = Field(...)
    total: int = Field(...)


class KeypressCount(BaseModel):
    total: int = Field(...)


class Stats(BaseModel):
    max: int = Field(...)
    mean: float = Field(...)
    std: float = Field(...)
    sum: int = Field(...)
    active_time: int = Field(...)


class WindowData(BaseModel):
    size: int = Field(...)
    mouse_stats: Stats = Field(...)
    mouse_data: List[int] = Field(...)
    keyboard_stats: Stats = Field(...)
    keyboard_data: List[int] = Field(...)


class DailySummary(BaseModel):
    date: str = Field(...)
    complete: bool = Field(...)
    window_sizes: List[int] = Field(...)
    inactive_limit: int = Field(...)
    mouse_active: int = Field(...)
    keyboard_active: int = Field(...)
    total_active: int = Field(...)
    time_data: List[datetime] = Field(...)
    window_data: List[WindowData] = Field(...)


class Settings(BaseModel):
    timestamp: datetime = Field(...)
    daily_clicking_limit: int = Field(...)
    extra_clicking_limit: Optional[Dict[str, int]] = None
    daily_typing_limit: int = Field(...)
    extra_typing_limit: Optional[Dict[str, int]] = None
    inactivity_limit: time = Field(...)


class RecentData(BaseModel):
    clicks: List[int] = Field(...)
    keypresses: List[int] = Field(...)
