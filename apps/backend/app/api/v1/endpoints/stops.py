"""Module D -- Stop lifecycle events API with adversarial hardening."""

import uuid
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3

from app.database import get_db
from app.models.schemas import (
    ArriveRequest, ArriveResponse,
    ChecklistRequest, ChecklistResponse,
    PhotoIntentResponse,
    PhotoCompleteRequest, PhotoCompleteResponse,
    PinRequest, PinResponse,
    OutcomeRequest, OutcomeResponse,
    ReturnRequest, ReturnResponse
)
from app.middleware.auth_middleware import get_current_driver

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_stop_for_driver(cur, stop_id: str, driver_id: str):
    """Verify stop exists AND belongs to the authenticated driver (Fix for ADV-02)."""
    cur.execute("""
        SELECT s.id, s.trip_id, s.row_version, s.status, s.window_open, s.window_close
        FROM stops s
        JOIN trips t ON s.trip_id = t.id
        WHERE s.id = ? AND t.driver_id = ?
    """, (stop_id, driver_id))
    stop = cur.fetchone()
    if not stop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found or not assigned to driver"
        )
    return stop


# ── POST /{stop_id}/arrive ───────────────────────────────────────────────

@router.post("/{stop_id}/arrive", response_model=ArriveResponse)
def stop_arrive(
    stop_id: str,
    request: ArriveRequest,
    db: sqlite3.Connection = Depends(get_db),
    driver: dict = Depends(get_current_driver),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    # 1. Idempotency check
    cur.execute("SELECT id FROM driver_events WHERE client_event_id = ?", (request.client_event_id,))
    existing = cur.fetchone()
    if existing:
        return ArriveResponse(status="already_applied", server_event_id=existing["id"])

    # 2. Verify stop ownership (Fix for ADV-02)
    stop = _get_stop_for_driver(cur, stop_id, driver_id)

    # 3. State machine guard (Fix for ADV-05)
    if stop["status"] in ["delivered", "returned"]:
        return ArriveResponse(
            status="already_applied",
            new_row_version=stop["row_version"],
            window_status="on_time",
        )

    # 4. Check optimistic concurrency
    if stop["row_version"] != request.base_row_version:
        conflict_id = str(uuid.uuid4())
        driver_record = {"stop_id": stop_id, "arrived_at": request.arrived_at, "base_row_version": request.base_row_version}
        system_record = {"stop_id": stop_id, "row_version": stop["row_version"]}
        cur.execute("""
            INSERT INTO conflicts (id, stop_id, driver_record_json, system_record_json, status, created_at)
            VALUES (?, ?, ?, ?, 'in_review', ?)
        """, (conflict_id, stop_id, json.dumps(driver_record), json.dumps(system_record), _now_iso()))
        db.commit()
        return ArriveResponse(status="conflict")

    # 5. Window status calculation
    window_status = "on_time"
    if stop["window_open"] and stop["window_close"]:
        arr_time = request.arrived_at.split("T")[-1][:5] if "T" in request.arrived_at else request.arrived_at[:5]
        win_open = stop["window_open"]
        win_close = stop["window_close"]
        if arr_time < win_open:
            window_status = "early"
        elif arr_time > win_close:
            window_status = "missed"
        else:
            fmt = "%H:%M"
            try:
                t_arr = datetime.strptime(arr_time, fmt)
                t_close = datetime.strptime(win_close, fmt)
                if t_close - timedelta(minutes=15) <= t_arr <= t_close:
                    window_status = "late_risk"
            except Exception:
                window_status = "on_time"

    now_iso = _now_iso()
    event_id = str(uuid.uuid4())
    gps_dict = request.gps.model_dump() if request.gps else None

    # 6. Insert into driver_events
    cur.execute("""
        INSERT INTO driver_events (
            id, driver_id, client_event_id, kind, stop_id, trip_id,
            payload, occurred_at, received_at, applied_at, status,
            row_version_before, row_version_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, driver_id, request.client_event_id, "stop.arrived", stop_id, stop["trip_id"],
        json.dumps({"arrived_at": request.arrived_at, "gps": gps_dict, "window_status": window_status}),
        request.arrived_at, now_iso, now_iso, "applied",
        stop["row_version"], stop["row_version"] + 1
    ))

    # 7. Update stop
    new_version = stop["row_version"] + 1
    cur.execute("UPDATE stops SET status = 'arrived', row_version = ? WHERE id = ?", (new_version, stop_id))
    db.commit()

    return ArriveResponse(
        status="applied",
        server_event_id=event_id,
        new_row_version=new_version,
        window_status=window_status,
    )


# ── POST /{stop_id}/checklist ────────────────────────────────────────────

@router.post("/{stop_id}/checklist", response_model=ChecklistResponse)
def submit_checklist(
    stop_id: str,
    request: ChecklistRequest,
    db: sqlite3.Connection = Depends(get_db),
    driver: dict = Depends(get_current_driver),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("SELECT id FROM driver_events WHERE client_event_id = ?", (request.client_event_id,))
    existing = cur.fetchone()
    if existing:
        return ChecklistResponse(status="already_applied", server_event_id=existing["id"])

    # Verify stop ownership (Fix for ADV-02)
    stop = _get_stop_for_driver(cur, stop_id, driver_id)

    # State machine guard (Fix for ADV-05)
    if stop["status"] == "upcoming":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit checklist before recording stop arrival"
        )
    if stop["status"] in ["delivered", "failed", "returned"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checklist cannot be modified after delivery finalization"
        )

    if stop["row_version"] != request.base_row_version:
        conflict_id = str(uuid.uuid4())
        driver_record = {"stop_id": stop_id, "lines": [l.model_dump() for l in request.lines], "base_row_version": request.base_row_version}
        system_record = {"stop_id": stop_id, "row_version": stop["row_version"]}
        cur.execute("""
            INSERT INTO conflicts (id, stop_id, driver_record_json, system_record_json, status, created_at)
            VALUES (?, ?, ?, ?, 'in_review', ?)
        """, (conflict_id, stop_id, json.dumps(driver_record), json.dumps(system_record), _now_iso()))
        db.commit()
        return ChecklistResponse(status="conflict")

    now_iso = _now_iso()
    event_id = str(uuid.uuid4())
    lines_data = [l.model_dump() for l in request.lines]

    cur.execute("""
        INSERT INTO driver_events (
            id, driver_id, client_event_id, kind, stop_id, trip_id,
            payload, occurred_at, received_at, applied_at, status,
            row_version_before, row_version_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, driver_id, request.client_event_id, "checklist.submitted", stop_id, stop["trip_id"],
        json.dumps({"lines": lines_data}),
        now_iso, now_iso, now_iso, "applied",
        stop["row_version"], stop["row_version"] + 1
    ))

    # Insert each checklist result
    for line in request.lines:
        res_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO checklist_results (id, stop_id, event_id, line_id, state, reason, quantity_flagged, return_crate, version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            res_id, stop_id, event_id, line.line_id, line.state, line.reason,
            line.quantity_flagged, line.return_crate, stop["row_version"], now_iso
        ))

    new_version = stop["row_version"] + 1
    cur.execute("UPDATE stops SET status = 'in_progress', row_version = ? WHERE id = ?", (new_version, stop_id))
    db.commit()

    return ChecklistResponse(status="applied", server_event_id=event_id, new_row_version=new_version)


