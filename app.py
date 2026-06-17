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

    if "@" in text:
        score += 5

    if any(char.isdigit() for char in text):
        score += 5

    education_keywords = [
        "education", "btech", "b.e", "degree", "college", "university"
    ]
    if any(word in text_lower for word in education_keywords):
        score += 15

    skill_score = min(len(skills) * 2, 20)
    score += skill_score

    project_keywords = [
        "project", "projects", "developed", "implemented", "built"
    ]
    if any(word in text_lower for word in project_keywords):
        score += 20

    experience_keywords = [
        "experience", "internship", "intern", "employment", "worked"
    ]
    if any(word in text_lower for word in experience_keywords):
        score += 20

    cert_keywords = [
        "certification", "certificate", "aws", "azure",
        "google cloud", "coursera", "udemy"
    ]
    if any(word in text_lower for word in cert_keywords):
        score += 10

    sections = ["summary", "skills", "education", "project", "experience"]
    structure_count = sum(1 for s in sections if s in text_lower)
    score += min(structure_count, 5)

    return min(score, 100)


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