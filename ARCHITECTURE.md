# Architecture Documentation
## Document Intelligence & Question Extraction Service

---

## 1. Overall Architecture

The **Pragati Bharati – Document Intelligence & Question Extraction Service** is built on a decoupled, microservices-oriented architecture designed to ingest multi-format educational documents, perform text and visual content extraction, generate grounded assessment questions via Large Language Models (LLMs), align answer keys, and manage structured question banks with owner-level multi-tenancy.

### System Components

- **Frontend**: A single-page application (SPA) built with React, Vite, and Tailwind CSS. It provides a Dark Editorial Document Studio interface for file ingestion, job status tracking, chunk inspection, question bank filtering/editing, document association, and export.
- **Backend / API Layer**: Built with Python and FastAPI, serving RESTful APIs with Pydantic schema validation, JWT bearer authentication, user authorization, and file upload handling.
- **Document Ingestion & Text Extractor Layer**: A modular extractor subsystem dispatching file formats (`PDF`, `DOCX`, `PPTX`, `TXT`, `PNG`, `JPG`, `JPEG`) to dedicated native parsers or multimodal vision models.
- **AI / LLM Layer**: Powered by Google Gemini (`gemini-3.6-flash` via official `google-genai` SDK) utilizing strict JSON schema enforcement and grounding prompts to extract educational questions, distractor options, answer statuses, difficulty levels, and Bloom's Taxonomy classifications.
- **Background Processing & Job Queue**: Dual-mode asynchronous processing using a Redis-backed queue (`docu_intel:jobs`) with a dedicated worker process (`worker.py`) using blocking pops (`BLPOP`). Falls back to FastAPI `BackgroundTasks` if Redis is unavailable.
- **Database Layer**: Relational database (PostgreSQL / SQLite via SQLAlchemy 2.0 ORM) persisting user accounts, document metadata, extracted text chunks, and structured question banks.
- **File Storage**: Local disk storage preserving original uploaded documents with SHA-256 deduplication per user.

### End-to-End Processing Flow

```
[User / Browser]
       |
       v
[FastAPI API Layer] ----(JWT Auth & Validation)
       |
       +----------------------------+
       |                            |
       v                            v
[Local Disk Storage]        [Redis Job Queue]
 (Upload Preservation)              |
                                    v
                          [Worker Process (worker.py)]
                                    |
                                    v
                         [Document Text Extraction]
                         (PyMuPDF / Docx / Pptx / Gemini Vision)
                                    |
                                    v
                         [Database Chunk Storage]
                                    |
                                    v
                         [Gemini LLM Extraction]
                         (Question Paper + Answer Key Alignment)
                                    |
                                    v
                         [Validation & Sanitization]
                         (No Silent Guessing / Answer Status)
                                    |
                                    v
                         [Database Persistence]
                         (Documents, Chunks, Questions)
```

---

## 2. Document-Processing Approach

The service processes text-based documents, presentation decks, raw text files, and visual images through specialized extraction strategy classes registered in `TextExtractorService`.

### Supported Document Types & Processing Mechanisms

| Document Type | Extractor Strategy | Primary Processing Method |
|---|---|---|
| **PDF** (`.pdf`) | `PDFTextExtractor` | Page-by-page text extraction via PyMuPDF (`fitz.open()`). |
| **DOCX** (`.docx`) | `DOCXTextExtractor` | Native document parsing via `python-docx` covering paragraphs and embedded tables. |
| **PPTX** (`.pptx`) | `PPTXTextExtractor` | Slide-by-slide parsing via `python-pptx` covering shape text frames and table cells. |
| **TXT** (`.txt`) | `TXTTextExtractor` | Text reading with fallback encoding resolution (UTF-8, Latin-1). |
| **Image / Scanned** (`.png`, `.jpg`, `.jpeg`) | `ImageExtractor` | Multimodal OCR and visual parsing using Gemini Vision (`gemini-3.6-flash`). |

### Page Handling & Text Extraction Behaviors

