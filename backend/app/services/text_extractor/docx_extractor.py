from typing import List
import docx
from app.services.text_extractor.base import BaseTextExtractor, ExtractedChunk

class DOCXTextExtractor(BaseTextExtractor):
    def extract_chunks(self, file_path: str) -> List[ExtractedChunk]:
        chunks: List[ExtractedChunk] = []
        try:
            doc = docx.Document(file_path)
            full_text = []
            
            # Extract paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            
            # Extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        full_text.append(" | ".join(row_text))
            
            combined_text = "\n\n".join(full_text)
            if not combined_text:
                return chunks

            # Split into reasonable section chunks (approx ~1000 characters per chunk)
            paragraphs = combined_text.split("\n\n")
            current_chunk = []
            current_len = 0
            chunk_idx = 0
            page_estimate = 1

            for p in paragraphs:
                current_chunk.append(p)
                current_len += len(p)
                if current_len >= 1200:
                    chunks.append(
                        ExtractedChunk(
                            content="\n\n".join(current_chunk),
                            page_number=page_estimate,
                            chunk_index=chunk_idx
                        )
                    )
                    chunk_idx += 1
                    page_estimate += 1
                    current_chunk = []
                    current_len = 0

            if current_chunk:
                chunks.append(
                    ExtractedChunk(
                        content="\n\n".join(current_chunk),
                        page_number=page_estimate,
                        chunk_index=chunk_idx
                    )
                )

        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX file: {str(e)}")

        return chunks
