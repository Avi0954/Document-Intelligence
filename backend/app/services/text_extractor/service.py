import os
from typing import List
from app.services.text_extractor.base import ExtractedChunk
from app.services.text_extractor.pdf_extractor import PDFTextExtractor
from app.services.text_extractor.docx_extractor import DOCXTextExtractor
from app.services.text_extractor.pptx_extractor import PPTXTextExtractor
from app.services.text_extractor.txt_extractor import TXTTextExtractor
from app.services.text_extractor.image_extractor import image_extractor

class TextExtractorService:
    def __init__(self):
        self.extractors = {
            "pdf": PDFTextExtractor(),
            "docx": DOCXTextExtractor(),
            "pptx": PPTXTextExtractor(),
            "txt": TXTTextExtractor(),
            "png": image_extractor,
            "jpg": image_extractor,
            "jpeg": image_extractor
        }

    def extract(self, file_path: str, file_type: str) -> List[ExtractedChunk]:
        normalized_type = file_type.lower().strip().replace(".", "")
        extractor = self.extractors.get(normalized_type)
        if not extractor:
            # Fallback based on extension
            ext = os.path.splitext(file_path)[1].lower().replace(".", "")
            extractor = self.extractors.get(ext)

        if not extractor:
            raise ValueError(f"Unsupported document type: '{file_type}'. Supported types: pdf, docx, pptx, txt, png, jpg, jpeg")

        return extractor.extract_chunks(file_path)

text_extractor_service = TextExtractorService()
