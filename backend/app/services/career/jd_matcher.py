from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


def extract_keywords(text: str) -> set:
    """
    Extract meaningful keywords from text.
    Removes common stop words and keeps tech terms.
    """
    # Common tech keywords to look for
    tech_keywords = {
        "python", "java", "javascript", "react", "node", "fastapi",
        "django", "flask", "sql", "mysql", "postgresql", "mongodb",
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "docker", "kubernetes", "aws", "azure", "git", "github",
        "rest api", "graphql", "html", "css", "tailwind", "typescript",
        "langchain", "llm", "ai", "data science", "analytics",
        "communication", "teamwork", "leadership", "problem solving",
        "agile", "scrum", "devops", "ci/cd", "linux", "bash"
    }

    text_lower = text.lower()
    found_keywords = set()

    for keyword in tech_keywords:
        if keyword in text_lower:
            found_keywords.add(keyword)

    return found_keywords


def calculate_match_score(resume_text: str, job_description: str) -> dict:
    """
    Calculate how well a resume matches a job description.

    Method:
    1. TF-IDF vectorization of both texts
    2. Cosine similarity gives overall match score
    3. Keyword extraction finds specific matches/gaps

    Returns:
    - match_score: 0-100
    - matched_skills: skills in both
    - missing_skills: skills in JD but not resume
    - recommendation: AI advice
    """

    # Step 1 — TF-IDF + Cosine Similarity for overall score
    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),    # single words + pairs
            max_features=500
        )

        tfidf_matrix = vectorizer.fit_transform(
            [resume_text, job_description]
        )

        similarity = cosine_similarity(
            tfidf_matrix[0:1],
            tfidf_matrix[1:2]
        )[0][0]

        match_score = round(float(similarity) * 100, 1)

    except Exception as e:
        print(f"TF-IDF error: {e}")
        match_score = 0.0

    # Step 2 — Extract specific skill matches/gaps
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(job_description)

    matched_skills = list(resume_keywords & jd_keywords)
    missing_skills = list(jd_keywords - resume_keywords)

    # Step 3 — Generate recommendation
    if match_score >= 75:
        recommendation = (
            f"Strong match! ({match_score}%) Your resume aligns well. "
            f"Focus on highlighting: {', '.join(matched_skills[:3])}. "
            f"Consider adding: {', '.join(missing_skills[:2]) if missing_skills else 'nothing major missing'}."
        )
    elif match_score >= 50:
        recommendation = (
            f"Good match ({match_score}%) with room to improve. "
            f"Add these missing skills to your resume: {', '.join(missing_skills[:4])}. "
            f"Tailor your project descriptions to mention these keywords."
        )
    elif match_score >= 30:
        recommendation = (
            f"Partial match ({match_score}%). "
            f"You're missing several key requirements: {', '.join(missing_skills[:5])}. "
            f"Consider upskilling or applying to more suitable roles."
        )
    else:
        recommendation = (
            f"Low match ({match_score}%). "
            f"This role requires skills you haven't listed yet: {', '.join(missing_skills[:6])}. "
            f"Build these skills first or look for entry-level positions in this area."
        )

    return {
        "match_score": match_score,
        "matched_skills": sorted(matched_skills),
        "missing_skills": sorted(missing_skills),
        "recommendation": recommendation
    }