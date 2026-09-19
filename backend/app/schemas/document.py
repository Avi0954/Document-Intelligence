from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class DocumentBase(BaseModel):
    filename: str
    original_name: str
    file_type: str
    file_size: int

class DocumentCreate(DocumentBase):
    file_path: str
    file_hash: str

class DocumentResponse(DocumentBase):
    id: str
    file_hash: str
    status: str
    document_role: str = "PRIMARY"
    related_document_id: Optional[str] = None
    error_message: Optional[str] = None
    chunk_count: int
    question_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentDetailResponse(DocumentResponse):
    pass

class DocumentAssociate(BaseModel):
    related_document_id: Optional[str] = None
    relationship_type: str = "ANSWER_KEY"  # ANSWER_KEY or SUPPLEMENT
