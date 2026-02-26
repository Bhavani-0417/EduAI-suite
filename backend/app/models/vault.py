from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class DocumentType(str, enum.Enum):
    MARKSHEET = "marksheet"
    CERTIFICATE = "certificate"
    TRANSCRIPT = "transcript"
    ID_CARD = "id_card"
    OFFER_LETTER = "offer_letter"
    OTHER = "other"

class VaultDocument(Base):
    __tablename__ = "vault_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    doc_type = Column(Enum(DocumentType), nullable=False)
    file_name = Column(String, nullable=False)
    encrypted_url = Column(String, nullable=False)  # Cloudinary private URL
    ocr_text = Column(Text, nullable=True)          # extracted text
    
    # Sharing
    share_token = Column(String, nullable=True)     # for time-limited sharing
    share_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    student = relationship("User", back_populates="documents")