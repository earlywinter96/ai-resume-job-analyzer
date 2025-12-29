from flask import Flask, render_template, request, redirect, url_for, session
from resume_parser import extract_resume_text
from gemini_service import analyze_resume
from jd_parser import extract_jd_from_url, extract_jd_from_pdf
import os


app = Flask(__name__)

# -------------------------
# App configuration
# -------------------------
app.secret_key = "resume_ai_secret_key"
UPLOAD_RESUME_PATH = "uploaded_resume.pdf"
UPLOAD_JD_PATH = "uploaded_jd.pdf"


# -------------------------
# Home page
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")


# -------------------------
# Resume Analyzer
# -------------------------
@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if request.method == "POST":

        resume = request.files.get("resume")
        jd_url = request.form.get("jd_url", "").strip()
        jd_text = request.form.get("job_description", "").strip()
        jd_pdf = request.files.get("jd_pdf")

        # -------------------------
        # Validation
        # -------------------------
        if not resume:
            return redirect(url_for("analyze"))

        # Save resume
        resume.save(UPLOAD_RESUME_PATH)

        try:
            # Extract resume text
            resume_text = extract_resume_text(UPLOAD_RESUME_PATH)

            # -------------------------
            # Determine JD source priority
            # -------------------------
            job_desc = ""

            if jd_url:
                job_desc = extract_jd_from_url(jd_url)

            elif jd_pdf:
                jd_pdf.save(UPLOAD_JD_PATH)
                job_desc = extract_jd_from_pdf(UPLOAD_JD_PATH)

            elif jd_text:
                job_desc = jd_text

            else:
                raise ValueError("No job description provided")

            # -------------------------
            # Analyze
            # -------------------------
            result = analyze_resume(resume_text, job_desc)

            session["result"] = result
            print("✅ RESULT GENERATED")

        except Exception as e:
            print("❌ ANALYSIS ERROR:", e)
            session["result"] = {
                "error": str(e),
                "ats_score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "ai_strengths": [],
                "ai_improvements": [],
                "detected_role": "unknown",
                "job_fit": "Unknown"
            }

        finally:
            # Cleanup files
            if os.path.exists(UPLOAD_RESUME_PATH):
                os.remove(UPLOAD_RESUME_PATH)

            if os.path.exists(UPLOAD_JD_PATH):
                os.remove(UPLOAD_JD_PATH)

        return redirect(url_for("results"))

    return render_template("index.html")


# -------------------------
# Results page
# -------------------------
@app.route("/results")
def results():
    result = session.get("result")

    if not result:
        return redirect(url_for("analyze"))

    return render_template("results.html", result=result)

# -------------------------
# Resume Tailoring Advisor Page
# -------------------------
@app.route("/tailor")
def tailor():
    result = session.get("result")

    if not result:
        return redirect(url_for("analyze"))

    return render_template("tailor.html", result=result)


# -------------------------
# App runner (local + Render)
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
