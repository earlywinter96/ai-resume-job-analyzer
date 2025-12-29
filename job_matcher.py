from analysis_engine import extract_skills, extract_experience_signals


def score_job(resume_text, job):
    """
    Score job using:
    - Experience match (50%)
    - Skill match (30%)
    - Title similarity (20%)
    """

    resume_skills = extract_skills(resume_text)
    resume_exp = extract_experience_signals(resume_text)

    job_desc = job.get("description", "") or ""
    job_title = job.get("title", "").lower()

    job_skills = set(extract_skills(job_desc))
    job_exp = set(extract_experience_signals(job_desc))

    # ---- Experience score (MOST IMPORTANT)
    exp_score = len(resume_exp & job_exp) / max(len(job_exp), 1)

    # ---- Skill score
    skill_score = len(resume_skills & job_skills) / max(len(job_skills), 1)

    # ---- Title relevance
    title_score = 0.2 if any(word in job_title for word in resume_exp) else 0

    # ---- Final weighted score
    final_score = (
        (exp_score * 0.5) +
        (skill_score * 0.3) +
        (title_score * 0.2)
    )

    return round(final_score * 100)
def rank_jobs(resume_text, jobs, min_score=30):
    scored = []

    for job in jobs:
        score = score_job(resume_text, job)

        scored.append({
            "title": job.get("title"),
            "company": job.get("company", {}).get("display_name"),
            "location": job.get("location", {}).get("display_name"),
            "url": job.get("redirect_url"),
            "score": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    strong = [j for j in scored if j["score"] >= min_score]

    return strong[:10] if strong else scored[:10]
