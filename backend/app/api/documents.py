import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentAssociate
from app.schemas.chunk import ChunkResponse
from app.utils.file_utils import validate_and_save_upload
from app.services.document_service import document_service
from app.services.redis_queue import redis_queue_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload educational document (.pdf, .docx, .pptx, .txt, .png, .jpg, .jpeg)."""
    try:
        file_path, file_type, file_hash, file_size = validate_and_save_upload(file)

        # Check if identical file hash already exists for this user
        existing_doc = db.query(Document).filter(
            Document.file_hash == file_hash,
            Document.user_id == current_user.id
        ).first()
        if existing_doc:
            return existing_doc

        new_doc = Document(
            user_id=current_user.id,
            filename=os.path.basename(file_path),
            original_name=file.filename or "uploaded_file",
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            file_hash=file_hash,
            status="PENDING"
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # Enqueue job into Redis Queue
        enqueued = redis_queue_service.enqueue_document_processing(new_doc.id)
        if not enqueued:
            # Fallback to in-process background task if Redis is offline/unreachable
            background_tasks.add_task(document_service.process_document_pipeline_with_new_db_session, new_doc.id)

        return new_doc

    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of uploaded documents belonging ONLY to current user."""
    return db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document details and current processing status for authorized owner."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc

@router.put("/{document_id}/associate", response_model=DocumentResponse)
def associate_document(
    document_id: str,
    payload: DocumentAssociate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Associate a document with another document (e.g. Question Paper + Answer Key)."""
    primary_doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not primary_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Primary document not found.")

    rel_doc_id = payload.related_document_id

    if rel_doc_id:
        if rel_doc_id == document_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A document cannot be associated with itself.")

        related_doc = db.query(Document).filter(Document.id == rel_doc_id, Document.user_id == current_user.id).first()
        if not related_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Related document not found or unauthorized.")

        rel_type = (payload.relationship_type or "ANSWER_KEY").upper().strip()
        if rel_type not in ["ANSWER_KEY", "SUPPLEMENT"]:
            rel_type = "ANSWER_KEY"

        primary_doc.related_document_id = rel_doc_id
        primary_doc.document_role = "QUESTION_PAPER"
        related_doc.document_role = rel_type
    else:
        # Clear association
        primary_doc.related_document_id = None
        primary_doc.document_role = "PRIMARY"

    db.commit()
    db.refresh(primary_doc)
    return primary_doc

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete document, physical file, chunks, and generated questions for authorized owner."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Clear references from other documents pointing to this document
    referencing_docs = db.query(Document).filter(Document.related_document_id == document_id).all()
    for ref in referencing_docs:
        ref.related_document_id = None
        ref.document_role = "PRIMARY"

    # Remove physical file if it exists
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()
    return {"success": True, "message": "Document deleted successfully."}

@router.post("/{document_id}/process", response_model=DocumentResponse)
def process_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger text extraction and LLM question generation pipeline for document asynchronously for authorized owner."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    doc.status = "PENDING"
    doc.error_message = None
    db.commit()
    db.refresh(doc)

    enqueued = redis_queue_service.enqueue_document_processing(document_id)
    if not enqueued:
        background_tasks.add_task(document_service.process_document_pipeline_with_new_db_session, document_id)

    return doc

@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get extracted text chunks for document belonging to authorized owner."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index.asc()).all()
    return chunks
