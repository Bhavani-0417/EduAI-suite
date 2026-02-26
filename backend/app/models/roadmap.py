from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import uuid

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    goal = Column(String, nullable=False)           # "Become a Data Scientist"
    phases = Column(JSON, nullable=False)           # full roadmap JSON
    progress_percent = Column(Float, default=0.0)  # 0 to 100
    completed_topics = Column(JSON, default=[])    # list of done topics
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    student = relationship("User", back_populates="roadmaps")