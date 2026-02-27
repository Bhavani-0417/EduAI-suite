from pydantic import BaseModel, Field
from typing import Optional, List


class MarkCreate(BaseModel):
    """Add a new mark entry"""
    subject: str
    semester: int = Field(..., ge=1, le=8)   # between 1 and 8
    marks_obtained: float = Field(..., ge=0, le=100)
    total_marks: float = Field(default=100.0, ge=1)
    exam_type: Optional[str] = "final"        # final, midterm, internal


class MarkResponse(BaseModel):
    """Mark data sent back"""
    id: str
    subject: str
    semester: int
    marks_obtained: float
    total_marks: float
    exam_type: Optional[str]
    percentage: float                          # calculated field

    class Config:
        from_attributes = True


class CGPAResponse(BaseModel):
    """CGPA calculation result"""
    cgpa: float
    percentage: float
    total_subjects: int
    semester_breakdown: dict                   # marks per semester


class WeaknessReport(BaseModel):
    """AI weakness analysis result"""
    weak_subjects: List[str]                   # subjects below threshold
    strong_subjects: List[str]                 # subjects above threshold
    improvement_tips: dict                     # subject → tip
    overall_grade: str                         # A, B, C, D, F


class ProfileUpdateRequest(BaseModel):
    """Update student profile"""
    full_name: Optional[str] = None
    college_id: Optional[str] = None
    year: Optional[int] = None
    semester: Optional[int] = None
    city: Optional[str] = None
    profile_picture: Optional[str] = None