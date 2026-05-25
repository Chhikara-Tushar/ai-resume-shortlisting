import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import require_candidate
from app.core.config import settings
from app.models.user import User
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.skill import Skill
from app.models.job import Job, JobSkill
from app.models.application import Application
from app.schemas.candidate import CandidateProfileUpdate, SkillAdd

router = APIRouter()


@router.get("/profile")
async def get_profile(current_user: User = Depends(require_candidate), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    skills_result = await db.execute(
        select(CandidateSkill, Skill)
        .join(Skill, Skill.id == CandidateSkill.skill_id)
        .where(CandidateSkill.candidate_id == profile.id)
    )
    skills = [{"name": s.name, "proficiency": cs.proficiency_level, "years": cs.years_of_experience} for cs, s in skills_result.all()]

    return {
        "id": profile.id,
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": profile.phone,
        "location": profile.location,
        "linkedin_url": profile.linkedin_url,
        "github_url": profile.github_url,
        "portfolio_url": profile.portfolio_url,
        "experience_years": profile.experience_years,
        "ats_score": profile.ats_score,
        "resume_path": profile.resume_path,
        "skills": skills,
    }


@router.put("/profile")
async def update_profile(data: CandidateProfileUpdate, current_user: User = Depends(require_candidate), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    for field, value in data.model_dump(exclude_none=True).items():
        if field == "full_name":
            current_user.full_name = value
        else:
            setattr(profile, field, value)

    await db.commit()
    return {"message": "Profile updated"}


@router.post("/skills")
async def add_skill(data: SkillAdd, current_user: User = Depends(require_candidate), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    normalized = data.name.lower().strip()
    skill_result = await db.execute(select(Skill).where(Skill.normalized_name == normalized))
    skill = skill_result.scalar_one_or_none()
    if not skill:
        skill = Skill(name=data.name, normalized_name=normalized)
        db.add(skill)
        await db.flush()

    existing = await db.execute(
        select(CandidateSkill).where(CandidateSkill.candidate_id == profile.id, CandidateSkill.skill_id == skill.id)
    )
    if not existing.scalar_one_or_none():
        db.add(CandidateSkill(candidate_id=profile.id, skill_id=skill.id, proficiency_level=data.proficiency_level, years_of_experience=data.years_of_experience))
        await db.commit()
    return {"message": "Skill added"}


@router.delete("/skills/{skill_name}")
async def remove_skill(skill_name: str, current_user: User = Depends(require_candidate), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    skill_result = await db.execute(select(Skill).where(Skill.normalized_name == skill_name.lower()))
    skill = skill_result.scalar_one_or_none()
    if skill:
        cs_result = await db.execute(select(CandidateSkill).where(CandidateSkill.candidate_id == profile.id, CandidateSkill.skill_id == skill.id))
        cs = cs_result.scalar_one_or_none()
        if cs:
            await db.delete(cs)
            await db.commit()
    return {"message": "Skill removed"}


@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_candidate),
    db: AsyncSession = Depends(get_db),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type. Allowed: {settings.ALLOWED_EXTENSIONS}")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {settings.MAX_UPLOAD_MB}MB")

    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    # Parse resume
    from app.ai.resume_parser import parse_resume, is_resume_like
    parsed = parse_resume(content, file.filename)

    if not is_resume_like(parsed):
        os.remove(file_path)
        raise HTTPException(
            400,
            "The uploaded file does not appear to be a resume. "
            "Please upload a resume (PDF or DOCX) that contains sections like Experience, Education, or Skills."
        )

    # Compute ATS score
    from app.ai.ats_scorer import compute_ats_score
    ats = compute_ats_score(parsed["raw_text"])

    # Generate embedding and upsert into FAISS
    from app.ai.embeddings import embed_text
    from app.ai.vector_store import vector_store
    try:
        embedding = embed_text(parsed["raw_text"][:8192])
        vector_store.upsert_candidate(profile.id, embedding)
    except Exception:
        pass

    # Update profile
    profile.resume_path = filename
    profile.resume_text = parsed["raw_text"][:50000]
    profile.experience_years = parsed["experience_years"]
    profile.ats_score = ats.total_score
    profile.parsed_data = {
        "name": parsed["name"], "email": parsed["email"], "phone": parsed["phone"],
        "skills": parsed["skills"], "experience_years": parsed["experience_years"],
        "education": parsed["education"], "word_count": parsed["word_count"],
        "sections": parsed.get("sections", {}),
    }

    # Auto-add extracted skills
    for skill_name in parsed["skills"][:20]:
        normalized = skill_name.lower().strip()
        skill_result = await db.execute(select(Skill).where(Skill.normalized_name == normalized))
        skill = skill_result.scalar_one_or_none()
        if not skill:
            skill = Skill(name=skill_name, normalized_name=normalized)
            db.add(skill)
            await db.flush()
        existing = await db.execute(select(CandidateSkill).where(CandidateSkill.candidate_id == profile.id, CandidateSkill.skill_id == skill.id))
        if not existing.scalar_one_or_none():
            db.add(CandidateSkill(candidate_id=profile.id, skill_id=skill.id))

    await db.commit()
    return {
        "message": "Resume uploaded and analyzed successfully",
        "ats_score": ats.total_score,
        "skills_extracted": len(parsed["skills"]),
        "experience_years": parsed["experience_years"],
    }


@router.get("/resume/analysis")
async def get_resume_analysis(current_user: User = Depends(require_candidate), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile or not profile.resume_text:
        raise HTTPException(404, "No resume uploaded yet")

    from app.ai.ats_scorer import compute_ats_score
    ats = compute_ats_score(profile.resume_text)

    return {
        "parsed_data": profile.parsed_data or {},
        "ats_score": {
            "total_score": ats.total_score,
            "contact_info_score": ats.contact_info_score,
            "skills_score": ats.skills_score,
            "experience_score": ats.experience_score,
            "education_score": ats.education_score,
            "formatting_score": ats.formatting_score,
            "keyword_density_score": ats.keyword_density_score,
            "recommendations": ats.recommendations,
        },
    }


@router.get("/ats-score")
async def get_ats_score(current_user: User = Depends(require_candidate), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    if not profile.resume_text:
        return {"ats_score": 0, "message": "Upload a resume to get your ATS score"}

    from app.ai.ats_scorer import compute_ats_score
    ats = compute_ats_score(profile.resume_text)
    return {
        "total_score": ats.total_score,
        "breakdown": {
            "contact_info": ats.contact_info_score,
            "skills": ats.skills_score,
            "experience": ats.experience_score,
            "education": ats.education_score,
            "formatting": ats.formatting_score,
            "keywords": ats.keyword_density_score,
        },
        "recommendations": ats.recommendations,
    }


@router.get("/recommendations/jobs")
async def get_job_recommendations(
    limit: int = Query(10, le=20),
    current_user: User = Depends(require_candidate),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile or not profile.resume_text:
        return []

    skills_result = await db.execute(select(Skill).join(CandidateSkill).where(CandidateSkill.candidate_id == profile.id))
    candidate_skills = [s.name.lower() for s in skills_result.scalars().all()]

    from app.ai.embeddings import embed_text
    from app.ai.vector_store import vector_store
    try:
        candidate_embedding = embed_text(profile.resume_text[:4000])
        similar_jobs = vector_store.search_jobs(candidate_embedding, top_k=limit * 2)
    except Exception:
        similar_jobs = []

    matched_job_ids = {job_id: score for job_id, score in similar_jobs}

    # Fallback: get active jobs if no vector matches
    if not matched_job_ids:
        active_jobs = await db.execute(select(Job).where(Job.status == "active").limit(limit))
        for j in active_jobs.scalars().all():
            matched_job_ids[j.id] = 0.5

    recommendations = []
    for job_id, semantic_score in list(matched_job_ids.items())[:limit]:
        job_result = await db.execute(select(Job).where(Job.id == job_id, Job.status == "active"))
        job = job_result.scalar_one_or_none()
        if not job:
            continue

        job_skills_result = await db.execute(select(Skill).join(JobSkill).where(JobSkill.job_id == job_id))
        job_skills = [s.name.lower() for s in job_skills_result.scalars().all()]

        matching = [s for s in job_skills if s in candidate_skills]
        missing = [s for s in job_skills if s not in candidate_skills]
        match_score = len(matching) / max(len(job_skills), 1) if job_skills else semantic_score

        recommendations.append({
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "job_type": job.job_type,
            "experience_required": job.experience_required,
            "match_score": round(max(semantic_score, match_score) * 100, 1),
            "required_skills": job_skills[:8],
            "matching_skills": matching[:8],
            "missing_skills": missing[:5],
        })

    return sorted(recommendations, key=lambda x: x["match_score"], reverse=True)[:limit]


@router.get("/recommendations/skills")
async def get_skill_recommendations(current_user: User = Depends(require_candidate), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    skills_result = await db.execute(select(Skill).join(CandidateSkill).where(CandidateSkill.candidate_id == profile.id))
    candidate_skills = [s.name for s in skills_result.scalars().all()]

    from app.ai.insights import suggest_skill_improvements
    recommendations = await suggest_skill_improvements(candidate_skills, profile.experience_years)
    return {"current_skills": candidate_skills, "recommendations": recommendations}


@router.get("/skill-gaps")
async def get_skill_gaps(
    job_id: str = Query(None),
    current_user: User = Depends(require_candidate),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    skills_result = await db.execute(select(Skill).join(CandidateSkill).where(CandidateSkill.candidate_id == profile.id))
    candidate_skills = [s.name.lower() for s in skills_result.scalars().all()]

    if job_id:
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(404, "Job not found")
        job_skills_result = await db.execute(select(Skill).join(JobSkill).where(JobSkill.job_id == job_id))
        required_skills = [s.name.lower() for s in job_skills_result.scalars().all()]
        job_title = job.title
    else:
        required_skills = ["python", "sql", "docker", "aws", "react", "git", "machine learning", "typescript"]
        job_title = "General Tech Roles"

    matching = [s for s in required_skills if s in candidate_skills]
    missing = [s for s in required_skills if s not in candidate_skills]
    match_pct = len(matching) / max(len(required_skills), 1) * 100

    from app.ai.insights import generate_skill_gap_analysis
    gap_analysis = await generate_skill_gap_analysis(current_user.full_name, candidate_skills, job_title, required_skills)

    return {
        "job_id": job_id,
        "job_title": job_title,
        "candidate_skills": candidate_skills,
        "required_skills": required_skills,
        "matching_skills": matching,
        "missing_skills": missing,
        "match_percentage": round(match_pct, 1),
        "recommendations": gap_analysis.get("recommendations", []),
    }


@router.get("/applications")
async def get_applications(current_user: User = Depends(require_candidate), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    result = await db.execute(
        select(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .where(Application.candidate_id == profile.id)
        .order_by(Application.applied_at.desc())
    )
    return [
        {
            "id": app.id, "job_id": job.id, "job_title": job.title,
            "company": job.company, "status": app.status, "ai_score": app.ai_score,
            "overall_rank": app.overall_rank,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
        }
        for app, job in result.all()
    ]


@router.post("/apply/{job_id}", status_code=201)
async def apply_to_job(job_id: str, current_user: User = Depends(require_candidate), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    profile = r.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")
    if not profile.resume_text:
        raise HTTPException(400, "Please upload a resume before applying")

    job_result = await db.execute(select(Job).where(Job.id == job_id, Job.status == "active"))
    if not job_result.scalar_one_or_none():
        raise HTTPException(404, "Job not found or not accepting applications")

    existing = await db.execute(select(Application).where(Application.candidate_id == profile.id, Application.job_id == job_id))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already applied to this job")

    db.add(Application(candidate_id=profile.id, job_id=job_id))
    await db.commit()
    return {"message": "Application submitted successfully"}
