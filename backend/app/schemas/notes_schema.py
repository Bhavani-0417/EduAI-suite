from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class NoteSourceEnum(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"


class NoteResponse(BaseModel):
    """Note data sent back to client"""
    id: str
    subject: Optional[str]
    topic: Optional[str]
    chapter: Optional[str]
    file_name: str
    file_type: str
    file_url: str
    source: str
    summary: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    total: int
    notes: List[NoteResponse]


class AskQuestionRequest(BaseModel):
    """Request body for asking a question about notes"""
    question: str
    subject: Optional[str] = None   # filter to specific subject
    semester: Optional[int] = None  # filter to specific semester


class AskQuestionResponse(BaseModel):
    """Response from RAG Q&A"""
    question: str
    answer: str
    sources: List[str]              # which notes were used to answer