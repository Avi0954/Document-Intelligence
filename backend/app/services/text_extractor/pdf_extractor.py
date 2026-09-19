import pymupdf as fitz  # PyMuPDF
from typing import List
from app.services.text_extractor.base import BaseTextExtractor, ExtractedChunk

class PDFTextExtractor(BaseTextExtractor):
    def extract_chunks(self, file_path: str) -> List[ExtractedChunk]:
        chunks: List[ExtractedChunk] = []
        try:
            doc = fitz.open(file_path)
            chunk_idx = 0
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text").strip()
                if text:
                    chunks.append(
                        ExtractedChunk(
                            content=text,
                            page_number=page_num + 1,
                            chunk_index=chunk_idx
                        )
                    )
                    chunk_idx += 1
            doc.close()
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF file: {str(e)}")
        
        return chunks
