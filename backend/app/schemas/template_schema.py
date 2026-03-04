from pydantic import BaseModel
from typing import Optional
from enum import Enum


class PPTStyleEnum(str, Enum):
    ACADEMIC = "academic"
    SIMPLE = "simple"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    COLLEGE = "college"         # new — uses college template


class DocTypeEnum(str, Enum):
    ASSIGNMENT = "assignment"
    PROJECT_REPORT = "project_report"
    LAB_MANUAL = "lab_manual"
    RESEARCH_PAPER = "research_paper"


class CollegeTemplate(BaseModel):
    """
    Template config fetched from college record.
    Passed to PPT/doc builder to apply branding.
    """
    college_name: str
    primary_color: str = "#1E3A5F"
    secondary_color: str = "#2E75B6"
    logo_url: Optional[str] = None
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    font_name: str = "Arial"
    watermark_text: Optional[str] = None


class TemplatePPTRequest(BaseModel):
    """PPT generation with college template support"""
    topic: str
    key_points: Optional[list] = None
    num_slides: int = 8
    style: PPTStyleEnum = PPTStyleEnum.COLLEGE   # default to college template
    subject: Optional[str] = None
    include_speaker_notes: bool = True
    use_college_template: bool = True            # flag to apply college branding


class TemplateDocRequest(BaseModel):
    """Document generation with college template support"""
    title: str
    topic: str
    doc_type: DocTypeEnum = DocTypeEnum.ASSIGNMENT
    key_points: Optional[list] = None
    subject: Optional[str] = None
    include_references: bool = True
    use_college_template: bool = True            # flag to apply college branding


class CollegeTemplateUpdate(BaseModel):
    """Update college template settings"""
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    logo_url: Optional[str] = None
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    font_name: Optional[str] = None
    watermark_text: Optional[str] = None