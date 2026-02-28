from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from app.core.config import settings
import json
import re


# Initialize Gemini through LangChain
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.7       # some creativity but not too random
)


def plan_presentation(
    topic: str,
    num_slides: int,
    style: str,
    key_points: list = None,
    subject: str = None
) -> list:
    """
    Use LangChain to plan the full presentation structure.

    LangChain here:
    PromptTemplate → fills in variables
    LLMChain       → sends to Gemini, gets response
    We parse       → structured slide list

    Returns list of slide dicts:
    [
        {"title": "...", "bullet_points": [...], "speaker_notes": "..."},
        ...
    ]
    """

    key_points_text = ""
    if key_points:
        key_points_text = f"Make sure to cover these points: {', '.join(key_points)}"

    subject_text = f"Subject area: {subject}" if subject else ""

    prompt = PromptTemplate(
        input_variables=["topic", "num_slides", "style", "key_points", "subject"],
        template="""
        Create a {style} presentation plan on: {topic}
        {subject}
        Number of slides: {num_slides}
        {key_points}

        Create exactly {num_slides} slides including title and conclusion slides.

        For each slide provide:
        - A clear, concise title
        - 3-5 bullet points (each max 10 words)
        - Brief speaker notes (2-3 sentences)

        Format your response as valid JSON array like this:
        [
            {{
                "title": "slide title here",
                "bullet_points": ["point 1", "point 2", "point 3"],
                "speaker_notes": "speaker notes here"
            }}
        ]

        Return ONLY the JSON array, no other text.
        """
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    try:
        response = chain.run(
            topic=topic,
            num_slides=num_slides,
            style=style,
            key_points=key_points_text,
            subject=subject_text
        )

        # Clean response — remove markdown code blocks if present
        cleaned = response.strip()
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        slides = json.loads(cleaned)
        print(f"✅ Planned {len(slides)} slides for: {topic}")
        return slides

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {response}")
        # Fallback — create basic slides manually
        return _fallback_slides(topic, num_slides)
    except Exception as e:
        print(f"LangChain error: {e}")
        return _fallback_slides(topic, num_slides)


def plan_document(
    title: str,
    topic: str,
    doc_type: str,
    key_points: list = None,
    subject: str = None
) -> dict:
    """
    Plan document structure and content using LangChain.

    Returns dict with sections:
    {
        "abstract": "...",
        "introduction": "...",
        "sections": [{"heading": "...", "content": "..."}],
        "conclusion": "...",
        "references": [...]
    }
    """

    key_points_text = ""
    if key_points:
        key_points_text = f"Cover these points: {', '.join(key_points)}"

    doc_instructions = {
        "assignment": "Write as a student assignment with introduction, main body, and conclusion",
        "project_report": "Write as a technical project report with abstract, introduction, methodology, results, conclusion",
        "lab_manual": "Write as a lab manual with objective, theory, procedure, observations, result",
        "research_paper": "Write as an academic research paper with abstract, introduction, literature review, methodology, results, conclusion"
    }

    instruction = doc_instructions.get(doc_type, doc_instructions["assignment"])

    prompt = PromptTemplate(
        input_variables=["title", "topic", "instruction", "key_points", "subject"],
        template="""
        Write content for a {title} document about: {topic}
        Subject: {subject}
        Document type instruction: {instruction}
        {key_points}

        Generate the complete document content in this JSON format:
        {{
            "abstract": "150 word abstract/overview",
            "introduction": "300 word introduction",
            "sections": [
                {{
                    "heading": "Section heading",
                    "content": "Section content (200-300 words)"
                }}
            ],
            "conclusion": "200 word conclusion",
            "references": ["Reference 1", "Reference 2", "Reference 3"]
        }}

        Include 3-5 main sections. Make content educational and accurate.
        Return ONLY valid JSON, no other text.
        """
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    try:
        response = chain.run(
            title=title,
            topic=topic,
            instruction=instruction,
            key_points=key_points_text,
            subject=subject or "General"
        )

        cleaned = response.strip()
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        content = json.loads(cleaned)
        print(f"✅ Document content planned for: {title}")
        return content

    except Exception as e:
        print(f"Document planning error: {e}")
        return _fallback_document(title, topic)


def _fallback_slides(topic: str, num_slides: int) -> list:
    """Fallback if AI fails — generate basic slide structure"""
    slides = [
        {
            "title": topic,
            "bullet_points": ["Overview", "Key Concepts", "Applications", "Summary"],
            "speaker_notes": f"Welcome to this presentation about {topic}."
        }
    ]

    for i in range(2, num_slides):
        slides.append({
            "title": f"Section {i}: {topic}",
            "bullet_points": [f"Key point {j}" for j in range(1, 5)],
            "speaker_notes": f"This slide covers important aspects of {topic}."
        })

    slides.append({
        "title": "Conclusion",
        "bullet_points": ["Summary of key points", "Future scope", "Thank you"],
        "speaker_notes": "Thank you for your attention."
    })

    return slides[:num_slides]


def _fallback_document(title: str, topic: str) -> dict:
    """Fallback document content"""
    return {
        "abstract": f"This document covers {topic} in detail.",
        "introduction": f"Introduction to {topic}. This document aims to provide a comprehensive overview.",
        "sections": [
            {"heading": "Main Content", "content": f"Detailed discussion about {topic}."},
            {"heading": "Analysis", "content": f"Analysis and evaluation of {topic}."},
        ],
        "conclusion": f"In conclusion, {topic} is an important subject that requires careful study.",
        "references": ["Textbook references", "Online resources", "Research papers"]
    }