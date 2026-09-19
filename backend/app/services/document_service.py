import os
import traceback
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.models.question import Question
from app.schemas.question import validate_and_sanitize_question_data
from app.services.text_extractor import text_extractor_service
from app.services.llm import gemini_llm_service

import re

def is_answer_key_chunk(content: str) -> bool:
    if not content or not content.strip():
        return False
    patterns = [
        r"(?i)\b(official\s+)?answer\s*keys?\b",
        r"(?i)\b(correct\s+)?answers?\b",
        r"(?i)\banswer\s*sheet\b",
        r"(?i)\bsolutions?\b",
        r"(?i)\bcorrect\s*options?\b",
        r"(?i)\banswers\s*key\b",
    ]
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    for line in lines[:10]:
        if re.search(r"(?i)\b(explain|write|give|check|find)\s+(your\s+)?answer", line):
            continue
        for p in patterns:
            if re.search(p, line):
                return True
    return False

def split_content_at_answer_key(content: str):
    if not content:
        return content, ""
    patterns = [
        r"(?i)\n\s*(official\s+)?answer\s*keys?\b",
        r"(?i)\n\s*(correct\s+)?answers?\b",
        r"(?i)\n\s*answer\s*sheet\b",
        r"(?i)\bsolutions?\b",
        r"(?i)\n\s*correct\s*options?\b",
        r"(?i)\n\s*answers\s*key\b",
    ]
    for p in patterns:
        m = re.search(p, content)
        if m:
            idx = m.start()
            qp_part = content[:idx].strip()
            ak_part = content[idx:].strip()
            return qp_part, ak_part
    return content, ""

def sanitize_error_message(raw_error: str) -> str:
    if not raw_error:
        return "Document processing failed due to an unexpected error."

    err_lower = raw_error.lower()
    if "quota" in err_lower or "rate limit" in err_lower or "429" in err_lower or "resource_exhausted" in err_lower:
        return "AI service rate limit or quota exceeded. Please wait a moment and click Process again."
    if "api key" in err_lower or "api_key" in err_lower:
        return "AI service API key configuration error. Please verify backend settings."
    if "no readable text" in err_lower:
        return "No readable text content could be extracted from this document."
    if "unsupported document type" in err_lower:
        return "Unsupported document file type."
    if "file" in err_lower and "not found" in err_lower:
        return "Source document file could not be retrieved from storage."

    # Clean line breaks and sanitize any key patterns
    first_line = raw_error.strip().split("\n")[0]
    cleaned = re.sub(r"(?i)(api[_-]?key|secret|token|password)=[\w-]+", r"\1=***", first_line)
    cleaned = re.sub(r"(?i)bearer\s+[\w.-]+", "Bearer ***", cleaned)
    return cleaned[:200]

class VirtualChunk:
    def __init__(self, content: str, page_number: int):
        self.content = content
        self.page_number = page_number

