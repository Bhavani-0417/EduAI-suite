from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class UserRole(str, enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"

class Branch(str, enum.Enum):
    BTECH_CS = "btech_cs"
    BTECH_AIDS = "btech_aids"
    BTECH_ECE = "btech_ece"
    MBBS = "mbbs"
    INTERMEDIATE = "intermediate"
    SCHOOL = "school"
    OTHER = "other"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)  # null if using Google OAuth
    
    # Profile
    full_name = Column(String, nullable=False)
    college_id = Column(String, ForeignKey("colleges.id"), nullable=True)
    student_roll_number = Column(String, nullable=True)
    branch = Column(Enum(Branch), nullable=True)
    year = Column(Integer, nullable=True)        # 1, 2, 3, 4
    semester = Column(Integer, nullable=True)    # 1 to 8
    city = Column(String, nullable=True)         # for geo-based events
    
    # Account
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    google_id = Column(String, nullable=True)    # if logged in via Google
    profile_picture = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships — these let you do user.notes, user.marks etc.
    college = relationship("College", back_populates="students")
    marks = relationship("Mark", back_populates="student")
    notes = relationship("Note", back_populates="student")
    job_applications = relationship("JobApplication", back_populates="student")
    roadmaps = relationship("Roadmap", back_populates="student")
    documents = relationship("VaultDocument", back_populates="student")