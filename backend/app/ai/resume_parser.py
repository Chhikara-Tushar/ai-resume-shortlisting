import re
import io
from typing import Optional
import pdfplumber
from docx import Document


SECTION_PATTERNS = {
    "experience": r"(?i)(work experience|professional experience|employment|experience)",
    "education": r"(?i)(education|academic|qualifications|degree)",
    "skills": r"(?i)(skills|technical skills|core competencies|expertise)",
    "projects": r"(?i)(projects|personal projects|academic projects)",
    "certifications": r"(?i)(certifications|certificates|licenses)",
    "summary": r"(?i)(summary|profile|objective|about me)",
}

# Soft skills — stable, small list; not discoverable from text alone
SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "team player", "problem solving",
    "problem-solving", "critical thinking", "time management", "adaptability",
    "creativity", "collaboration", "interpersonal skills", "presentation skills",
    "public speaking", "negotiation", "conflict resolution", "decision making",
    "analytical thinking", "attention to detail", "multitasking", "mentoring",
    "coaching", "emotional intelligence", "self-motivated", "organized",
    "planning", "research", "documentation", "reporting", "fast learner",
    "quick learner", "detail-oriented", "team management", "project management",
    "stakeholder management", "client management", "people management",
    "strategic thinking", "innovative", "proactive", "result-oriented",
]

# Words that look like skills but are actually noise to exclude
_NOISE_WORDS = {
    "and", "or", "the", "a", "an", "in", "of", "to", "for", "with", "on",
    "at", "by", "from", "as", "is", "it", "be", "this", "that", "etc",
    "including", "such", "using", "used", "good", "strong", "excellent",
    "knowledge", "understanding", "ability", "experience", "proficiency",
    "working", "exposure", "hands", "basic", "advanced", "intermediate",
    "senior", "junior", "years", "year", "month", "months",
}


def extract_text_from_pdf(content: bytes) -> str:
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass
    return text.strip()


def extract_text_from_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = re.search(r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{3,4}", text)
    return match.group(0) if match else None


def extract_name(text: str) -> Optional[str]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:
        if 2 <= len(line.split()) <= 4 and not any(c in line for c in ["@", "http", "www"]):
            if re.match(r"^[A-Za-z\s\-\.]+$", line):
                return line
    return None


def _is_valid_skill(text: str) -> bool:
    """Quick sanity check — reject obvious non-skills."""
    t = text.strip()
    if not t or len(t) < 2 or len(t) > 60:
        return False
    if t.lower() in _NOISE_WORDS:
        return False
    words = t.split()
    if len(words) > 6:
        return False
    # Skip pure numbers or single special chars
    if re.fullmatch(r'[\d\s\W]+', t):
        return False
    return True


def _get_ner_excludes(text: str) -> set:
    """Use spaCy NER to collect person names, locations, dates — things to exclude."""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text[:6000])
        return {
            ent.text.lower().strip()
            for ent in doc.ents
            if ent.label_ in ("PERSON", "GPE", "LOC", "DATE", "TIME", "CARDINAL", "ORDINAL", "NORP")
        }
    except Exception:
        return set()


def extract_skills(text: str) -> list[str]:
    sections = split_sections(text)
    collected: list[str] = []

    # ── Layer 1: Skills section (most reliable source) ──────────────────────
    skills_text = sections.get("skills", "")
    if skills_text:
        # Split by common delimiters used in skill lists
        raw_items = re.split(r'[,\n•·▪▸\-\|;/\\]+', skills_text)
        for item in raw_items:
            item = item.strip(" \t\r:–—")
            # Skills sections sometimes group like "Languages: Python, Java"
            # Strip the category label before the colon
            if ":" in item:
                item = item.split(":", 1)[1].strip()
            # Some items are "Skill (X years)" — extract just the skill name
            item = re.sub(r'\s*\(.*?\)', '', item).strip()
            if _is_valid_skill(item):
                collected.append(item)

    # ── Layer 2: Contextual patterns in full text ────────────────────────────
    context_patterns = [
        r'(?:proficient|experienced?|skilled|expertise|competent|knowledgeable)\s+(?:in|with|of)\s+([A-Za-z][A-Za-z0-9 \+\#\.\-/]+?)(?:\s*[,\.\n;]|$)',
        r'(?:hands[- ]on experience|working knowledge|strong knowledge|good knowledge)\s+(?:in|with|of)?\s*([A-Za-z][A-Za-z0-9 \+\#\.\-/]+?)(?:\s*[,\.\n;]|$)',
        r'(?:familiar|experience)\s+(?:in|with)\s+([A-Za-z][A-Za-z0-9 \+\#\.\-/]+?)(?:\s*[,\.\n;]|$)',
    ]
    for pattern in context_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            skill = match.group(1).strip()
            if _is_valid_skill(skill):
                collected.append(skill)

    # ── Layer 3: Soft skills scan across full text ───────────────────────────
    text_lower = text.lower()
    for soft in SOFT_SKILLS:
        if re.search(r'\b' + re.escape(soft) + r'\b', text_lower):
            collected.append(soft.title() if ' ' not in soft else soft.title())

    # ── Layer 4: spaCy NER filter — remove person names, cities, dates ───────
    excludes = _get_ner_excludes(text)

    seen: set[str] = set()
    result: list[str] = []
    for skill in collected:
        normalized = skill.lower().strip()
        if normalized in seen:
            continue
        if normalized in _NOISE_WORDS:
            continue
        # Reject if the whole skill matches a known person/place/date entity
        if normalized in excludes:
            continue
        # Reject if it's a single word that is a known named entity (partial match check)
        if len(skill.split()) == 1 and any(normalized == ex for ex in excludes):
            continue
        seen.add(normalized)
        result.append(skill.strip())

    return result[:50]


