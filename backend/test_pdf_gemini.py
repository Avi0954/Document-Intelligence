import os
import requests
import json
import pymupdf

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_PDF_PATH = os.path.join(os.path.dirname(__file__), "document_intelligence_test_sample.pdf")

def create_sample_ai_pdf():
    doc = pymupdf.open()
    page = doc.new_page()
    ai_pdf_text = """
    # Fundamentals of Artificial Intelligence and Machine Learning

    Artificial Intelligence (AI) refers to computer systems engineered to simulate human cognitive functions such as learning, reasoning, and problem-solving.

    Machine Learning (ML) is a foundational subset of AI that relies on statistical algorithms to learn patterns directly from training data rather than relying on explicit rule-based programming.

    Natural Language Processing (NLP) is a specialized branch of AI that enables machines to comprehend, interpret, process, and generate human text and language.

    Model Evaluation is a critical phase in the ML workflow. During evaluation, models are assessed on unseen test datasets using performance metrics like accuracy, precision, recall, and F1-score.

    Inference refers to the real-world execution phase where a trained AI model makes predictions on new, live incoming data.

    Responsible AI encompasses ethical guidelines, fairness, transparency, accountability, and privacy controls to ensure AI systems are deployed safely and without bias.
    """
    page.insert_text((50, 50), ai_pdf_text)
    doc.save(TEST_PDF_PATH)
    doc.close()
    return TEST_PDF_PATH

def test_pdf_gemini_extraction():
    print("=== STARTING GROUNDED PDF QUESTION EXTRACTION TEST ===")
    pdf_path = create_sample_ai_pdf()
    
    # 1. Health check
    print("\n[Step 1] Checking API Health...")
    r_health = requests.get(f"{BASE_URL}/health")
    assert r_health.status_code == 200, f"Health check failed: {r_health.text}"
    health_json = r_health.json()
    print("Health Status:", health_json)
    assert health_json["llm_configured"] == True, "Gemini API key is not configured!"

    # 2. Upload AI PDF
    print("\n[Step 2] Uploading Sample Educational AI PDF...")
    with open(pdf_path, "rb") as f:
        r_upload = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("document_intelligence_test_sample.pdf", f, "application/pdf")})
    assert r_upload.status_code in (200, 201), f"PDF Upload failed: {r_upload.text}"
    doc_data = r_upload.json()
    doc_id = doc_data["id"]
    print(f"PDF Uploaded! ID: {doc_id}, Format: {doc_data['file_type']}, Status: {doc_data['status']}")

    # 3. Process PDF with Gemini 3.6 Flash
    print("\n[Step 3] Running Text Extraction & Grounded Gemini Processing...")
    r_proc = requests.post(f"{BASE_URL}/documents/{doc_id}/process")
    assert r_proc.status_code == 200, f"Processing failed: {r_proc.text}"
    proc_data = r_proc.json()
    print(f"Processing Complete! Status: {proc_data['status']}, Chunks: {proc_data['chunk_count']}, Questions Generated: {proc_data['question_count']}")
    assert proc_data["status"] == "COMPLETED"

    # 4. Fetch Chunks
    print("\n[Step 4] Verifying PyMuPDF Text Chunks...")
    r_chunks = requests.get(f"{BASE_URL}/documents/{doc_id}/chunks")
    assert r_chunks.status_code == 200
    chunks = r_chunks.json()
    print(f"Retrieved {len(chunks)} page chunk(s). Content Sample:")
    print("--- CHUNK TEXT ---")
    print(chunks[0]['content'])
    print("------------------")

    # 5. Fetch Extracted Questions
    print("\n[Step 5] Verifying Grounded Questions (AI/ML/NLP/Responsible AI)...")
    r_q = requests.get(f"{BASE_URL}/documents/{doc_id}/questions")
    assert r_q.status_code == 200
    questions = r_q.json()
    print(f"Retrieved {len(questions)} grounded question(s):")
    print(json.dumps(questions, indent=2))

    # Verify Strict Grounding: NO quantum computing, Shor's algorithm, or qubits!
    forbidden_terms = ["quantum", "qubit", "shor", "grover", "classical computer"]
    for q in questions:
        q_full_str = (q["question_text"] + " " + q["correct_answer"] + " " + (q["explanation"] or "")).lower()
        for forbidden in forbidden_terms:
            assert forbidden not in q_full_str, f"Found un-grounded hallucinated concept '{forbidden}' in question: {q['question_text']}"

    print("\n=== GROUNDED PDF END-TO-END GEMINI 3.6 FLASH VERIFICATION PASSED 100% ===")

if __name__ == "__main__":
    test_pdf_gemini_extraction()
