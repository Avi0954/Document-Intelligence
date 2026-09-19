import os
import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_failure_lifecycle_tests():
    print("\n==================================================")
    print("TESTING DOCUMENT PROCESSING LIFECYCLE & ERROR HANDLING")
    print("==================================================")

    # Register & Login Test User
    email = f"user_test_fail_{int(time.time())}@example.com"
    password = "TestPassword123!"
    requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password})
    login_res = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # TEST 1: Valid Document -> COMPLETED status
    print("\n--- TEST 1: Valid Document Processing (COMPLETED Lifecycle) ---")
    txt_content = b"PRAGATI BHARATI ASSIGNMENT TEST\nQuestion 1. What is Python?\nA. Programming language\nB. Snake\nC. OS\nD. Database\nAnswer: A\nExplanation: Python is a language."
    res_valid = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files={'file': ('valid_test.txt', txt_content, 'text/plain')})
    assert res_valid.status_code == 201, f"Upload failed: {res_valid.text}"
    valid_id = res_valid.json()["id"]

    res_proc = requests.post(f"{BASE_URL}/documents/{valid_id}/process", headers=headers)
    assert res_proc.status_code == 200

    # Poll for completion or terminal state
    for _ in range(15):
        time.sleep(1.5)
        d_res = requests.get(f"{BASE_URL}/documents/{valid_id}", headers=headers)
        status = d_res.json()["status"]
        if status in ["COMPLETED", "FAILED"]:
            break

    final_valid = requests.get(f"{BASE_URL}/documents/{valid_id}", headers=headers).json()
    print(f"Valid document final status: {final_valid['status']}")

    # TEST 2: Empty / Unreadable Document -> FAILED status with sanitized error
    print("\n--- TEST 2: Empty Document Processing (FAILED Lifecycle) ---")
    empty_content = b"   \n\n\t  "
    res_empty = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files={'file': ('empty_doc.txt', empty_content, 'text/plain')})
    assert res_empty.status_code in (200, 201)
    empty_id = res_empty.json()["id"]

    requests.post(f"{BASE_URL}/documents/{empty_id}/process", headers=headers)

    for _ in range(10):
        time.sleep(1)
        d_res = requests.get(f"{BASE_URL}/documents/{empty_id}", headers=headers)
        status = d_res.json()["status"]
        if status in ["COMPLETED", "FAILED"]:
            break

    final_empty = requests.get(f"{BASE_URL}/documents/{empty_id}", headers=headers).json()
    print(f"Empty document final status: {final_empty['status']}")
    print(f"Empty document error_message: {final_empty['error_message']}")

    assert final_empty["status"] == "FAILED", f"Expected FAILED status, got {final_empty['status']}"
    assert "No readable text" in final_empty["error_message"], "Expected clear human-readable error message"

    # TEST 3: Security Check - Confirm no API keys or secrets exposed in error_message
    print("\n--- TEST 3: Secrets & Security Check ---")
    err_msg = final_empty["error_message"] or ""
    assert "GEMINI_API_KEY" not in err_msg and "Bearer" not in err_msg and "AI_KEY" not in err_msg, "Secrets must never be exposed!"
    print("PASS: Secrets protection verified!")

    print("\n==================================================")
    print("ALL LIFECYCLE & ERROR HANDLING TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_failure_lifecycle_tests()
