import csv
import io
import json
from typing import List
from app.models.question import Question

def export_questions_to_json(questions: List[Question]) -> str:
    data = []
    for q in questions:
        data.append({
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "options": q.options if q.options else [],
            "correct_answer": q.correct_answer,
            "answer_status": getattr(q, 'answer_status', 'NOT_FOUND') or 'NOT_FOUND',
            "explanation": q.explanation or "",
            "difficulty": q.difficulty,
            "bloom_taxonomy": q.bloom_taxonomy or "",
            "page_reference": q.page_reference,
            "created_at": q.created_at.isoformat() if q.created_at else None
        })
    return json.dumps(data, indent=2)

def export_questions_to_csv(questions: List[Question]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([
        "Question ID",
        "Question Text",
        "Type",
        "Options",
        "Correct Answer",
        "Answer Status",
        "Explanation",
        "Difficulty",
        "Bloom's Taxonomy",
        "Page/Slide Reference"
    ])

    for q in questions:
        options_str = ", ".join(q.options) if isinstance(q.options, list) else ""
        writer.writerow([
            q.id,
            q.question_text,
            q.question_type,
            options_str,
            q.correct_answer or "",
            getattr(q, 'answer_status', 'NOT_FOUND') or 'NOT_FOUND',
            q.explanation or "",
            q.difficulty,
            q.bloom_taxonomy or "",
            q.page_reference or ""
        ])

    return output.getvalue()
