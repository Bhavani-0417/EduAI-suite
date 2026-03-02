from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.roadmap import Roadmap
from app.schemas.roadmap_schema import RoadmapCreate
from app.services.ai.roadmap_agent import generate_roadmap
import uuid
import json


def create_roadmap(
    db: Session,
    student_id: str,
    data: RoadmapCreate
) -> Roadmap:
    """
    Generate and save a new roadmap.
    Calls LangGraph agent → saves result to PostgreSQL.
    """
    print(f"🗺️ Creating roadmap for: {data.goal}")

    # Run LangGraph agent
    result = generate_roadmap(
        goal=data.goal,
        current_skills=data.current_skills or [],
        hours_per_day=data.available_hours_per_day or 2,
        target_months=data.target_months or 6
    )

    roadmap = Roadmap(
        id=str(uuid.uuid4()),
        student_id=student_id,
        goal=data.goal,
        phases=result["phases"],
        progress_percent=0.0,
        completed_topics=[]
    )

    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)
    return roadmap


def get_roadmaps(db: Session, student_id: str) -> list:
    """Get all roadmaps for a student"""
    return db.query(Roadmap).filter(
        Roadmap.student_id == student_id
    ).order_by(Roadmap.created_at.desc()).all()


def get_roadmap_by_id(
    db: Session,
    roadmap_id: str,
    student_id: str
) -> Roadmap:
    """Get a specific roadmap"""
    roadmap = db.query(Roadmap).filter(
        Roadmap.id == roadmap_id,
        Roadmap.student_id == student_id
    ).first()

    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found."
        )
    return roadmap


def mark_topic_complete(
    db: Session,
    roadmap_id: str,
    student_id: str,
    topic: str
) -> Roadmap:
    """
    Mark a topic as completed and update progress %.

    Progress = completed topics / total topics * 100
    """
    roadmap = get_roadmap_by_id(db, roadmap_id, student_id)

    completed = roadmap.completed_topics or []

    if topic not in completed:
        completed.append(topic)
        roadmap.completed_topics = completed

        # Recalculate progress
        total_topics = sum(
            len(phase.get("topics", []))
            for phase in (roadmap.phases or [])
        )

        if total_topics > 0:
            roadmap.progress_percent = round(
                (len(completed) / total_topics) * 100, 1
            )

    db.commit()
    db.refresh(roadmap)
    return roadmap


def delete_roadmap(
    db: Session,
    roadmap_id: str,
    student_id: str
):
    """Delete a roadmap"""
    roadmap = get_roadmap_by_id(db, roadmap_id, student_id)
    db.delete(roadmap)
    db.commit()


def format_roadmap_response(roadmap: Roadmap) -> dict:
    """Format roadmap for API response"""
    phases = roadmap.phases or []
    completed = roadmap.completed_topics or []

    total_topics = sum(
        len(phase.get("topics", []))
        for phase in phases
    )

    total_weeks = sum(
        phase.get("duration_weeks", 4)
        for phase in phases
    )

    return {
        "id": roadmap.id,
        "goal": roadmap.goal,
        "phases": phases,
        "progress_percent": roadmap.progress_percent or 0.0,
        "completed_topics": completed,
        "total_topics": total_topics,
        "total_weeks": total_weeks,
        "created_at": str(roadmap.created_at)
    }