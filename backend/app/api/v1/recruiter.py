from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import require_recruiter
from app.models.user import User
from app.models.recruiter import RecruiterProfile
from app.models.job import Job
from app.models.application import Application
from app.models.skill import Skill

router = APIRouter()


@router.get("/dashboard")
async def recruiter_dashboard(
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    total_jobs = (await db.execute(select(func.count(Job.id)).where(Job.recruiter_id == profile.id))).scalar() or 0
    active_jobs = (await db.execute(select(func.count(Job.id)).where(Job.recruiter_id == profile.id, Job.status == "active"))).scalar() or 0

    job_ids_result = await db.execute(select(Job.id).where(Job.recruiter_id == profile.id))
    job_ids = [r[0] for r in job_ids_result.all()]

    total_applicants = 0
    shortlisted = 0
    if job_ids:
        total_applicants = (await db.execute(select(func.count(Application.id)).where(Application.job_id.in_(job_ids)))).scalar() or 0
        shortlisted = (await db.execute(select(func.count(Application.id)).where(Application.job_id.in_(job_ids), Application.status == "shortlisted"))).scalar() or 0

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applicants": total_applicants,
        "shortlisted": shortlisted,
        "company_name": profile.company_name,
        "recruiter_name": current_user.full_name,
    }


@router.put("/profile")
async def update_profile(
    data: dict,
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    allowed = {"company_name", "department", "phone", "bio"}
    for key, value in data.items():
        if key in allowed:
            setattr(profile, key, value)

    if "full_name" in data:
        current_user.full_name = data["full_name"]

    await db.commit()
    return {"message": "Profile updated"}


@router.get("/skills/suggest")
async def suggest_skills(q: str = "", db: AsyncSession = Depends(get_db)):
    query = select(Skill).where(Skill.normalized_name.ilike(f"%{q.lower()}%")).limit(20)
    result = await db.execute(query)
    skills = result.scalars().all()
    return [{"id": s.id, "name": s.name, "category": s.category} for s in skills]
