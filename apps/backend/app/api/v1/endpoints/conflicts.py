"""Conflict management API for driver portal."""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from typing import List

from app.database import get_db
from app.middleware.auth_middleware import get_current_driver
from app.models.schemas import ConflictDTO, ForwardConflictRequest, ForwardConflictResponse

router = APIRouter()


@router.get("", response_model=List[ConflictDTO])
@router.get("/", response_model=List[ConflictDTO])
def get_conflicts(
    driver: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("""
        SELECT c.id, c.stop_id, c.driver_record_json, c.system_record_json,
               c.status, c.created_at, c.forwarded_at, c.resolved_at
        FROM conflicts c
        LEFT JOIN stops s ON c.stop_id = s.id
        LEFT JOIN trips t ON s.trip_id = t.id
        WHERE t.driver_id = ? OR t.driver_id IS NULL
        ORDER BY c.created_at DESC
    """, (driver_id,))

    rows = cur.fetchall()
    conflicts = []
    for r in rows:
        conflicts.append(ConflictDTO(
            id=r["id"],
            stop_id=r["stop_id"],
            driver_record=json.loads(r["driver_record_json"]) if r["driver_record_json"] else None,
            system_record=json.loads(r["system_record_json"]) if r["system_record_json"] else None,
            status=r["status"],
            created_at=r["created_at"],
            forwarded_at=r["forwarded_at"],
            resolved_at=r["resolved_at"],
        ))
    return conflicts


@router.post("/{conflict_id}/forward", response_model=ForwardConflictResponse)
def forward_conflict(
    conflict_id: str,
    request: ForwardConflictRequest = ForwardConflictRequest(),
    driver: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("SELECT id, status FROM conflicts WHERE id = ?", (conflict_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Conflict not found")

    if row["status"] != "in_review":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot forward conflict with status '{row['status']}' — already processed or resolved"
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    note = request.note if request else None

    cur.execute("""
        UPDATE conflicts
        SET status = 'forwarded', forwarded_at = ?, resolution_note = ?
        WHERE id = ? AND status = 'in_review'
    """, (now_iso, note, conflict_id))

    # Audit log
    cur.execute("""
        INSERT INTO audit_log (id, actor_role, actor_id, action, entity_type, entity_id, detail)
        VALUES (?, 'driver', ?, 'conflict_forwarded', 'conflict', ?, ?)
    """, (f"AUD-{conflict_id[:8]}", driver_id, conflict_id, note or "Forwarded by driver"))

    db.commit()

    return ForwardConflictResponse(
        status="forwarded",
        conflict_id=conflict_id,
        forwarded_at=now_iso,
    )
