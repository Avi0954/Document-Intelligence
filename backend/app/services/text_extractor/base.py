from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ExtractedChunk:
    def __init__(self, content: str, page_number: int | None = None, chunk_index: int = 0):
        self.content = content
        self.page_number = page_number
        self.chunk_index = chunk_index

class BaseTextExtractor(ABC):
    @abstractmethod
    def extract_chunks(self, file_path: str) -> List[ExtractedChunk]:
        """Extract text chunks with page/slide references from document file."""
        pass
