import os
import json
import re
from dotenv import load_dotenv
from google import genai

from analysis_engine import calculate_ats_score
from job_fetcher import fetch_jobs
from job_matcher import rank_jobs

# ==================================================
# ENV SETUP
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
API_KEY = os.getenv("GOOGLE_API_KEY")

# ==================================================
# SAFE JSON EXTRACTOR
# ==================================================
def extract_json(text: str):
    if not text:
        return None

    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    stack, start = [], None
    for i, ch in enumerate(text):
        if ch == "{":
            if not stack:
                start = i
            stack.append(ch)
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start is not None:
                    return text[start:i + 1]
    return None


# ==================================================
# HELPERS
# ==================================================
def normalize(value, allowed, default):
    if not isinstance(value, str):
        return default
    value = value.strip().title()
    return value if value in allowed else default


def classify_gap(effort: str, impact: str) -> str:
    return "Career Gap" if effort == "High" and impact == "High" else "Resume Fix"


# ==================================================
# GEMINI INSIGHTS (DETAILED & SAFE)
# ==================================================
def gemini_insights(resume_text: str, job_description: str):
    if not API_KEY:
        return {"strengths": [], "improvements": []}

    prompt = f"""
You are a senior ATS consultant and hiring manager.

Analyze the resume against the job description.

Return ONLY valid JSON.

JSON FORMAT:
{{
  "strengths": [
    {{
      "title": "string",
      "evidence": "string",
      "why_it_matters": "string"
    }}
  ],
  "improvements": [
    {{
      "area": "string",
      "priority": "High | Medium | Low",
      "expected_impact": "High | Medium | Low",
      "effort": "High | Medium | Low",
      "why_missing": "string",
      "how_to_fix": "string",
      "example_bullet": "string"
    }}
  ]
}}

Rules:
- Use resume evidence only
- Do NOT invent experience
- Be ATS-safe
- Be specific

Resume:
{resume_text}

Job Description:
{job_description}
"""

    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        raw = extract_json(response.text)
        if not raw:
            raise ValueError("No JSON returned by Gemini")

        data = json.loads(raw)

        return {
            "strengths": data.get("strengths", []),
            "improvements": data.get("improvements", [])
        }

    except Exception as e:
        print("🔥 Gemini Error:", e)
        return {"strengths": [], "improvements": []}


# ==================================================
# FINAL ORCHESTRATOR (SOURCE OF TRUTH)
# ==================================================
def analyze_resume(resume_text: str, job_description: str):
    """
    Guarantees:
    - Correct ATS score
    - Detailed improvement plan
    - Accurate summary stats
    - Resume-based job recommendations
    """

    # -------------------------
    # ATS SCORE (RULE-BASED)
    # -------------------------
    stats = calculate_ats_score(resume_text, job_description)

    # -------------------------
    # AI INSIGHTS
    # -------------------------
    ai = gemini_insights(resume_text, job_description)

    # -------------------------
    # BUILD IMPROVEMENTS (AI FIRST)
    # -------------------------
    improvements = []

    for item in ai.get("improvements", []):
        priority = normalize(item.get("priority"), ["High", "Medium", "Low"], "Medium")
        effort = normalize(item.get("effort"), ["High", "Medium", "Low"], "Medium")
        impact = normalize(item.get("expected_impact"), ["High", "Medium", "Low"], "Medium")

        improvements.append({
            "area": item.get("area", "General improvement"),
            "priority": priority,
            "expected_impact": impact,
            "effort": effort,
            "gap_type": classify_gap(effort, impact),
            "why_missing": item.get("why_missing", ""),
            "how_to_fix": item.get("how_to_fix", ""),
            "example_bullet": item.get("example_bullet", ""),
            "source": "ai"
        })

    # -------------------------
    # GUARANTEED FALLBACK
    # -------------------------
    if not improvements:
        for skill in stats.get("missing_skills", [])[:5]:
            improvements.append({
                "area": f"Add {skill} to resume",
                "priority": "High",
                "expected_impact": "High",
                "effort": "Medium",
                "gap_type": "Resume Fix",
                "why_missing": f"{skill} is required but not found in resume",
                "how_to_fix": f"Add a bullet showing hands-on use of {skill}",
                "example_bullet": "",
                "source": "skill_gap"
            })

    # -------------------------
    # IMPROVEMENT SUMMARY (FIXED & TRUSTWORTHY)
    # -------------------------
    improvement_stats = {
        "total": len(improvements),
        "resume_fixes": sum(1 for i in improvements if i["gap_type"] == "Resume Fix"),
        "career_gaps": sum(1 for i in improvements if i["gap_type"] == "Career Gap"),
        "high_priority": sum(1 for i in improvements if i["priority"] == "High"),
        "quick_wins": sum(
            1 for i in improvements
            if i["priority"] == "High" and i["effort"] == "Low"
        )
    }

    print("🧠 IMPROVEMENTS:", improvements)
    print("📊 SUMMARY:", improvement_stats)

    # -------------------------
    # JOB RECOMMENDATIONS (RESUME-BASED)
    # -------------------------
    recommended_jobs = []

    try:
        resume_role = stats.get("resume_role", "generic")
        if resume_role != "generic":
            jobs = fetch_jobs(resume_role)
            recommended_jobs = rank_jobs(resume_text, jobs)
            print(f"💼 Jobs fetched: {len(jobs)} | Recommended: {len(recommended_jobs)}")
    except Exception as e:
        print("⚠️ Job recommendation error:", e)

    # -------------------------
    # FINAL RESPONSE (UI CONTRACT)
    # -------------------------
    return {
        "ats_score": stats.get("ats_score", 0),
        "matched_skills": stats.get("matched_skills", []),
        "missing_skills": stats.get("missing_skills", []),

        "jd_role": stats.get("jd_role", "generic"),
        "resume_role": stats.get("resume_role", "generic"),
        "job_fit": stats.get("job_fit", "Unknown"),

        "ai_strengths": ai.get("strengths", []),
        "ai_improvements": improvements,
        "improvement_stats": improvement_stats,

        "recommended_jobs": recommended_jobs
    }
