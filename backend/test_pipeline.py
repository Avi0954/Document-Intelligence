import os
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "uploads", "sample_educational_material.txt")

def test_pipeline():
    print("[Test 1] Checking API Health...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("Health check response:", r.json())

    print("\n[Test 2] Uploading Document...")
    with open(TEST_FILE_PATH, "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("sample_educational_material.txt", f, "text/plain")})
    assert r.status_code == 201 or r.status_code == 200, f"Upload failed: {r.text}"
    doc = r.json()
    doc_id = doc["id"]
    print(f"Document uploaded successfully! ID: {doc_id}, Name: {doc['original_name']}")

    print("\n[Test 3] Manually Adding Custom Question...")
    q_payload = {
        "question_text": "What is the primary difference between Supervised and Unsupervised Learning?",
        "question_type": "SHORT_ANSWER",
        "options": None,
        "correct_answer": "Supervised learning uses labeled datasets whereas Unsupervised learning trains on unlabeled data to find hidden patterns.",
        "explanation": "Supervised algorithms learn an explicit mapping function, while unsupervised methods cluster or reduce dimensionality of unlabeled data.",
        "difficulty": "MEDIUM",
        "bloom_taxonomy": "UNDERSTAND",
        "page_reference": 1
    }
    r_q = requests.post(f"{BASE_URL}/documents/{doc_id}/questions", json=q_payload)
    assert r_q.status_code == 201, f"Failed to add question: {r_q.text}"
    new_q = r_q.json()
    print("Created question successfully! ID:", new_q["id"])

    print("\n[Test 4] Querying Questions with Filter...")
    r = requests.get(f"{BASE_URL}/documents/{doc_id}/questions?difficulty=MEDIUM")
    assert r.status_code == 200
    questions = r.json()
    assert len(questions) > 0, "Expected filtered question"
    print(f"Retrieved {len(questions)} question(s) matching filter 'difficulty=MEDIUM'.")
    print("Question Statement:", questions[0]["question_text"])

    print("\n[Test 5] Testing JSON and CSV Export Endpoints...")
    r_json = requests.get(f"{BASE_URL}/documents/{doc_id}/export?format=json")
    assert r_json.status_code == 200
    assert "Supervised learning" in r_json.text
    print("JSON Export Sample:\n", r_json.text[:250])

    r_csv = requests.get(f"{BASE_URL}/documents/{doc_id}/export?format=csv")
    assert r_csv.status_code == 200
    assert "Supervised learning" in r_csv.text
    print("\nCSV Export Sample:\n", r_csv.text[:250])

    print("\n[ALL API PIPELINE INTEGRATION TESTS PASSED 100% CLEANLY!]")

if __name__ == "__main__":
    test_pipeline()
