from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.services.notifications_service import (
    get_events, create_event, seed_events
)
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User
from app.models.events import EventType

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)


@router.get("/events")
def list_events(
    city: Optional[str] = Query(None, description="Filter by city"),
    event_type: Optional[str] = Query(None, description="hackathon/workshop/college_event/exam"),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get upcoming events for the student.

    GET /api/notifications/events?city=Hyderabad&event_type=hackathon

    Auto-filters by student's city if no city provided.
    Returns nearest upcoming events first.
    """
    # Use student's city if not specified
    filter_city = city or current_user.city

    events = get_events(db, filter_city, event_type, limit=limit)

    return {
        "total": len(events),
        "city_filter": filter_city,
        "events": [
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
                "event_date": str(event.event_date),
                "location": event.location,
                "city": event.city,
                "registration_url": event.registration_url,
                "tags": event.tags
            }
            for event in events
        ]
    }


@router.post("/events/seed")
def seed(db: Session = Depends(get_db)):
    """
    Seed sample events for testing.
    Run once to populate events table.
    """
    seed_events(db)
    return {"message": "Sample events seeded!"}


@router.post("/events/create", status_code=201)
def add_event(
    title: str,
    event_type: str,
    event_date: str,
    description: Optional[str] = None,
    city: Optional[str] = None,
    location: Optional[str] = None,
    registration_url: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new event (for college admins or testing).
    """
    event_type_map = {
        "hackathon": EventType.HACKATHON,
        "workshop": EventType.WORKSHOP,
        "college_event": EventType.COLLEGE_EVENT,
        "exam": EventType.EXAM,
        "deadline": EventType.DEADLINE
    }

    event = create_event(db, {
        "title": title,
        "description": description,
        "event_type": event_type_map.get(event_type, EventType.COLLEGE_EVENT),
        "event_date": datetime.fromisoformat(event_date),
        "city": city,
        "location": location,
        "registration_url": registration_url,
        "is_external": True
    })

    return {
        "message": "Event created!",
        "id": event.id,
        "title": event.title,
        "event_date": str(event.event_date)
    }