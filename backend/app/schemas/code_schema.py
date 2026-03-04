from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    C = "c"
    CPP = "cpp"
    SQL = "sql"
    OTHER = "other"


class CodeErrorRequest(BaseModel):
    """Request to explain a code error"""
    code: str                              # the student's code
    error_message: str                     # the error/traceback
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON
    additional_context: Optional[str] = None  # extra info student wants to add


class CodeFixRequest(BaseModel):
    """Request to just fix the code directly"""
    code: str
    error_message: str
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON


class CodeReviewRequest(BaseModel):
    """Request to review code quality"""
    code: str
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON


class CodeErrorResponse(BaseModel):
    """Full error explanation response"""
    error_type: str                        # e.g. "NameError", "NullPointerException"
    simple_explanation: str                # what went wrong in plain English
    line_causing_error: str                # specific line that caused it
    how_to_fix: str                        # step by step fix
    fixed_code: str                        # corrected version of the code
    concept_explanation: str               # why this happens (for learning)
    prevention_tips: List[str]             # how to avoid this in future
    related_errors: List[str]              # similar errors to watch out for