- **Selectable Text PDFs**: PyMuPDF extracts readable text page by page into indexed `DocumentChunk` records containing page numbers and token estimates.
- **Scanned PDFs / Images**: Dispatched to `ImageExtractor`, which converts image bytes into `types.Part.from_bytes()` and invokes Gemini Vision with a temperature setting of `0.1` to extract structured statements, lists, formulas, and headings without introducing external concepts.
- **Low-Quality / Low-Confidence OCR**: If an image or scanned document yields unreadable text, Gemini Vision returns empty text, triggering an explicit `ValueError` that transitions the document state to `FAILED` with details recorded in `error_message`.
- **Intermediate Representation**: All extractors output uniform `ExtractedChunk` dataclasses containing `content`, `page_number`, and `chunk_index`.

---

## 3. OCR / AI Technology Choices

### OCR & Vision Layer: Google Gemini Vision

- **Technology**: Google Gemini Multimodal Vision (`gemini-3.6-flash` via `google-genai` SDK).
- **Usage**: Handles visual OCR for uploaded images (`PNG`, `JPG`, `JPEG`) and scanned educational documents.
- **Input / Output**: Accepts binary image payloads; outputs formatted plain text preserving original math formulas, lists, and headings.
- **Rationale**: Replaces brittle legacy Tesseract/C++ dependencies with cloud-native multimodal vision capable of deciphering handwritten, noisy, or multi-column layout text.

### AI / LLM Layer: Google Gemini API

- **Model**: `gemini-3.6-flash` (configurable via `GEMINI_MODEL` environment variable).
- **SDK**: Official `google-genai` client package (`google.genai.Client`).
- **Structured Output**: Uses `response_mime_type="application/json"` combined with Pydantic `LLMQuestionResponse` schema enforcement (`response_schema=LLMQuestionResponse`).
- **Deterministic Validation**: Response items pass through `validate_and_sanitize_question_data()` in `app/schemas/question.py`, which normalizes MCQ options to 4 choices, verifies answer option matching, and enforces non-empty question statements.
- **Rate Limit & Resiliency Handling**: Implements backoff retries (up to 6 attempts) detecting HTTP `429`, `503`, and `RESOURCE_EXHAUSTED` responses, dynamically extracting retry intervals from error bodies.

---

## 4. Storage Design

### File Storage Implementation

- **Location**: `backend/storage/uploads/` directory on local disk.
- **File Naming**: UUID-based stored filenames (`<uuid>.<ext>`) to prevent filesystem path traversal attacks. Original user-uploaded file names are preserved in the `Document.original_name` column.
- **Deduplication**: Calculates SHA-256 file hashes (`hashlib.sha256`) during upload. If a file with an identical hash already exists for the authenticated user, duplicate uploads return the existing record without re-processing.

### Database Schema (Relational Models)

```
[User] 1 ---- * [Document] (Owner)
                   |
                   +-- 1 ---- * [DocumentChunk] (Page Text Chunks)
                   |
                   +-- 1 ---- * [Question] (Extracted Question Bank)
                   |
                   +-- 1 ---- 0..1 [Document] (Related Answer Key / Supplement)
```

#### Entities Summary

1. **`users` (`User`)**:
   - `id`: String(36) UUID primary key
   - `email`: String(255) unique indexed email
   - `password_hash`: String(255) bcrypt password hash
   - `created_at`: DateTime UTC timestamp

2. **`documents` (`Document`)**:
   - `id`: String(36) UUID primary key
   - `user_id`: ForeignKey(`users.id`)
   - `related_document_id`: ForeignKey(`documents.id`) nullable self-reference
   - `document_role`: String(30) enum (`PRIMARY`, `QUESTION_PAPER`, `ANSWER_KEY`, `SUPPLEMENT`)
   - `filename`, `original_name`, `file_type`, `file_size`, `file_path`, `file_hash`
   - `status`: String(30) enum (`PENDING`, `EXTRACTING_TEXT`, `EXTRACTING_QUESTIONS`, `COMPLETED`, `FAILED`)
   - `chunk_count`, `question_count`, `error_message`, `created_at`, `updated_at`

3. **`document_chunks` (`DocumentChunk`)**:
   - `id`: String(36) UUID primary key
   - `document_id`: ForeignKey(`documents.id` with CASCADE delete)
   - `chunk_index`, `page_number`, `content`, `token_count_estimate`, `created_at`

