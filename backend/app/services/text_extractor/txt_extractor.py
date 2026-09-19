from typing import List
from app.services.text_extractor.base import BaseTextExtractor, ExtractedChunk

class TXTTextExtractor(BaseTextExtractor):
    def extract_chunks(self, file_path: str) -> List[ExtractedChunk]:
        chunks: List[ExtractedChunk] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
            
            if not content:
                return chunks

            paragraphs = content.split("\n\n")
            current_chunk = []
            current_len = 0
            chunk_idx = 0
            page_num = 1

            for p in paragraphs:
                p_clean = p.strip()
                if not p_clean:
                    continue
                current_chunk.append(p_clean)
                current_len += len(p_clean)

                if current_len >= 1200:
                    chunks.append(
                        ExtractedChunk(
                            content="\n\n".join(current_chunk),
                            page_number=page_num,
                            chunk_index=chunk_idx
                        )
                    )
                    chunk_idx += 1
                    page_num += 1
                    current_chunk = []
                    current_len = 0

            if current_chunk:
                chunks.append(
                    ExtractedChunk(
                        content="\n\n".join(current_chunk),
                        page_number=page_num,
                        chunk_index=chunk_idx
                    )
                )

        except Exception as e:
            raise ValueError(f"Failed to read TXT file: {str(e)}")

        return chunks
