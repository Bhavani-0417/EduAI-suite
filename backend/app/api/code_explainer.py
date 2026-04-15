from fastapi import APIRouter
from app.schemas.code_schema import CodeErrorRequest, CodeErrorResponse

router = APIRouter(prefix="/api/code", tags=["Code Explainer"])


@router.post("/explain", response_model=CodeErrorResponse)
def explain_code_error(request: CodeErrorRequest):
    # Dummy response (for testing)
    return {
        "error_type": "TypeError",
        "simple_explanation": "You are trying to add an integer and a string.",
        "line_causing_error": "print(a + b)",
        "how_to_fix": "Convert string to int using int(b)",
        "fixed_code": "a = 10\nb = int('5')\nprint(a + b)",
        "concept_explanation": "Python does not allow adding int and string directly.",
        "prevention_tips": ["Check variable types", "Use type casting"],
        "related_errors": ["ValueError", "TypeError"]
    }