import logging
import re

logger = logging.getLogger(__name__)

try:
    import spacy
    nlp = spacy.load("en_core_web_md")
    SPACY_AVAILABLE = True
    logger.info("spaCy loaded.")
except Exception:
    nlp = None
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available — using text matching only.")

# Canonical synonym map
SYNONYM_MAP = {
    "js": "javascript", "javascript": "javascript",
    "typescript": "typescript", "ts": "typescript",
    "node": "node.js", "node.js": "node.js", "nodejs": "node.js",
    "reactjs": "react", "react.js": "react", "react": "react",
    "vuejs": "vue", "vue.js": "vue", "vue": "vue",
    "angular": "angular", "angularjs": "angular",
    "py": "python", "python": "python",
    "c++": "c++", "cpp": "c++",
    "c#": "c#", "csharp": "c#",
    "golang": "go", "go": "go",
    "postgres": "postgresql", "postgresql": "postgresql",
    "mysql": "sql", "sql": "sql", "nosql": "nosql",
    "mongo": "mongodb", "mongodb": "mongodb",
    "ml": "machine learning", "machine learning": "machine learning",
    "ai": "artificial intelligence", "artificial intelligence": "artificial intelligence",
    "dl": "deep learning", "deep learning": "deep learning",
    "nlp": "natural language processing", "natural language processing": "natural language processing",
    "aws": "aws", "amazon web services": "aws",
    "gcp": "google cloud", "google cloud": "google cloud",
    "azure": "azure",
    "devops": "devops",
    "ci/cd": "ci/cd", "cicd": "ci/cd",
    "docker": "docker",
    "kubernetes": "kubernetes", "k8s": "kubernetes",
    "rest": "rest api", "rest api": "rest api", "restful": "rest api",
    "graphql": "graphql",
    "html": "html", "css": "css", "sass": "css", "scss": "css",
    "flask": "flask", "django": "django", "fastapi": "fastapi",
    "spring": "spring", "springboot": "spring",
    "git": "git", "github": "git",
    "agile": "agile", "scrum": "scrum", "jira": "jira",
    "communication": "communication", "teamwork": "teamwork",
    "leadership": "leadership",
    "problem solving": "problem solving", "problem-solving": "problem solving",
    "excel": "excel", "word": "microsoft word", "powerpoint": "powerpoint",
    "linux": "linux", "unix": "linux", "bash": "bash", "shell": "bash",
    "java": "java", "kotlin": "kotlin", "swift": "swift",
    "r": "r", "matlab": "matlab",
    "tableau": "tableau", "power bi": "power bi", "powerbi": "power bi",
    "figma": "figma", "photoshop": "photoshop", "illustrator": "illustrator",
    "tensorflow": "tensorflow", "pytorch": "pytorch",
    "microsoft office": "microsoft office",
    "technical troubleshooting": "technical troubleshooting",
    "customer service": "customer service",
    "sales": "sales",
    "project management": "project management",
    "data analysis": "data analysis",
    "website development": "website development",
    "web development": "website development",
}

