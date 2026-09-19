import os
import sys
import time
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

USER_A_EMAIL = f"user_assoc_a_{int(time.time())}@example.com"
USER_A_PASS = "Password123!"

USER_B_EMAIL = f"user_assoc_b_{int(time.time())}@example.com"
USER_B_PASS = "Password456!"

def run_association_suite():
    print("\n==================================================")
    print("STARTING RELATED DOCUMENT ASSOCIATION TEST SUITE")
    print("==================================================")

    # Register & Login User A
    requests.post(f"{BASE_URL}/auth/register", json={"email": USER_A_EMAIL, "password": USER_A_PASS})
    login_a = requests.post(f"{BASE_URL}/auth/login", json={"email": USER_A_EMAIL, "password": USER_A_PASS})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register & Login User B
    requests.post(f"{BASE_URL}/auth/register", json={"email": USER_B_EMAIL, "password": USER_B_PASS})
    login_b = requests.post(f"{BASE_URL}/auth/login", json={"email": USER_B_EMAIL, "password": USER_B_PASS})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # TEST 1 — Upload Question Paper and Answer Key as User A
    print("\n--- TEST 1: Multiple Document Upload (Question Paper & Answer Key) ---")
    qp_bytes = b"EXAMINATION QUESTION PAPER\n1. What is Machine Learning?\n2. What is Natural Language Processing?"
    ak_bytes = b"OFFICIAL ANSWER KEY\n1. Machine Learning is a subset of AI enabling systems to learn from data.\n2. Natural Language Processing enables computers to understand human language."
    
    res_qp = requests.post(f"{BASE_URL}/documents/upload", headers=headers_a, files={'file': ('qp_test.txt', qp_bytes, 'text/plain')})
    assert res_qp.status_code == 201, f"QP Upload failed: {res_qp.text}"
    qp_doc = res_qp.json()
    qp_id = qp_doc["id"]

    res_ak = requests.post(f"{BASE_URL}/documents/upload", headers=headers_a, files={'file': ('ak_test.txt', ak_bytes, 'text/plain')})
    assert res_ak.status_code == 201, f"AK Upload failed: {res_ak.text}"
    ak_doc = res_ak.json()
    ak_id = ak_doc["id"]

    print(f"PASS: Uploaded QP ID: {qp_id} (Role: {qp_doc['document_role']}), AK ID: {ak_id} (Role: {ak_doc['document_role']})")

    # TEST 8 — Self-Association Error
    print("\n--- TEST 8: Self-Association Error Check ---")
    res_self = requests.put(f"{BASE_URL}/documents/{qp_id}/associate", headers=headers_a, json={"related_document_id": qp_id, "relationship_type": "ANSWER_KEY"})
    assert res_self.status_code == 400, f"Expected 400 Bad Request for self-association, got {res_self.status_code}"
    print("PASS: Self-association rejected with HTTP 400 Bad Request.")

    # TEST 7 — Cross-User Unauthorized Association
    print("\n--- TEST 7: Cross-User Unauthorized Association ---")
    res_cross = requests.put(f"{BASE_URL}/documents/{qp_id}/associate", headers=headers_b, json={"related_document_id": ak_id, "relationship_type": "ANSWER_KEY"})
    assert res_cross.status_code == 404, f"Expected 404 Not Found for cross-user association, got {res_cross.status_code}"
    print("PASS: Cross-user association attempt returned HTTP 404 Not Found.")

    # TEST 2 & 3 — Assign Roles & Associate Answer Key
    print("\n--- TEST 2 & 3: Associate Answer Key with Question Paper ---")
    res_assoc = requests.put(f"{BASE_URL}/documents/{qp_id}/associate", headers=headers_a, json={"related_document_id": ak_id, "relationship_type": "ANSWER_KEY"})
    assert res_assoc.status_code == 200, f"Association failed: {res_assoc.text}"
    updated_qp = res_assoc.json()
    assert updated_qp["related_document_id"] == ak_id, "related_document_id must match AK ID"
    assert updated_qp["document_role"] == "QUESTION_PAPER", "Role must be QUESTION_PAPER"
    
    # Check Answer Key document role
    res_ak_check = requests.get(f"{BASE_URL}/documents/{ak_id}", headers=headers_a)
    assert res_ak_check.json()["document_role"] == "ANSWER_KEY", "AK role must be ANSWER_KEY"
    print("PASS: Associated Answer Key with Question Paper successfully. Roles updated!")

    # TEST 4 — Process Question Paper with Answer Key Attached
    print("\n--- TEST 4: Process Combined Question Paper + Answer Key ---")
    res_proc = requests.post(f"{BASE_URL}/documents/{qp_id}/process", headers=headers_a)
    assert res_proc.status_code == 200, f"Process trigger failed: {res_proc.text}"
    
    # Wait for async worker processing
    for _ in range(15):
        time.sleep(2)
        st_res = requests.get(f"{BASE_URL}/documents/{qp_id}", headers=headers_a)
        if st_res.status_code == 200:
            st = st_res.json()["status"]
            print(f"Polling QP status: {st}")
            if st in ["COMPLETED", "FAILED"]:
                break

    qp_final = requests.get(f"{BASE_URL}/documents/{qp_id}", headers=headers_a).json()
    print("Final QP Document state:", json.dumps(qp_final, indent=2))
    assert qp_final["status"] in ["COMPLETED", "FAILED"], "QP must reach terminal status"
    print("PASS: Combined processing completed terminal state.")

    # TEST 9 — Safe Delete Answer Key
    print("\n--- TEST 9: Delete Associated Answer Key Safely ---")
    res_del_ak = requests.delete(f"{BASE_URL}/documents/{ak_id}", headers=headers_a)
    assert res_del_ak.status_code == 200, f"AK Delete failed: {res_del_ak.text}"
    
    # Verify QP relationship cleared
    qp_after_del = requests.get(f"{BASE_URL}/documents/{qp_id}", headers=headers_a).json()
    assert qp_after_del["related_document_id"] is None, "related_document_id should be cleared to None"
    assert qp_after_del["document_role"] == "PRIMARY", "Role should reset to PRIMARY"
    print("PASS: Deleting Answer Key safely cleared Question Paper association without deleting Question Paper!")

    print("\n==================================================")
    print("ALL RELATED DOCUMENT ASSOCIATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_association_suite()
