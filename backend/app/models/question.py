import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), nullable=False)  # MCQ, SHORT_ANSWER, LONG_ANSWER, TRUE_FALSE
    options = Column(JSON, nullable=True)  # List of strings e.g. ["A", "B", "C", "D"]
    correct_answer = Column(Text, nullable=True)
    answer_status = Column(String(30), nullable=False, default="NOT_FOUND")  # VERIFIED, UNCERTAIN, NOT_FOUND
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=False)  # EASY, MEDIUM, HARD
    bloom_taxonomy = Column(String(30), nullable=True)  # REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE
    page_reference = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="questions")
