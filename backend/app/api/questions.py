from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.question import Question
from app.schemas.question import (
    QuestionResponse,
    QuestionCreate,
    QuestionUpdate,
    DifficultyLevel,
    QuestionType,
    BloomTaxonomy,
    validate_and_sanitize_question_data
)
from app.utils.exporter import export_questions_to_json, export_questions_to_csv
from app.api.deps import get_current_user

router = APIRouter(tags=["Questions"])

@router.get("/documents/{document_id}/questions", response_model=List[QuestionResponse])
def get_document_questions(
    document_id: str,
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty: EASY, MEDIUM, HARD"),
    question_type: Optional[QuestionType] = Query(None, description="Filter by type: MCQ, SHORT_ANSWER, LONG_ANSWER, TRUE_FALSE"),
    bloom_taxonomy: Optional[BloomTaxonomy] = Query(None, description="Filter by Bloom's Taxonomy"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve extracted questions for a document belonging to authorized owner."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    query = db.query(Question).filter(Question.document_id == document_id)

    if difficulty:
        query = query.filter(Question.difficulty == difficulty.value)
    if question_type:
        query = query.filter(Question.question_type == question_type.value)
    if bloom_taxonomy:
        query = query.filter(Question.bloom_taxonomy == bloom_taxonomy.value)

    return query.order_by(Question.created_at.asc()).all()

@router.post("/documents/{document_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def add_custom_question(
    document_id: str,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually add a question to a document belonging to authorized owner."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    try:
        clean = validate_and_sanitize_question_data(
            question_text=payload.question_text,
            question_type=payload.question_type,
            options=payload.options,
            correct_answer=payload.correct_answer,
            explanation=payload.explanation,
            difficulty=payload.difficulty,
            bloom_taxonomy=payload.bloom_taxonomy,
            page_reference=payload.page_reference,
            answer_status=payload.answer_status
        )

        new_q = Question(
            document_id=document_id,
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
        doc.question_count += 1
        db.commit()
        db.refresh(new_q)
        return new_q

    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: str,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing question belonging to authorized owner's document."""
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    doc = db.query(Document).filter(Document.id == q.document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    try:
        new_text = payload.question_text if payload.question_text is not None else q.question_text
        new_type = payload.question_type if payload.question_type is not None else q.question_type
        new_options = payload.options if payload.options is not None else q.options
        new_answer = payload.correct_answer if payload.correct_answer is not None else q.correct_answer
        new_status = payload.answer_status if payload.answer_status is not None else q.answer_status
        new_explanation = payload.explanation if payload.explanation is not None else q.explanation
        new_diff = payload.difficulty if payload.difficulty is not None else q.difficulty
        new_bloom = payload.bloom_taxonomy if payload.bloom_taxonomy is not None else q.bloom_taxonomy
        new_page = payload.page_reference if payload.page_reference is not None else q.page_reference

        clean = validate_and_sanitize_question_data(
            question_text=new_text,
            question_type=new_type,
            options=new_options,
            correct_answer=new_answer,
            explanation=new_explanation,
            difficulty=new_diff,
            bloom_taxonomy=new_bloom,
            page_reference=new_page,
            answer_status=new_status
        )

        q.question_text = clean["question_text"]
        q.question_type = clean["question_type"]
        q.options = clean["options"]
        q.correct_answer = clean["correct_answer"]
        q.answer_status = clean["answer_status"]
        q.explanation = clean["explanation"]
        q.difficulty = clean["difficulty"]
        q.bloom_taxonomy = clean["bloom_taxonomy"]
        q.page_reference = clean["page_reference"]

        db.commit()
        db.refresh(q)
        return q

    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

@router.delete("/questions/{question_id}")
def delete_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a question belonging to authorized owner's document."""
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    doc = db.query(Document).filter(Document.id == q.document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    if doc.question_count > 0:
        doc.question_count -= 1

    db.delete(q)
    db.commit()
    return {"success": True, "message": "Question deleted successfully."}

@router.get("/documents/{document_id}/export")
def export_document_questions(
    document_id: str,
    format: str = Query("json", description="Export format: json or csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export document questions as JSON or CSV file download for authorized owner."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    questions = db.query(Question).filter(Question.document_id == document_id).order_by(Question.created_at.asc()).all()
    
    clean_title = doc.original_name.rsplit(".", 1)[0]
    
    if format.lower() == "csv":
        csv_content = export_questions_to_csv(questions)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{clean_title}_questions.csv"'}
        )
    else:
        json_content = export_questions_to_json(questions)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{clean_title}_questions.json"'}
        )
