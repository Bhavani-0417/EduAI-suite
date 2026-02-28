from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ApplicationStatusEnum(str, Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


# ─────────────────────────────────────────
# RESUME SCHEMAS
# ─────────────────────────────────────────

class EducationItem(BaseModel):
    degree: str
    institution: str
    year: str
    cgpa: Optional[str] = None


class ExperienceItem(BaseModel):
    role: str
    company: str
    duration: str
    description: str


class ProjectItem(BaseModel):
    name: str
    description: str
    tech_stack: str


class ResumeRequest(BaseModel):
    """Data to build a resume"""
    full_name: str
    email: str
    phone: str
    city: str
    objective: Optional[str] = None
    education: List[EducationItem]
    skills: List[str]
    projects: List[ProjectItem]
    experience: Optional[List[ExperienceItem]] = []
    target_role: Optional[str] = None          # AI uses this to optimize


class ResumeResponse(BaseModel):
    message: str
    download_url: str
    ats_tips: List[str]                        # AI-generated ATS improvement tips


# ─────────────────────────────────────────
# JOB APPLICATION SCHEMAS
# ─────────────────────────────────────────

class JobApplicationCreate(BaseModel):
    company: str
    role: str
    job_description: Optional[str] = None
    resume_version_url: Optional[str] = None
    notes: Optional[str] = None


class JobApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatusEnum] = None
    notes: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: str
    company: str
    role: str
    match_score: Optional[float] = None
    status: str
    applied_date: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# JD MATCHER SCHEMAS
# ─────────────────────────────────────────

class JDMatchRequest(BaseModel):
    resume_text: str
    job_description: str


class JDMatchResponse(BaseModel):
    match_score: float                         # 0-100
    matched_skills: List[str]                 # skills in both resume & JD
    missing_skills: List[str]                 # skills in JD but not resume
    recommendation: str                        # overall advice


# ─────────────────────────────────────────
# ANALYTICS SCHEMAS
# ─────────────────────────────────────────

class CareerAnalyticsResponse(BaseModel):
    total_applications: int
    status_breakdown: dict                    # {applied: 5, interview: 2, ...}
    response_rate: float                       # % that got any response
    top_roles: List[str]                      # most applied roles
    top_companies: List[str]                  # most applied companies
    average_match_score: float
    monthly_applications: dict                # {Jan: 3, Feb: 5, ...}