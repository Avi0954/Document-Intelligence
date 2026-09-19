import os
import sys
import time
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

USER_A_EMAIL = f"usera_{int(time.time())}@example.com"
USER_A_PASS = "Password123!"

USER_B_EMAIL = f"userb_{int(time.time())}@example.com"
USER_B_PASS = "Password456!"

def run_auth_suite():
    print("\n==================================================")
    print("STARTING SECURITY & AUTHENTICATION COMPLIANCE SUITE")
    print("==================================================")

    # TEST 1 — Register User A
    print("\n--- TEST 1: Register User A ---")
    reg_payload = {"email": USER_A_EMAIL, "password": USER_A_PASS}
    res_reg_a = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
    assert res_reg_a.status_code == 201, f"User A registration failed: {res_reg_a.text}"
    user_a_data = res_reg_a.json()
    user_a_id = user_a_data["id"]
    print(f"PASS: User A registered successfully. ID: {user_a_id}, Email: {user_a_data['email']}")
    assert "password" not in user_a_data and "password_hash" not in user_a_data, "Password hash must not be returned!"

    # TEST 2 — Login User A
    print("\n--- TEST 2: Login User A & JWT Access Token ---")
    login_payload = {"email": USER_A_EMAIL, "password": USER_A_PASS}
    res_login_a = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    assert res_login_a.status_code == 200, f"User A login failed: {res_login_a.text}"
    token_a = res_login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print("PASS: User A logged in successfully. JWT token received.")

    # TEST 11 — Invalid Token / Unauthenticated request
    print("\n--- TEST 11: Call Protected Endpoint without Token ---")
    res_unauth = requests.get(f"{BASE_URL}/documents")
    assert res_unauth.status_code == 401, f"Expected 401 Unauthorized, got {res_unauth.status_code}"
    print("PASS: Unauthenticated request returned 401 Unauthorized.")

    # TEST 12 — Invalid Password
    print("\n--- TEST 12: Login with Invalid Password ---")
    bad_login = requests.post(f"{BASE_URL}/auth/login", json={"email": USER_A_EMAIL, "password": "WrongPassword"})
    assert bad_login.status_code == 401, f"Expected 401 Unauthorized, got {bad_login.status_code}"
    print("PASS: Invalid password login rejected with 401 Unauthorized.")

    # TEST 3 — Upload document as User A
    print("\n--- TEST 3: Upload Document as User A ---")
    files_a = {'file': ('doc_user_a.txt', b'Content belonging exclusively to User A.', 'text/plain')}
    res_up_a = requests.post(f"{BASE_URL}/documents/upload", headers=headers_a, files=files_a)
    assert res_up_a.status_code == 201, f"User A upload failed: {res_up_a.text}"
    doc_a_data = res_up_a.json()
    doc_a_id = doc_a_data['id']
    print(f"PASS: User A uploaded document ID: {doc_a_id}")

    # TEST 4 — List documents as User A
    print("\n--- TEST 4: List Documents as User A ---")
    res_list_a = requests.get(f"{BASE_URL}/documents", headers=headers_a)
    assert res_list_a.status_code == 200, f"User A document list failed: {res_list_a.text}"
    docs_a = res_list_a.json()
    assert any(d['id'] == doc_a_id for d in docs_a), "User A's document must appear in User A's list"
    print(f"PASS: User A retrieved {len(docs_a)} documents including {doc_a_id}.")

    # TEST 5 — Register User B & Login User B
    print("\n--- TEST 5: Register & Login User B (Isolation Check) ---")
    res_reg_b = requests.post(f"{BASE_URL}/auth/register", json={"email": USER_B_EMAIL, "password": USER_B_PASS})
    assert res_reg_b.status_code == 201, f"User B registration failed: {res_reg_b.text}"
    
    res_login_b = requests.post(f"{BASE_URL}/auth/login", json={"email": USER_B_EMAIL, "password": USER_B_PASS})
    assert res_login_b.status_code == 200, "User B login failed"
    token_b = res_login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    res_list_b = requests.get(f"{BASE_URL}/documents", headers=headers_b)
    docs_b = res_list_b.json()
    assert not any(d['id'] == doc_a_id for d in docs_b), "User B must NOT see User A's documents!"
    print("PASS: User B document list is strictly isolated (User A's document is invisible).")

    # TEST 6 — Direct document access as User B for User A's document ID
    print("\n--- TEST 6: Direct Access User A Document ID as User B ---")
    res_access_b = requests.get(f"{BASE_URL}/documents/{doc_a_id}", headers=headers_b)
    assert res_access_b.status_code == 404, f"Expected 404 Not Found, got {res_access_b.status_code}"
    print("PASS: Requesting User A's document ID as User B returns 404 Not Found.")

    # TEST 8 — Chunks access as User B
    print("\n--- TEST 8: Access User A Chunks as User B ---")
    res_chunks_b = requests.get(f"{BASE_URL}/documents/{doc_a_id}/chunks", headers=headers_b)
    assert res_chunks_b.status_code == 404, f"Expected 404 Not Found, got {res_chunks_b.status_code}"
    print("PASS: Accessing User A's chunks as User B returns 404 Not Found.")

    # TEST 10 — Processing as User B for User A's document
    print("\n--- TEST 10: Trigger Processing on User A Document as User B ---")
    res_proc_b = requests.post(f"{BASE_URL}/documents/{doc_a_id}/process", headers=headers_b)
    assert res_proc_b.status_code == 404, f"Expected 404 Not Found, got {res_proc_b.status_code}"
    print("PASS: Attempting to process User A's document as User B returns 404 Not Found.")

    # Create a question on User A's document for Question Ownership testing
    q_payload = {
        "question_text": "What is the secret text in User A's document?",
        "question_type": "SHORT_ANSWER",
        "correct_answer": "Content belonging exclusively to User A.",
        "explanation": "Extracted text",
        "difficulty": "EASY",
        "bloom_taxonomy": "REMEMBER",
        "page_reference": 1
    }
    res_add_q = requests.post(f"{BASE_URL}/documents/{doc_a_id}/questions", headers=headers_a, json=q_payload)
    assert res_add_q.status_code == 201, f"Failed creating User A question: {res_add_q.text}"
    q_a_id = res_add_q.json()["id"]
    print(f"Created question ID: {q_a_id} for User A.")

    # TEST 7 — Question ownership check as User B
    print("\n--- TEST 7: Attempt Access/Edit/Delete User A Question as User B ---")
    res_q_get_b = requests.get(f"{BASE_URL}/documents/{doc_a_id}/questions", headers=headers_b)
    assert res_q_get_b.status_code == 404, f"Expected 404 Not Found, got {res_q_get_b.status_code}"

    res_q_put_b = requests.put(f"{BASE_URL}/questions/{q_a_id}", headers=headers_b, json={"question_text": "Hacked question?"})
    assert res_q_put_b.status_code == 404, f"Expected 404 Not Found, got {res_q_put_b.status_code}"

    res_q_del_b = requests.delete(f"{BASE_URL}/questions/{q_a_id}", headers=headers_b)
    assert res_q_del_b.status_code == 404, f"Expected 404 Not Found, got {res_q_del_b.status_code}"
    print("PASS: All unauthorized question access/edit/delete attempts as User B returned 404 Not Found.")

    # TEST 9 — Export authorization as User B
    print("\n--- TEST 9: Export User A Document Questions as User B ---")
    res_exp_b = requests.get(f"{BASE_URL}/documents/{doc_a_id}/export?format=json", headers=headers_b)
    assert res_exp_b.status_code == 404, f"Expected 404 Not Found, got {res_exp_b.status_code}"
    print("PASS: Unauthorized export attempt returned 404 Not Found.")

    print("\n==================================================")
    print("ALL 12 AUTHENTICATION & OWNERSHIP TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_auth_suite()
