import re

CAREERS = [
    {"role": "Python Developer", "skills": {"python", "django", "sql", "api", "git"}, "interests": {"backend", "web development", "automation"}, "description": "Build backend services, APIs, and Python applications."},
    {"role": "Full Stack Developer", "skills": {"html", "css", "javascript", "python", "django", "react", "sql"}, "interests": {"web development", "frontend", "backend"}, "description": "Build complete web applications from interface to database."},
    {"role": "Data Analyst", "skills": {"python", "sql", "excel", "power bi", "statistics"}, "interests": {"data", "analytics", "visualization"}, "description": "Turn datasets into insights, reports, and dashboards."},
    {"role": "AI / Machine Learning Engineer", "skills": {"python", "machine learning", "scikit-learn", "statistics", "pandas"}, "interests": {"ai", "machine learning", "data"}, "description": "Develop and evaluate models that learn patterns from data."},
    {"role": "Frontend Developer", "skills": {"html", "css", "javascript", "react", "git"}, "interests": {"frontend", "web development", "design"}, "description": "Create accessible, responsive, interactive user interfaces."},
    {"role": "QA Automation Engineer", "skills": {"python", "testing", "selenium", "api", "git"}, "interests": {"testing", "automation", "quality"}, "description": "Test software and automate repeatable quality checks."},
]

def tokens(text):
    return {x.strip().lower() for x in re.split(r"[,;\n|]+", text or "") if x.strip()}

def recommend_careers(skills, interests):
    skill_set, interest_set = tokens(skills), tokens(interests)
    results = []
    for career in CAREERS:
        skill_hits = len(skill_set & career["skills"])
        interest_hits = len(interest_set & career["interests"])
        total = len(career["skills"]) + len(career["interests"])
        score = round(100 * (skill_hits + interest_hits) / max(total, 1))
        missing = sorted(career["skills"] - skill_set)
        results.append({**career, "score": min(score, 100), "missing": missing})
    return sorted(results, key=lambda x: x["score"], reverse=True)

def compare_job(skills, description):
    known = tokens(skills)
    # A practical baseline vocabulary; not a substitute for semantic AI matching.
    vocabulary = {
        "python", "django", "flask", "sql", "mysql", "postgresql", "html", "css",
        "javascript", "react", "git", "rest api", "api", "machine learning",
        "scikit-learn", "pandas", "numpy", "communication", "testing", "selenium",
        "docker", "aws", "linux", "java", "c++", "problem solving", "data analysis",
        "excel", "power bi", "fastapi", "bootstrap", "authentication"
    }
    text = (description or "").lower()
    found = {term for term in vocabulary if term in text}
    matched = sorted(found & known)
    missing = sorted(found - known)
    score = round(100 * len(matched) / max(len(found), 1))
    return {"score": score, "required": sorted(found), "matched": matched, "missing": missing}
