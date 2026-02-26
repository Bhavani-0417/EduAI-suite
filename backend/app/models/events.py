from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class EventType(str, enum.Enum):
    COLLEGE_EVENT = "college_event"
    HACKATHON = "hackathon"
    WORKSHOP = "workshop"
    EXAM = "exam"
    DEADLINE = "deadline"

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    college_id = Column(String, ForeignKey("colleges.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(Enum(EventType), nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String, nullable=True)
    city = Column(String, nullable=True)
    registration_url = Column(String, nullable=True)
    is_external = Column(Boolean, default=False)  # scraped from internet?
    tags = Column(String, nullable=True)           # "AI,ML,Python"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    college = relationship("College", back_populates="events")