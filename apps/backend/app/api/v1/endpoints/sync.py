"""Module E -- Offline sync engine API."""

import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
import sqlite3

from app.database import get_db
from app.middleware.auth_middleware import get_current_driver
from app.models.schemas import SyncRequest, SyncResponse, SyncEventResult

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("", response_model=SyncResponse)
@router.post("/", response_model=SyncResponse)
def batch_sync(
    request: SyncRequest,
    driver: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    results = []
    cur = db.cursor()
    driver_id = driver["sub"]
    now_iso = _now_iso()

    for ev in request.events:
        try:
            # 1. Idempotency check
            cur.execute("SELECT id FROM driver_events WHERE client_event_id = ?", (ev.client_event_id,))
            existing = cur.fetchone()
            if existing:
                results.append(SyncEventResult(
                    client_event_id=ev.client_event_id,
                    status="already_applied",
                    server_event_id=existing["id"],
                ))
                continue

            payload = ev.payload or {}
            stop_id = payload.get("stop_id")
            trip_id = payload.get("trip_id")
            base_row_version = payload.get("base_row_version")

            stop = None
            if stop_id:
                cur.execute("SELECT id, trip_id, row_version, status FROM stops WHERE id = ?", (stop_id,))
                stop = cur.fetchone()
                if stop and not trip_id:
                    trip_id = stop["trip_id"]

            # 2. Check row version mismatch for conflict
            if stop and base_row_version is not None and stop["row_version"] != base_row_version:
                conflict_id = str(uuid.uuid4())
                driver_rec = {"client_event_id": ev.client_event_id, "kind": ev.kind, "payload": payload}
                system_rec = {"stop_id": stop_id, "row_version": stop["row_version"], "current_status": stop["status"]}
                cur.execute("""
                    INSERT INTO conflicts (id, stop_id, driver_record_json, system_record_json, status, created_at)
                    VALUES (?, ?, ?, ?, 'in_review', ?)
                """, (conflict_id, stop_id, json.dumps(driver_rec), json.dumps(system_rec), now_iso))
                db.commit()

                results.append(SyncEventResult(
                    client_event_id=ev.client_event_id,
                    status="conflict",
                    conflict_id=conflict_id,
                    reason="row_version_mismatch",
                    system_record=system_rec,
                ))
                continue

            # 3. Apply event
            server_event_id = str(uuid.uuid4())
            curr_ver = stop["row_version"] if stop else None
            new_row_version = None

            # Determine kind-specific updates
            if ev.kind == "stop.arrived" and stop_id:
                new_row_version = (curr_ver or 1) + 1
                cur.execute("UPDATE stops SET status = 'arrived', row_version = ? WHERE id = ?", (new_row_version, stop_id))

            elif ev.kind == "checklist.submitted" and stop_id:
                new_row_version = (curr_ver or 1) + 1
                cur.execute("UPDATE stops SET status = 'in_progress', row_version = ? WHERE id = ?", (new_row_version, stop_id))
                lines = payload.get("lines", [])
                for line in lines:
                    cur.execute("""
                        INSERT INTO checklist_results (id, stop_id, event_id, line_id, state, reason, quantity_flagged, return_crate, version, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), stop_id, server_event_id,
                        line.get("line_id", ""), line.get("state", "delivered"),
                        line.get("reason"), line.get("quantity_flagged"), line.get("return_crate"),
                        curr_ver or 1, now_iso
                    ))

            elif ev.kind == "pod.photo.complete" and stop_id:
                new_row_version = (curr_ver or 1) + 1
                cur.execute("UPDATE stops SET row_version = ? WHERE id = ?", (new_row_version, stop_id))

            elif ev.kind == "pod.pin.submitted" and stop_id:
                cur.execute("SELECT id FROM pod_records WHERE stop_id = ?", (stop_id,))
                pod = cur.fetchone()
                if pod:
                    cur.execute("""
                        UPDATE pod_records
                        SET pin_state = 'verified', pin_verified = 1, pin_submitted_at = ?, pin_verified_at = ?
                        WHERE stop_id = ?
                    """, (now_iso, now_iso, stop_id))
                else:
                    cur.execute("""
                        INSERT INTO pod_records (id, stop_id, pin_state, pin_verified, pin_submitted_at, pin_verified_at, created_at)
                        VALUES (?, ?, 'verified', 1, ?, ?, ?)
                    """, (str(uuid.uuid4()), stop_id, now_iso, now_iso, now_iso))

            elif ev.kind == "stop.outcome.submitted" and stop_id:
                new_row_version = (curr_ver or 1) + 1
                outcome = payload.get("outcome", "delivered")
                del_units = payload.get("delivered_units", 0)
                ret_units = payload.get("return_units", 0)
                crate = payload.get("return_crate")
                cur.execute("""
                    UPDATE stops
                    SET status = ?, row_version = ?, deliverable_units = ?, return_units = ?, return_crate = ?
                    WHERE id = ?
                """, (outcome, new_row_version, del_units, ret_units, crate, stop_id))

                if outcome == "partial" or (ret_units and ret_units > 0):
                    ret_id = str(uuid.uuid4())
                    items = [{"name": "Returned items", "quantity": ret_units}]
                    cur.execute("""
                        INSERT INTO return_custody (id, stop_id, trip_id, items, return_crate, destination_depot, handover_location, status, created_at)
                        VALUES (?, ?, ?, ?, ?, 'Kandy hub', 'Returns desk · bay 3', 'pending', ?)
                    """, (ret_id, stop_id, trip_id, json.dumps(items), crate or "R-04", now_iso))

            elif ev.kind == "return.created" and stop_id:
                cur.execute("UPDATE stops SET status = 'return_pending' WHERE id = ?", (stop_id,))
                ret_id = str(uuid.uuid4())
                items = payload.get("items", [])
                cur.execute("""
                    INSERT INTO return_custody (id, stop_id, trip_id, items, return_crate, destination_depot, handover_location, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """, (
                    ret_id, stop_id, trip_id, json.dumps(items),
                    payload.get("return_crate"), payload.get("destination_depot", "Kandy hub"),
                    payload.get("handover_location", "Returns desk · bay 3"), now_iso
                ))

            elif ev.kind == "depot_return.confirmed":
                ret_id = payload.get("return_id")
                if ret_id:
                    cur.execute("""
                        UPDATE return_custody
                        SET status = 'confirmed', confirmed_at = ?, officer_name = ?, condition = ?
                        WHERE id = ?
                    """, (now_iso, payload.get("officer_name"), payload.get("condition"), ret_id))

            elif ev.kind == "trip.departed" and trip_id:
                cur.execute("UPDATE trips SET status = 'departed' WHERE id = ?", (trip_id,))

            # Store the event
            cur.execute("""
                INSERT INTO driver_events (
                    id, driver_id, device_id, client_event_id, kind, stop_id, trip_id,
                    payload, occurred_at, received_at, applied_at, status,
                    row_version_before, row_version_after
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'applied', ?, ?)
            """, (
                server_event_id, driver_id, request.device_id, ev.client_event_id, ev.kind,
                stop_id, trip_id, json.dumps(payload), ev.occurred_at or now_iso,
                now_iso, now_iso, curr_ver, new_row_version
            ))

            db.commit()
            results.append(SyncEventResult(
                client_event_id=ev.client_event_id,
                status="applied",
                server_event_id=server_event_id,
                new_row_version=new_row_version,
            ))

        except Exception as e:
            results.append(SyncEventResult(
                client_event_id=ev.client_event_id,
                status="failed",
                error=str(e),
            ))

    return SyncResponse(results=results, new_cursor=now_iso)
