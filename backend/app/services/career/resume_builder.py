import os
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from app.services.career.resume_ai_service import (
    optimize_resume_objective,
    optimize_project_description,
    generate_ats_tips
)

OUTPUT_DIR = "generated_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Color palette
PRIMARY = HexColor("#1E3A5F")
ACCENT = HexColor("#2E75B6")
LIGHT = HexColor("#F5F8FF")
GRAY = HexColor("#555555")
LIGHT_GRAY = HexColor("#EEEEEE")


def build_resume_pdf(resume_data: dict) -> dict:
    """
    Build a professional ATS-optimized PDF resume.

    Sections:
    1. Header (name, contact)
    2. Objective
    3. Education
    4. Skills
    5. Projects
    6. Experience (if any)
    """

    file_id = str(uuid.uuid4())
    name_slug = resume_data["full_name"].replace(" ", "_")
    file_name = f"{file_id}_{name_slug}_Resume.pdf"
    file_path = os.path.join(OUTPUT_DIR, file_name)

    # Page setup
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    # Styles
    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "NameStyle",
        fontSize=26,
        textColor=white,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=2
    )

    contact_style = ParagraphStyle(
        "ContactStyle",
        fontSize=9,
        textColor=white,
        alignment=TA_CENTER,
        fontName="Helvetica",
        spaceAfter=0
    )

    section_header_style = ParagraphStyle(
        "SectionHeader",
        fontSize=11,
        textColor=PRIMARY,
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        "Body",
        fontSize=9,
        textColor=black,
        fontName="Helvetica",
        spaceAfter=3,
        leading=13
    )

    bold_style = ParagraphStyle(
        "Bold",
        fontSize=9,
        textColor=black,
        fontName="Helvetica-Bold",
        spaceAfter=1
    )

    small_style = ParagraphStyle(
        "Small",
        fontSize=8,
        textColor=GRAY,
        fontName="Helvetica",
        spaceAfter=2
    )

    story = []

    # ── HEADER BLOCK ──────────────────────────────
    header_data = [[
        Paragraph(resume_data["full_name"], name_style),
    ]]
    header_table = Table(header_data, colWidths=[6.8 * inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(header_table)

    # Contact row
    contact_text = f"{resume_data['email']}  |  {resume_data['phone']}  |  {resume_data['city']}"
    contact_data = [[Paragraph(contact_text, contact_style)]]
    contact_table = Table(contact_data, colWidths=[6.8 * inch])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ACCENT),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(contact_table)
    story.append(Spacer(1, 0.1 * inch))

    # ── OBJECTIVE ──────────────────────────────
    objective = resume_data.get("objective", "")
    target_role = resume_data.get("target_role", "Software Engineer")
    skills = resume_data.get("skills", [])

    optimized_objective = optimize_resume_objective(
        objective, target_role, skills
    )

    story.append(Paragraph("OBJECTIVE", section_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph(optimized_objective, body_style))
    story.append(Spacer(1, 0.08 * inch))

    # ── EDUCATION ──────────────────────────────
    story.append(Paragraph("EDUCATION", section_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.05 * inch))

    for edu in resume_data.get("education", []):
        degree_text = f"<b>{edu['degree']}</b> — {edu['institution']}"
        story.append(Paragraph(degree_text, body_style))
        year_cgpa = f"{edu['year']}"
        if edu.get("cgpa"):
            year_cgpa += f"  |  CGPA: {edu['cgpa']}"
        story.append(Paragraph(year_cgpa, small_style))
        story.append(Spacer(1, 0.04 * inch))

    story.append(Spacer(1, 0.04 * inch))

    # ── SKILLS ──────────────────────────────
    story.append(Paragraph("TECHNICAL SKILLS", section_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.05 * inch))

    # Split skills into rows of 4
    skills_list = resume_data.get("skills", [])
    skill_chunks = [skills_list[i:i+4] for i in range(0, len(skills_list), 4)]

    for chunk in skill_chunks:
        skill_row = "  •  ".join(chunk)
        story.append(Paragraph(skill_row, body_style))

    story.append(Spacer(1, 0.08 * inch))

    # ── PROJECTS ──────────────────────────────
    story.append(Paragraph("PROJECTS", section_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.05 * inch))

    for project in resume_data.get("projects", []):
        story.append(Paragraph(f"<b>{project['name']}</b>", bold_style))
        story.append(Paragraph(
            f"<i>Tech Stack: {project['tech_stack']}</i>", small_style
        ))

        # AI optimizes project description
        optimized_desc = optimize_project_description(
            project["description"], target_role
        )
        story.append(Paragraph(optimized_desc, body_style))
        story.append(Spacer(1, 0.06 * inch))

    # ── EXPERIENCE ──────────────────────────────
    experience = resume_data.get("experience", [])
    if experience:
        story.append(Paragraph("EXPERIENCE", section_header_style))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
        story.append(Spacer(1, 0.05 * inch))

        for exp in experience:
            story.append(Paragraph(
                f"<b>{exp['role']}</b> — {exp['company']}", bold_style
            ))
            story.append(Paragraph(exp["duration"], small_style))
            story.append(Paragraph(exp["description"], body_style))
            story.append(Spacer(1, 0.05 * inch))

    # ── BUILD PDF ──────────────────────────────
    doc.build(story)

    # Generate ATS tips
    ats_tips = generate_ats_tips(skills, target_role)

    print(f"✅ Resume PDF saved: {file_path}")

    return {
        "file_path": file_path,
        "file_name": file_name,
        "ats_tips": ats_tips
    }