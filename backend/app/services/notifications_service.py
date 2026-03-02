from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.events import Event, EventType
import uuid
from datetime import datetime


def get_events(
    db: Session,
    city: str = None,
    event_type: str = None,
    college_id: str = None,
    limit: int = 20
) -> list:
    """
    Get upcoming events filtered by city/type/college.
    Sorted by nearest date first.
    """
    query = db.query(Event).filter(
        Event.event_date >= datetime.utcnow()
    )

    if city:
        query = query.filter(
            Event.city.ilike(f"%{city}%")
        )

    if event_type:
        query = query.filter(
            Event.event_type == event_type
        )

    if college_id:
        query = query.filter(
            Event.college_id == college_id
        )

    return query.order_by(Event.event_date.asc()).limit(limit).all()


def create_event(db: Session, data: dict) -> Event:
    """Create a new event (admin/college use)"""
    event = Event(
        id=str(uuid.uuid4()),
        title=data["title"],
        description=data.get("description"),
        event_type=data["event_type"],
        event_date=data["event_date"],
        location=data.get("location"),
        city=data.get("city"),
        college_id=data.get("college_id"),
        registration_url=data.get("registration_url"),
        is_external=data.get("is_external", False),
        tags=data.get("tags")
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def seed_events(db: Session):
    """Seed some sample events for testing"""
    sample_events = [
        {
            "title": "Smart India Hackathon 2025",
            "description": "National level hackathon for college students",
            "event_type": EventType.HACKATHON,
            "event_date": datetime(2025, 8, 15),
            "city": "Pan India",
            "registration_url": "https://sih.gov.in",
            "is_external": True,
            "tags": "hackathon,coding,national"
        },
        {
            "title": "ML Workshop — Hyderabad",
            "description": "Hands-on workshop on Machine Learning basics",
            "event_type": EventType.WORKSHOP,
            "event_date": datetime(2025, 7, 20),
            "city": "Hyderabad",
            "is_external": True,
            "tags": "ml,workshop,beginners"
        },
        {
            "title": "Devfolio Campus Hackathon",
            "description": "Build anything in 24 hours",
            "event_type": EventType.HACKATHON,
            "event_date": datetime(2025, 9, 5),
            "city": "Bangalore",
            "registration_url": "https://devfolio.co",
            "is_external": True,
            "tags": "hackathon,devfolio"
        },
        {
            "title": "GATE 2026 Preparation Seminar",
            "description": "Expert guidance for GATE exam preparation",
            "event_type": EventType.WORKSHOP,
            "event_date": datetime(2025, 7, 28),
            "city": "Hyderabad",
            "is_external": False,
            "tags": "gate,exam,preparation"
        },
        {
            "title": "Internship Drive — TCS",
            "description": "Campus placement drive for internships",
            "event_type": EventType.COLLEGE_EVENT,
            "event_date": datetime(2025, 8, 1),
            "city": "Hyderabad",
            "is_external": False,
            "tags": "placement,internship,tcs"
        },
    ]

    for event_data in sample_events:
        existing = db.query(Event).filter(
            Event.title == event_data["title"]
        ).first()

        if not existing:
            event = Event(id=str(uuid.uuid4()), **event_data)
            db.add(event)

    db.commit()
    print("✅ Events seeded successfully")