4. **`questions` (`Question`)**:
   - `id`: String(36) UUID primary key
   - `document_id`: ForeignKey(`documents.id` with CASCADE delete)
   - `question_text`: Text statement
   - `question_type`: String(30) (`MCQ`, `SHORT_ANSWER`, `LONG_ANSWER`, `TRUE_FALSE`)
   - `options`: JSON array of strings e.g. `["A. ...", "B. ...", "C. ...", "D. ..."]`
   - `correct_answer`: Text
   - `answer_status`: String(30) (`VERIFIED`, `UNCERTAIN`, `NOT_FOUND`)
   - `explanation`, `difficulty` (`EASY`, `MEDIUM`, `HARD`), `bloom_taxonomy` (`REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`, `EVALUATE`, `CREATE`), `page_reference`

---

## 5. Asynchronous Processing

Document extraction and LLM pipeline calls execute asynchronously to avoid blocking API request threads.

### Asynchronous Execution Architecture

```
User Upload Request -> Save File & Insert Document (status="PENDING")
                           |
            +--------------+--------------+
            |                             |
     [Redis Available]           [Redis Offline]
            |                             |
   rpush("docu_intel:jobs")     FastAPI BackgroundTasks
            |                             |
    worker.py (BLPOP)            In-process Thread Pool
            \                             /
             v                           v
          DocumentService.process_document_pipeline()
```

- **Job Lifecycle**:
  1. Upload endpoint sets `Document.status = "PENDING"`.
  2. Enqueues job ID to Redis list `docu_intel:jobs`.
  3. `worker.py` pops the job ID using `blpop()`.
  4. Worker updates status to `"EXTRACTING_TEXT"`, extracts chunks, saves `DocumentChunk` records.
  5. Status updates to `"EXTRACTING_QUESTIONS"`, passes content to Gemini LLM.
  6. Saves `Question` entities, updates status to `"COMPLETED"`, sets `question_count`.
  7. On error, rolls back transaction, sets status to `"FAILED"`, stores error string in `error_message`.
- **Frontend Status Tracking**: Frontend polls `GET /documents/{document_id}` or lists documents to observe status transitions (`PENDING` $\rightarrow$ `EXTRACTING_TEXT` $\rightarrow$ `EXTRACTING_QUESTIONS` $\rightarrow$ `COMPLETED`).

---

## 6. Question Extraction Strategy

### Question Structuring & Generation Pipeline

1. **Text Chunking**: Document is converted into ordered page text chunks.
2. **Grounding Directive**: Prompts explicitly command the LLM to restrict question generation exclusively to facts in the input text chunk.
3. **Structured JSON Extraction**: The model returns structured objects matching `LLMQuestionItem`:
   ```json
   {
     "question_text": "What is the primary function of mitochondria in eukaryotic cells?",
     "question_type": "MCQ",
     "options": [
       "A. Production of ATP through cellular respiration",
       "B. Protein synthesis on ribosomes",
       "C. Lipid storage and modification",
       "D. DNA replication during mitosis"
     ],
     "correct_answer": "A. Production of ATP through cellular respiration",
     "explanation": "Mitochondria generate cellular energy (ATP) via aerobic respiration.",
     "difficulty": "EASY",
     "bloom_taxonomy": "REMEMBER",
     "page_reference": 3,
     "answer_status": "VERIFIED"
   }
   ```
4. **Deterministic Validation & Sanitization**:
   - MCQ options are cleaned, deduplicated, and normalized to 4 options (`A`, `B`, `C`, `D`).
   - Correct answer string matching validates against options list.
   - If no correct answer can be verified from the text or answer key, `correct_answer` is set to `None`, and `answer_status` is marked as `NOT_FOUND` or `UNCERTAIN`. **No silent guessing or defaulting to Option A occurs.**

---

## 7. Answer-Key Association

The system supports answer key association across two scenarios:

### 1. Same-Document Answer Keys
- `is_answer_key_chunk()` uses regular expressions to detect header indicators such as `ANSWER KEY`, `CORRECT ANSWERS`, `OFFICIAL SOLUTIONS`, or `ANSWER SHEET` in page chunks.
- If an answer key section is found at the end or beginning of a single document, the system splits question content from answer key content.
- Combined prompt `build_question_extraction_with_answer_key_prompt()` supplies both Question Paper text and Answer Key text to Gemini.

