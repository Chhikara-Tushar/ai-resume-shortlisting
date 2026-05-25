from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


class UserAdminOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsOverview(BaseModel):
    total_users: int
    total_candidates: int
    total_recruiters: int
    total_jobs: int
    total_applications: int
    active_jobs: int
    avg_ai_score: float


class ActivityTrend(BaseModel):
    date: str
    new_users: int
    new_jobs: int
    new_applications: int


class RecruiterSummary(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: str
    company_name: Optional[str]
    job_count: int
    application_count: int
    created_at: datetime


class SettingOut(BaseModel):
    key: str
    value: Optional[str]
    description: Optional[str]


class SettingsUpdate(BaseModel):
    settings: Dict[str, str]
