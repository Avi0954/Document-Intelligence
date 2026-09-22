import os
import mimetypes
from typing import List
from google import genai
from google.genai import types
from dotenv import load_dotenv

from app.config import settings
from app.services.text_extractor.base import BaseTextExtractor, ExtractedChunk

class ImageExtractor(BaseTextExtractor):
    def _get_active_api_key(self) -> str:
        env_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
        if os.path.exists(env_file_path):
            load_dotenv(env_file_path, override=True)
        key = os.environ.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY or ""
        return key.strip()

    def _get_active_model_name(self) -> str:
        model = os.environ.get("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-2.5-flash"
        return model.strip()

    def extract(self, file_path: str) -> List[ExtractedChunk]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file '{file_path}' not found.")

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not mime_type.startswith("image/"):
            ext = os.path.splitext(file_path)[1].lower().replace(".", "")
            if ext in ["jpg", "jpeg"]:
                mime_type = "image/jpeg"
            elif ext == "png":
                mime_type = "image/png"
            else:
                mime_type = "image/jpeg"

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        key = self._get_active_api_key()
        if not key:
            raise ValueError("Gemini API key is required to process image files.")

        client = genai.Client(api_key=key)
        primary_model = self._get_active_model_name()
        candidate_models = [primary_model]
        for fallback in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        prompt = (
            "Extract all readable text, statements, formulas, lists, diagrams, and educational information "
            "from this image clearly and accurately. Preserve original formatting, headings, and structure. "
            "Strictly do not introduce outside knowledge or unmentioned facts."
        )

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        last_err = None

        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[image_part, prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.1
                    )
                )

                extracted_text = (response.text or "").strip()
                if not extracted_text:
                    raise ValueError("No readable text could be extracted from the uploaded image.")

                return [
                    ExtractedChunk(
                        chunk_index=0,
                        page_number=1,
                        content=extracted_text
                    )
                ]

            except Exception as e:
                last_err = e
                continue

        raise ValueError(f"Image extraction via Gemini Vision failed: {str(last_err)}")

    def extract_chunks(self, file_path: str) -> List[ExtractedChunk]:
        return self.extract(file_path)

image_extractor = ImageExtractor()
