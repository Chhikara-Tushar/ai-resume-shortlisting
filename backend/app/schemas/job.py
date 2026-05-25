from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SkillIn(BaseModel):
    name: str
    importance: str = "required"
    weight: float = 1.0


class JobCreate(BaseModel):
    title: str
    description: str
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: str = "full_time"
    experience_required: float = 0.0
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    skills: List[SkillIn] = []


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_required: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    status: Optional[str] = None
    skills: Optional[List[SkillIn]] = None


class SkillOut(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    importance: str
    weight: float

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    id: str
    title: str
    description: str
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: str
    experience_required: float
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    status: str
    created_at: datetime
    skills: List[SkillOut] = []
    application_count: int = 0

    class Config:
        from_attributes = True


class RankedCandidate(BaseModel):
    candidate_id: str
    user_id: str
    full_name: str
    email: str
    experience_years: float
    ats_score: float
    ai_score: float
    semantic_score: float
    skill_match_score: float
    experience_score: float
    overall_rank: int
    status: str
    skills: List[str] = []


class CompareRequest(BaseModel):
    candidate_ids: List[str]