def is_resume_like(parsed: dict) -> bool:
    """Return True only if the document looks like a resume, not an admit card or certificate."""
    word_count = parsed.get("word_count", 0)
    if word_count < 80:
        return False

    text_lower = parsed.get("raw_text", "").lower()
    sections = parsed.get("sections", {})

    # Hard reject: admit cards, hall tickets, marksheets, invoices, ID cards
    non_resume_indicators = [
        "admit card", "hall ticket", "roll number", "roll no", "examination centre",
        "exam centre", "centre code", "invigilator", "question paper", "admit",
        "marksheet", "mark sheet", "transcript", "result sheet", "grade sheet",
        "invoice", "receipt", "payment", "aadhar", "aadhaar", "voter id",
        "driving licence", "pan card", "passport", "date of birth",
        "father's name", "mother's name", "registration number",
        "enrollment number", "seat number", "subject code",
    ]
    non_resume_hits = sum(1 for ind in non_resume_indicators if ind in text_lower)
    if non_resume_hits >= 2:
        return False

    # Positive resume signals
    has_resume_section = any(k in sections for k in ["experience", "education", "skills", "summary"])
    has_contact = bool(parsed.get("email") or parsed.get("phone"))
    has_email = bool(parsed.get("email"))

    # Strong resume-specific language (not found in admit cards)
    strong_resume_keywords = [
        "work experience", "professional experience", "employment history",
        "job responsibilities", "key skills", "technical skills", "core competencies",
        "career objective", "professional summary", "achievements",
        "internship", "designation", "responsibilities", "projects",
        "certifications", "references", "curriculum vitae",
    ]
    strong_hits = sum(1 for kw in strong_resume_keywords if kw in text_lower)

    # Must have at least one strong signal: a proper resume section header,
    # OR email + strong resume language, OR multiple strong resume keywords
    return has_resume_section or (has_email and strong_hits >= 1) or strong_hits >= 2


def extract_experience_years(text: str) -> float:
    # Pattern: "X years of experience"
    match = re.search(r"(\d+\.?\d*)\s*\+?\s*years?\s+(?:of\s+)?(?:work\s+)?experience", text, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Count date ranges like "2019 - 2023"
    date_ranges = re.findall(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\s*\d{4})\s*[-–—]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\s*\d{4}|Present|Current)", text, re.IGNORECASE)
    total = 0.0
    for start, end in date_ranges:
        try:
            s_year = int(re.search(r"\d{4}", start).group())
            e_year = 2024 if end.lower() in ("present", "current") else int(re.search(r"\d{4}", end).group())
            total += max(0, e_year - s_year)
        except Exception:
            pass
    return min(total, 40.0)


def extract_education(text: str) -> list[str]:
    education = []
    patterns = [
        r"(?:Bachelor|B\.?S\.?|B\.?E\.?|B\.?Tech\.?|B\.?Sc\.?)[^\n.]*",
        r"(?:Master|M\.?S\.?|M\.?E\.?|M\.?Tech\.?|M\.?Sc\.?|MBA)[^\n.]*",
        r"(?:Ph\.?D|Doctor)[^\n.]*",
        r"(?:Diploma|Certificate|Associate)[^\n.]*",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        education.extend([m.strip() for m in matches[:2]])
    return education[:4]


def split_sections(text: str) -> dict:
    sections = {}
    lines = text.split("\n")
    current_section = "general"
    current_content = []

    for line in lines:
        matched_section = None
        for section, pattern in SECTION_PATTERNS.items():
            if re.match(pattern, line.strip()) and len(line.strip()) < 60:
                matched_section = section
                break

        if matched_section:
            if current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = matched_section
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_section] = "\n".join(current_content)
    return sections


def parse_resume(content: bytes, filename: str) -> dict:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        text = extract_text_from_pdf(content)
    elif ext in ("docx", "doc"):
        text = extract_text_from_docx(content)
    else:
        text = content.decode("utf-8", errors="ignore")

    sections = split_sections(text)
    skills = extract_skills(text)
    experience_years = extract_experience_years(text)
    education = extract_education(text)
    email = extract_email(text)
    phone = extract_phone(text)
    name = extract_name(text)

    return {
        "raw_text": text,
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "experience_years": experience_years,
        "education": education,
        "sections": {k: v[:500] for k, v in sections.items()},
        "word_count": len(text.split()),
    }
