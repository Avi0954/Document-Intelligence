import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    related_document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    document_role = Column(String(30), nullable=False, default="PRIMARY")  # PRIMARY, QUESTION_PAPER, ANSWER_KEY, SUPPLEMENT
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, pptx, txt, png, jpg, jpeg
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING")  # PENDING, EXTRACTING_TEXT, EXTRACTING_QUESTIONS, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    question_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="documents")
    related_document = relationship("Document", remote_side=[id])
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="document", cascade="all, delete-orphan")
