import json
from typing import List, Optional
from app.core.config import settings


def _get_openai_client():
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_hiring_insights(job_title: str, job_description: str, ranked_candidates: list) -> str:
    if not settings.OPENAI_API_KEY:
        return _mock_hiring_insights(job_title, len(ranked_candidates))

    client = _get_openai_client()
    top_candidates = ranked_candidates[:5]
    candidate_summary = "\n".join(
        f"- {c.get('full_name', 'Candidate')} (Score: {c.get('ai_score', 0):.1f}, Skills: {', '.join(c.get('skills', [])[:5])})"
        for c in top_candidates
    )

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert HR analyst. Generate concise, actionable hiring insights."},
            {"role": "user", "content": f"""
Job: {job_title}
Description: {job_description[:500]}

Top Candidates:
{candidate_summary}

Generate hiring insights in 3-4 sentences covering:
1. Overall candidate pool quality
2. Key strengths observed
3. Gaps or concerns
4. Recommendation on next steps
"""}
        ],
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


async def generate_skill_gap_analysis(candidate_name: str, candidate_skills: List[str], job_title: str, required_skills: List[str]) -> dict:
    if not settings.OPENAI_API_KEY:
        missing = [s for s in required_skills if s.lower() not in [c.lower() for c in candidate_skills]]
        return {"missing_skills": missing, "recommendations": [f"Learn {s}" for s in missing[:3]]}

    client = _get_openai_client()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Respond with JSON only."},
            {"role": "user", "content": f"""
Candidate: {candidate_name}
Candidate skills: {', '.join(candidate_skills)}
Job: {job_title}
Required skills: {', '.join(required_skills)}

Return JSON: {{"missing_skills": [...], "recommendations": [...], "learning_resources": [...]}}
"""}
        ],
        max_tokens=300,
    )
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"missing_skills": [], "recommendations": [], "learning_resources": []}


async def generate_interview_questions(candidate_name: str, candidate_skills: List[str], job_title: str, job_description: str) -> List[str]:
    if not settings.OPENAI_API_KEY:
        return [
            f"Tell me about your experience with {candidate_skills[0] if candidate_skills else 'relevant technologies'}.",
            "Describe a challenging project you completed.",
            "How do you stay updated with industry trends?",
            "Tell me about a time you worked in a team under pressure.",
            "What are your career goals for the next 3 years?",
        ]

    client = _get_openai_client()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Respond with JSON only."},
            {"role": "user", "content": f"""
Generate 5 targeted interview questions for {candidate_name} applying for {job_title}.
Candidate skills: {', '.join(candidate_skills[:8])}
Job context: {job_description[:300]}

Return JSON: {{"questions": ["q1", "q2", "q3", "q4", "q5"]}}
"""}
        ],
        max_tokens=400,
    )
    try:
        data = json.loads(response.choices[0].message.content)
        return data.get("questions", [])
    except Exception:
        return []


async def generate_resume_summary(parsed_data: dict) -> str:
    if not settings.OPENAI_API_KEY:
        name = parsed_data.get("name", "The candidate")
        years = parsed_data.get("experience_years", 0)
        skills = parsed_data.get("skills", [])
        return f"{name} has {years:.0f} years of experience with skills in {', '.join(skills[:5])}."

    client = _get_openai_client()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Write a brief 2-sentence professional summary based on resume data."},
            {"role": "user", "content": f"Resume data: {json.dumps(parsed_data, default=str)[:600]}"},
        ],
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


async def suggest_skill_improvements(candidate_skills: List[str], experience_years: float) -> List[str]:
    if not settings.OPENAI_API_KEY:
        suggestions = ["Docker & Kubernetes", "Cloud Platforms (AWS/Azure/GCP)", "CI/CD pipelines"]
        return [s for s in suggestions if s.lower() not in " ".join(candidate_skills).lower()][:5]

    client = _get_openai_client()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Respond with JSON only."},
            {"role": "user", "content": f"""
Current skills: {', '.join(candidate_skills[:10])}
Experience: {experience_years:.1f} years

Return JSON: {{"recommendations": ["skill1", "skill2", "skill3", "skill4", "skill5"]}}
Suggest 5 in-demand skills to learn that complement their profile.
"""}
        ],
        max_tokens=200,
    )
    try:
        data = json.loads(response.choices[0].message.content)
        return data.get("recommendations", [])
    except Exception:
        return []


def _mock_hiring_insights(job_title: str, candidate_count: int) -> str:
    return (
        f"The candidate pool for {job_title} includes {candidate_count} applicants with varying levels of qualification. "
        "The top candidates demonstrate strong technical skills aligned with job requirements and solid experience. "
        "Some gaps exist in advanced cloud and DevOps skills across the pool. "
        "We recommend proceeding with the top 3 candidates for technical interviews."
    )
