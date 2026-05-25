from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import require_recruiter, get_current_user
from app.models.user import User
from app.models.job import Job, JobSkill
from app.models.skill import Skill
from app.models.application import Application
from app.models.candidate import CandidateProfile, CandidateSkill
from app.schemas.job import JobCreate, JobUpdate, JobOut, RankedCandidate
from app.ai.ranking_engine import score_candidate, rank_results
from app.ai.embeddings import embed_text
from app.ai.vector_store import vector_store

router = APIRouter()


async def _get_or_create_skill(name: str, db: AsyncSession) -> Skill:
    normalized = name.lower().strip()
    result = await db.execute(select(Skill).where(Skill.normalized_name == normalized))
    skill = result.scalar_one_or_none()
    if not skill:
        skill = Skill(name=name, normalized_name=normalized)
        db.add(skill)
        await db.flush()
    return skill


async def _build_job_out(job: Job, db: AsyncSession) -> dict:
    app_count = (await db.execute(select(func.count(Application.id)).where(Application.job_id == job.id))).scalar() or 0
    skills = []
    for js in job.skills:
        skills.append({"id": js.skill_id, "name": js.skill.name if js.skill else "", "category": None, "importance": js.importance, "weight": js.weight})
    return {
        "id": job.id, "title": job.title, "description": job.description,
        "company": job.company, "location": job.location, "job_type": job.job_type,
        "experience_required": job.experience_required, "salary_min": job.salary_min,
        "salary_max": job.salary_max, "status": job.status, "created_at": job.created_at,
        "skills": skills, "application_count": app_count,
    }


@router.post("", status_code=201)
async def create_job(
    data: JobCreate,
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    from app.models.recruiter import RecruiterProfile
    r = await db.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Recruiter profile not found")

    job = Job(
        recruiter_id=profile.id, title=data.title, description=data.description,
        company=data.company or profile.company_name, location=data.location,
        job_type=data.job_type, experience_required=data.experience_required,
        salary_min=data.salary_min, salary_max=data.salary_max,
    )
    db.add(job)
    await db.flush()

    for skill_in in data.skills:
        skill = await _get_or_create_skill(skill_in.name, db)
        db.add(JobSkill(job_id=job.id, skill_id=skill.id, importance=skill_in.importance, weight=skill_in.weight))

    await db.commit()
    await db.refresh(job)

    # Generate and store job embedding
    try:
        job_text = f"{job.title} {job.description} {' '.join(s.name for s in data.skills)}"
        embedding = embed_text(job_text)
        vector_store.upsert_job(job.id, embedding)
    except Exception:
        pass

    return {"id": job.id, "message": "Job created successfully"}


@router.get("")
async def list_jobs(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Job)
    if current_user.role in ("recruiter",):
        from app.models.recruiter import RecruiterProfile
        r = await db.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == current_user.id))
        profile = r.scalar_one_or_none()
        if profile:
            q = q.where(Job.recruiter_id == profile.id)
    elif current_user.role == "candidate":
        q = q.where(Job.status == "active")

    if status:
        q = q.where(Job.status == status)

    q = q.order_by(Job.created_at.desc())
    result = await db.execute(q)
    jobs = result.scalars().all()

    job_list = []
    for job in jobs:
        app_count = (await db.execute(select(func.count(Application.id)).where(Application.job_id == job.id))).scalar() or 0
        job_list.append({
            "id": job.id, "title": job.title, "company": job.company,
            "location": job.location, "job_type": job.job_type, "status": job.status,
            "experience_required": job.experience_required,
            "salary_min": job.salary_min, "salary_max": job.salary_max,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "application_count": app_count,
        })
    return job_list


