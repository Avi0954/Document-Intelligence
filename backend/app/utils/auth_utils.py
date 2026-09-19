import os
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from app.config import settings

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

def _get_jwt_secret() -> str:
    secret = os.environ.get("SECRET_KEY") or settings.SECRET_KEY or "dev_secret_key_change_in_production"
    return secret.strip()

def hash_password(password: str) -> str:
    """Hash a password using salted PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    derived_key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    return f"pbkdf2_sha256${salt}${derived_key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored PBKDF2 hash string."""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3 or parts[0] != 'pbkdf2_sha256':
            return False
        salt = parts[1]
        stored_hash = parts[2]
        pwd_bytes = plain_password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        derived_key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
        return hmac.compare_digest(derived_key.hex(), stored_hash)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generate a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    secret_key = _get_jwt_secret()
    token = jwt.encode(to_encode, secret_key, algorithm=JWT_ALGORITHM)
    return token

def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises ValueError on invalid/expired token."""
    secret_key = _get_jwt_secret()
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid authentication token.")
