import google.generativeai as genai
from app.core.config import settings
import json
import re

genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


def explain_code_error(
    code: str,
    error_message: str,
    language: str = "python",
    additional_context: str = None
) -> dict:
    """
    Main function — explains a code error completely.

    Takes student's broken code + error message.
    Returns full breakdown in simple language.
    """

    context_text = f"\nAdditional context: {additional_context}" if additional_context else ""

    prompt = f"""
    You are a friendly programming tutor helping a student understand their code error.
    
    PROGRAMMING LANGUAGE: {language.upper()}
    
    STUDENT'S CODE:
```{language}
    {code}
```
    
    ERROR MESSAGE:
    {error_message}
    {context_text}
    
    Explain this error completely. Return ONLY valid JSON with this exact structure:
    {{
        "error_type": "the type/name of error (e.g. NameError, NullPointerException)",
        "simple_explanation": "explain what went wrong in simple English a beginner can understand, max 3 sentences",
        "line_causing_error": "copy the exact line from the code that caused this error",
        "how_to_fix": "clear step by step explanation of how to fix it",
        "fixed_code": "the complete corrected version of the code",
        "concept_explanation": "explain the programming concept behind this error so student learns why it happens",
        "prevention_tips": ["tip 1", "tip 2", "tip 3"],
        "related_errors": ["similar error 1", "similar error 2"]
    }}
    
    Rules:
    - Use simple language — assume student is a beginner
    - fixed_code must be complete working code not just a snippet
    - prevention_tips must be practical and specific
    - Be encouraging and supportive in tone
    - Return ONLY JSON, no extra text
    """

    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip()
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        result = json.loads(cleaned)
        print(f"✅ Error explained: {result.get('error_type', 'Unknown')}")
        return result

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return _fallback_explanation(error_message, language)
    except Exception as e:
        print(f"Gemini error: {e}")
        return _fallback_explanation(error_message, language)


def fix_code(
    code: str,
    error_message: str,
    language: str = "python"
) -> dict:
    """
    Just fix the code — no long explanation.
    Returns fixed code + one line of what changed.
    Useful when student just wants working code fast.
    """

    prompt = f"""
    Fix this {language.upper()} code that has an error.
    
    BROKEN CODE:
```{language}
    {code}
```
    
    ERROR:
    {error_message}
    
    Return ONLY valid JSON:
    {{
        "fixed_code": "complete corrected working code here",
        "what_changed": "one clear sentence explaining what you changed and why",
        "changes_list": ["change 1", "change 2"]
    }}
    
    Return ONLY JSON, nothing else.
    """

    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip()
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        return json.loads(cleaned)

    except Exception as e:
        print(f"Fix code error: {e}")
        return {
            "fixed_code": code,
            "what_changed": "Could not auto-fix. Please review the error message manually.",
            "changes_list": []
        }


def review_code(code: str, language: str = "python") -> dict:
    """
    Review code quality — no errors needed.
    Gives improvement suggestions, best practices,
    and identifies potential bugs before they happen.
    """

    prompt = f"""
    Review this {language.upper()} code like a senior developer doing a code review.
    
    CODE:
```{language}
    {code}
```
    
    Return ONLY valid JSON:
    {{
        "overall_rating": "Good / Average / Needs Improvement",
        "summary": "2 sentence overall assessment",
        "issues_found": [
            {{
                "severity": "high/medium/low",
                "issue": "description of the issue",
                "line": "the problematic line or section",
                "fix": "how to fix it"
            }}
        ],
        "good_practices": ["what student did well 1", "what student did well 2"],
        "improvement_suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
        "optimized_code": "improved version of the entire code"
    }}
    
    Be encouraging. Focus on learning.
    Return ONLY JSON, no extra text.
    """

    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip()
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        return json.loads(cleaned)

    except Exception as e:
        print(f"Code review error: {e}")
        return {
            "overall_rating": "Review failed",
            "summary": "Could not complete review. Please try again.",
            "issues_found": [],
            "good_practices": [],
            "improvement_suggestions": [],
            "optimized_code": code
        }


def explain_concept_from_error(error_type: str, language: str = "python") -> dict:
    """
    Given just an error type name — explain the concept deeply.
    e.g. "IndexError" → full explanation of list indexing in Python
    """

    prompt = f"""
    A student is getting a "{error_type}" in {language.upper()}.
    
    Explain this error type completely as a teaching moment.
    
    Return ONLY valid JSON:
    {{
        "error_name": "{error_type}",
        "what_it_means": "clear explanation of what this error type means",
        "common_causes": ["cause 1", "cause 2", "cause 3"],
        "example_that_causes_it": "short code example that causes this error",
        "example_that_fixes_it": "corrected version of the above example",
        "memory_trick": "a simple way for student to remember when this happens",
        "official_docs_topic": "what topic to search in official docs to learn more"
    }}
    
    Return ONLY JSON.
    """

    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip()
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)

        return json.loads(cleaned.strip())

    except Exception as e:
        print(f"Concept explain error: {e}")
        return {
            "error_name": error_type,
            "what_it_means": f"{error_type} is a programming error.",
            "common_causes": ["Check your code carefully"],
            "example_that_causes_it": "",
            "example_that_fixes_it": "",
            "memory_trick": "",
            "official_docs_topic": error_type
        }


def _fallback_explanation(error_message: str, language: str) -> dict:
    """Fallback if Gemini fails"""
    return {
        "error_type": "Unknown Error",
        "simple_explanation": f"There is an error in your {language} code. Please check the error message carefully: {error_message[:200]}",
        "line_causing_error": "Could not identify the specific line.",
        "how_to_fix": "Review the error message and check the line numbers mentioned.",
        "fixed_code": "Could not auto-generate fix. Please review manually.",
        "concept_explanation": "Please try again for a detailed explanation.",
        "prevention_tips": [
            "Read error messages carefully",
            "Check line numbers mentioned in the error",
            "Search the error message online for more help"
        ],
        "related_errors": []
    }