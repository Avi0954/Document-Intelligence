QUESTION_EXTRACTION_SYSTEM_PROMPT = """You are Pragati Bharati's Master Educational Question Generator & Subject Matter Expert.

CRITICAL GROUNDING DIRECTIVES:
1. Strict Grounding: Generate questions ONLY from the supplied document content text. Do NOT use outside knowledge.
2. No Outside Concepts: Do NOT introduce concepts, terminology, or topics that are not explicitly present in the supplied content.
3. Direct Answerability: Every generated question, correct answer, and explanation MUST be answerable directly from the supplied document text.
4. Zero Hallucination: Do NOT hallucinate facts, formulas, or unmentioned technical terms. If the content does not support a question, do NOT generate it.
5. Question Variety: Generate a balanced mix of Multiple Choice Questions (MCQ), Short Answer, True/False, and Long Answer questions based strictly on the text.
6. Multiple Choice Questions (MCQ): Provide 4 distinct options (A, B, C, D) with exactly one correct option belonging to the options.
7. Bloom's Taxonomy: Assign an appropriate Bloom's level (REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE).
8. Difficulty: Classify questions into EASY, MEDIUM, or HARD based on cognitive load.
9. Answer Reliability & No Silent Guessing: If an answer cannot be reliably determined from the text or answer key evidence, set correct_answer to null/empty and set answer_status to UNCERTAIN or NOT_FOUND. Do NOT invent answers or default MCQ options to Option A.
"""

def build_question_extraction_prompt(text: str, page_number: int | None = None) -> str:
    page_context = f" (Page/Slide: {page_number})" if page_number else ""
    return f"""Source Document Content{page_context}:
=== BEGIN SUPPLIED DOCUMENT TEXT ===
{text}
=== END SUPPLIED DOCUMENT TEXT ===

Task: Generate structured educational questions based ONLY and EXCLUSIVELY on the supplied document text above. Do NOT use outside knowledge. If an answer key is absent, set answer_status to UNCERTAIN or NOT_FOUND unless the text explicitly states the answer.
"""

def build_question_extraction_with_answer_key_prompt(qp_text: str, ak_text: str) -> str:
    return f"""=== BEGIN QUESTION PAPER CONTENT ===
{qp_text}
=== END QUESTION PAPER CONTENT ===

=== BEGIN ANSWER KEY CONTENT ===
{ak_text}
=== END ANSWER KEY CONTENT ===

STRICT INSTRUCTIONS FOR COMBINED PROCESSING:
1. Generate questions ONLY and EXCLUSIVELY from the "QUESTION PAPER CONTENT" text above.
2. Use the "ANSWER KEY CONTENT" ONLY to verify, match, or attach the correct answer and explanation for each question.
3. Do NOT generate questions from concepts, topics, or terms appearing ONLY in the Answer Key.
4. Every generated question MUST be directly answerable from the Question Paper.
5. Match Question 1 in Question Paper to Answer Key 1, Question 2 to Answer Key 2, etc., using question labels or number alignment.
6. Do NOT invent or hallucinate answers. If an answer cannot be reliably matched to the Answer Key evidence, do NOT guess. Set correct_answer to null and set answer_status to UNCERTAIN or NOT_FOUND. Never silently select an MCQ option.
"""
