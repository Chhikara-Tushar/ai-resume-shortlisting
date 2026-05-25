from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, MeResponse
from app.services.auth_service import register_user, login_user, refresh_tokens

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await register_user(data, db)
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        role=result["user"].role,
        user_id=result["user"].id,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await login_user(data, db)
    return TokenResponse(**result)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    result = await refresh_tokens(data.refresh_token, db)
    return TokenResponse(**result)


@router.get("/me")
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    profile = None
    if current_user.role == "candidate":
        from app.models.candidate import CandidateProfile
        r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
        p = r.scalar_one_or_none()
        if p:
            profile = {
                "id": p.id, "phone": p.phone, "location": p.location,
                "linkedin_url": p.linkedin_url, "github_url": p.github_url,
                "experience_years": p.experience_years, "ats_score": p.ats_score,
                "resume_path": p.resume_path,
            }
    elif current_user.role == "recruiter":
        from app.models.recruiter import RecruiterProfile
        r = await db.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == current_user.id))
        p = r.scalar_one_or_none()
        if p:
            profile = {
                "id": p.id, "company_name": p.company_name,
                "department": p.department, "phone": p.phone, "bio": p.bio,
            }
    return {
        "user": {
            "id": current_user.id, "email": current_user.email,
            "full_name": current_user.full_name, "role": current_user.role,
            "is_active": current_user.is_active,
        },
        "profile": profile,
    }
