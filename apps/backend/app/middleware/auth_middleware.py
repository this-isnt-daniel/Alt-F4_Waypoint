"""
JWT auth middleware — creates/verifies tokens, provides FastAPI dependency.
Enforces session revocation and timing-safe hash comparison.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import hmac
import sqlite3

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from app.database import get_db

bearer_scheme = HTTPBearer()


# ── Password / PIN hashing (SHA-256 + salt — timing attack resistant) ───

def hash_pin(pin: str) -> str:
    """Hash a PIN with a random salt."""
    import secrets
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}:{pin}".encode()).hexdigest()
    return f"{salt}${h}"


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify a PIN against its hash using constant-time comparison."""
    if not hashed_pin or "$" not in hashed_pin:
        return False
    salt, expected_hash = hashed_pin.split("$", 1)
    h = hashlib.sha256(f"{salt}:{plain_pin}".encode()).hexdigest()
    return hmac.compare_digest(h, expected_hash)


# ── Token hashing (for DB storage — we store hash, not raw token) ────────

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ── JWT creation ─────────────────────────────────────────────────────────

import uuid

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── JWT verification ─────────────────────────────────────────────────────

def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependency ───────────────────────────────────────────────────

def get_current_driver(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    """
    FastAPI dependency — extracts and validates the JWT from Authorization header.
    Also verifies active driver status and checks that session has not been revoked (ADV-03).
    """
    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — use access token",
        )

    driver_id = payload.get("sub")
    if not driver_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing driver identity",
        )

    # Verify active driver account
    cur = db.cursor()
    cur.execute("SELECT active FROM drivers WHERE id = ?", (driver_id,))
    driver_row = cur.fetchone()
    if not driver_row or not driver_row["active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Driver account is inactive or not found",
        )

    # Verify session has not been revoked (Fix for ADV-03)
    token_hash = hash_token(credentials.credentials)
    cur.execute("SELECT revoked FROM driver_sessions WHERE access_token_hash = ?", (token_hash,))
    session_row = cur.fetchone()
    if session_row and session_row["revoked"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked",
        )

    return payload
