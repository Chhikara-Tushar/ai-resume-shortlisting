import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ATSScore:
    total_score: float
    contact_info_score: float
    skills_score: float
    experience_score: float
    education_score: float
    formatting_score: float
    keyword_density_score: float
    recommendations: list = field(default_factory=list)


def compute_ats_score(resume_text: str, job_description: Optional[str] = None) -> ATSScore:
    text = resume_text.lower()
    recommendations = []
    scores = {}

    # Contact info (20 pts)
    has_email = bool(re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", resume_text))
    has_phone = bool(re.search(r"[\+]?[0-9][\s\-\.]?[(]?[0-9]{2,4}[)]?[\s\-\.]?[0-9]{3,4}[\s\-\.]?[0-9]{3,4}", resume_text))
    has_linkedin = "linkedin" in text
    has_name = bool(re.search(r"^[A-Z][a-z]+ [A-Z][a-z]+", resume_text, re.MULTILINE))

    contact_score = 0
    if has_email: contact_score += 8
    else: recommendations.append("Add your email address")
    if has_phone: contact_score += 7
    else: recommendations.append("Add a phone number")
    if has_linkedin: contact_score += 3
    if has_name: contact_score += 2
    scores["contact_info"] = min(contact_score, 20)

    # Skills section (20 pts)
    has_skills_section = bool(re.search(r"(?i)skills|competencies|expertise|technologies", resume_text))
    skill_count = len(re.findall(r"\b(?:python|java|javascript|react|sql|aws|docker|git|node|html|css|machine learning|data)\b", text))
    skills_score = 0
    if has_skills_section: skills_score += 10
    else: recommendations.append("Add a dedicated Skills section")
    skills_score += min(skill_count * 2, 10)
    scores["skills"] = min(skills_score, 20)

    # Experience section (20 pts)
    has_exp_section = bool(re.search(r"(?i)experience|employment|work history", resume_text))
    has_dates = bool(re.search(r"\d{4}\s*[-–]\s*(?:\d{4}|present|current)", resume_text, re.IGNORECASE))
    has_bullets = resume_text.count("•") + resume_text.count("-") + resume_text.count("*")
    has_quantified = bool(re.search(r"\d+%|\$\d+|\d+ (?:million|thousand|users|customers|team)", resume_text, re.IGNORECASE))

    exp_score = 0
    if has_exp_section: exp_score += 8
    else: recommendations.append("Add a Work Experience section")
    if has_dates: exp_score += 5
    else: recommendations.append("Include dates for your work experience")
    if has_bullets > 3: exp_score += 4
    if has_quantified: exp_score += 3
    else: recommendations.append("Quantify achievements with numbers (e.g. improved performance by 30%)")
    scores["experience"] = min(exp_score, 20)

    # Education (15 pts)
    has_edu_section = bool(re.search(r"(?i)education|degree|university|college|bachelor|master|phd", resume_text))
    has_degree = bool(re.search(r"(?i)bachelor|master|phd|b\.s\.|m\.s\.|b\.e\.|m\.e\.", resume_text))
    edu_score = 0
    if has_edu_section: edu_score += 8
    else: recommendations.append("Add an Education section")
    if has_degree: edu_score += 7
    scores["education"] = min(edu_score, 15)

    # Formatting (15 pts)
    word_count = len(resume_text.split())
    has_sections = sum(1 for p in SECTION_PATTERNS if re.search(p, resume_text, re.IGNORECASE))
    format_score = 0
    if 300 <= word_count <= 1200: format_score += 8
    elif word_count < 200: recommendations.append("Resume is too short; add more detail")
    elif word_count > 1500: recommendations.append("Resume is too long; aim for 1-2 pages")
    format_score += min(has_sections * 2, 7)
    scores["formatting"] = min(format_score, 15)

    # Keyword density vs job description (10 pts)
    kw_score = 0
    if job_description:
        jd_words = set(re.findall(r"\b[a-z]{3,}\b", job_description.lower()))
        resume_words = set(re.findall(r"\b[a-z]{3,}\b", text))
        overlap = len(jd_words & resume_words) / max(len(jd_words), 1)
        kw_score = min(int(overlap * 10 * 3), 10)
        if overlap < 0.3:
            recommendations.append("Tailor your resume to include more keywords from the job description")
    else:
        kw_score = 5
    scores["keyword_density"] = kw_score

    total = sum(scores.values())
    return ATSScore(
        total_score=round(total, 1),
        contact_info_score=scores["contact_info"],
        skills_score=scores["skills"],
        experience_score=scores["experience"],
        education_score=scores["education"],
        formatting_score=scores["formatting"],
        keyword_density_score=scores["keyword_density"],
        recommendations=recommendations[:6],
    )


SECTION_PATTERNS = [
    r"experience", r"education", r"skills", r"projects", r"certifications", r"summary",
]