CAREER_RECOMMENDATIONS = [
    {"title": "Backend Developer",
     "keywords": ["python", "java", "flask", "django", "fastapi", "sql", "postgresql",
                  "mongodb", "rest api", "node.js", "go", "c#", "spring"],
     "min_matches": 1},
    {"title": "Frontend Developer",
     "keywords": ["react", "vue", "angular", "javascript", "typescript", "html", "css", "figma"],
     "min_matches": 1},
    {"title": "Full Stack Developer",
     "keywords": ["react", "node.js", "javascript", "python", "sql", "rest api", "html", "css",
                  "mongodb", "flask", "django"],
     "min_matches": 2},
    {"title": "Data Scientist",
     "keywords": ["python", "machine learning", "deep learning", "natural language processing",
                  "sql", "r", "matlab", "tableau", "power bi", "tensorflow", "pytorch"],
     "min_matches": 1},
    {"title": "Machine Learning Engineer",
     "keywords": ["python", "machine learning", "deep learning", "artificial intelligence",
                  "natural language processing", "tensorflow", "pytorch"],
     "min_matches": 1},
    {"title": "DevOps Engineer",
     "keywords": ["docker", "kubernetes", "ci/cd", "aws", "azure", "google cloud",
                  "git", "devops", "linux", "bash"],
     "min_matches": 1},
    {"title": "Cloud Engineer",
     "keywords": ["aws", "azure", "google cloud", "docker", "kubernetes", "devops", "linux"],
     "min_matches": 1},
    {"title": "Software Engineer",
     "keywords": ["python", "java", "c++", "c#", "go", "git", "agile",
                  "rest api", "javascript", "typescript", "linux"],
     "min_matches": 1},
    {"title": "Mobile Developer",
     "keywords": ["swift", "kotlin", "java", "react", "javascript", "typescript"],
     "min_matches": 1},
    {"title": "Data Analyst",
     "keywords": ["sql", "python", "excel", "tableau", "power bi", "r", "matlab", "data analysis"],
     "min_matches": 1},
    {"title": "UI/UX Designer",
     "keywords": ["figma", "photoshop", "illustrator", "css", "html", "javascript"],
     "min_matches": 1},
    {"title": "Project Manager / Scrum Master",
     "keywords": ["agile", "scrum", "jira", "leadership", "communication",
                  "teamwork", "project management"],
     "min_matches": 1},
    {"title": "Insurance / Financial Services",
     "keywords": ["sales", "customer service", "communication", "leadership", "microsoft office"],
     "min_matches": 1},
    {"title": "Technical Support Specialist",
     "keywords": ["technical troubleshooting", "customer service", "communication",
                  "microsoft office", "linux"],
     "min_matches": 1},
    {"title": "Web Developer",
     "keywords": ["website development", "html", "css", "javascript", "react", "vue"],
     "min_matches": 1},
]


def normalize_skill(skill):
    return SYNONYM_MAP.get(skill.strip().lower(), skill.strip().lower())


def skill_matches_resume(skill, resume_text, resume_token_str):
    canonical = normalize_skill(skill)

    # Direct substring match
    if canonical in resume_text:
        return True

    # Check all aliases for this canonical skill
    for alias, canon in SYNONYM_MAP.items():
        if canon == canonical and alias in resume_text:
            return True

    # spaCy semantic similarity (optional enhancement)
    if SPACY_AVAILABLE and nlp:
        try:
            skill_doc = nlp(canonical)
            snippet = resume_text[:8000]
            resume_doc = nlp(snippet)
            if skill_doc.has_vector and resume_doc.has_vector:
                if skill_doc.similarity(resume_doc) > 0.82:
                    return True
        except Exception as e:
            logger.debug(f"spaCy similarity error for '{skill}': {e}")

    return False


def generate_recommendations(matched_skills):
    matched_set = set(matched_skills)
    scored = []
    for role in CAREER_RECOMMENDATIONS:
        overlap = matched_set.intersection(set(role["keywords"]))
        if len(overlap) >= role["min_matches"]:
            scored.append((len(overlap), role["title"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [title for _, title in scored[:3]]


def match_skills(resume_text, resume_tokens, job_skills, experience_years=0):
    """
    Matches job skills against resume.
    Returns matched, missing, weighted score (0-100), and recommendations.
    Weights: 70% skill overlap + 30% experience.
    """
    matched = []
    missing = []
    resume_token_str = " ".join(resume_tokens)

    for skill in job_skills:
        if skill_matches_resume(skill, resume_text, resume_token_str):
            matched.append(normalize_skill(skill))
        else:
            missing.append(normalize_skill(skill))

    total = len(matched) + len(missing)
    skill_score = (len(matched) / total * 100) if total > 0 else 0
    experience_score = min((experience_years / 3) * 100, 100) if experience_years > 0 else 50
    final_score = int((skill_score * 0.70) + (experience_score * 0.30))

    recommendations = generate_recommendations(matched)

    return matched, missing, final_score, recommendations