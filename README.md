## Architecture

```
Frontend (React / Vite)
   ↓ Upload Document / Poll Status
FastAPI Web Layer (documents.py)
   ↓ Save File & Create Record (PENDING)
PostgreSQL Database (documents, chunks, questions)
   ↓ Enqueue document_id
Redis Queue (redis://localhost:6379/0)
   ↓ Dequeue document_id
Standalone Background Worker (worker.py)
   ↓ Extract Text / Vision OCR (PyMuPDF / Gemini Vision for Images)
Gemini 3.6 Flash LLM Service
   ↓ Persist Extracted Chunks & Grounded Questions
PostgreSQL Database
```

---

## Key Features

1. **Multi-Format Document Ingestion:**
   - **PDF:** Native page-by-page text extraction via `PyMuPDF`.
   - **DOCX:** Structured paragraph and table extraction via `python-docx`.
   - **PPTX:** Slide-indexed text extraction via `python-pptx`.
   - **TXT:** Plain UTF-8 text decoding.
   - **PNG / JPG / JPEG:** Vision OCR content extraction via Google Gemini Vision API.
2. **Redis-Backed Asynchronous Job Queue:**
   - Decoupled API upload layer from processing pipeline.
   - Redis queue (`docu_intel:jobs`) triggers standalone background worker (`worker.py`).
   - Supports concurrent processing of multiple documents.
3. **AI Question Extraction Engine:**
   - Isolated LLM service interface (`BaseLLMService` / `GeminiLLMService`).
   - Uses `google-genai` SDK with Pydantic JSON schemas to guarantee structured output.
   - Generates MCQs (with 4 options), Short Answer, Long Answer, and True/False questions.
   - Classifies questions by Difficulty (`EASY`, `MEDIUM`, `HARD`) and Bloom's Taxonomy (`REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`, `EVALUATE`, `CREATE`).
4. **Related Document Association (Question Paper + Answer Key):**
   - Simple document pairing mechanism allowing a Question Paper to be linked with an Answer Key.
   - Preserves grounded question generation strictly from Question Paper while utilizing the associated Answer Key to verify correct answers and option selections.
5. **Structured API & Exporter:**
   - RESTful endpoints for document upload, document association, pipeline processing, question CRUD, and search filtering.
   - One-click export to **JSON** and **CSV** formats.
6. **Modern Web UI:**
   - Clean, modern, black-and-white SaaS dashboard built with React, Vite, and Tailwind CSS.
   - Drag-and-drop uploader with real-time status polling (`PENDING` $\rightarrow$ `COMPLETED`).
   - Interactive document associate modal and question explorer with expandable answer rationales, inline editor modal, and export toolbar.

---

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL, Redis, Pydantic v2, Uvicorn
- **Background Queue:** Redis Queue (`redis>=5.0.0`), Standalone Python Worker (`worker.py`)
- **AI / LLM:** Google Gemini API (`google-genai` SDK, `gemini-3.6-flash`, Gemini Vision OCR)
- **Document Parsers:** `pymupdf`, `python-docx`, `python-pptx`, `pillow`
- **Frontend:** React 19, Vite, Tailwind CSS, Axios

---

## Project Structure

```
Docu Intelligence/
├── backend/
├── app/
│   ├── main.py                   # FastAPI app entry point & CORS
│   ├── config.py                 # Pydantic Settings & Env configuration
│   ├── database.py               # SQLAlchemy Engine (PostgreSQL/SQLite)
│   ├── models/                   # SQLAlchemy DB Models (Document, Chunk, Question)
│   ├── schemas/                  # Pydantic Request/Response validation
│   ├── api/                      # REST Endpoints (health, documents, questions)
│   ├── services/                 # Core Business Logic
│   │   ├── document_service.py   # Extraction pipeline runner
│   │   ├── redis_queue.py        # Redis job queue service
│   │   ├── text_extractor/       # PDF, DOCX, PPTX, TXT, and Image extractors
│   │   └── llm/                  # BaseLLMService & GeminiLLMService
│   └── utils/                    # Exporter (CSV/JSON), File Hashing
├── worker.py                     # Standalone Redis job worker process
├── storage/uploads/              # Uploaded document storage
├── requirements.txt
├── .env.example
└── run.py                        # Uvicorn backend launcher
│
├── frontend/
│   ├── src/
│   │   ├── components/               # Navbar, Upload, DocumentList, QuestionCard, Filters, Modals
│   │   ├── services/api.js           # Axios API client
│   │   ├── App.jsx                   # Main layout component with polling
│   │   └── index.css                 # Tailwind CSS & monochrome theme
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Getting Started

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
cp .env.example .env

# Edit backend/.env and add your Gemini API Key:
# GEMINI_API_KEY="AIzaSy..."

# Start the FastAPI Backend Server
python run.py
```
The API server will run on `http://127.0.0.1:8000`. API Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite Development Server
npm run dev
```
The web dashboard will run on `http://127.0.0.1:5173`.

---

## API Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Check backend & Gemini API configuration status |
| `POST` | `/api/v1/documents/upload` | Upload `.pdf`, `.docx`, `.pptx`, or `.txt` document |
| `GET` | `/api/v1/documents` | List uploaded documents |
| `GET` | `/api/v1/documents/{id}` | Get document metadata & status |
| `PUT` | `/api/v1/documents/{id}/associate` | Associate document with another (e.g., Question Paper + Answer Key) |
| `DELETE` | `/api/v1/documents/{id}` | Delete document and associated questions |
| `POST` | `/api/v1/documents/{id}/process` | Trigger text extraction & AI question generation |
| `GET` | `/api/v1/documents/{id}/chunks` | View extracted text chunks by page/slide |
| `GET` | `/api/v1/documents/{id}/questions` | Get questions for document (supports `difficulty`, `question_type`, `bloom_taxonomy` query filters) |
| `POST` | `/api/v1/documents/{id}/questions` | Manually add custom question |
| `PUT` | `/api/v1/questions/{id}` | Edit an existing question |
| `DELETE` | `/api/v1/questions/{id}` | Delete a question |
| `GET` | `/api/v1/documents/{id}/export` | Export questions (`?format=json` or `?format=csv`) |
