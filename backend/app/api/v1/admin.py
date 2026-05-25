from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.security import hash_password
from app.models.user import User
from app.models.recruiter import RecruiterProfile
from app.models.candidate import CandidateProfile
from app.models.job import Job
from app.models.application import Application, SystemSetting
from app.schemas.admin import (
    UserCreate, UserUpdate, UserAdminOut, AnalyticsOverview,
    ActivityTrend, RecruiterSummary, SettingOut, SettingsUpdate,
)

router = APIRouter()


@router.get("/users", response_model=List[UserAdminOut])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(User)
    if role:
        q = q.where(User.role == role)
    if search:
        q = q.where(User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
    q = q.offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/users", response_model=UserAdminOut, status_code=201)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    user = User(email=data.email, password_hash=hash_password(data.password), full_name=data.full_name, role=data.role)
    db.add(user)
    await db.flush()

    if data.role == "candidate":
        db.add(CandidateProfile(user_id=user.id))
    elif data.role == "recruiter":
        db.add(RecruiterProfile(user_id=user.id))

    await db.commit()
    await db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserAdminOut)
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.role is not None:
        user.role = data.role

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = False
    await db.commit()


@router.get("/analytics/overview", response_model=AnalyticsOverview)
async def analytics_overview(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_candidates = (await db.execute(select(func.count(User.id)).where(User.role == "candidate"))).scalar()
    total_recruiters = (await db.execute(select(func.count(User.id)).where(User.role == "recruiter"))).scalar()
    total_jobs = (await db.execute(select(func.count(Job.id)))).scalar()
    total_applications = (await db.execute(select(func.count(Application.id)))).scalar()
    active_jobs = (await db.execute(select(func.count(Job.id)).where(Job.status == "active"))).scalar()
    avg_score = (await db.execute(select(func.avg(Application.ai_score)).where(Application.ai_score > 0))).scalar() or 0.0

    return AnalyticsOverview(
        total_users=total_users,
        total_candidates=total_candidates,
        total_recruiters=total_recruiters,
        total_jobs=total_jobs,
        total_applications=total_applications,
        active_jobs=active_jobs,
        avg_ai_score=round(float(avg_score), 2),
    )


@router.get("/analytics/trends", response_model=List[ActivityTrend])
async def analytics_trends(
    days: int = 30,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    trends = []
    for i in range(days, 0, -5):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=5)
        new_users = (await db.execute(select(func.count(User.id)).where(User.created_at.between(start, end)))).scalar() or 0
        new_jobs = (await db.execute(select(func.count(Job.id)).where(Job.created_at.between(start, end)))).scalar() or 0
        new_apps = (await db.execute(select(func.count(Application.id)).where(Application.applied_at.between(start, end)))).scalar() or 0
        trends.append(ActivityTrend(date=date_str, new_users=new_users, new_jobs=new_jobs, new_applications=new_apps))
    return trends


@router.get("/recruiters", response_model=List[RecruiterSummary])
async def list_recruiters(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RecruiterProfile, User)
        .join(User, User.id == RecruiterProfile.user_id)
        .order_by(RecruiterProfile.created_at.desc())
    )
    rows = result.all()
    summaries = []
    for profile, user in rows:
        job_count = (await db.execute(select(func.count(Job.id)).where(Job.recruiter_id == profile.id))).scalar() or 0
        app_count = (await db.execute(
            select(func.count(Application.id)).join(Job).where(Job.recruiter_id == profile.id)
        )).scalar() or 0
        summaries.append(RecruiterSummary(
            id=profile.id, user_id=user.id, full_name=user.full_name,
            email=user.email, company_name=profile.company_name,
            job_count=job_count, application_count=app_count, created_at=user.created_at,
        ))
    return summaries


@router.get("/system/settings", response_model=List[SettingOut])
async def get_settings(current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemSetting))
    return result.scalars().all()


@router.put("/system/settings", status_code=200)
async def update_settings(
    data: SettingsUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    for key, value in data.settings.items():
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            db.add(SystemSetting(key=key, value=value))
    await db.commit()
    return {"message": "Settings updated"}
