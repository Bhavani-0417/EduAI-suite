from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class PresentationStyle(str, Enum):
    ACADEMIC = "academic"       # formal, structured
    SIMPLE = "simple"           # clean, minimal
    TECHNICAL = "technical"     # detailed, code-friendly
    CREATIVE = "creative"       # engaging, storytelling


class DocumentType(str, Enum):
    ASSIGNMENT = "assignment"
    PROJECT_REPORT = "project_report"
    LAB_MANUAL = "lab_manual"
    RESEARCH_PAPER = "research_paper"


class PPTRequest(BaseModel):
    """Request to generate a PPT"""
    topic: str = Field(..., min_length=3, description="Topic of the presentation")
    key_points: Optional[List[str]] = None      # specific points to cover
    num_slides: int = Field(default=8, ge=3, le=20)
    style: PresentationStyle = PresentationStyle.ACADEMIC
    subject: Optional[str] = None               # subject area
    include_speaker_notes: bool = True


class SlideContent(BaseModel):
    """Content for a single slide"""
    title: str
    bullet_points: List[str]
    speaker_notes: Optional[str] = None


class PPTResponse(BaseModel):
    """Response after PPT generation"""
    message: str
    topic: str
    num_slides: int
    download_url: str
    slides_preview: List[SlideContent]          # preview of content


class DocumentRequest(BaseModel):
    """Request to generate a document"""
    title: str
    topic: str
    doc_type: DocumentType = DocumentType.ASSIGNMENT
    key_points: Optional[List[str]] = None
    subject: Optional[str] = None
    student_name: Optional[str] = None
    college_name: Optional[str] = None
    include_references: bool = True


class DocumentResponse(BaseModel):
    """Response after document generation"""
    message: str
    title: str
    doc_type: str
    download_url: str
    word_count: int