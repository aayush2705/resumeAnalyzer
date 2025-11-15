import re
import docx2txt
import PyPDF2
import difflib
import unicodedata
import io

# Optional: use pdfplumber if available (better PDF text extraction)
try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except Exception:
    _HAS_PDFPLUMBER = False

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

def _normalize_token(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFKC", s)
    s = s.replace(".", "")
    s = s.replace("/", " ")
    s = s.replace("-", " ")
    s = s.replace("&", " and ")
    s = re.sub(r"\s+", " ", s)
    return s

NORMALIZED_SKILLS = { _normalize_token(s): s for s in SKILL_BANK }

# ---------------- Text extraction ----------------
def extract_text(file_path: str) -> str:
    text = ""
    if file_path.lower().endswith(".pdf"):
        if _HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(file_path) as pdf:
                    pages = []
                    for p in pdf.pages:
                        ptext = p.extract_text() or ""
                        pages.append(ptext)
                    text = "\n".join(pages)
            except Exception:
                text = _extract_pdf_pypdf2(file_path)
        else:
            text = _extract_pdf_pypdf2(file_path)
    elif file_path.lower().endswith(".docx"):
        try:
            text = docx2txt.process(file_path) or ""
        except Exception:
            text = ""
    else:
        text = _extract_pdf_pypdf2(file_path)

    text = text.replace("\u2022", "•")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\r\n?", "\n", text)
    text = "\n".join(re.sub(r"[ \t]{2,}", " ", ln).strip() for ln in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _extract_pdf_pypdf2(file_path: str) -> str:
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pages = []
            for page in reader.pages:
                ptext = page.extract_text() or ""
                pages.append(ptext)
            text = "\n".join(pages)
    except Exception:
        text = ""
    return text

# ---------------- Name extraction ----------------
def extract_name(text: str) -> str:
    if not text:
        return "Unknown"
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    lines = [ln for ln in lines if not re.search(r"\b(resume|curriculum vitae|cv)\b", ln, re.I)]

    patterns = [
        r"^[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,3}$",
        r"^[A-Z][A-Z\s\-']{1,40}$",
        r"^[A-Za-z]{2,}\s[A-Za-z]{2,}$"
    ]
    for ln in lines[:12]:
        for p in patterns:
            if re.match(p, ln):
                return ln.strip()

    email = re.search(r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
    if email:
        local = email.group(1)
        pretty = local.replace(".", " ").replace("_", " ").title()
        if len(pretty.split()) <= 4:
            return pretty

    return lines[0] if lines else "Unknown"

# ---------------- Experience extraction ----------------
_NUMBER_WORDS = {
    "zero":0, "one":1, "two":2, "three":3, "four":4, "five":5,
    "six":6, "seven":7, "eight":8, "nine":9, "ten":10
}

def extract_experience(text: str) -> int:
    lowered = text.lower()
    m = re.findall(r"(\d+)\s*(?:\+|-)?\s*(?:to\s*)?(\d+)?\s*(?:years|year|yrs|yr)\b", lowered)
    if m:
        nums = [int(n) for n in m[0] if n]
        return max(nums) if nums else 0

    m2 = re.search(r"(\d+)\s*(?:\+)?\s*(?:years|year|yrs|yr)\b", lowered)
    if m2:
        return int(m2.group(1))

    for w, val in _NUMBER_WORDS.items():
        if re.search(rf"\b{w}\b\s*(?:years|year|yrs|yr)\b", lowered):
            return val

    return 0

# ---------------- Skill extraction ----------------
def analyze_resume(text: str) -> dict:
    lowered = (text or "").lower()
    lines = [ln.strip() for ln in lowered.splitlines() if ln.strip()]

    skill_headers = [
        "skills", "technical skills", "key skills", "skillset", "skills & tools",
        "competencies", "software skills", "languages/tools", "skills summary",
        "professional skills", "strengths", "skills:", "skillset:", "technical competency","key expertise"
    ]

    skill_section = ""
    found_header = False
    for i, ln in enumerate(lines):
        for header in skill_headers:
            if ln.startswith(header) or ln.startswith(header + ":") or header in ln.split("|")[0]:
                section_lines = []
                for nxt in lines[i+1:i+15]:
                    if re.search(r"(education|experience|projects|certificat|achiev|contact|declaration)", nxt):
                        break
                    section_lines.append(nxt)
                skill_section = "\n".join(section_lines).strip()
                found_header = True
                break
        if found_header:
            break

    if not skill_section:
        candidates = []
        for ln in lines:
            if ("," in ln) or ("•" in ln) or (" -" in ln[:3]) or any(tok in ln for tok in NORMALIZED_SKILLS):
                candidates.append(ln)
        skill_section = "\n".join(candidates[:12])

    if not skill_section.strip():
        for ln in lines:
            if ("," in ln) or any(tok in ln for tok in NORMALIZED_SKILLS):
                skill_section += ln + "\n"

    found_skills = set()
    section_text = _normalize_token(skill_section)

    possible_items = re.split(r"[,\|\;/•\n]+", section_text)
    possible_items = [p.strip() for p in possible_items if p.strip()]

    # ---------------- FIXED: SAFE MATCHING ----------------
    def match_token(token: str):
        token_n = _normalize_token(token)

        # 1. EXACT MATCH
        if token_n in NORMALIZED_SKILLS:
            return NORMALIZED_SKILLS[token_n]

        # 2. STRICT MATCH FOR SHORT & SINGLE-LETTER SKILLS
        if token_n in ("c", "c++", "c#"):
            return token_n if token_n in NORMALIZED_SKILLS else None

        # 3. SUBSTRING MATCH ONLY FOR MULTI-WORD SKILLS
        for nk, original in NORMALIZED_SKILLS.items():
            if len(nk) > 1 and nk in token_n:
                return original

        # 4. FUZZY MATCH
        close = difflib.get_close_matches(token_n, NORMALIZED_SKILLS.keys(), n=1, cutoff=0.85)
        if close:
            return NORMALIZED_SKILLS[close[0]]

        return None
    # -----------------------------------------------------

    for item in possible_items:
        candidate = match_token(item)
        if candidate:
            found_skills.add(candidate)

    if not found_skills:
        words = re.findall(r"\w[\w+#.+-]*", section_text)
        for n in (3,2,1):
            for i in range(len(words)-n+1):
                phrase = " ".join(words[i:i+n])
                match = match_token(phrase)
                if match:
                    found_skills.add(match)

    if not found_skills:
        whole = _normalize_token(lowered)
        for nk, original in NORMALIZED_SKILLS.items():
            if re.search(rf"\b{re.escape(nk)}\b", whole):
                found_skills.add(original)

    found_skills = sorted(found_skills, key=lambda s: s.lower())
    experience = extract_experience(text)

    summary = f"Skills Found: {', '.join(found_skills) if found_skills else 'None'} | Experience: {experience} years"

    return {
        "skills_found": found_skills,
        "experience": experience,
        "summary": summary
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