from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class QuestionType(str, Enum):
    MCQ = "MCQ"
    SHORT_ANSWER = "SHORT_ANSWER"
    LONG_ANSWER = "LONG_ANSWER"
    TRUE_FALSE = "TRUE_FALSE"

class DifficultyLevel(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class BloomTaxonomy(str, Enum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"

class AnswerStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNCERTAIN = "UNCERTAIN"
    NOT_FOUND = "NOT_FOUND"

# Schema used for Gemini structured JSON extraction output
class LLMQuestionItem(BaseModel):
    question_text: str = Field(description="The question statement")
    question_type: QuestionType = Field(description="Type of question: MCQ, SHORT_ANSWER, LONG_ANSWER, or TRUE_FALSE")
    options: Optional[List[str]] = Field(default=None, description="Array of options if type is MCQ, e.g. ['A. ...', 'B. ...']")
    correct_answer: Optional[str] = Field(default=None, description="The correct answer or ideal answer")
    explanation: Optional[str] = Field(default="", description="Detailed rationale or step-by-step answer explanation")
    difficulty: DifficultyLevel = Field(description="Difficulty level: EASY, MEDIUM, or HARD")
    bloom_taxonomy: Optional[BloomTaxonomy] = Field(default=BloomTaxonomy.UNDERSTAND, description="Bloom's Taxonomy category")
    page_reference: Optional[int] = Field(default=None, description="Page or slide number source reference")
    answer_status: Optional[AnswerStatus] = Field(default=AnswerStatus.NOT_FOUND, description="VERIFIED if grounded in Answer Key, UNCERTAIN if inferred, NOT_FOUND if missing")

class LLMQuestionResponse(BaseModel):
    questions: List[LLMQuestionItem]

# Schemas used for API requests & responses
class QuestionCreate(BaseModel):
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    answer_status: Optional[AnswerStatus] = AnswerStatus.NOT_FOUND
    explanation: Optional[str] = None
    difficulty: DifficultyLevel
    bloom_taxonomy: Optional[BloomTaxonomy] = None
    page_reference: Optional[int] = None

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    answer_status: Optional[AnswerStatus] = None
    explanation: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    bloom_taxonomy: Optional[BloomTaxonomy] = None
    page_reference: Optional[int] = None

class QuestionResponse(QuestionCreate):
    id: str
    document_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

def validate_and_sanitize_question_data(
    question_text: str,
    question_type: str,
    options: Optional[List[str]],
    correct_answer: Optional[str],
    explanation: Optional[str],
    difficulty: str,
    bloom_taxonomy: Optional[str],
    page_reference: Optional[int],
    has_ak_evidence: bool = False,
    answer_status: Optional[str] = None
) -> dict:
    q_text = (question_text or "").strip()
    if not q_text:
        raise ValueError("Question text cannot be empty.")

    c_ans = (correct_answer or "").strip() if correct_answer else ""
    if c_ans.upper() in ["NONE", "NULL", "NOT_FOUND", "UNKNOWN", "N/A", "MISSING", ""]:
        c_ans = None

    q_type = str(question_type.value if hasattr(question_type, 'value') else question_type).upper().strip() if question_type else "SHORT_ANSWER"
    if q_type not in ["MCQ", "SHORT_ANSWER", "LONG_ANSWER", "TRUE_FALSE"]:
        q_type = "SHORT_ANSWER"

    diff = str(difficulty.value if hasattr(difficulty, 'value') else difficulty).upper().strip() if difficulty else "MEDIUM"
    if diff not in ["EASY", "MEDIUM", "HARD"]:
        diff = "MEDIUM"

    bloom = str(bloom_taxonomy.value if hasattr(bloom_taxonomy, 'value') else bloom_taxonomy).upper().strip() if bloom_taxonomy else "UNDERSTAND"
    if bloom not in ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"]:
        bloom = "UNDERSTAND"

    status_str = str(answer_status.value if hasattr(answer_status, 'value') else answer_status).upper().strip() if answer_status else None
    if status_str not in ["VERIFIED", "UNCERTAIN", "NOT_FOUND"]:
        status_str = None

    clean_options = None
    final_status = "NOT_FOUND"

    if q_type == "MCQ":
        raw_opts = options if isinstance(options, list) else []
        clean_opts = [str(o).strip() for o in raw_opts if str(o).strip()]

        unique_opts = []
        for o in clean_opts:
            if o not in unique_opts:
                unique_opts.append(o)

        labels = ["A", "B", "C", "D"]
        if len(unique_opts) < 4:
            for i in range(len(unique_opts), 4):
                unique_opts.append(f"{labels[i]}. Option {i+1}")
        elif len(unique_opts) > 4:
            unique_opts = unique_opts[:4]

        clean_options = unique_opts

        if c_ans:
            matched = False
            for opt in clean_options:
                if c_ans.lower() == opt.lower():
                    c_ans = opt
                    matched = True
                    break

            if not matched:
                c_ans_upper = c_ans.upper()
                for idx, label in enumerate(labels):
                    if c_ans_upper == label or c_ans_upper == f"OPTION {label}" or c_ans_upper.startswith(f"{label}."):
                        c_ans = clean_options[idx]
                        matched = True
                        break

            if not matched:
                for opt in clean_options:
                    if c_ans.lower() in opt.lower() or opt.lower() in c_ans.lower():
                        c_ans = opt
                        matched = True
                        break

            if matched:
                final_status = status_str or ("VERIFIED" if has_ak_evidence else "UNCERTAIN")
            else:
                # NO SILENT OPTION-A FALLBACK!
                c_ans = None
                final_status = "UNCERTAIN" if has_ak_evidence else "NOT_FOUND"
        else:
            final_status = "NOT_FOUND"
    else:
        if c_ans:
            final_status = status_str or ("VERIFIED" if has_ak_evidence else "UNCERTAIN")
        else:
            final_status = "NOT_FOUND"

    return {
        "question_text": q_text,
        "question_type": q_type,
        "options": clean_options,
        "correct_answer": c_ans,
        "answer_status": final_status,
        "explanation": (explanation or "").strip(),
        "difficulty": diff,
        "bloom_taxonomy": bloom,
        "page_reference": page_reference
    }
