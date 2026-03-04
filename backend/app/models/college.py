from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from sqlalchemy import Column, String, JSON
import uuid

class College(Base):
    __tablename__ = "colleges"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    university = Column(String, nullable=True)    # affiliated university
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    college_code = Column(String, nullable=True, unique=True)
    primary_color     = Column(String, default="#1E3A5F")    # main brand color
    secondary_color   = Column(String, default="#2E75B6")    # accent color
    logo_url          = Column(String, nullable=True)        # college logo image URL
    header_text       = Column(String, nullable=True)        # e.g. "JNTU Hyderabad"
    footer_text       = Column(String, nullable=True)        # e.g. "Department of AI & DS"
    font_name         = Column(String, default="Arial")      # official font
    watermark_text    = Column(String, nullable=True)        # e.g. college name as watermark
    template_config   = Column(JSON, nullable=True)          # extra config as JSON
    
    # SSO config — stores OAuth/SAML settings if college has it
    sso_config = Column(JSON, nullable=True)
    has_sso = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    students = relationship("User", back_populates="college")
    events = relationship("Event", back_populates="college")