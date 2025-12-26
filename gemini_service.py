import os
import json
import re
from dotenv import load_dotenv
from google import genai
from analysis_engine import calculate_ats_score

# --------------------------------------------------
# Environment setup
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("GOOGLE_API_KEY")


# --------------------------------------------------
# Helper: Safe JSON extractor
# --------------------------------------------------
def extract_json(text: str):
    """
    Extract JSON object safely from Gemini output.
    Handles markdown, extra text, and formatting noise.
    """
    if not text:
        return None

    text = re.sub(r"```json|```", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)

    return match.group(0) if match else None


# --------------------------------------------------
# Helper: Gap classification
# --------------------------------------------------
def classify_gap(effort: str) -> str:
    """
    High effort = Career Gap
    Low/Medium effort = Resume Fix
    """
    return "Career Gap" if effort == "High" else "Resume Fix"


# --------------------------------------------------
# Gemini structured insights
# --------------------------------------------------
def gemini_insights(resume_text: str, job_description: str):
    """
    Uses Gemini to return structured resume insights.
    Always returns a dict with strengths & improvements.
    """
    if not API_KEY:
        return {"strengths": [], "improvements": []}

    prompt = f"""
You are a senior ATS consultant.

Analyze the resume against the job description.

Return ONLY valid JSON in this exact format:

{{
  "strengths": ["string"],
  "improvements": [
    {{
      "area": "string",
      "priority": "High | Medium | Low",
      "expected_impact": "High | Medium | Low",
      "effort": "Low | Medium | High"
    }}
  ]
}}

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

        json_text = extract_json(response.text)

        if not json_text:
            raise ValueError("No valid JSON returned by Gemini")

        return json.loads(json_text)

    except Exception as e:
        print("🔥 Gemini Error:", e)
        return {"strengths": [], "improvements": []}


# --------------------------------------------------
# Final combined analysis
# --------------------------------------------------
def analyze_resume(resume_text: str, job_description: str):
    """
    Combines rule-based ATS scoring with Gemini insights.
    Always returns a structured dictionary.
    """

    # Rule-based ATS stats
    stats = calculate_ats_score(resume_text, job_description)

    # Gemini insights
    ai_data = gemini_insights(resume_text, job_description)

    # ✅ Normalize improvements safely
    normalized_improvements = []
    for item in ai_data.get("improvements", []):
        effort = item.get("effort", "Medium")

        normalized_improvements.append({
            "area": item.get("area", ""),
            "priority": item.get("priority", "Medium"),
            "expected_impact": item.get("expected_impact", "Medium"),
            "effort": effort,
            "gap_type": classify_gap(effort)
        })

    return {
        "ats_score": stats["ats_score"],
        "matched_skills": stats["matched_skills"],
        "missing_skills": stats["missing_skills"],
        "detected_role": stats.get("detected_role", "generic"),
        "ai_strengths": ai_data.get("strengths", []),
        "ai_improvements": normalized_improvements
    }
