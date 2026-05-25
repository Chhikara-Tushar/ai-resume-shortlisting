from dataclasses import dataclass
from typing import List, Optional
from app.ai.embeddings import cosine_similarity, embed_text
import numpy as np


@dataclass
class RankingResult:
    candidate_id: str
    ai_score: float
    semantic_score: float
    skill_match_score: float
    experience_score: float
    ats_contribution: float
    rank: int = 0


def normalize_experience(candidate_years: float, required_years: float) -> float:
    if required_years <= 0:
        return 1.0
    ratio = candidate_years / required_years
    if ratio >= 1.0:
        return min(1.0, 0.8 + 0.2 * min(ratio - 1.0, 1.0))
    return ratio * 0.8


def compute_skill_match(candidate_skills: List[str], job_skills: List[str]) -> float:
    if not job_skills:
        return 1.0
    candidate_lower = {s.lower() for s in candidate_skills}
    job_lower = [s.lower() for s in job_skills]
    exact_matches = sum(1 for s in job_lower if s in candidate_lower)
    exact_ratio = exact_matches / len(job_lower)

    # Semantic fallback: check if any candidate skill contains job skill substring
    semantic_matches = 0
    for job_skill in job_lower:
        if any(job_skill in cs or cs in job_skill for cs in candidate_lower):
            semantic_matches += 1
    semantic_ratio = semantic_matches / len(job_lower)

    return min(max(exact_ratio, semantic_ratio * 0.85), 1.0)


def score_candidate(
    candidate_id: str,
    resume_text: str,
    job_description: str,
    candidate_skills: List[str],
    job_skills: List[str],
    candidate_years: float,
    required_years: float,
    ats_score: float,
    job_embedding: Optional[np.ndarray] = None,
) -> RankingResult:
    # Semantic score
    if job_embedding is not None:
        candidate_embedding = embed_text(resume_text[:4000])
        semantic_score = max(0.0, cosine_similarity(candidate_embedding, job_embedding))
    else:
        candidate_embedding = embed_text(resume_text[:4000])
        job_emb = embed_text(job_description[:4000])
        semantic_score = max(0.0, cosine_similarity(candidate_embedding, job_emb))

    # Skill match
    skill_match_score = compute_skill_match(candidate_skills, job_skills)

    # Experience score
    experience_score = normalize_experience(candidate_years, required_years)

    # ATS contribution (normalized 0-1)
    ats_contribution = ats_score / 100.0

    # Weighted final score
    ai_score = (
        0.40 * semantic_score
        + 0.25 * skill_match_score
        + 0.20 * experience_score
        + 0.15 * ats_contribution
    )

    return RankingResult(
        candidate_id=candidate_id,
        ai_score=round(ai_score * 100, 2),
        semantic_score=round(semantic_score * 100, 2),
        skill_match_score=round(skill_match_score * 100, 2),
        experience_score=round(experience_score * 100, 2),
        ats_contribution=round(ats_contribution * 100, 2),
    )


def rank_results(results: List[RankingResult]) -> List[RankingResult]:
    sorted_results = sorted(results, key=lambda r: r.ai_score, reverse=True)
    for i, r in enumerate(sorted_results):
        r.rank = i + 1
    return sorted_results