class DocumentService:
    def process_document_pipeline(self, db: Session, document_id: str) -> Document:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document with ID '{document_id}' not found.")

        try:
            # Step 1: Text Extraction
            doc.status = "EXTRACTING_TEXT"
            doc.error_message = None
            db.commit()

            chunks = text_extractor_service.extract(doc.file_path, doc.file_type)
            if not chunks:
                raise ValueError("No readable text content found in document.")

            # Clear any previous chunks/questions if re-processing
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
            db.query(Question).filter(Question.document_id == document_id).delete()
            db.commit()

            # Save chunks to database
            db_chunks = []
            for chunk in chunks:
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    content=chunk.content,
                    token_count_estimate=len(chunk.content.split())
                )
                db.add(db_chunk)
                db_chunks.append(db_chunk)

            doc.chunk_count = len(db_chunks)
            db.commit()

            # Check for Answer Key evidence (separate document OR same-document scanning)
            related_doc = None
            if doc.related_document_id:
                related_doc = db.query(Document).filter(Document.id == doc.related_document_id).first()

            # Step 2: Question Extraction via Gemini LLM Service
            doc.status = "EXTRACTING_QUESTIONS"
            db.commit()

            total_questions = 0
            ak_text = ""
            question_chunks = db_chunks
            has_ak_evidence = False

            if related_doc and os.path.exists(related_doc.file_path):
                # Separate document Answer Key
                ak_chunks = text_extractor_service.extract(related_doc.file_path, related_doc.file_type)
                ak_text = "\n\n".join([c.content for c in ak_chunks]) if ak_chunks else ""
                has_ak_evidence = bool(ak_text)
            else:
                # Same-document Answer Key scanning across all chunks
                same_doc_ak_chunks = [c for c in db_chunks if is_answer_key_chunk(c.content)]
                if same_doc_ak_chunks and len(db_chunks) > len(same_doc_ak_chunks):
                    ak_text = "\n\n".join([c.content for c in same_doc_ak_chunks])
                    question_chunks = [c for c in db_chunks if c not in same_doc_ak_chunks]
                    has_ak_evidence = True
                elif len(db_chunks) == 1:
                    qp_part, ak_part = split_content_at_answer_key(db_chunks[0].content)
                    if ak_part and qp_part:
                        ak_text = ak_part
                        has_ak_evidence = True
                        question_chunks = [VirtualChunk(qp_part, db_chunks[0].page_number)]

            if has_ak_evidence and ak_text:
                # Combined processing with Answer Key evidence
                for chunk in question_chunks:
                    llm_response = gemini_llm_service.extract_questions_from_text_with_answer_key(
                        qp_text=chunk.content,
                        ak_text=ak_text
                    )

                    for item in llm_response.questions:
                        clean = validate_and_sanitize_question_data(
                            question_text=item.question_text,
                            question_type=item.question_type,
                            options=item.options,
                            correct_answer=item.correct_answer,
                            explanation=item.explanation,
                            difficulty=item.difficulty,
                            bloom_taxonomy=item.bloom_taxonomy,
                            page_reference=item.page_reference or chunk.page_number,
                            has_ak_evidence=True,
                            answer_status=item.answer_status
                        )

                        new_q = Question(
                            document_id=doc.id,
                            question_text=clean["question_text"],
                            question_type=clean["question_type"],
                            options=clean["options"],
                            correct_answer=clean["correct_answer"],
                            answer_status=clean["answer_status"],
                            explanation=clean["explanation"],
                            difficulty=clean["difficulty"],
                            bloom_taxonomy=clean["bloom_taxonomy"],
                            page_reference=clean["page_reference"]
                        )
                        db.add(new_q)
                        total_questions += 1
            else:
                # Standalone processing without Answer Key
                for chunk in question_chunks:
                    llm_response = gemini_llm_service.extract_questions_from_text(
                        text_chunk=chunk.content,
                        page_number=chunk.page_number
                    )

                    for item in llm_response.questions:
                        clean = validate_and_sanitize_question_data(
                            question_text=item.question_text,
                            question_type=item.question_type,
                            options=item.options,
                            correct_answer=item.correct_answer,
                            explanation=item.explanation,
                            difficulty=item.difficulty,
                            bloom_taxonomy=item.bloom_taxonomy,
                            page_reference=item.page_reference or chunk.page_number,
                            has_ak_evidence=False,
                            answer_status=item.answer_status
                        )

                        new_q = Question(
                            document_id=doc.id,
                            question_text=clean["question_text"],
                            question_type=clean["question_type"],
                            options=clean["options"],
                            correct_answer=clean["correct_answer"],
                            answer_status=clean["answer_status"],
                            explanation=clean["explanation"],
                            difficulty=clean["difficulty"],
                            bloom_taxonomy=clean["bloom_taxonomy"],
                            page_reference=clean["page_reference"]
                        )
                        db.add(new_q)
                        total_questions += 1

            doc.question_count = total_questions
            doc.status = "COMPLETED"
            doc.error_message = None
            db.commit()
            db.refresh(doc)
            return doc

        except Exception as e:
            err_str = str(e)
            safe_error = sanitize_error_message(err_str)

            print(f"[Pipeline Error] Failed processing document {document_id}: {err_str}")
            traceback.print_exc()

            try:
                db.rollback()
                doc = db.query(Document).filter(Document.id == document_id).first()
                if doc:
                    doc.status = "FAILED"
                    doc.error_message = safe_error
                    db.commit()
            except Exception as db_err:
                print(f"[DB Error Recording Failure] Using fallback session: {str(db_err)}")
                try:
                    from app.database import SessionLocal
                    fresh_db = SessionLocal()
                    fresh_doc = fresh_db.query(Document).filter(Document.id == document_id).first()
                    if fresh_doc:
                        fresh_doc.status = "FAILED"
                        fresh_doc.error_message = safe_error
                        fresh_db.commit()
                    fresh_db.close()
                except Exception as fresh_err:
                    print(f"[Fallback DB Session Error] {str(fresh_err)}")

            raise e

    def process_document_pipeline_with_new_db_session(self, document_id: str) -> None:
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            self.process_document_pipeline(db, document_id)
        except Exception as e:
            print(f"[Worker/Background Processing Error] {str(e)}")
        finally:
            db.close()

document_service = DocumentService()
