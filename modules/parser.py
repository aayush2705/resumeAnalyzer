import re
import io
import docx2txt
import PyPDF2
import difflib
import unicodedata

# Optional pdfplumber
try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except:
    _HAS_PDFPLUMBER = False

def extract_text(file_path):
    """
    Filepath-based extraction (used in view_resume only).
    """
    try:
        if file_path.lower().endswith(".pdf"):
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = []
                for page in reader.pages:
                    pages.append(page.extract_text() or "")
                return "\n".join(pages)

        if file_path.lower().endswith(".docx"):
            return docx2txt.process(file_path)

        return ""

    except:
        return ""

# ---------------- NORMALIZATION ----------------
def _normalize_token(s: str):
    s = s.lower().strip()
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[.\-/&]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


# ---------------- SKILL BANK ----------------
SKILL_BANK = [
    "c", "c++", "java", "python", "scala", "go",
    "c#", "dart", "kotlin", "swift", "javascript", "typescript",
    "html", "css", "bootstrap", "tailwind", "react", "nodejs", "express",
    "php", "laravel", "wordpress", "mongodb", "mysql", "postgresql",
    "rest api", "api development", "spring", "spring boot", "hibernate",
    "servlets", "j2ee", "microservices", "django", "flask", "fastapi",
    "automation", "scripting", "machine learning", "deep learning",
    "nlp", "opencv", "tensorflow", "pytorch", "scikit-learn",
    "huggingface", "transformers", "bert", "dbms", "sql", "pl/sql",
    "oracle", "normalization", "performance tuning", "backup", "rds",
    "excel", "power bi", "tableau", "data cleaning", "analytics",
    "azure", "aws", "gcp", "docker", "kubernetes", "jenkins",
    "terraform", "ci/cd", "ansible", "android", "jetpack compose",
    "firebase", "ios", "swiftui", "xcode", "uikit",
    "cybersecurity", "ethical hacking", "penetration testing",
    "network security", "firewall", "siem", "burp suite", "kali linux",
    "selenium", "pytest", "cypress", "quality assurance", "api testing",
    "figma", "adobe xd", "wireframes", "prototyping", "mockups",
    "ux design", "ui design", "dsa", "data structures",
    "object oriented programming", "git", "github", "postman",
    "matlab", "power automate"
]

NORMALIZED_SKILLS = {_normalize_token(s): s for s in SKILL_BANK}


# ---------------- CLEAN TEXT ----------------
def _clean_text(text):
    if not text:
        return ""
    text = text.replace("\u2022", "•")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    return text.strip()


# ---------------- OLD (RELIABLE) BYTE PDF EXTRACTOR ----------------
def _extract_pdf_bytes_pypdf2(file_bytes):
    """Stable extraction method that always worked for you."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    except:
        return ""


# ---------------- COMBINED PDF EXTRACTOR ----------------
def extract_text_bytes(file_bytes, mime):
    """
    Best hybrid approach:
    1. pdfplumber → if text is usable
    2. PyPDF2 (OLD version) → always worked reliably
    """

    if mime == "application/pdf":
        # 1. Try pdfplumber (but only keep if text is valid)
        if _HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    pages = [p.extract_text() or "" for p in pdf.pages]
                    text = "\n".join(pages).strip()
                    # pdfplumber sometimes returns garbage text, so verify:
                    if len(text) > 40:  # valid text
                        return _clean_text(text)
            except:
                pass

        # 2. Your old reliable method
        text = _extract_pdf_bytes_pypdf2(file_bytes)
        return _clean_text(text)

    # ------------ DOCX -------------
    if mime in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ]:
        try:
            return docx2txt.process(io.BytesIO(file_bytes)) or ""
        except:
            return ""

    return ""


# ---------------- NAME EXTRACTION ----------------
def extract_name(text):
    if not text:
        return "Unknown"
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for l in lines[:10]:
        if re.match(r"^[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}$", l):
            return l
    return lines[0] if lines else "Unknown"


# ---------------- EXPERIENCE EXTRACTION ----------------
def extract_experience(text):
    nums = re.findall(r'(\d+)\+?\s*(years?|yrs?)', text, re.I)
    if nums:
        return max(int(n[0]) for n in nums)
    return 0


# ---------------- SKILL EXTRACTION ----------------
def analyze_resume(text):
    lowered = (text or "").lower()

    found = []
    for skill in SKILL_BANK:
        sl = skill.lower()
        if re.search(rf"\b{re.escape(sl)}\b", lowered):
            found.append(sl)

    found = sorted(list(set(found)))
    exp = extract_experience(text)
    name = extract_name(text)

    return {
        "candidate_name": name,
        "skills_found": found,
        "experience": exp,
        "summary": f"Skills Found: {', '.join(found) if found else 'None'} | Experience: {exp} years"
    }
