from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class NoteSource(str, enum.Enum):
    STUDENT = "student"      # student uploaded
    FACULTY = "faculty"      # professor uploaded

class Note(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Classification (AI fills these automatically)
    subject = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    chapter = Column(String, nullable=True)
    
    # File info
    file_url = Column(String, nullable=False)       # Cloudinary URL
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)      # pdf, image, pptx
    
    # Content
    extracted_text = Column(Text, nullable=True)    # OCR/parsed text
    summary = Column(Text, nullable=True)           # AI summary
    
    source = Column(Enum(NoteSource), default=NoteSource.STUDENT)
    chroma_collection_id = Column(String, nullable=True)  # reference to vector store
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    student = relationship("User", back_populates="notes")