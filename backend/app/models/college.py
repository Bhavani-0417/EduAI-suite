from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import uuid

class College(Base):
    __tablename__ = "colleges"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    university = Column(String, nullable=True)    # affiliated university
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    college_code = Column(String, nullable=True, unique=True)
    
    # SSO config — stores OAuth/SAML settings if college has it
    sso_config = Column(JSON, nullable=True)
    has_sso = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    students = relationship("User", back_populates="college")
    events = relationship("Event", back_populates="college")