@router.get("/{job_id}")
async def get_job(job_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    skills_result = await db.execute(
        select(JobSkill, Skill).join(Skill).where(JobSkill.job_id == job_id)
    )
    skills = [{"name": s.name, "importance": js.importance, "weight": js.weight} for js, s in skills_result.all()]
    app_count = (await db.execute(select(func.count(Application.id)).where(Application.job_id == job_id))).scalar() or 0

    return {
        "id": job.id, "title": job.title, "description": job.description,
        "company": job.company, "location": job.location, "job_type": job.job_type,
        "experience_required": job.experience_required, "salary_min": job.salary_min,
        "salary_max": job.salary_max, "status": job.status,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "skills": skills, "application_count": app_count,
    }


@router.put("/{job_id}")
async def update_job(
    job_id: str,
    data: JobUpdate,
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    for field, value in data.model_dump(exclude_none=True, exclude={"skills"}).items():
        setattr(job, field, value)

    if data.skills is not None:
        await db.execute(select(JobSkill).where(JobSkill.job_id == job_id))
        for js in job.skills:
            await db.delete(js)
        await db.flush()
        for skill_in in data.skills:
            skill = await _get_or_create_skill(skill_in.name, db)
            db.add(JobSkill(job_id=job.id, skill_id=skill.id, importance=skill_in.importance, weight=skill_in.weight))

    await db.commit()
    return {"message": "Job updated"}


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, current_user: User = Depends(require_recruiter), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    job.status = "closed"
    await db.commit()


@router.get("/{job_id}/candidates")
async def get_ranked_candidates(
    job_id: str,
    min_score: float = Query(0, ge=0, le=100),
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    apps_result = await db.execute(
        select(Application, CandidateProfile, User)
        .join(CandidateProfile, CandidateProfile.id == Application.candidate_id)
        .join(User, User.id == CandidateProfile.user_id)
        .where(Application.job_id == job_id)
    )
    rows = apps_result.all()
    if not rows:
        return []

    job_skills_result = await db.execute(select(JobSkill, Skill).join(Skill).where(JobSkill.job_id == job_id))
    job_skills = [s.name for _, s in job_skills_result.all()]

    try:
        job_embedding = embed_text(f"{job.title} {job.description}")
    except Exception:
        job_embedding = None

    ranking_results = []
    for app, candidate, user in rows:
        cand_skills_result = await db.execute(
            select(Skill).join(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id)
        )
        cand_skills = [s.name for s in cand_skills_result.scalars().all()]

        try:
            result = score_candidate(
                candidate_id=candidate.id,
                resume_text=candidate.resume_text or "",
                job_description=job.description,
                candidate_skills=cand_skills,
                job_skills=job_skills,
                candidate_years=candidate.experience_years,
                required_years=job.experience_required,
                ats_score=candidate.ats_score,
                job_embedding=job_embedding,
            )
            ranking_results.append({
                "result": result, "app": app, "candidate": candidate,
                "user": user, "skills": cand_skills,
            })
        except Exception:
            pass

    ranked = rank_results([r["result"] for r in ranking_results])
    rank_map = {r.candidate_id: r for r in ranked}

    output = []
    for item in ranking_results:
        r = rank_map.get(item["candidate"].id)
        if not r:
            continue
        if r.ai_score < min_score:
            continue

        app = item["app"]
        app.ai_score = r.ai_score
        app.semantic_score = r.semantic_score
        app.skill_match_score = r.skill_match_score
        app.experience_score = r.experience_score
        app.overall_rank = r.rank

        output.append({
            "candidate_id": item["candidate"].id,
            "user_id": item["user"].id,
            "full_name": item["user"].full_name,
            "email": item["user"].email,
            "experience_years": item["candidate"].experience_years,
            "ats_score": item["candidate"].ats_score,
            "ai_score": r.ai_score,
            "semantic_score": r.semantic_score,
            "skill_match_score": r.skill_match_score,
            "experience_score": r.experience_score,
            "overall_rank": r.rank,
            "status": app.status,
            "skills": item["skills"][:8],
        })

    await db.commit()
    return sorted(output, key=lambda x: x["overall_rank"])


@router.post("/{job_id}/candidates/{candidate_id}/shortlist")
async def shortlist_candidate(
    job_id: str, candidate_id: str,
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Application).where(Application.job_id == job_id, Application.candidate_id == candidate_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    app.status = "shortlisted"
    await db.commit()
    return {"message": "Candidate shortlisted"}


@router.post("/{job_id}/candidates/{candidate_id}/reject")
async def reject_candidate(
    job_id: str, candidate_id: str,
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Application).where(Application.job_id == job_id, Application.candidate_id == candidate_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    app.status = "rejected"
    await db.commit()
    return {"message": "Candidate rejected"}


@router.get("/{job_id}/insights")
async def get_job_insights(
    job_id: str,
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    from app.models.application import AIInsight
    from app.ai.insights import generate_hiring_insights

    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    existing = await db.execute(
        select(AIInsight).where(AIInsight.job_id == job_id, AIInsight.insight_type == "hiring_insights")
        .order_by(AIInsight.created_at.desc()).limit(1)
    )
    cached = existing.scalar_one_or_none()
    if cached:
        return {"insights": cached.content, "job_id": job_id, "cached": True}

    apps_result = await db.execute(
        select(Application, CandidateProfile, User)
        .join(CandidateProfile, CandidateProfile.id == Application.candidate_id)
        .join(User, User.id == CandidateProfile.user_id)
        .where(Application.job_id == job_id)
        .order_by(Application.ai_score.desc()).limit(10)
    )
    candidates = [{"full_name": u.full_name, "ai_score": a.ai_score, "skills": []} for a, c, u in apps_result.all()]

    insights = await generate_hiring_insights(job.title, job.description, candidates)
    db.add(AIInsight(job_id=job_id, insight_type="hiring_insights", content=insights))
    await db.commit()
    return {"insights": insights, "job_id": job_id, "cached": False}


@router.get("/{job_id}/compare")
async def compare_candidates(
    job_id: str,
    ids: str = Query(..., description="Comma-separated candidate IDs"),
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    candidate_ids = [cid.strip() for cid in ids.split(",")][:5]
    comparison = []

    for cid in candidate_ids:
        result = await db.execute(
            select(CandidateProfile, User)
            .join(User, User.id == CandidateProfile.user_id)
            .where(CandidateProfile.id == cid)
        )
        row = result.first()
        if not row:
            continue
        profile, user = row

        app_result = await db.execute(
            select(Application).where(Application.candidate_id == cid, Application.job_id == job_id)
        )
        app = app_result.scalar_one_or_none()

        skills_result = await db.execute(select(Skill).join(CandidateSkill).where(CandidateSkill.candidate_id == cid))
        skills = [s.name for s in skills_result.scalars().all()]

        comparison.append({
            "candidate_id": cid,
            "full_name": user.full_name,
            "email": user.email,
            "experience_years": profile.experience_years,
            "ats_score": profile.ats_score,
            "ai_score": app.ai_score if app else 0,
            "status": app.status if app else "not_applied",
            "skills": skills,
            "education": profile.parsed_data.get("education", []) if profile.parsed_data else [],
            "location": profile.location,
        })

    return {"candidates": comparison, "job_id": job_id}
