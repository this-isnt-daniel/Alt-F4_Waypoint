"""Module F -- Dispatcher deltas / route changes API."""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
import sqlite3
from typing import Optional

from app.database import get_db
from app.middleware.auth_middleware import get_current_driver
from app.models.schemas import ChangesResponse, ChangeDTO, AckChangeResponse

router = APIRouter()


@router.get("/changes", response_model=ChangesResponse)
def get_changes(
    since: Optional[str] = Query(None),
    driver: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    if since:
        cur.execute("""
            SELECT rc.id, rc.trip_id, rc.change_type, rc.payload, rc.issued_at, rc.acknowledged, rc.ack_at
            FROM route_changes rc
            JOIN trips t ON rc.trip_id = t.id
            WHERE t.driver_id = ? AND rc.issued_at > ?
            ORDER BY rc.issued_at ASC
        """, (driver_id, since))
    else:
        cur.execute("""
            SELECT rc.id, rc.trip_id, rc.change_type, rc.payload, rc.issued_at, rc.acknowledged, rc.ack_at
            FROM route_changes rc
            JOIN trips t ON rc.trip_id = t.id
            WHERE t.driver_id = ?
            ORDER BY rc.issued_at ASC
        """, (driver_id,))

    rows = cur.fetchall()
    changes = []
    for r in rows:
        payload_data = json.loads(r["payload"]) if r["payload"] else {}
        changes.append(ChangeDTO(
            change_id=r["id"],
            type=r["change_type"],
            issued_at=r["issued_at"],
            trip_id=r["trip_id"],
            payload=payload_data,
            acknowledged=bool(r["acknowledged"]),
        ))

    next_cursor = datetime.now(timezone.utc).isoformat()
    return ChangesResponse(changes=changes, next_cursor=next_cursor)


@router.post("/changes/{change_id}/ack", response_model=AckChangeResponse)
def ack_change(
    change_id: str,
    driver: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("""
        SELECT rc.id, rc.trip_id, rc.change_type, rc.payload, t.driver_id
        FROM route_changes rc
        JOIN trips t ON rc.trip_id = t.id
        WHERE rc.id = ? AND t.driver_id = ?
    """, (change_id, driver_id))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Change not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute("UPDATE route_changes SET acknowledged = 1, ack_at = ? WHERE id = ?", (now_iso, change_id))

    # If this was a resequencing change, apply sequence update to remaining stops
    if row["change_type"] == "route.resequenced" and row["payload"]:
        try:
            payload = json.loads(row["payload"])
            new_seq = payload.get("new_sequence", [])
            for index, stop_id in enumerate(new_seq, start=1):
                cur.execute("""
                    UPDATE stops
                    SET seq = ?
                    WHERE id = ? AND trip_id = ? AND status NOT IN ('delivered', 'failed', 'returned')
                """, (index, stop_id, row["trip_id"]))
        except Exception:
            pass

    db.commit()
    return AckChangeResponse(status="applied", change_id=change_id)
