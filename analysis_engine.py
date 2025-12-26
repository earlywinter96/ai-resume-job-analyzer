import re
from collections import Counter

# ==================================================
# 1️⃣ SKILL TAXONOMY (ROLE-AGNOSTIC)
# ==================================================
SKILL_SYNONYMS = {
    # ---------- TECH / DATA ----------
    "python": ["python", "pandas", "numpy"],
    "sql": ["sql", "mysql", "postgres", "sqlite"],
    "machine learning": ["machine learning", "ml"],
    "data analysis": ["data analysis", "analytics"],
    "excel": ["excel", "spreadsheets"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "aws": ["aws", "ec2", "s3"],
    "gcp": ["gcp", "bigquery"],

    # ---------- MARKETING ----------
    "seo": ["seo", "search engine optimization"],
    "content marketing": ["content marketing", "copywriting"],
    "google ads": ["google ads", "ppc", "adwords"],
    "social media marketing": ["social media", "facebook ads", "instagram ads"],
    "email marketing": ["email marketing", "mailchimp"],

    # ---------- SALES ----------
    "crm": ["crm", "salesforce", "hubspot"],
    "lead generation": ["lead generation", "prospecting"],
    "cold calling": ["cold calling", "outbound sales"],
    "account management": ["account management"],
    "negotiation": ["negotiation", "closing deals"],

    # ---------- PRODUCT / MANAGEMENT ----------
    "product management": ["product management", "product owner"],
    "roadmapping": ["roadmap", "roadmapping"],
    "stakeholder management": ["stakeholder management"],
    "agile": ["agile", "scrum"],

    # ---------- SOFT SKILLS ----------
    "communication": ["communication", "presentation"],
    "leadership": ["leadership", "team management"],
    "problem solving": ["problem solving"],
}

# ==================================================
# 2️⃣ ROLE DETECTION (CRITICAL FIX)
# ==================================================
ROLE_KEYWORDS = {
    "sales": ["business development", "bd executive", "sales", "account executive"],
    "marketing": ["marketing", "digital marketing", "seo", "growth"],
    "data": ["data analyst", "analytics", "business intelligence"],
    "product": ["product manager", "product owner"],
}

ROLE_EXPECTED_SKILLS = {
    "sales": ["crm", "lead generation", "negotiation", "account management"],
    "marketing": ["seo", "content marketing", "google ads"],
    "data": ["python", "sql", "data analysis"],
    "product": ["roadmapping", "stakeholder management"],
}

# ==================================================
# 3️⃣ TEXT HELPERS
# ==================================================
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text


def extract_skills(text: str):
    """
    Extract normalized skills using synonym matching.
    """
    text = clean_text(text)
    found = set()

    for skill, variants in SKILL_SYNONYMS.items():
        for v in variants:
            if v in text:
                found.add(skill)

    return list(found)


def detect_role(jd_text: str) -> str:
    """
    Detect job role based on JD keywords.
    """
    jd_text = clean_text(jd_text)

    for role, keywords in ROLE_KEYWORDS.items():
        for kw in keywords:
            if kw in jd_text:
                return role

    return "generic"


def get_skill_weight(skill: str, jd_text: str) -> int:
    """
    Core skills mentioned in JD are weighted higher.
    """
    jd_text = clean_text(jd_text)
    return 3 if skill in jd_text else 1


def keyword_overlap(resume_text: str, jd_text: str):
    resume_words = clean_text(resume_text).split()
    jd_words = clean_text(jd_text).split()

    common = set(resume_words) & set(jd_words)
    return len(common), len(set(jd_words))


# ==================================================
# 4️⃣ ATS SCORE ENGINE (FIXED & ROLE-AWARE)
# ==================================================
def calculate_ats_score(resume_text: str, jd_text: str):
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(jd_text))

    # 🔥 Detect role & inject expected skills
    role = detect_role(jd_text)
    role_skills = set(ROLE_EXPECTED_SKILLS.get(role, []))

    # Merge explicit JD skills + implicit role skills
    jd_skills = jd_skills | role_skills

    matched_skills = resume_skills & jd_skills
    missing_skills = jd_skills - resume_skills

    # 🔢 Skill score (50%)
    total_weight = sum(get_skill_weight(s, jd_text) for s in jd_skills)
    matched_weight = sum(get_skill_weight(s, jd_text) for s in matched_skills)
    skill_score = (matched_weight / max(total_weight, 1)) * 50

    # 🔑 Keyword relevance (30%)
    common_words, total_jd_words = keyword_overlap(resume_text, jd_text)
    keyword_score = (common_words / max(total_jd_words, 1)) * 30

    # 📄 Resume structure (20%)
    length_score = 20 if len(resume_text.split()) > 300 else 10

    ats_score = round(skill_score + keyword_score + length_score)

    job_fit = recommend_job_fit(resume_skills, jd_skills)

    return {
    "ats_score": min(ats_score, 100),
    "matched_skills": sorted(matched_skills),
    "missing_skills": sorted(missing_skills),
    "detected_role": role,
    "job_fit": job_fit
}





def recommend_job_fit(resume_skills, jd_skills):
    """
    Returns job fit category based on skill overlap.
    """
    if not jd_skills:
        return "Unknown"

    match_ratio = len(resume_skills & jd_skills) / len(jd_skills)

    if match_ratio >= 0.7:
        return "Strong Fit"
    elif match_ratio >= 0.4:
        return "Partial Fit"
    else:
        return "Weak Fit"