### 2. Separate-Document Answer Keys
- Users can associate a Question Paper document with a separate Answer Key document via `PUT /documents/{document_id}/associate`.
- Sets `Document.related_document_id` and assigns roles (`QUESTION_PAPER` and `ANSWER_KEY`).
- When processing the Question Paper, `DocumentService` reads chunks from the associated Answer Key file and submits combined context to Gemini for precise question-answer grounding.

---

## 8. Confidence / Review Mechanism

Uncertain or unverified extractions are flagged automatically for human inspection rather than returning false answers.

### Status Classification Rules

```
                      Extraction & Matching
                                |
             +------------------+------------------+
             |                                     |
    Answer Key Evidence Available          No Answer Key Evidence
             |                                     |
   +---------+---------+                 +-----------+-----------+
   |                   |                 |                       |
Exact Match       Unmatched /           Explicit Answer        Missing / Ambiguous
Found             Ambiguous             Stated in Text         Answer
   |                   |                 |                       |
   v                   v                 v                       v
VERIFIED           UNCERTAIN         VERIFIED                NOT_FOUND / UNCERTAIN
```

- **`VERIFIED`**: The correct answer is explicitly grounded in an attached/detected Answer Key or stated verbatim in text.
- **`UNCERTAIN`**: The question or option structure contains minor ambiguities, or the answer key was missing matching numbers.
- **`NOT_FOUND`**: No answer key evidence was provided and the text does not contain explicit answer statements.
- **Human Review & Manual Correction**: Users can edit any question parameter (`question_text`, `options`, `correct_answer`, `answer_status`, `difficulty`, `bloom_taxonomy`) via `PUT /questions/{question_id}` or delete questions via `DELETE /questions/{question_id}`.

---

## 9. Security Considerations

- **Authentication**: User accounts register and authenticate via `/auth/register` and `/auth/login`. Passwords are hashed using `bcrypt` via `passlib`.
- **JWT Authorization**: Authenticated sessions issue JSON Web Tokens (`pyjwt`) signed with HS256. API routes require `Authorization: Bearer <token>` via `get_current_user` dependency.
- **Owner Data Isolation**: All database queries filter explicitly by `user_id == current_user.id`, preventing unauthorized cross-user access to documents, chunks, or questions.
- **File Validation & Sanitization**:
  - Allowed file extensions checked against whitelist (`pdf`, `docx`, `pptx`, `txt`, `png`, `jpg`, `jpeg`).
  - Stored files assigned non-predictable UUID filenames to prevent path traversal (`../`).
  - Maximum upload file size enforced (`validate_and_save_upload`).
- **Secrets Management**: Secrets (`GEMINI_API_KEY`, `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`) loaded from environment variables / `.env` file via `pydantic-settings`.

---

## 10. Scalability Considerations

### Currently Implemented Architecture
- Single FastAPI app server handling stateless REST API requests.
- Asynchronous processing offloaded to Redis queue (`docu_intel:jobs`) and `worker.py` worker process.
- SQLAlchemy 2.0 connection pooling.
- Cloud API offloading for visual OCR and LLM extraction via Google Gemini.

### Recommended Future Production Scaling
- **Object Storage**: Migrate local file storage (`backend/storage/uploads/`) to Amazon S3 or Google Cloud Storage.
- **Distributed Worker Swarm**: Scale `worker.py` horizontally across multiple process instances using Celery or Redis Queue (`rq`).
- **Database Read Replicas**: Separate read query load for question browsing from document processing writes.
- **API Rate Limiting**: Introduce Redis-backed IP/user rate limiting middleware (`slowapi`).

---

## 11. Important Trade-offs and Limitations

