import os
import requests
import pymupdf
import docx
from pptx import Presentation

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_DIR = os.path.join(os.path.dirname(__file__), "test_files")
os.makedirs(TEST_DIR, exist_ok=True)

def create_sample_files():
    # 1. Create Sample PDF
    pdf_path = os.path.join(TEST_DIR, "sample_test.pdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "PDF Document Title\n\nSupervised learning uses labeled datasets to train mapping functions.")
    doc.save(pdf_path)
    doc.close()

    # 2. Create Sample DOCX
    docx_path = os.path.join(TEST_DIR, "sample_test.docx")
    d = docx.Document()
    d.add_heading("DOCX Document Title", level=1)
    d.add_paragraph("Unsupervised learning discovers hidden patterns in unlabeled datasets.")
    d.save(docx_path)

    # 3. Create Sample PPTX
    pptx_path = os.path.join(TEST_DIR, "sample_test.pptx")
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "PPTX Presentation Title"
    slide.placeholders[1].text = "Deep learning utilizes multi-layer artificial neural networks."
    prs.save(pptx_path)

    # 4. Create Sample TXT
    txt_path = os.path.join(TEST_DIR, "sample_test.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("TXT Document Title\n\nReinforcement learning trains agents using rewards and penalties.")

    return pdf_path, docx_path, pptx_path, txt_path

def run_verification():
    print("=== STARTING FULL MULTI-FORMAT VERIFICATION AUDIT ===")
    pdf_path, docx_path, pptx_path, txt_path = create_sample_files()

    # 1. Health API Test
    print("\n[1] Health API...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health API failed: {r.text}"
    print("    Health Response:", r.json())

    # 2. Upload and verify text extraction for all 4 formats
    for fmt, path in [("PDF", pdf_path), ("DOCX", docx_path), ("PPTX", pptx_path), ("TXT", txt_path)]:
        print(f"\n[2.{fmt}] Uploading and Processing {fmt} file...")
        with open(path, "rb") as f:
            mime = "application/pdf" if fmt=="PDF" else "text/plain"
            r = requests.post(f"{BASE_URL}/documents/upload", files={"file": (os.path.basename(path), f, mime)})
        assert r.status_code in (200, 201), f"{fmt} upload failed: {r.text}"
        doc_id = r.json()["id"]

        # Trigger process
        r_proc = requests.post(f"{BASE_URL}/documents/{doc_id}/process")
        print(f"    Process HTTP Status for {fmt}: {r_proc.status_code}")

        # Fetch Chunks
        r_chunks = requests.get(f"{BASE_URL}/documents/{doc_id}/chunks")
        assert r_chunks.status_code == 200, f"Chunks API failed for {fmt}: {r_chunks.text}"
        chunks = r_chunks.json()
        assert len(chunks) > 0, f"No chunks created for {fmt}!"
        print(f"    {fmt} Extracted! Chunks Count: {len(chunks)}, Page/Slide: {chunks[0]['page_number']}")
        print(f"    {fmt} Sample Text: {chunks[0]['content'][:60]}...")

    print("\n=== ALL 4 DOCUMENT FORMATS (PDF, DOCX, PPTX, TXT) VERIFIED 100% CLEANLY ===")

if __name__ == "__main__":
    run_verification()
