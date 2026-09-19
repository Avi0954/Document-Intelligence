from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.question import LLMQuestionResponse

class BaseLLMService(ABC):
    @abstractmethod
    def extract_questions_from_text(self, text_chunk: str, page_number: int | None = None) -> LLMQuestionResponse:
        """Extract high-quality educational questions from text chunk using LLM."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if LLM API key and client are properly configured."""
        pass
