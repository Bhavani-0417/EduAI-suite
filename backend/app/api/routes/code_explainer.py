from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.code_schema import (
    CodeErrorRequest,
    CodeFixRequest,
    CodeReviewRequest
)
from app.services.ai.code_explainer import (
    explain_code_error,
    fix_code,
    review_code,
    explain_concept_from_error
)
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/code",
    tags=["Code Error Explainer"]
)


@router.post("/explain")
def explain_error(
    request: CodeErrorRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Full error explanation with fix.

    POST /api/code/explain
    Body:
    {
        "code": "your broken code here",
        "error_message": "the error traceback",
        "language": "python",
        "additional_context": "optional extra info"
    }

    Returns:
    - What the error means in simple English
    - Which line caused it
    - How to fix it step by step
    - Complete fixed code
    - Concept explanation for learning
    - Prevention tips
    """
    result = explain_code_error(
        code=request.code,
        error_message=request.error_message,
        language=request.language.value,
        additional_context=request.additional_context
    )
    return result


@router.post("/fix")
def fix_my_code(
    request: CodeFixRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Quick fix — just returns corrected code.
    No long explanation, just the working code.

    POST /api/code/fix
    Body: { code, error_message, language }
    """
    result = fix_code(
        code=request.code,
        error_message=request.error_message,
        language=request.language.value
    )
    return result


@router.post("/review")
def review_my_code(
    request: CodeReviewRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Code quality review — no error needed.
    Finds potential bugs, bad practices, improvements.

    POST /api/code/review
    Body: { code, language }

    Returns rating, issues, suggestions, optimized version.
    """
    result = review_code(
        code=request.code,
        language=request.language.value
    )
    return result


@router.get("/explain-error-type/{error_type}")
def explain_error_type(
    error_type: str,
    language: str = "python",
    current_user: User = Depends(get_current_user)
):
    """
    Learn about any error type by name.

    GET /api/code/explain-error-type/NameError?language=python
    GET /api/code/explain-error-type/NullPointerException?language=java
    GET /api/code/explain-error-type/IndexError?language=python

    Perfect for when student just wants to
    understand what an error type means.
    """
    return explain_concept_from_error(error_type, language)