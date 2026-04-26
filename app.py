import logging
import io
import time
import re

import docx2txt
import pdfplumber
from flask import Flask, request, jsonify
from flask_cors import CORS

from preprocess import preprocess
from experience import extract_experience
from matcher import match_skills, normalize_skill, SYNONYM_MAP

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# ── Known skills list for auto-extraction from job descriptions ────────────────
ALL_KNOWN_SKILLS = sorted(set(SYNONYM_MAP.keys()), key=len, reverse=True)


def get_extension(filename):
    f = filename.lower()
    if f.endswith(".pdf"):  return ".pdf"
    if f.endswith(".docx"): return ".docx"
    return None


def validate_file(file):
    ext = get_extension(file.filename)
    if not ext:
        return False, "Unsupported file type. Please upload a PDF or DOCX file."
    file_bytes = file.read()
    file.seek(0)
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return False, "File exceeds the 10MB size limit."
    return True, None


def extract_text(file):
    ext = get_extension(file.filename)
    file_bytes = file.read()
    file.seek(0)
    try:
        if ext == ".pdf":
            text = ""
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text.lower()
        elif ext == ".docx":
            text = docx2txt.process(io.BytesIO(file_bytes))
            return text.lower() if text else ""
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
    return ""


def auto_extract_skills(job_text):
    """
    Automatically extracts skills from a full job description.
    Scans for all known skills/synonyms in the text and returns canonical names.
    Falls back to comma-split if no skills found via scanning.
    """
    job_lower = job_text.lower()
    found = set()

    for skill in ALL_KNOWN_SKILLS:
        # Use word boundary matching to avoid partial matches
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, job_lower):
            found.add(normalize_skill(skill))

    # If auto-extract found skills, use them
    if found:
        logger.info(f"Auto-extracted {len(found)} skills from job description.")
        return list(found)

    # Fallback: treat input as comma-separated skills list
    logger.info("Auto-extract found nothing — treating input as comma-separated skills.")
    return [s.strip().lower() for s in job_text.split(",") if s.strip()]


def generate_tips(missing_skills, matched_skills, experience_years):
    """
    Generates specific, actionable resume improvement tips based on results.
    """
    tips = []

    # Tips based on missing skills
    skill_tips = {
        "python":     "Add a Python projects section showcasing scripts, automation, or data analysis work.",
        "sql":        "Mention any database work (queries, schema design, reporting) in your experience bullets.",
        "javascript": "List any web projects or tools built with JavaScript, even personal/hobby projects.",
        "react":      "Include frontend projects using React — even a portfolio site counts.",
        "git":        "Add 'Version control with Git/GitHub' to your skills and link your GitHub profile.",
        "docker":     "Note any containerization or deployment experience, even from coursework.",
        "aws":        "Mention cloud platforms used in any project, internship, or coursework.",
        "machine learning": "Include ML coursework, Kaggle projects, or research in a Projects section.",
        "agile":      "Add 'Agile/Scrum methodology' if you've worked in sprints or used Jira.",
        "communication": "Highlight client-facing, presentation, or cross-team collaboration experience.",
        "leadership": "Include team lead roles, mentoring, or project ownership in your bullets.",
        "html":       "List any websites or web pages you've built, even simple ones.",
        "css":        "Mention UI/styling work in project descriptions.",
    }

    for skill in missing_skills[:3]:
        if skill in skill_tips:
            tips.append(skill_tips[skill])

    # General tips based on score patterns
    if len(missing_skills) > len(matched_skills):
        tips.append("Consider tailoring your resume specifically to each job by mirroring the job description's language.")

    if experience_years == 0:
        tips.append("Add a quantified experience section — include years or months for each role to strengthen your profile.")

    if len(matched_skills) > 0 and len(missing_skills) > 0:
        tips.append(f"Your resume matches {len(matched_skills)} required skill(s). Prioritize adding the missing ones through projects, courses, or certifications.")

    if not tips:
        tips.append("Your resume looks strong for this role. Consider adding metrics and outcomes to your experience bullets to stand out further.")

    return tips[:4]  # Max 4 tips


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/upload", methods=["POST"])
def upload():
    start = time.time()
    try:
        file = request.files.get("file")
        job_description = request.form.get("jobDescription", "").strip()

        if not file or file.filename == "":
            return jsonify({"error": "No file uploaded."}), 400

        if not job_description:
            return jsonify({"error": "Job description cannot be empty."}), 400

        is_valid, error_msg = validate_file(file)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        resume_text = extract_text(file)
        if not resume_text or len(resume_text.strip()) < 20:
            return jsonify({"error": "Could not read the file. Make sure it contains readable text."}), 400

        resume_tokens = preprocess(resume_text)
        experience_years = extract_experience(resume_text)

        # Auto-extract skills from full job description
        job_skills = auto_extract_skills(job_description)

        if not job_skills:
            return jsonify({"error": "No recognizable skills found. Try listing skills separated by commas."}), 400

        matched, missing, score, recommendations = match_skills(
            resume_text, resume_tokens, job_skills, experience_years
        )

        tips = generate_tips(missing, matched, experience_years)

        elapsed = time.time() - start
        logger.info(f"Done in {elapsed:.2f}s — Score:{score} Matched:{len(matched)} Missing:{len(missing)}")

        return jsonify({
            "score": score,
            "matched": matched,
            "missing": missing,
            "recommendations": recommendations,
            "tips": tips,
            "experience_years": experience_years,
            "skills_found": len(job_skills)
        })

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "An unexpected server error occurred. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)