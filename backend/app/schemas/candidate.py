from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class CandidateProfileUpdate(BaseModel):
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    full_name: Optional[str] = None


class SkillAdd(BaseModel):
    name: str
    proficiency_level: str = "intermediate"
    years_of_experience: float = 0.0


class ATSScoreOut(BaseModel):
    total_score: float
    contact_info_score: float
    skills_score: float
    experience_score: float
    education_score: float
    formatting_score: float
    keyword_density_score: float
    recommendations: List[str]


class ResumeAnalysisOut(BaseModel):
    parsed_data: Dict[str, Any]
    summary: str
    extracted_skills: List[str]
    experience_years: float
    education: List[str]
    contact_info: Dict[str, Any]
    ats_score: ATSScoreOut


class ApplicationOut(BaseModel):
    id: str
    job_id: str
    job_title: str
    company: Optional[str]
    status: str
    ai_score: float
    overall_rank: Optional[int]
    applied_at: datetime

    class Config:
        from_attributes = True


class JobRecommendation(BaseModel):
    job_id: str
    title: str
    company: Optional[str]
    location: Optional[str]
    job_type: str
    experience_required: float
    match_score: float
    required_skills: List[str]
    matching_skills: List[str]
    missing_skills: List[str]


class SkillGapOut(BaseModel):
    job_id: Optional[str]
    job_title: Optional[str]
    candidate_skills: List[str]
    required_skills: List[str]
    matching_skills: List[str]
    missing_skills: List[str]
    match_percentage: float
    recommendations: List[str]


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
