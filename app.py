from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os

from services.resume_parser import extract_text
from services.skill_extractor import extract_skills
from services.jobs_api import get_jobs

app = Flask(__name__)

# =========================
# CONFIG
# =========================
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# ATS LEVEL
# =========================
def get_ats_level(score):
    if score > 80:
        return "Excellent"
    elif score > 60:
        return "Good"
    else:
        return "Needs Improvement"


# =========================
# ATS SCORING ENGINE
# =========================
def calculate_ats_score(text, skills):

    text_lower = text.lower()
    score = 0

    # Contact
    if "@" in text:
        score += 10

    # Skills
    score += min(len(set(skills)) * 2, 20)

    # Experience
    if "experience" in text_lower or "internship" in text_lower:
        score += 15

    # Projects
    if "project" in text_lower:
        score += 15

    # Certifications
    if "certificate" in text_lower or "certification" in text_lower:
        score += 10

    # Education
    if any(word in text_lower for word in [
        "education", "btech", "degree", "university"
    ]):
        score += 10

    # Resume length
    words = len(text.split())

    if words > 400:
        score += 20
    elif words > 250:
        score += 10
    else:
        score += 0

    # Hard penalties
    if "experience" not in text_lower and "internship" not in text_lower:
        score -= 20

    if "certificate" not in text_lower and "certification" not in text_lower:
        score -= 10

    if len(skills) < 3:
        score -= 15

    return max(min(score, 100), 0)
# =========================
# JOB MATCHING ENGINE
# =========================
def job_match_score(job, skills, text):

    job_text = (
        job.get("title", "") + " " +
        job.get("company", "") + " " +
        job.get("location", "")
    ).lower()

    score = 0

    for skill in skills:
        if skill.lower() in job_text:
            score += 15

    common_words = set(text.lower().split()) & set(job_text.split())
    score += len(common_words) * 2

    if "developer" in job_text:
        score += 5
    if "engineer" in job_text:
        score += 5

    return score


# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    file = request.files.get("resume")

    if not file:
        return jsonify({"error": "No resume uploaded"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Extract resume
    text = extract_text(filepath)
    skills = extract_skills(text)

    # ATS SCORE
    ats_score = calculate_ats_score(text, skills)

    # JOB KEYWORD (improved)
    keyword = " ".join(skills[:3]) if skills else "software developer"

    # Get jobs
    jobs = get_jobs(keyword)

    # Rank jobs
    for job in jobs:
        job["match_score"] = job_match_score(job, skills, text)

    jobs = sorted(jobs, key=lambda x: x["match_score"], reverse=True)

    # Ensure minimum jobs
    if len(jobs) < 5:
        extra_jobs = get_jobs("software developer")

        for job in extra_jobs:
            job["match_score"] = job_match_score(job, skills, text)

        seen = set()
        unique_jobs = []

        for job in jobs + extra_jobs:
            title = job.get("title")
            if title not in seen:
                unique_jobs.append(job)
                seen.add(title)

        jobs = unique_jobs

    jobs = jobs[:10]

    return jsonify({
        "ats_score": ats_score,
        "ats_level": get_ats_level(ats_score),
        "skills": skills,
        "jobs": jobs
    })


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)