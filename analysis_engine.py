import re

# ==================================================
# 1️⃣ SKILL TAXONOMY (NORMALIZED)
# ==================================================
SKILL_SYNONYMS = {
    # ---- DATA / TECH ----
    "python": ["python", "pandas", "numpy"],
    "sql": ["sql", "mysql", "postgres", "sqlite"],
    "machine learning": ["machine learning", "ml"],
    "data analysis": ["data analysis", "analytics"],
    "excel": ["excel", "spreadsheets"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "aws": ["aws", "ec2", "s3"],
    "gcp": ["gcp", "bigquery"],

    # ---- MARKETING ----
    "seo": ["seo", "search engine optimization"],
    "content marketing": ["content marketing", "copywriting"],
    "google ads": ["google ads", "ppc", "adwords"],

    # ---- SALES ----
    "crm": ["crm", "salesforce", "hubspot"],
    "lead generation": ["lead generation", "prospecting"],
    "negotiation": ["negotiation", "closing deals"],

    # ---- PRODUCT ----
    "product management": ["product management", "product owner"],
    "roadmapping": ["roadmap", "roadmapping"],

    # ---- SUPPORT ----
    "customer support": ["customer support", "customer service"],
    "incident management": ["incident", "major incident"],
    "ticketing systems": ["zendesk", "servicenow", "freshdesk", "jira"],
    "sla management": ["sla", "service level agreement"],
    "escalation handling": ["escalation", "escalation management"],

    # ---- SOFT ----
    "communication": ["communication", "presentation"],
    "leadership": ["leadership", "team management"],
    "problem solving": ["problem solving"],
}

# ==================================================
# 2️⃣ ROLE DEFINITIONS
# ==================================================
ROLE_KEYWORDS = {
    "data": ["data analyst", "analytics", "business intelligence"],
    "marketing": ["marketing", "digital marketing", "seo"],
    "sales": ["sales", "business development", "account executive"],
    "product": ["product manager", "product owner"],
    "support": [
        "customer support", "service desk", "technical support",
        "incident", "escalation", "operations support"
    ],
}

ROLE_EXPECTED_SKILLS = {
    "data": {"python", "sql", "data analysis"},
    "marketing": {"seo", "content marketing", "google ads"},
    "sales": {"crm", "lead generation", "negotiation"},
    "product": {"product management", "roadmapping"},
    "support": {
        "customer support",
        "incident management",
        "ticketing systems",
        "sla management",
        "escalation handling",
    },
}

# ==================================================
# 3️⃣ TEXT HELPERS
# ==================================================
def clean_text(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower())


def extract_skills(text: str) -> set:
    """
    Strict, word-boundary-safe skill extraction
    """
    text = clean_text(text)
    found = set()

    for skill, variants in SKILL_SYNONYMS.items():
        for v in variants:
            if re.search(rf"\b{re.escape(v)}\b", text):
                found.add(skill)
                break

    return found


# ==================================================
# 4️⃣ ROLE DETECTION
# ==================================================
def detect_jd_role(jd_text: str) -> str:
    text = clean_text(jd_text)

    for role, keywords in ROLE_KEYWORDS.items():
        if any(k in text for k in keywords):
            return role

    return "generic"


def infer_resume_role(resume_skills: set) -> str:
    scores = {
        role: len(resume_skills & skills)
        for role, skills in ROLE_EXPECTED_SKILLS.items()
    }

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "generic"


# ==================================================
# 5️⃣ EXPERIENCE SIGNALS (REAL WORK INDICATORS)
# ==================================================
def extract_experience_signals(resume_text: str) -> set:
    keywords = [
        "incident", "escalation", "sla", "ticket",
        "dashboard", "reporting", "analysis",
        "automation", "root cause", "monitoring",
        "client handling", "stakeholder", "operations",
        "troubleshooting", "process improvement"
    ]

    text = clean_text(resume_text)
    return {k for k in keywords if k in text}


# ==================================================
# 6️⃣ ATS ENGINE (BALANCED & EXPLAINABLE)
# ==================================================
def keyword_overlap(resume_text: str, jd_text: str):
    resume_words = set(clean_text(resume_text).split())
    jd_words = set(clean_text(jd_text).split())
    return len(resume_words & jd_words), len(jd_words)


def recommend_job_fit(resume_skills: set, jd_skills: set) -> str:
    if not jd_skills:
        return "Unknown"

    ratio = len(resume_skills & jd_skills) / len(jd_skills)

    if ratio >= 0.7:
        return "Strong Fit"
    elif ratio >= 0.4:
        return "Partial Fit"
    return "Weak Fit"


def calculate_ats_score(resume_text: str, jd_text: str):
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    jd_role = detect_jd_role(jd_text)
    resume_role = infer_resume_role(resume_skills)

    core_skills = ROLE_EXPECTED_SKILLS.get(jd_role, set())
    jd_skills |= core_skills

    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills

    # ---- Skill score (50)
    skill_score = (len(matched) / max(len(jd_skills), 1)) * 50

    # ---- Keyword relevance (30)
    common, total = keyword_overlap(resume_text, jd_text)
    keyword_score = (common / max(total, 1)) * 30

    # ---- Resume completeness (10–20)
    length_score = 20 if len(resume_text.split()) >= 300 else 10

    # ---- Experience bonus (0–10)
    exp_bonus = min(len(extract_experience_signals(resume_text)) * 2, 10)

    ats = round(skill_score + keyword_score + length_score + exp_bonus)

    return {
        "ats_score": min(ats, 100),
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "jd_role": jd_role,
        "resume_role": resume_role,
        "job_fit": recommend_job_fit(resume_skills, jd_skills),
    }
