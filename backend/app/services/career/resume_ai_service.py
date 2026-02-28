from app.services.ai.gemini_service import model


def optimize_resume_objective(
    objective: str,
    target_role: str,
    skills: list
) -> str:
    """
    Use Gemini to rewrite the objective statement
    to be ATS-friendly and role-specific.
    """
    prompt = f"""
    Rewrite this resume objective to be ATS-optimized 
    for the role: {target_role}
    
    Current objective: {objective or "Not provided"}
    Key skills: {', '.join(skills[:8])}
    
    Requirements:
    - Max 3 sentences
    - Include relevant keywords for {target_role}
    - Sound professional and confident
    - Start with a strong action word
    
    Return ONLY the rewritten objective, no extra text.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini objective error: {e}")
        return objective or f"Motivated student seeking {target_role} role."


def optimize_project_description(description: str, target_role: str) -> str:
    """Rewrite project description to be ATS-friendly"""
    prompt = f"""
    Rewrite this project description for a resume targeting: {target_role}
    
    Original: {description}
    
    Requirements:
    - Start with a strong action verb (Built, Developed, Designed, etc.)
    - Include metrics if possible (improved by X%, reduced time by Y%)
    - Max 2 sentences
    - Highlight technical impact
    
    Return ONLY the rewritten description.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return description


def generate_ats_tips(skills: list, target_role: str) -> list:
    """
    Generate personalized ATS improvement tips
    based on student's skills and target role.
    """
    prompt = f"""
    Give 5 specific ATS (Applicant Tracking System) tips 
    for a student targeting: {target_role}
    Current skills: {', '.join(skills[:10])}
    
    Format as a simple list, one tip per line.
    Start each with an action word.
    No numbering, no bullet characters.
    """
    try:
        response = model.generate_content(prompt)
        tips = [
            line.strip()
            for line in response.text.strip().split('\n')
            if line.strip()
        ]
        return tips[:5]
    except Exception as e:
        return [
            "Include keywords from the job description",
            "Use standard section headings",
            "Quantify achievements where possible",
            "Keep formatting clean and simple",
            "List skills that match the job requirements"
        ]