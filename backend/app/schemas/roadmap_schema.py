from pydantic import BaseModel
from typing import Optional, List


class RoadmapPhase(BaseModel):
    """One phase in the learning roadmap"""
    phase_number: int
    title: str                          # e.g. "Python Fundamentals"
    duration_weeks: int                 # how long this phase takes
    topics: List[str]                   # list of topics to study
    resources: List[str]                # books, courses, links
    milestone: str                      # what student can do after this phase


class RoadmapCreate(BaseModel):
    """Request to generate a roadmap"""
    goal: str                           # e.g. "Become ML Engineer at Google"
    current_skills: Optional[List[str]] = []
    available_hours_per_day: Optional[int] = 2
    target_months: Optional[int] = 6


class RoadmapResponse(BaseModel):
    """Full roadmap sent back"""
    id: str
    goal: str
    phases: List[dict]
    progress_percent: float
    completed_topics: List[str]
    total_topics: int
    total_weeks: int

    class Config:
        from_attributes = True


class TopicCompleteRequest(BaseModel):
    """Mark a topic as completed"""
    topic: str


class PhaseCompleteRequest(BaseModel):
    """Mark entire phase as completed"""
    phase_number: int