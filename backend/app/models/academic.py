from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class Mark(Base):
    __tablename__ = "marks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    semester = Column(Integer, nullable=False)
    marks_obtained = Column(Float, nullable=False)
    total_marks = Column(Float, nullable=False, default=100.0)
    exam_type = Column(String, nullable=True)   # midterm, final, internal
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    student = relationship("User", back_populates="marks")