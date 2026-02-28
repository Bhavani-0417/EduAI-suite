import google.generativeai as genai
from app.core.config import settings

# Configure Gemini with your API key
genai.configure(api_key=settings.GOOGLE_API_KEY)

# Use Gemini Flash — free tier, fast responses
model = genai.GenerativeModel('gemini-1.5-flash')


def classify_note(text: str) -> dict:
    """
    Ask Gemini to identify what subject and topic
    a piece of text is about.
    
    Returns: {subject, topic, chapter}
    """
    prompt = f"""
    Analyze this academic text and identify:
    1. Subject (e.g., DBMS, Operating Systems, Machine Learning, Mathematics, Physics, etc.)
    2. Topic (specific topic within the subject)
    3. Chapter (chapter name if identifiable, else null)
    
    Text:
    {text[:1000]}
    
    Respond in this exact format (no extra text):
    SUBJECT: <subject name>
    TOPIC: <topic name>
    CHAPTER: <chapter name or null>
    """
    
    try:
        response = model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        
        result = {"subject": None, "topic": None, "chapter": None}
        
        for line in lines:
            if line.startswith("SUBJECT:"):
                result["subject"] = line.replace("SUBJECT:", "").strip()
            elif line.startswith("TOPIC:"):
                result["topic"] = line.replace("TOPIC:", "").strip()
            elif line.startswith("CHAPTER:"):
                chapter = line.replace("CHAPTER:", "").strip()
                result["chapter"] = None if chapter.lower() == "null" else chapter
        
        return result
    except Exception as e:
        print(f"Gemini classify error: {e}")
        return {"subject": "Unknown", "topic": "Unknown", "chapter": None}


def summarize_note(text: str) -> str:
    """
    Generate a concise summary of the note content.
    Used to show quick preview without reading whole note.
    """
    prompt = f"""
    Create a concise summary (3-5 bullet points) of this academic content.
    Focus on key concepts and important points.
    
    Content:
    {text[:3000]}
    
    Format:
    • Point 1
    • Point 2
    • Point 3
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini summarize error: {e}")
        return "Summary not available."


def answer_question_with_context(question: str, context_chunks: list[str]) -> str:
    """
    RAG — Answer Generation part.
    
    Takes:
    - question: what student asked
    - context_chunks: relevant text retrieved from ChromaDB
    
    Returns: AI-generated answer based ONLY on provided context
    """
    if not context_chunks:
        return "I couldn't find relevant information in your notes to answer this question. Try uploading more notes on this topic."
    
    context = "\n\n---\n\n".join(context_chunks)
    
    prompt = f"""
    You are a helpful study assistant. Answer the student's question 
    using ONLY the provided context from their notes.
    
    If the answer is not in the context, say: 
    "This topic doesn't appear in your uploaded notes."
    
    Be clear, concise, and educational in your response.
    
    CONTEXT FROM STUDENT'S NOTES:
    {context}
    
    STUDENT'S QUESTION:
    {question}
    
    ANSWER:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini answer error: {e}")
        return "Sorry, I couldn't generate an answer right now. Please try again."