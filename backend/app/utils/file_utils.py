import hashlib
import os
import shutil
from fastapi import UploadFile
from app.config import settings

ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "txt", "png", "jpg", "jpeg"}

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a local file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_and_save_upload(upload_file: UploadFile) -> tuple[str, str, str, int]:
    """Validate upload extension and save to local UPLOAD_DIR. Returns (file_path, file_type, file_hash, file_size)."""
    filename = upload_file.filename or "file.txt"
    ext = os.path.splitext(filename)[1].lower().replace(".", "")

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '.{ext}'. Allowed formats: PDF, DOCX, PPTX, TXT, PNG, JPG, JPEG."
        )

    # Save to temporary location inside UPLOAD_DIR to compute hash and size
    temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{upload_file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    file_size = os.path.getsize(temp_path)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        os.remove(temp_path)
        raise ValueError(f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    file_hash = calculate_file_hash(temp_path)
    
    # Store with hash as filename to prevent duplicates / collision
    final_filename = f"{file_hash[:16]}_{filename}"
    final_path = os.path.join(settings.UPLOAD_DIR, final_filename)

    if os.path.exists(temp_path):
        if os.path.exists(final_path):
            os.remove(temp_path)
        else:
            os.rename(temp_path, final_path)

    return final_path, ext, file_hash, file_size
