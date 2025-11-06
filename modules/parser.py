# import re
# import docx2txt
# import PyPDF2


# def extract_text(file_path):
#     """Extract raw text from .pdf or .docx resumes."""
#     text = ""
#     if file_path.endswith(".pdf"):
#         with open(file_path, "rb") as f:
#             reader = PyPDF2.PdfReader(f)
#             for page in reader.pages:
#                 text += page.extract_text() or ""
#     elif file_path.endswith(".docx"):
#         text = docx2txt.process(file_path)
#     return text.strip()


# def analyze_resume(text):
#     """Keyword-based analysis with suggested roles."""
#     skills = [
#         "Python", "Java", "C++", "Machine Learning", "Deep Learning",
#         "Data Analysis", "SQL", "HTML", "CSS", "JavaScript",
#         "Flask", "Django", "React", "AWS"
#     ]

#     # Detect skills
#     found = [s for s in skills if re.search(rf"\b{s}\b", text, re.I)]

#     # Extract experience years
#     experience = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', text, re.I)
#     exp_val = max(map(int, experience)) if experience else 0

#     # Suggested roles logic
#     suggestions = []
#     if "Machine Learning" in found or "Deep Learning" in found:
#         suggestions.append("Data Scientist")
#     if "Flask" in found or "Django" in found:
#         suggestions.append("Backend Developer")
#     if "React" in found or "JavaScript" in found:
#         suggestions.append("Frontend Developer")
#     if "SQL" in found and "Python" in found:
#         suggestions.append("Data Analyst")

#     # Final dictionary returned to Flask
#     return {
#         "skills_found": found,
#         "experience": exp_val,
#         "summary": f"Skills: {', '.join(found) if found else 'None found'} | Experience: {exp_val} years",
#         "suggested_roles": ', '.join(suggestions) if suggestions else "Not enough data"
#     }


import re
import docx2txt
import PyPDF2


def extract_text(file_path):
    """Extract raw text from .pdf or .docx resumes."""
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
    """
    Attempt to extract candidate name from resume text.
    Basic heuristics:
    - Looks for the first line or a capitalized full name.
    - Skips lines with keywords like 'Resume', 'Curriculum Vitae', etc.
    """
    # Split text into lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    possible_name = ""

    for line in lines[:10]:  # check top 10 lines
        if re.search(r"(resume|curriculum vitae|cv)", line, re.I):
            continue
        # Looks for a line with 2-3 capitalized words (common in names)
        if re.match(r"^[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}$", line):
            possible_name = line
            break

    if not possible_name and lines:
        possible_name = lines[0]  # fallback: take the first line

    return possible_name.strip()


def analyze_resume(text):
    """Keyword-based analysis with suggested roles."""
    skills = [
        "Python", "Java", "C++", "Machine Learning", "Deep Learning",
        "Data Analysis", "SQL", "HTML", "CSS", "JavaScript",
        "Flask", "Django", "React", "AWS"
    ]

    # Detect skills
    found = [s for s in skills if re.search(rf"\b{s}\b", text, re.I)]

    # Extract experience years
    experience = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', text, re.I)
    exp_val = max(map(int, experience)) if experience else 0

    # Suggested roles logic
    suggestions = []
    if "Machine Learning" in found or "Deep Learning" in found:
        suggestions.append("Data Scientist")
    if "Flask" in found or "Django" in found:
        suggestions.append("Backend Developer")
    if "React" in found or "JavaScript" in found:
        suggestions.append("Frontend Developer")
    if "SQL" in found and "Python" in found:
        suggestions.append("Data Analyst")

    # Extract candidate name
    candidate_name = extract_name(text)

    # Final dictionary returned to Flask
    return {
        "candidate_name": candidate_name or "Unknown",
        "skills_found": found,
        "experience": exp_val,
        "summary": f"Skills: {', '.join(found) if found else 'None found'} | Experience: {exp_val} years",
        "suggested_roles": ', '.join(suggestions) if suggestions else "Not enough data"
    }
