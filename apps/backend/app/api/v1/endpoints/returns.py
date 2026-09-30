"""Module D -- Returns / depot confirmation API."""

import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
import sqlite3

from app.database import get_db
from app.models.schemas import DepotConfirmRequest, DepotConfirmResponse
from app.middleware.auth_middleware import get_current_driver

router = APIRouter()


@router.post("/{return_id}/depot-confirm", response_model=DepotConfirmResponse)
def depot_confirm(
    return_id: str,
    request: DepotConfirmRequest,
    db: sqlite3.Connection = Depends(get_db),
    driver: dict = Depends(get_current_driver),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    # 1. Idempotency check
    cur.execute("SELECT id FROM driver_events WHERE client_event_id = ?", (request.client_event_id,))
    existing = cur.fetchone()
    if existing:
        return DepotConfirmResponse(status="already_applied", return_id=return_id, server_event_id=existing["id"])

    # 2. Check return_custody record
    cur.execute("SELECT * FROM return_custody WHERE id = ?", (return_id,))
    record = cur.fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="Return custody record not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid.uuid4())

    # 3. Log event
    cur.execute("""
        INSERT INTO driver_events (
            id, driver_id, client_event_id, kind, stop_id, trip_id,
            payload, occurred_at, received_at, applied_at, status
        ) VALUES (?, ?, ?, 'depot_return.confirmed', ?, ?, ?, ?, ?, ?, 'applied')
    """, (
        event_id, driver_id, request.client_event_id, record["stop_id"], record["trip_id"],
        json.dumps(request.model_dump()),
        request.confirmed_at, now_iso, now_iso
    ))

    # 4. Update custody record
    cur.execute("""
        UPDATE return_custody
        SET status = 'confirmed', confirmed_at = ?, officer_name = ?,
            officer_pin_state = ?, condition = ?
        WHERE id = ?
    """, (
        request.confirmed_at, request.officer_name or "Kasun Kalhara",
        request.officer_pin_state or "verified", request.condition or "seal_intact",
        return_id
    ))

    # 5. Update stop status if applicable
    if record["stop_id"]:
        cur.execute("UPDATE stops SET status = 'returned' WHERE id = ?", (record["stop_id"],))

    # 6. Check if trip 1 is complete to unlock trip 2
    trip_id = record["trip_id"]
    if trip_id:
        cur.execute("SELECT trip_no FROM trips WHERE id = ?", (trip_id,))
        trip_row = cur.fetchone()
        if trip_row and trip_row["trip_no"] == 1:
            # Check if any stops on trip 1 are still unfinished
            cur.execute("""
                SELECT COUNT(*) as unfinished
                FROM stops
                WHERE trip_id = ? AND status NOT IN ('delivered', 'partial', 'failed', 'returned')
            """, (trip_id,))
            res = cur.fetchone()
            if res and res["unfinished"] == 0:
                # Mark trip 1 completed and unlock trip 2
                cur.execute("UPDATE trips SET status = 'completed' WHERE id = ?", (trip_id,))
                cur.execute("""
                    UPDATE trips SET status = 'planned'
                    WHERE driver_id = ? AND trip_no = 2 AND status = 'locked'
                """, (driver_id,))

    db.commit()

    return DepotConfirmResponse(status="applied", return_id=return_id, server_event_id=event_id)
