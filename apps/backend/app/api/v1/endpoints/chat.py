"""Module G -- Chat / call intent API for driver."""

import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from typing import List

from app.database import get_db
from app.middleware.auth_middleware import get_current_driver
from app.models.schemas import (
    MessageDTO, SendMessageRequest, SendMessageResponse,
    CallIntentRequest, CallIntentResponse
)

router = APIRouter()


@router.get("/stops/{stop_id}/messages", response_model=List[MessageDTO])
def get_messages(
    stop_id: str,
    driver: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    driver_id = driver["sub"]
    cur.execute("""
        SELECT s.id
        FROM stops s
        JOIN trips t ON s.trip_id = t.id
        WHERE s.id = ? AND t.driver_id = ?
    """, (stop_id, driver_id))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Stop not found or not assigned to driver")

    cur.execute("""
        SELECT id, stop_id, sender_role, sender_id, body, client_event_id, quick_reply, created_at
        FROM messages
        WHERE stop_id = ?
        ORDER BY created_at ASC
    """, (stop_id,))

    rows = cur.fetchall()
    messages = []
    for r in rows:
        messages.append(MessageDTO(
            id=r["id"],
            stop_id=r["stop_id"],
            sender_role=r["sender_role"],
            sender_id=r["sender_id"],
            body=r["body"],
            quick_reply=bool(r["quick_reply"]),
            created_at=r["created_at"],
        ))
    return messages


@router.post("/stops/{stop_id}/messages", response_model=SendMessageResponse)
def send_message(
    stop_id: str,
    request: SendMessageRequest,
    driver: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("""
        SELECT s.id
        FROM stops s
        JOIN trips t ON s.trip_id = t.id
        WHERE s.id = ? AND t.driver_id = ?
    """, (stop_id, driver_id))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Stop not found or not assigned to driver")

    cur.execute("SELECT id FROM messages WHERE client_event_id = ?", (request.client_event_id,))
    existing = cur.fetchone()
    if existing:
        return SendMessageResponse(status="already_applied", message_id=existing["id"])

    msg_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    cur.execute("""
        INSERT INTO messages (id, stop_id, sender_role, sender_id, body, client_event_id, quick_reply, created_at)
        VALUES (?, ?, 'driver', ?, ?, ?, ?, ?)
    """, (msg_id, stop_id, driver_id, request.body, request.client_event_id, 1 if request.quick_reply else 0, now_iso))

    db.commit()
    return SendMessageResponse(status="sent", message_id=msg_id)


@router.post("/stops/{stop_id}/call-intent", response_model=CallIntentResponse)
def call_intent(
    stop_id: str,
    request: CallIntentRequest = CallIntentRequest(stop_id=""),
    driver: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("""
        SELECT s.id, s.manager_phone_masked
        FROM stops s
        JOIN trips t ON s.trip_id = t.id
        WHERE s.id = ? AND t.driver_id = ?
    """, (stop_id, driver_id))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Stop not found or not assigned to driver")

    masked_num = row["manager_phone_masked"] if row and row["manager_phone_masked"] else "+94 11 700 0042"
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    now_iso = datetime.now(timezone.utc).isoformat()
    session_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO call_sessions (id, stop_id, requested_by, masked_dial_number, expires_at, created_at)
        VALUES (?, ?, 'driver', ?, ?, ?)
    """, (session_id, stop_id, masked_num, expires_at, now_iso))

    db.commit()
    return CallIntentResponse(masked_dial_number=masked_num, expires_at=expires_at)
