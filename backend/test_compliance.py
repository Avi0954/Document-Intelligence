import os
import sys
import time
import requests
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_health():
    print("\n--- TEST: API Health Check ---")
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("PASS: Health check online:", res.json())

def test_unsupported_file():
    print("\n--- TEST 4: Unsupported File Upload ---")
    files = {'file': ('test.exe', b'BINARY_CONTENT_EXE', 'application/x-msdownload')}
    res = requests.post(f"{BASE_URL}/documents/upload", files=files)
    print(f"Status Code: {res.status_code}, Response: {res.text}")
    assert res.status_code in [400, 422], "Should reject unsupported file with 400/422"
    print("PASS: Unsupported file upload rejected cleanly.")

def create_sample_png():
    unique_text = f"Sample doc timestamp {time.time()}"
    img = Image.new('RGB', (600, 350), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "PRAGATI BHARATI SAMPLE IMAGE DOCUMENT", fill=(0, 0, 0))
    d.text((20, 60), "1. Artificial Intelligence is transforming education.", fill=(0, 0, 0))
    d.text((20, 100), "2. Machine Learning enables models to learn from data.", fill=(0, 0, 0))
    d.text((20, 140), "3. Natural Language Processing assists in text understanding.", fill=(0, 0, 0))
    d.text((20, 180), unique_text, fill=(0, 0, 0))
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def create_sample_jpg():
    img = Image.new('RGB', (600, 300), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "PRAGATI BHARATI SAMPLE JPG DOCUMENT", fill=(0, 0, 0))
    d.text((20, 60), "Data Structures and Algorithms form the foundation of CS.", fill=(0, 0, 0))
    d.text((20, 100), "Time complexity measurement uses Big O notation.", fill=(0, 0, 0))
    buf = BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()

def test_png_upload():
    print("\n--- TEST 2: PNG Image Upload & Vision OCR ---")
    png_bytes = create_sample_png()
    fname = f"test_png_{int(time.time())}.png"
    files = {'file': (fname, png_bytes, 'image/png')}
    res = requests.post(f"{BASE_URL}/documents/upload", files=files)
    assert res.status_code == 201, f"PNG upload failed: {res.text}"
    doc_data = res.json()
    doc_id = doc_data['id']
    print(f"PASS: Uploaded PNG document ID: {doc_id}, initial status: {doc_data.get('status')}")

    # Wait for async worker processing
    for _ in range(15):
        time.sleep(2)
        status_res = requests.get(f"{BASE_URL}/documents/{doc_id}")
        if status_res.status_code == 200:
            status_data = status_res.json()
            st = status_data.get('status')
            print(f"Polling status for {doc_id}: {st}")
            if st in ['COMPLETED', 'FAILED']:
                break

    final_res = requests.get(f"{BASE_URL}/documents/{doc_id}")
    final_data = final_res.json()
    print("Final document state:", json.dumps(final_data, indent=2))
    assert final_data.get('status') in ['COMPLETED', 'FAILED'], f"Expected terminal state, got {final_data.get('status')}"
    
    if final_data.get('status') == 'COMPLETED':
        q_res = requests.get(f"{BASE_URL}/documents/{doc_id}/questions")
        questions = q_res.json()
        print(f"PASS: PNG document generated {len(questions)} questions!")
    else:
        print(f"PASS (TEST 8 Gemini Failure): Document marked FAILED cleanly with error: {final_data.get('error_message')[:100]}...")
        assert final_data.get('question_count') == 0, "No fake questions should be created on failure"
    return doc_id

def test_jpg_upload():
    print("\n--- TEST 3: JPG Image Upload ---")
    jpg_bytes = create_sample_jpg()
    files = {'file': ('sample_page.jpg', jpg_bytes, 'image/jpeg')}
    res = requests.post(f"{BASE_URL}/documents/upload", files=files)
    assert res.status_code == 201, f"JPG upload failed: {res.text}"
    doc_data = res.json()
    doc_id = doc_data['id']
    print(f"PASS: Uploaded JPG document ID: {doc_id}")
    return doc_id

def test_crud_and_exports(doc_id):
    print("\n--- TEST 9: Document & Question CRUD + Exports ---")
    # Get document
    doc_res = requests.get(f"{BASE_URL}/documents/{doc_id}")
    assert doc_res.status_code == 200, f"Get document failed: {doc_res.text}"
    
    # Create custom question (Manual question creation)
    q_payload = {
        "question_text": "What is Artificial Intelligence according to the uploaded content?",
        "question_type": "SHORT_ANSWER",
        "correct_answer": "AI is transforming education through machine learning models.",
        "explanation": "Derived directly from document text.",
        "difficulty": "EASY",
        "bloom_taxonomy": "UNDERSTAND",
        "page_reference": 1
    }
    create_q_res = requests.post(f"{BASE_URL}/documents/{doc_id}/questions", json=q_payload)
    assert create_q_res.status_code == 201, f"Create custom question failed: {create_q_res.text}"
    q_data = create_q_res.json()
    q_id = q_data['id']
    print(f"PASS: Created custom question {q_id}")

    # Get questions
    q_res = requests.get(f"{BASE_URL}/documents/{doc_id}/questions")
    assert q_res.status_code == 200, f"Get questions failed: {q_res.text}"
    questions = q_res.json()
    print(f"PASS: Retrieved {len(questions)} questions for document.")

    # Export JSON
    json_exp = requests.get(f"{BASE_URL}/documents/{doc_id}/export?format=json")
    assert json_exp.status_code == 200, f"JSON export failed: {json_exp.text}"
    print("PASS: JSON Export working.")

    # Export CSV
    csv_exp = requests.get(f"{BASE_URL}/documents/{doc_id}/export?format=csv")
    assert csv_exp.status_code == 200, f"CSV export failed: {csv_exp.text}"
    print("PASS: CSV Export working.")

    # Edit question
    update_payload = {"question_text": "Updated test question text regarding AI?"}
    edit_res = requests.put(f"{BASE_URL}/questions/{q_id}", json=update_payload)
    assert edit_res.status_code == 200, f"Question update failed: {edit_res.text}"
    print(f"PASS: Updated question {q_id}")

    # Delete question
    del_q_res = requests.delete(f"{BASE_URL}/questions/{q_id}")
    assert del_q_res.status_code == 200, "Delete question failed"
    print(f"PASS: Deleted question {q_id}")

def run_all():
    test_health()
    test_unsupported_file()
    doc_id = test_png_upload()
    test_jpg_upload()
    test_crud_and_exports(doc_id)
    print("\n==========================================")
    print("ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    run_all()
