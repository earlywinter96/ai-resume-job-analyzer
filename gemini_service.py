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
# Helper: Robust JSON extractor (FIXED)
# --------------------------------------------------
def extract_json(text: str):
    """
    Extract first valid JSON object using brace matching.
    Handles markdown, extra text, nested objects.
    """
    if not text:
        return None

    # Remove markdown blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    stack = []
    start = None

    for i, ch in enumerate(text):
        if ch == "{":
            if not stack:
                start = i
            stack.append("{")
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start is not None:
                    return text[start:i + 1]

    return None


# --------------------------------------------------
# Helper: Gap classification
# --------------------------------------------------
def classify_gap(effort: str) -> str:
    return "Career Gap" if effort == "High" else "Resume Fix"


# --------------------------------------------------
# Gemini structured insights
# --------------------------------------------------
def gemini_insights(resume_text: str, job_description: str):
    if not API_KEY:
        return {"strengths": [], "improvements": []}

    prompt = f"""
STRICT RULES:
- Output ONLY valid JSON
- No markdown
- No explanations
- No text outside JSON
- Use double quotes only

Required JSON format:

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

        raw = response.text
        json_text = extract_json(raw)

        if not json_text:
            raise ValueError("Gemini returned no JSON")

        data = json.loads(json_text)

        # Validate structure
        if "strengths" not in data or "improvements" not in data:
            raise ValueError("Invalid JSON structure")

        return data

    except Exception as e:
        print("🔥 Gemini JSON Error:", e)
        return {"strengths": [], "improvements": []}


# --------------------------------------------------
# Final combined analysis
# --------------------------------------------------
def analyze_resume(resume_text: str, job_description: str):
    stats = calculate_ats_score(resume_text, job_description)
    ai_data = gemini_insights(resume_text, job_description)

    improvements = []

    for item in ai_data.get("improvements", []):
        effort = item.get("effort", "Medium")

        improvements.append({
            "area": item.get("area", "General improvement"),
            "priority": item.get("priority", "Medium"),
            "impact": item.get("expected_impact", "Medium"),
            "effort": effort,
            "gap_type": classify_gap(effort)
        })

    # --------------------------------------------------
    # 🔥 GUARANTEED FALLBACK (CRITICAL)
    # --------------------------------------------------
    if not improvements:
        for skill in stats.get("missing_skills", []):
            improvements.append({
                "area": f"Add {skill} to resume",
                "priority": "High",
                "impact": "High",
                "effort": "Medium",
                "gap_type": "Resume Fix"
            })

    improvement_stats = {
        "resume_fixes": sum(1 for i in improvements if i["gap_type"] == "Resume Fix"),
        "career_gaps": sum(1 for i in improvements if i["gap_type"] == "Career Gap"),
        "high_priority": sum(1 for i in improvements if i["priority"] == "High")
    }

    return {
        "ats_score": stats.get("ats_score", 0),
        "matched_skills": stats.get("matched_skills", []),
        "missing_skills": stats.get("missing_skills", []),
        "detected_role": stats.get("detected_role", "generic"),
        "job_fit": stats.get("job_fit", "Unknown"),
        "ai_strengths": ai_data.get("strengths", []),
        "ai_improvements": improvements,
        "improvement_stats": improvement_stats
    }
