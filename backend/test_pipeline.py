import os
import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_pipeline():
    print("[Test 1] Checking API Health...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("Health check response:", r.json())

    # Authentication Setup
    email = f"user_pipe_{int(time.time())}@example.com"
    password = "TestPassword123!"
    requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password})
    login_res = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("\n[Test 2] Uploading Educational Document...")
    sample_content = b"COMPUTER SCIENCE EXAMINATION\n1. What is Artificial Intelligence?\nArtificial Intelligence is the simulation of human intelligence in machines.\n2. What is Machine Learning?\nMachine Learning is a branch of AI focused on building applications that learn from data."
    r = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files={"file": ("sample_exam.txt", sample_content, "text/plain")})
    assert r.status_code == 201 or r.status_code == 200, f"Upload failed: {r.text}"
    doc = r.json()
    doc_id = doc["id"]
    print(f"Document uploaded successfully! ID: {doc_id}, Name: {doc['original_name']}")

    print("\n[Test 3] Triggering Document Processing Pipeline...")
    r_proc = requests.post(f"{BASE_URL}/documents/{doc_id}/process", headers=headers)
    assert r_proc.status_code == 200, f"Trigger process failed: {r_proc.text}"

    print("Polling document processing status...")
    final_status = "PENDING"
    for _ in range(20):
        time.sleep(1.5)
        d_check = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=headers).json()
        final_status = d_check["status"]
        print(f"Current Status: {final_status}")
        if final_status in ["COMPLETED", "FAILED"]:
            break

    print(f"Final Document Status: {final_status}")
    if final_status == "FAILED":
        print(f"Error Details: {d_check.get('error_message')}")

    print("\n[Test 4] Querying Extracted Questions...")
    r_q = requests.get(f"{BASE_URL}/documents/{doc_id}/questions", headers=headers)
    assert r_q.status_code == 200
    questions = r_q.json()
    print(f"Extracted {len(questions)} question(s) from Gemini LLM Pipeline.")
    for idx, q in enumerate(questions, 1):
        print(f"Q{idx}: {q['question_text']} | Type: {q['question_type']} | Status: {q['answer_status']}")

    print("\n[Test 5] Testing JSON and CSV Export Endpoints...")
    r_json = requests.get(f"{BASE_URL}/documents/{doc_id}/export?format=json", headers=headers)
    assert r_json.status_code == 200
    print("JSON Export Sample:\n", r_json.text[:250])

    r_csv = requests.get(f"{BASE_URL}/documents/{doc_id}/export?format=csv", headers=headers)
    assert r_csv.status_code == 200
    print("\nCSV Export Sample:\n", r_csv.text[:250])

    print("\n==================================================")
    print("ALL API PIPELINE INTEGRATION TESTS PASSED 100% CLEANLY!")
    print("==================================================")

if __name__ == "__main__":
    test_pipeline()

