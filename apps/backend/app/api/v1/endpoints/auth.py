"""Module A -- Driver Auth endpoints."""

import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3

from app.database import get_db
from app.models.schemas import LoginRequest, TokenResponse, RefreshRequest, DriverProfile
from app.middleware.auth_middleware import (
    hash_pin, verify_pin, hash_token, create_access_token, create_refresh_token,
    decode_token, get_current_driver, bearer_scheme
)
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM drivers WHERE id = ?", (request.driver_id,))
    driver = cursor.fetchone()

    if not driver:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid driver_id or PIN")

    if not driver["active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Driver account is inactive")

    if not verify_pin(request.pin, driver["pin_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid driver_id or PIN")

    token_payload = {"sub": request.driver_id, "device_id": request.device_id}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    now_iso = datetime.now(timezone.utc).isoformat()
    session_id = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO driver_sessions (
            id, driver_id, device_id, access_token_hash,
            refresh_token_hash, expires_at, created_at, revoked
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id, request.driver_id, request.device_id,
        hash_token(access_token), hash_token(refresh_token),
        now_iso, now_iso, 0
    ))
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        driver_id=request.driver_id,
        driver_name=driver["name"],
    )


@router.get("/me", response_model=DriverProfile)
def me(payload: dict = Depends(get_current_driver), db: sqlite3.Connection = Depends(get_db)):
    driver_id = payload.get("sub")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
    driver = cursor.fetchone()

    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    return DriverProfile(
        driver_id=driver["id"],
        name=driver["name"],
        home_depot=driver["home_depot"],
        phone_masked=driver["phone_masked"],
        active=bool(driver["active"]),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: sqlite3.Connection = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    driver_id = payload.get("sub")
    device_id = payload.get("device_id")

    # Look up driver name for response
    cursor = db.cursor()
    cursor.execute("SELECT name FROM drivers WHERE id = ?", (driver_id,))
    driver = cursor.fetchone()
    driver_name = driver["name"] if driver else ""

    new_access_payload = {"sub": driver_id, "device_id": device_id}
    new_access_token = create_access_token(new_access_payload)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=request.refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        driver_id=driver_id,
        driver_name=driver_name,
    )


@router.post("/logout")
def logout(
    payload: dict = Depends(get_current_driver),
    token=Depends(bearer_scheme),
    db: sqlite3.Connection = Depends(get_db),
):
    credentials = token.credentials if hasattr(token, "credentials") else str(token)
    token_hash = hash_token(credentials)

    cursor = db.cursor()
    cursor.execute("UPDATE driver_sessions SET revoked = 1 WHERE access_token_hash = ?", (token_hash,))
    db.commit()

    return {"message": "Logged out successfully"}