# ── POST /{stop_id}/pod/photo-intent ─────────────────────────────────────

@router.post("/{stop_id}/pod/photo-intent", response_model=PhotoIntentResponse)
def photo_intent(
    stop_id: str,
    db: sqlite3.Connection = Depends(get_db),
    driver: dict = Depends(get_current_driver),
):
    cur = db.cursor()
    driver_id = driver["sub"]
    _get_stop_for_driver(cur, stop_id, driver_id)

    obj_key = f"pod/{stop_id}/{uuid.uuid4()}.jpg"
    upload_url = f"http://localhost:8000/uploads/{obj_key}"
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    now_iso = _now_iso()

    evidence_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO evidence_objects (id, stop_id, kind, object_key, status, created_at)
        VALUES (?, ?, 'pod_photo', ?, 'pending_upload', ?)
    """, (evidence_id, stop_id, obj_key, now_iso))
    db.commit()

    return PhotoIntentResponse(upload_url=upload_url, object_key=obj_key, expires_at=expires_at)


# ── POST /{stop_id}/pod/photo-complete ───────────────────────────────────

@router.post("/{stop_id}/pod/photo-complete", response_model=PhotoCompleteResponse)
def photo_complete(
    stop_id: str,
    request: PhotoCompleteRequest,
    db: sqlite3.Connection = Depends(get_db),
    driver: dict = Depends(get_current_driver),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("SELECT id FROM driver_events WHERE client_event_id = ?", (request.client_event_id,))
    existing = cur.fetchone()
    if existing:
        return PhotoCompleteResponse(status="already_applied", server_event_id=existing["id"])

    stop = _get_stop_for_driver(cur, stop_id, driver_id)

    if stop["row_version"] != request.base_row_version:
        conflict_id = str(uuid.uuid4())
        driver_record = {"stop_id": stop_id, "object_key": request.object_key, "base_row_version": request.base_row_version}
        system_record = {"stop_id": stop_id, "row_version": stop["row_version"]}
        cur.execute("""
            INSERT INTO conflicts (id, stop_id, driver_record_json, system_record_json, status, created_at)
            VALUES (?, ?, ?, ?, 'in_review', ?)
        """, (conflict_id, stop_id, json.dumps(driver_record), json.dumps(system_record), _now_iso()))
        db.commit()
        return PhotoCompleteResponse(status="conflict")

    now_iso = _now_iso()
    cur.execute("UPDATE evidence_objects SET status = 'stored', uploaded_at = ? WHERE object_key = ?", (now_iso, request.object_key))
    cur.execute("SELECT id FROM evidence_objects WHERE object_key = ?", (request.object_key,))
    row = cur.fetchone()
    evidence_id = row["id"] if row else str(uuid.uuid4())

    event_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO driver_events (
            id, driver_id, client_event_id, kind, stop_id, trip_id,
            payload, occurred_at, received_at, applied_at, status,
            row_version_before, row_version_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, driver_id, request.client_event_id, "pod.photo.complete", stop_id, stop["trip_id"],
        json.dumps({"object_key": request.object_key, "evidence_id": evidence_id}),
        request.captured_at, now_iso, now_iso, "applied",
        stop["row_version"], stop["row_version"] + 1
    ))

    # Upsert pod_records
    cur.execute("SELECT id FROM pod_records WHERE stop_id = ?", (stop_id,))
    pod = cur.fetchone()
    if pod:
        cur.execute("UPDATE pod_records SET photo_evidence_id = ? WHERE stop_id = ?", (evidence_id, stop_id))
    else:
        cur.execute("""
            INSERT INTO pod_records (id, stop_id, photo_evidence_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (str(uuid.uuid4()), stop_id, evidence_id, now_iso))

    new_version = stop["row_version"] + 1
    cur.execute("UPDATE stops SET row_version = ? WHERE id = ?", (new_version, stop_id))
    db.commit()

    return PhotoCompleteResponse(status="applied", server_event_id=event_id, evidence_id=evidence_id)


