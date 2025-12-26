from flask import Flask, render_template, request, redirect, url_for, session
from resume_parser import extract_resume_text
from gemini_service import analyze_resume
import os

app = Flask(__name__)

# -------------------------
# App configuration
# -------------------------
app.secret_key = "resume_ai_secret_key"   # must stay constant
UPLOAD_PATH = "uploaded_resume.pdf"


# -------------------------
# Home page
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")


# -------------------------
# Resume Analyzer (Form)
# -------------------------
@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if request.method == "POST":
        resume = request.files.get("resume")
        job_desc = request.form.get("job_description", "").strip()

        # Basic validation
        if not resume or not job_desc:
            return redirect(url_for("analyze"))

        resume.save(UPLOAD_PATH)

        try:
            resume_text = extract_resume_text(UPLOAD_PATH)
            result = analyze_resume(resume_text, job_desc)

            # 🔍 Debug: confirm result creation
            print("✅ RESULT GENERATED:", result)

            session["result"] = result

        except Exception as e:
            print("❌ ANALYSIS ERROR:", e)
            session["result"] = {
                "error": str(e),
                "ats_score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "ai_strengths": [],
                "ai_improvements": [],
                "detected_role": "unknown"
            }

        finally:
            if os.path.exists(UPLOAD_PATH):
                os.remove(UPLOAD_PATH)

        return redirect(url_for("results"))

    return render_template("index.html")


# -------------------------
# Results page
# -------------------------
@app.route("/results")
def results():
    result = session.get("result")

    # 🔍 Debug: confirm session persistence
    print("📊 RESULT IN SESSION:", result)

    if not result:
        return redirect(url_for("analyze"))

    return render_template("results.html", result=result)


# -------------------------
# App runner
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

