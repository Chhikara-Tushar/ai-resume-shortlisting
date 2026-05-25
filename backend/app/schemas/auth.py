from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "candidate"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("candidate", "recruiter"):
            raise ValueError("Role must be candidate or recruiter")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user_id: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RecruiterProfileOut(BaseModel):
    id: str
    company_name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True


class CandidateProfileOut(BaseModel):
    id: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    experience_years: float = 0.0
    ats_score: float = 0.0
    resume_path: Optional[str] = None

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    user: UserOut
    profile: Optional[dict] = None
