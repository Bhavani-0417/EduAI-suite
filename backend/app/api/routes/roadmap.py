from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.roadmap_schema import RoadmapCreate, TopicCompleteRequest
from app.services.roadmap_service import (
    create_roadmap, get_roadmaps, get_roadmap_by_id,
    mark_topic_complete, delete_roadmap, format_roadmap_response
)
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/roadmap",
    tags=["Goal & Roadmap"]
)


@router.post("/generate", status_code=201)
def generate(
    data: RoadmapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an AI learning roadmap.

    POST /api/roadmap/generate
    Body: { goal, current_skills, available_hours_per_day, target_months }

    LangGraph agent:
    1. Analyzes skill gap
    2. Generates phases
    3. Validates timeline
    """
    roadmap = create_roadmap(db, current_user.id, data)
    return {
        "message": "Roadmap generated successfully!",
        **format_roadmap_response(roadmap)
    }


@router.get("/")
def list_roadmaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roadmaps for logged-in student"""
    roadmaps = get_roadmaps(db, current_user.id)
    return {
        "total": len(roadmaps),
        "roadmaps": [format_roadmap_response(r) for r in roadmaps]
    }


@router.get("/{roadmap_id}")
def get_roadmap(
    roadmap_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific roadmap with full phase details"""
    roadmap = get_roadmap_by_id(db, roadmap_id, current_user.id)
    return format_roadmap_response(roadmap)


@router.post("/{roadmap_id}/complete-topic")
def complete_topic(
    roadmap_id: str,
    data: TopicCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a topic as completed.
    Progress % auto-updates.

    POST /api/roadmap/{id}/complete-topic
    Body: { topic: "Python Basics" }
    """
    roadmap = mark_topic_complete(
        db, roadmap_id, current_user.id, data.topic
    )
    return {
        "message": f"Topic '{data.topic}' marked complete!",
        "progress_percent": roadmap.progress_percent,
        "completed_topics": roadmap.completed_topics
    }


@router.delete("/{roadmap_id}")
def delete(
    roadmap_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a roadmap"""
    delete_roadmap(db, roadmap_id, current_user.id)
    return {"message": "Roadmap deleted."}