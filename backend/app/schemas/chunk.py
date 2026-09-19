from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    page_number: Optional[int] = None
    content: str
    token_count_estimate: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
