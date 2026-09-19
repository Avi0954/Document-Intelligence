import os
import json
import time
import re
from typing import List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError, ClientError

from app.config import settings
from app.schemas.question import LLMQuestionResponse
from app.services.llm.base import BaseLLMService
from app.services.llm.prompts import (
    QUESTION_EXTRACTION_SYSTEM_PROMPT,
    build_question_extraction_prompt,
    build_question_extraction_with_answer_key_prompt
)

class GeminiLLMService(BaseLLMService):
    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._current_key: str = ""

    def _get_active_api_key(self) -> str:
        env_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
        if os.path.exists(env_file_path):
            load_dotenv(env_file_path, override=True)
        
        key = os.environ.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY or ""
        return key.strip()

    def _get_active_model_name(self) -> str:
        model = os.environ.get("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-3.6-flash"
        return model.strip()

    def is_configured(self) -> bool:
        key = self._get_active_api_key()
        return bool(key != "")

    def _ensure_client(self) -> genai.Client:
        key = self._get_active_api_key()
        if not key:
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env file."
            )
        
        if not self._client or self._current_key != key:
            self._current_key = key
            self._client = genai.Client(api_key=key)
        
        return self._client

    def extract_questions_from_text(self, text_chunk: str, page_number: Optional[int] = None) -> LLMQuestionResponse:
        client = self._ensure_client()
        prompt = build_question_extraction_prompt(text_chunk, page_number)
        return self._execute_generate_content(client, prompt)

    def extract_questions_from_text_with_answer_key(self, qp_text: str, ak_text: str) -> LLMQuestionResponse:
        client = self._ensure_client()
        prompt = build_question_extraction_with_answer_key_prompt(qp_text, ak_text)
        return self._execute_generate_content(client, prompt)

    def _execute_generate_content(self, client: genai.Client, prompt: str) -> LLMQuestionResponse:
        primary_model = self._get_active_model_name()

        candidate_models = [primary_model]
        if "gemini-3.6-flash" not in candidate_models:
            candidate_models.append("gemini-3.6-flash")

        max_retries = 6
        last_error = None

        for model_name in candidate_models:
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=QUESTION_EXTRACTION_SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            response_schema=LLMQuestionResponse,
                            temperature=0.2,
                        )
                    )

                    if hasattr(response, "parsed") and response.parsed is not None:
                        parsed_data = response.parsed
                        if isinstance(parsed_data, LLMQuestionResponse):
                            return parsed_data
                        elif isinstance(parsed_data, dict):
                            return LLMQuestionResponse.model_validate(parsed_data)

                    if hasattr(response, "text") and response.text:
                        return LLMQuestionResponse.model_validate_json(response.text)

                except Exception as api_err:
                    last_error = api_err
                    full_err_str = (str(api_err) + " " + str(getattr(api_err, "message", "")) + " " + repr(api_err)).lower()
                    if "404" in full_err_str or "not found" in full_err_str:
                        break  # Try next model
                    
                    if "503" in full_err_str or "429" in full_err_str or "high demand" in full_err_str or "unavailable" in full_err_str or "quota" in full_err_str or "resource_exhausted" in full_err_str:
                        if attempt < max_retries - 1:
                            match = re.search(r"retry in (\d+(\.\d+)?)s", full_err_str)
                            if match:
                                sleep_secs = float(match.group(1)) + 3.0
                            else:
                                sleep_secs = 20.0
                            print(f"[Gemini Rate Limit] Waiting {sleep_secs:.1f}s for quota reset (attempt {attempt+1}/{max_retries})...")
                            time.sleep(sleep_secs)
                            continue
                        else:
                            break  # Try next model candidate if retries exhausted

                    # Non-retryable error
                    raise ValueError(f"Gemini API error: {getattr(api_err, 'message', str(api_err))}")

        err_detail = getattr(last_error, "message", str(last_error)) if last_error else "High demand or rate limit reached."
        raise ValueError(f"Gemini API error: {err_detail}")

gemini_llm_service = GeminiLLMService()