| Area | Current Approach | Benefit | Trade-off / Limitation |
|---|---|---|---|
| **OCR / Vision** | Gemini Vision Cloud API | High accuracy on complex/noisy layouts without native C++ OCR dependencies. | Requires active internet connection and API quota consumption. |
| **File Storage** | Local Disk Storage | Simple, zero-cost setup for single-server demonstration. | Cannot scale horizontally across multi-node server clusters without shared volumes. |
| **Background Queue** | Dual Redis BLPOP / FastAPI Fallback | Guarantees background execution even if Redis instance is temporarily unavailable. | Fallback in-process thread execution shares CPU/RAM resources with API server. |
| **Structured Output** | Gemini Pydantic Schema Enforcement | Strict JSON outputs matching required TypeScript/Pydantic types. | Dependent on Google Gemini API availability and rate limits. |
| **Multi-Tenancy** | Soft Owner Isolation | Simple relational user mapping per row. | Does not include complex multi-tenant enterprise org/team RBAC permissions. |

---

## 12. End-to-End Processing Flow

```
[Upload Document] (POST /documents/upload)
       │
       ▼
[Validate Extension & SHA-256 Hash]
       │
       ▼
[Save UUID File to storage/uploads/]
       │
       ▼
[Insert Document Record (status="PENDING")]
       │
       ▼
[Enqueue Document ID to Redis Queue (docu_intel:jobs)]
       │
       ▼
[Worker Process Dequeues Job (worker.py)]
       │
       ▼
[Extract Text Chunks (PyMuPDF / Docx / Pptx / Gemini Vision)]
       │
       ▼
[Insert DocumentChunk Records (status="EXTRACTING_TEXT")]
       │
       ▼
[Detect / Load Answer Key Context (Same-doc or Related-doc)]
       │
       ▼
[Gemini LLM Extraction (status="EXTRACTING_QUESTIONS")]
       │
       ▼
[Validate & Sanitize Question Data (Answer Status Evaluation)]
       │
       ▼
[Persist Questions to DB & Update Status to "COMPLETED"]
       │
       ▼
[Frontend Fetches Questions & Export JSON / CSV]
```

---

## 13. Technology Stack Summary

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend UI** | React 18, Vite, Tailwind CSS | Dark Editorial Document Studio interface |
| **Backend Framework** | FastAPI (Python 3.11/3.12+), Uvicorn | High-performance asynchronous API server |
| **Database** | PostgreSQL / SQLite, SQLAlchemy 2.0 ORM | Relational persistence layer |
| **Task Queue** | Redis, Python `redis` client (`BLPOP`) | Asynchronous background processing queue |
| **OCR & Vision** | Google Gemini Vision (`gemini-3.6-flash`) | Visual text extraction for images & scans |
| **AI / LLM Engine** | Google Gemini API (`google-genai` SDK) | Grounded educational question generation |
| **PDF Extraction** | PyMuPDF (`fitz`) | High-speed native PDF parsing |
| **Office Doc Parsing** | `python-docx`, `python-pptx` | Microsoft Word & PowerPoint text extraction |
| **Authentication** | PyJWT, Passlib (Bcrypt) | Bearer token authorization & password security |

---

## 14. Architecture Decisions Summary

1. **Decision**: Use Google Gemini Multimodal Vision for OCR instead of Tesseract.  
   **Reason**: Delivers superior extraction accuracy on complex scanned documents, mathematical notation, and multi-column layouts without requiring native C++ binary installations.  
   **Impact**: Simplifies backend deployment while depending on Gemini API connectivity.

2. **Decision**: Enforce Strict Grounding Prompts and Pydantic JSON Schema Validation.  
   **Reason**: Prevents LLM hallucinations, outside concept injection, and ungrounded answer guesses.  
   **Impact**: Ensures generated questions are 100% answerable from uploaded source documents.

3. **Decision**: Dual-Mode Asynchronous Processing (Redis Queue + FastAPI Fallback).  
   **Reason**: Guarantees document processing succeeds seamlessly regardless of whether a standalone Redis server is active.  
   **Impact**: High operational resiliency across different deployment environments.

4. **Decision**: Explicit `AnswerStatus` Classification (`VERIFIED`, `UNCERTAIN`, `NOT_FOUND`).  
   **Reason**: Eliminates silent answer guessing or arbitrary Option-A defaulting when answer keys are missing or ambiguous.  
   **Impact**: Transparents flags questions requiring human review.

5. **Decision**: SHA-256 Hash Deduplication per User.  
   **Reason**: Prevents redundant storage consumption and repetitive LLM processing costs when identical files are uploaded.  
   **Impact**: Optimizes server storage and API quota usage.
