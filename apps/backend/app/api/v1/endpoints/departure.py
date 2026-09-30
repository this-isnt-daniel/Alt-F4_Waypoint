"""Module C -- Departure / load confirmation API."""

import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
import sqlite3

from app.database import get_db
from app.models.schemas import DepartRequest, DepartResponse
from app.middleware.auth_middleware import get_current_driver

router = APIRouter()


@router.post("/{trip_id}/depart", response_model=DepartResponse)
def depart_trip(
    trip_id: str,
    request: DepartRequest,
    payload: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    driver_id = payload["sub"]
    cur = db.cursor()

    # Verify trip exists and belongs to driver
    cur.execute("SELECT * FROM trips WHERE id = ? AND driver_id = ?", (trip_id, driver_id))
    trip_row = cur.fetchone()
    if not trip_row:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Idempotency check
    cur.execute("SELECT id FROM driver_events WHERE client_event_id = ?", (request.client_event_id,))
    existing = cur.fetchone()
    if existing:
        return DepartResponse(
            status="already_applied",
            trip_id=trip_id,
            trip_status="departed",
            server_event_id=existing["id"],
            flagged_count=0,
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid.uuid4())

    # Build groups data
    groups_data = [g.model_dump() for g in request.load_confirmation.groups]
    flagged_count = sum(1 for g in groups_data if g.get("state") == "flagged")

    # Store event in driver_events
    cur.execute("""
        INSERT INTO driver_events (id, driver_id, client_event_id, kind, trip_id,
            payload, occurred_at, received_at, applied_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, driver_id, request.client_event_id, "trip.departed", trip_id,
        json.dumps({"departed_at": request.departed_at, "load_confirmation": groups_data}),
        request.departed_at, now_iso, now_iso, "applied",
    ))

    # Store load confirmation
    conf_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO load_confirmations (id, trip_id, driver_id, event_id, departed_at, groups_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (conf_id, trip_id, driver_id, event_id, request.departed_at, json.dumps(groups_data)))

    # Update trip status
    cur.execute("UPDATE trips SET status = 'departed' WHERE id = ?", (trip_id,))

    # Audit log for flagged load shortfalls
    if flagged_count > 0:
        audit_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO audit_log (id, actor_role, actor_id, action, entity_type, entity_id, detail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_id, "driver", driver_id, "load_shortfall_flagged",
            "trip", trip_id, json.dumps({"flagged_count": flagged_count}),
        ))

    db.commit()

    return DepartResponse(
        status="applied",
        trip_id=trip_id,
        trip_status="departed",
        server_event_id=event_id,
        flagged_count=flagged_count,
    )