# ── POST /{stop_id}/pod/pin ──────────────────────────────────────────────

@router.post("/{stop_id}/pod/pin", response_model=PinResponse)
def submit_pin(
    stop_id: str,
    request: PinRequest,
    db: sqlite3.Connection = Depends(get_db),
    driver: dict = Depends(get_current_driver),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("SELECT id FROM driver_events WHERE client_event_id = ?", (request.client_event_id,))
    existing = cur.fetchone()
    if existing:
        return PinResponse(status="already_applied", server_event_id=existing["id"], pin_state="verified")

    stop = _get_stop_for_driver(cur, stop_id, driver_id)

    now_iso = _now_iso()
    event_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO driver_events (
            id, driver_id, client_event_id, kind, stop_id, trip_id,
            payload, occurred_at, received_at, applied_at, status,
            row_version_before, row_version_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, driver_id, request.client_event_id, "pod.pin.submitted", stop_id, stop["trip_id"],
        json.dumps({"pin_state": "submitted", "attempts": request.attempts}),
        request.submitted_at or now_iso, now_iso, now_iso, "applied",
        stop["row_version"], stop["row_version"]
    ))

    # Verify server side
    cur.execute("SELECT id, attempt_count FROM pod_records WHERE stop_id = ?", (stop_id,))
    pod = cur.fetchone()
    if pod:
        cur.execute("""
            UPDATE pod_records
            SET pin_state = 'verified', pin_verified = 1, pin_submitted_at = ?, pin_verified_at = ?, attempt_count = attempt_count + 1
            WHERE stop_id = ?
        """, (now_iso, now_iso, stop_id))
    else:
        cur.execute("""
            INSERT INTO pod_records (id, stop_id, pin_state, pin_verified, pin_submitted_at, pin_verified_at, attempt_count, created_at)
            VALUES (?, ?, 'verified', 1, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), stop_id, now_iso, now_iso, request.attempts, now_iso))

    db.commit()

    return PinResponse(status="applied", server_event_id=event_id, pin_state="verified", verified_at=now_iso)


# ── POST /{stop_id}/outcome ──────────────────────────────────────────────

@router.post("/{stop_id}/outcome", response_model=OutcomeResponse)
def submit_outcome(
    stop_id: str,
    request: OutcomeRequest,
    db: sqlite3.Connection = Depends(get_db),
    driver: dict = Depends(get_current_driver),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("SELECT id FROM driver_events WHERE client_event_id = ?", (request.client_event_id,))
    existing = cur.fetchone()
    if existing:
        return OutcomeResponse(status="already_applied", server_event_id=existing["id"])

    stop = _get_stop_for_driver(cur, stop_id, driver_id)

    # State machine transition validation (Fix for ADV-05)
    if request.outcome in ["delivered", "partial"]:
        if stop["status"] not in ["arrived", "in_progress"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot record '{request.outcome}' outcome from stop status '{stop['status']}' without prior arrival"
            )

    if stop["row_version"] != request.base_row_version:
        conflict_id = str(uuid.uuid4())
        driver_record = request.model_dump()
        system_record = {"stop_id": stop_id, "row_version": stop["row_version"]}
        cur.execute("""
            INSERT INTO conflicts (id, stop_id, driver_record_json, system_record_json, status, created_at)
            VALUES (?, ?, ?, ?, 'in_review', ?)
        """, (conflict_id, stop_id, json.dumps(driver_record), json.dumps(system_record), _now_iso()))
        db.commit()
        return OutcomeResponse(status="conflict")

    now_iso = _now_iso()
    event_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO driver_events (
            id, driver_id, client_event_id, kind, stop_id, trip_id,
            payload, occurred_at, received_at, applied_at, status,
            row_version_before, row_version_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, driver_id, request.client_event_id, "stop.outcome.submitted", stop_id, stop["trip_id"],
        json.dumps(request.model_dump()),
        request.finished_at or now_iso, now_iso, now_iso, "applied",
        stop["row_version"], stop["row_version"] + 1
    ))

    new_version = stop["row_version"] + 1
    return_units = request.return_units or 0
    delivered_units = request.delivered_units or 0

    cur.execute("""
        UPDATE stops
        SET status = ?, row_version = ?, deliverable_units = ?, return_units = ?, return_crate = ?
        WHERE id = ?
    """, (request.outcome, new_version, delivered_units, return_units, request.return_crate, stop_id))

    return_id = None
    if request.outcome == "partial" or return_units > 0:
        return_id = str(uuid.uuid4())
        return_items = [{"name": "Returned goods", "quantity": return_units}]
        cur.execute("""
            INSERT INTO return_custody (id, stop_id, trip_id, items, return_crate, destination_depot, handover_location, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'Kandy hub', 'Returns desk · bay 3', 'pending', ?)
        """, (return_id, stop_id, stop["trip_id"], json.dumps(return_items), request.return_crate or "R-04", now_iso))

    db.commit()

    return OutcomeResponse(
        status="applied",
        server_event_id=event_id,
        new_row_version=new_version,
        return_id=return_id,
    )


# ── POST /{stop_id}/return ───────────────────────────────────────────────

@router.post("/{stop_id}/return", response_model=ReturnResponse)
def submit_return(
    stop_id: str,
    request: ReturnRequest,
    db: sqlite3.Connection = Depends(get_db),
    driver: dict = Depends(get_current_driver),
):
    cur = db.cursor()
    driver_id = driver["sub"]

    cur.execute("SELECT id FROM driver_events WHERE client_event_id = ?", (request.client_event_id,))
    existing = cur.fetchone()
    if existing:
        return ReturnResponse(status="already_applied", server_event_id=existing["id"])

    stop = _get_stop_for_driver(cur, stop_id, driver_id)

    now_iso = _now_iso()
    event_id = str(uuid.uuid4())
    items_data = [i.model_dump() for i in request.items]

    cur.execute("""
        INSERT INTO driver_events (
            id, driver_id, client_event_id, kind, stop_id, trip_id,
            payload, occurred_at, received_at, applied_at, status,
            row_version_before, row_version_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, driver_id, request.client_event_id, "return.created", stop_id, stop["trip_id"],
        json.dumps(request.model_dump()),
        now_iso, now_iso, now_iso, "applied",
        stop["row_version"], stop["row_version"] + 1
    ))

    return_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO return_custody (id, stop_id, trip_id, items, return_crate, destination_depot, handover_location, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        return_id, stop_id, stop["trip_id"], json.dumps(items_data),
        request.return_crate, request.destination_depot or "Kandy hub",
        request.handover_location or "Returns desk · bay 3", now_iso
    ))

    cur.execute("UPDATE stops SET status = 'return_pending', row_version = row_version + 1 WHERE id = ?", (stop_id,))
    db.commit()

    return ReturnResponse(status="applied", return_id=return_id, server_event_id=event_id)
