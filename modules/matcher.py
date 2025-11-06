from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def clean_text(text):
    """
    Preprocess text: lowercase, remove special characters, extra spaces
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def match_resume_job(resume_text, job_text):
    """
    Input:
        resume_text: str -> text extracted from resume
        job_text: str -> text extracted from job description
    Output:
        result: dict -> match score, strengths, weaknesses
    """
    resume_text = clean_text(resume_text)
    job_text = clean_text(job_text)

    # Convert texts to TF-IDF vectors
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_text, job_text])

    # Compute cosine similarity
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    match_score = round(similarity * 100, 2)  # percentage

    # Find strengths (keywords in both resume & job)
    resume_words = set(resume_text.split())
    job_words = set(job_text.split())
    strengths = list(resume_words.intersection(job_words))

    # Weaknesses (keywords in job but missing in resume)
    weaknesses = list(job_words.difference(resume_words))

    # Limit displayed items to first 10 for readability
    strengths = strengths[:10]
    weaknesses = weaknesses[:10]

    result = {
        'score': match_score,
        'strengths': strengths,
        'weaknesses': weaknesses
    }
    return result
