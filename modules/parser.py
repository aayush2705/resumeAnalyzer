import re
import docx2txt
import PyPDF2
import io
SKILL_BANK = {

    # ------------------- PROGRAMMING LANGUAGES -------------------
    "python", "java", "c", "c++", "c#", "javascript", "typescript",
    "go", "dart", "swift", "kotlin", "ruby", "php", "r", "scala",
    "matlab", "rust", "bash", "powershell",

    # ------------------- DATA SCIENCE / ML -----------------------
    "machine learning", "deep learning", "ai", "nlp", "computer vision",
    "tensorflow", "keras", "pytorch", "scikit-learn", "transformers",
    "bert", "gpt", "data mining", "regression", "classification",
    "clustering", "time series", "statistics", "probability",
    "matplotlib", "seaborn", "numpy", "pandas",

    # ------------------- DATA ANALYST ------------------------------
    "sql", "mysql", "postgresql", "mongodb", "power bi", "tableau",
    "excel", "google sheets", "analytics", "dashboarding",
    "etl", "bigquery", "data visualization", "data cleaning",

    # ------------------- WEB DEVELOPMENT ---------------------------
    "html", "css", "bootstrap", "sass", "react", "redux", "angular",
    "vue", "nextjs", "tailwind", "jquery", "ajax", "node", "express",
    "django", "flask", "laravel", "spring boot", "graphql", "rest api",
    "wordpress",

    # ------------------- FRONTEND UX / UI --------------------------
    "ui design", "ux design", "responsive design", "figma",
    "adobe xd", "wireframing", "prototyping", "photoshop",
    "design systems",

    # ------------------- CLOUD / DEVOPS ----------------------------
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "jenkins", "github actions", "ci/cd", "linux", "nginx",
    "prometheus", "grafana", "microservices", "api gateway",

    # ------------------- CYBERSECURITY -----------------------------
    "cybersecurity", "ethical hacking", "penetration testing",
    "network security", "nmap", "burp suite", "kali linux",
    "firewall", "siem", "cryptography", "vulnerability assessment",

    # ------------------- QUALITY ASSURANCE -------------------------
    "manual testing", "automation testing", "selenium", "cypress",
    "postman", "pytest", "test cases", "bug tracking", "jira",

    # ------------------- DATABASE ADMIN ----------------------------
    "oracle", "dbms", "database design", "normalization",
    "backup", "performance tuning", "sql server",

    # ------------------- PRODUCT MANAGEMENT ------------------------
    "product management", "product owner", "scrum", "agile",
    "roadmap", "market research", "competitive analysis",

    # ------------------- BUSINESS ANALYST --------------------------
    "requirements gathering", "requirement analysis", "process mapping",
    "user stories", "use cases", "documentation", "reporting",
    "ms visio",

    # ------------------- PROJECT MANAGEMENT ------------------------
    "project management", "pmp", "kanban", "trello", "asana",
    "leadership", "risk management"
}



def extract_text(file_path):
    text = ""
    if file_path.endswith(".pdf"):
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    elif file_path.endswith(".docx"):
        text = docx2txt.process(file_path)
    return text.strip()


def extract_name(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:10]:
        if re.search(r"(resume|curriculum vitae|cv)", line, re.I):
            continue
        if re.match(r"^[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}$", line):
            return line.strip()
    return lines[0] if lines else "Unknown"


def analyze_resume(text):
    """Extract skills automatically using SKILL_BANK and detect experience."""
    
    # normalize resume text
    lowered = text.lower()

    # -------------------------------
    # 1) Extract Skills Automatically
    # -------------------------------
    found_skills = []

    for skill in SKILL_BANK:
        skill_lower = skill.lower().strip()

        # multi-word matching
        pattern = r"\b" + re.escape(skill_lower) + r"\b"

        if re.search(pattern, lowered, re.IGNORECASE):
            found_skills.append(skill_lower)

    # remove duplicates & sort
    found_skills = sorted(list(set(found_skills)))

    # ----------------------------------
    # 2) Extract Experience in Years
    # ----------------------------------
    experience = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', text, re.I)
    exp_val = max(map(int, experience)) if experience else 0

    # ----------------------------------
    # 3) Extract candidate name
    # ----------------------------------
    candidate_name = extract_name(text)

    # ----------------------------------
    # RETURN FINAL RESULT
    # ----------------------------------
    return {
        "candidate_name": candidate_name or "Unknown",
        "skills_found": found_skills,
        "experience": exp_val,
        "summary": f"Skills: {', '.join(found_skills) if found_skills else 'None found'} "
                   f"| Experience: {exp_val} years",
        "suggested_roles": "Auto-role handled in app.py"
    }

def extract_text_bytes(file_bytes, mime):
    if mime == "application/pdf":
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    if mime in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ]:
        buffer = io.BytesIO(file_bytes)
        return docx2txt.process(buffer)

    return ""