"""
Comprehensive Test Suite for Waypoint Driver Backend API.
Tests Modules A through G end-to-end.
"""

import os
import uuid
import pytest
from fastapi.testclient import TestClient

# Ensure test DB is used
os.environ["DATABASE_PATH"] = "test_waypoint_driver.db"

from app.database import init_db, get_db
from app.seed import seed
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Clean up old test db if present
    if os.path.exists("test_waypoint_driver.db"):
        os.remove("test_waypoint_driver.db")
    # Seed fresh canonical dataset
    seed()
    yield
    # Teardown
    if os.path.exists("test_waypoint_driver.db"):
        try:
            os.remove("test_waypoint_driver.db")
        except Exception:
            pass


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    res = client.post("/api/driver/auth/login", json={
        "driver_id": "DRV-DANIRU",
        "pin": "1234",
        "device_id": "test-device"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════════════════════════════════════
# Module A: Driver Auth + Device Session
# ═══════════════════════════════════════════════════════════════════════════

def test_login_success(client):
    res = client.post("/api/driver/auth/login", json={
        "driver_id": "DRV-DANIRU",
        "pin": "1234",
        "device_id": "dev-001"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["driver_id"] == "DRV-DANIRU"
    assert data["driver_name"] == "Daniru Dinsara"


def test_login_invalid_pin(client):
    res = client.post("/api/driver/auth/login", json={
        "driver_id": "DRV-DANIRU",
        "pin": "9999",
        "device_id": "dev-001"
    })
    assert res.status_code == 401


def test_driver_me(client, auth_headers):
    # Test GET /api/driver/me
    res = client.get("/api/driver/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["driver_id"] == "DRV-DANIRU"
    assert data["home_depot"] == "Kandy hub"

    # Test GET /api/driver/auth/me
    res_auth = client.get("/api/driver/auth/me", headers=auth_headers)
    assert res_auth.status_code == 200
    assert res_auth.json()["driver_id"] == "DRV-DANIRU"


def test_token_refresh(client):
    login_res = client.post("/api/driver/auth/login", json={
        "driver_id": "DRV-DANIRU",
        "pin": "1234",
        "device_id": "dev-001"
    })
    refresh_token = login_res.json()["refresh_token"]

    res = client.post("/api/driver/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_logout(client, auth_headers):
    res = client.post("/api/driver/auth/logout", headers=auth_headers)
    assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# Module B: Today's Trips / Route Snapshot
# ═══════════════════════════════════════════════════════════════════════════

def test_get_today_trips(client, auth_headers):
    res = client.get("/api/driver/trips/today", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["driver_id"] == "DRV-DANIRU"
    assert len(data["trips"]) == 2
    trip1 = data["trips"][0]
    assert trip1["brand"] == "Fresh"
    assert trip1["stop_count"] == 8
    trip2 = data["trips"][1]
    assert trip2["brand"] == "Style"
    assert trip2["status"] == "locked"


def test_get_trip_detail(client, auth_headers):
    res = client.get("/api/driver/trips/TRIP-VEH014-2026-09-26-1", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["trip_id"] == "TRIP-VEH014-2026-09-26-1"
    assert data["weight_kg"] == 890


def test_get_trip_briefing(client, auth_headers):
    res = client.get("/api/driver/trips/TRIP-VEH014-2026-09-26-1/briefing", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "stops" in data
    assert "flagged_stops" in data
    assert "STOP-006" in data["flagged_stops"]
    assert data["total_distance_km"] > 0


def test_get_trip_manifest(client, auth_headers):
    res = client.get("/api/driver/trips/TRIP-VEH014-2026-09-26-1/manifest", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["stops"]) == 8
    assert len(data["manifest_lines"]) == 1
    assert data["manifest_lines"][0]["stop_id"] == "STOP-006"
    assert data["manifest_lines"][0]["pre_flagged"] is True
    assert data["manifest_lines"][0]["return_crate"] == "R-04"
    assert len(data["legs"]) == 9


# ═══════════════════════════════════════════════════════════════════════════
# Module C: Departure + Load Confirmation
# ═══════════════════════════════════════════════════════════════════════════

def test_depart_trip_with_flag(client, auth_headers):
    ev_id = str(uuid.uuid4())
    req = {
        "client_event_id": ev_id,
        "departed_at": "05:43",
        "load_confirmation": {
            "groups": [
                {
                    "stop_id": "STOP-002",
                    "outlet_id": "OUT047",
                    "state": "matches",
                    "van_units": 25
                },
                {
                    "stop_id": "STOP-006",
                    "outlet_id": "OUT058",
                    "state": "flagged",
                    "van_units": 12,
                    "deliverable_units": 10,
                    "return_units": 2,
                    "reason": "damaged_in_staging",
                    "return_crate": "R-04",
                    "note": "Loader pre-flag confirmed"
                }
            ]
        }
    }
    res = client.post("/api/driver/trips/TRIP-VEH014-2026-09-26-1/depart", json=req, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "applied"
    assert data["trip_status"] == "departed"
    assert data["flagged_count"] == 1

    # Idempotent retry test
    res_retry = client.post("/api/driver/trips/TRIP-VEH014-2026-09-26-1/depart", json=req, headers=auth_headers)
    assert res_retry.status_code == 200
    assert res_retry.json()["status"] == "already_applied"


# ═══════════════════════════════════════════════════════════════════════════
# Module D: Stop Lifecycle Events
# ═══════════════════════════════════════════════════════════════════════════

def test_stop_lifecycle_flow(client, auth_headers):
    # 1. Arrive at STOP-001 (seq 1, window 05:30-06:30)
    arrive_ev_id = str(uuid.uuid4())
    arrive_req = {
        "client_event_id": arrive_ev_id,
        "arrived_at": "05:55",
        "gps": {"lat": 7.168, "lng": 80.776},
        "base_row_version": 1
    }
    res_arrive = client.post("/api/driver/stops/STOP-001/arrive", json=arrive_req, headers=auth_headers)
    assert res_arrive.status_code == 200
    arr_data = res_arrive.json()
    assert arr_data["status"] == "applied"
    assert arr_data["window_status"] == "on_time"
    assert arr_data["new_row_version"] == 2

    # Idempotent arrival
    res_arr_dup = client.post("/api/driver/stops/STOP-001/arrive", json=arrive_req, headers=auth_headers)
    assert res_arr_dup.json()["status"] == "already_applied"

    # 2. Checklist for STOP-001
    check_ev_id = str(uuid.uuid4())
    check_req = {
        "client_event_id": check_ev_id,
        "base_row_version": 2,
        "lines": [
            {"line_id": "L1", "state": "delivered"}
        ]
    }
    res_check = client.post("/api/driver/stops/STOP-001/checklist", json=check_req, headers=auth_headers)
    assert res_check.status_code == 200
    assert res_check.json()["status"] == "applied"
    assert res_check.json()["new_row_version"] == 3

    # 3. POD photo-intent & complete
    res_intent = client.post("/api/driver/stops/STOP-001/pod/photo-intent", headers=auth_headers)
    assert res_intent.status_code == 200
    intent_data = res_intent.json()
    assert "upload_url" in intent_data
    obj_key = intent_data["object_key"]

    photo_ev_id = str(uuid.uuid4())
    photo_complete_req = {
        "client_event_id": photo_ev_id,
        "object_key": obj_key,
        "captured_at": "06:10",
        "base_row_version": 3
    }
    res_photo = client.post("/api/driver/stops/STOP-001/pod/photo-complete", json=photo_complete_req, headers=auth_headers)
    assert res_photo.status_code == 200
    assert res_photo.json()["status"] == "applied"

    # 4. POD pin
    pin_ev_id = str(uuid.uuid4())
    pin_req = {
        "client_event_id": pin_ev_id,
        "pin_state": "submitted",
        "submitted_at": "06:12",
        "attempts": 1,
        "base_row_version": 4
    }
    res_pin = client.post("/api/driver/stops/STOP-001/pod/pin", json=pin_req, headers=auth_headers)
    assert res_pin.status_code == 200
    assert res_pin.json()["pin_state"] == "verified"

    # 5. Outcome (delivered)
    outcome_ev_id = str(uuid.uuid4())
    outcome_req = {
        "client_event_id": outcome_ev_id,
        "outcome": "delivered",
        "delivered_units": 120,
        "return_units": 0,
        "finished_at": "06:15",
        "base_row_version": 4
    }
    res_outcome = client.post("/api/driver/stops/STOP-001/outcome", json=outcome_req, headers=auth_headers)
    assert res_outcome.status_code == 200
    assert res_outcome.json()["status"] == "applied"


def test_partial_delivery_and_return_custody(client, auth_headers):
    # STOP-006 (OUT058 - 10 delivered, 2 returned in crate R-04)
    # 1. Arrive at STOP-006
    arr_res = client.post("/api/driver/stops/STOP-006/arrive", json={
        "client_event_id": str(uuid.uuid4()),
        "arrived_at": "07:12",
        "base_row_version": 1
    }, headers=auth_headers)
    assert arr_res.status_code == 200

    # 2. Outcome with partial
    ev_id = str(uuid.uuid4())
    outcome_req = {
        "client_event_id": ev_id,
        "outcome": "partial",
        "delivered_units": 10,
        "return_units": 2,
        "reason": "damaged_in_staging",
        "return_crate": "R-04",
        "finished_at": "07:55",
        "base_row_version": 2
    }
    res = client.post("/api/driver/stops/STOP-006/outcome", json=outcome_req, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "applied"
    return_id = data["return_id"]
    assert return_id is not None

    # Depot confirmation of the return
    depot_ev_id = str(uuid.uuid4())
    depot_req = {
        "client_event_id": depot_ev_id,
        "confirmed_at": "09:51",
        "officer_name": "Kasun Kalhara",
        "officer_pin_state": "verified",
        "condition": "seal_intact"
    }
    res_confirm = client.post(f"/api/driver/returns/{return_id}/depot-confirm", json=depot_req, headers=auth_headers)
    assert res_confirm.status_code == 200
    assert res_confirm.json()["status"] == "applied"


# ═══════════════════════════════════════════════════════════════════════════
# Module E: Offline Sync Engine & Conflict Detection
# ═══════════════════════════════════════════════════════════════════════════

def test_offline_sync_and_conflict(client, auth_headers):
    # Send a sync batch:
    # 1st event: regular arrival at STOP-003 with correct base_row_version (1)
    # 2nd event: event with stale base_row_version (e.g. 99) -> triggers conflict
    ev1 = str(uuid.uuid4())
    ev2 = str(uuid.uuid4())

    sync_req = {
        "driver_id": "DRV-DANIRU",
        "device_id": "dev-001",
        "last_sync_cursor": "2026-09-26T06:00:00Z",
        "events": [
            {
                "client_event_id": ev1,
                "kind": "stop.arrived",
                "occurred_at": "06:18",
                "payload": {
                    "stop_id": "STOP-003",
                    "base_row_version": 1
                }
            },
            {
                "client_event_id": ev2,
                "kind": "stop.arrived",
                "occurred_at": "06:20",
                "payload": {
                    "stop_id": "STOP-003",
                    "base_row_version": 99  # Stale version!
                }
            }
        ]
    }
    res = client.post("/api/driver/sync", json=sync_req, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["status"] == "applied"
    assert data["results"][1]["status"] == "conflict"
    assert data["results"][1]["conflict_id"] is not None


# ═══════════════════════════════════════════════════════════════════════════
# Module F: Dispatcher Deltas / Route Changes
# ═══════════════════════════════════════════════════════════════════════════

def test_get_changes_and_acknowledge(client, auth_headers):
    res = client.get("/api/driver/changes", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["changes"]) >= 1
    chg = data["changes"][0]
    assert chg["type"] == "route.resequenced"
    assert chg["acknowledged"] is False

    # Acknowledge change
    change_id = chg["change_id"]
    res_ack = client.post(f"/api/driver/changes/{change_id}/ack", headers=auth_headers)
    assert res_ack.status_code == 200
    assert res_ack.json()["status"] == "applied"


# ═══════════════════════════════════════════════════════════════════════════
# Conflicts: Forward API
# ═══════════════════════════════════════════════════════════════════════════

def test_list_and_forward_conflict(client, auth_headers):
    res = client.get("/api/driver/conflicts", headers=auth_headers)
    assert res.status_code == 200
    conflicts = res.json()
    assert len(conflicts) >= 1
    conf_id = conflicts[0]["id"]

    res_fwd = client.post(f"/api/driver/conflicts/{conf_id}/forward", json={"note": "Confirmed in field"}, headers=auth_headers)
    assert res_fwd.status_code == 200
    assert res_fwd.json()["status"] == "forwarded"


# ═══════════════════════════════════════════════════════════════════════════
# Module G: Chat & Call Intent
# ═══════════════════════════════════════════════════════════════════════════

def test_chat_and_call(client, auth_headers):
    # Send message
    msg_ev_id = str(uuid.uuid4())
    msg_req = {
        "client_event_id": msg_ev_id,
        "body": "On my way. ETA 12 minutes.",
        "quick_reply": True
    }
    res_msg = client.post("/api/driver/stops/STOP-002/messages", json=msg_req, headers=auth_headers)
    assert res_msg.status_code == 200
    assert res_msg.json()["status"] == "sent"

    # Get messages
    res_list = client.get("/api/driver/stops/STOP-002/messages", headers=auth_headers)
    assert res_list.status_code == 200
    msgs = res_list.json()
    assert len(msgs) == 1
    assert msgs[0]["body"] == "On my way. ETA 12 minutes."

    # Call intent
    call_req = {"stop_id": "STOP-002", "requested_by": "driver"}
    res_call = client.post("/api/driver/stops/STOP-002/call-intent", json=call_req, headers=auth_headers)
    assert res_call.status_code == 200
    assert "masked_dial_number" in res_call.json()


# ═══════════════════════════════════════════════════════════════════════════
# Adversarial Security & Concurrency Verification
# ═══════════════════════════════════════════════════════════════════════════

def test_revoked_session_rejection(client):
    """ADV-03: Ensure logged out tokens are immediately rejected."""
    login_res = client.post("/api/driver/auth/login", json={
        "driver_id": "DRV-DANIRU",
        "pin": "1234",
        "device_id": "device-logout-test"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify token works before logout
    res_me = client.get("/api/driver/me", headers=headers)
    assert res_me.status_code == 200

    # Logout
    res_logout = client.post("/api/driver/auth/logout", headers=headers)
    assert res_logout.status_code == 200

    # Token must now be rejected
    res_post_logout = client.get("/api/driver/me", headers=headers)
    assert res_post_logout.status_code == 401


def test_idor_rejection_for_unassigned_stop(client, auth_headers):
    """ADV-02: Ensure driver cannot access or mutate stops not assigned to them."""
    # STOP-999 or non-existent stop
    res = client.post("/api/driver/stops/STOP-NONEXISTENT/arrive", json={
        "client_event_id": str(uuid.uuid4()),
        "arrived_at": "06:00",
        "base_row_version": 1
    }, headers=auth_headers)
    assert res.status_code == 404


def test_state_machine_invalid_outcome_jump(client, auth_headers):
    """ADV-05: Ensure delivery outcome cannot bypass prior arrival."""
    # STOP-004 is upcoming (has not arrived yet)
    res = client.post("/api/driver/stops/STOP-004/outcome", json={
        "client_event_id": str(uuid.uuid4()),
        "outcome": "delivered",
        "delivered_units": 160,
        "base_row_version": 1
    }, headers=auth_headers)
    assert res.status_code == 400


def test_conflict_cannot_be_re_forwarded(client, auth_headers):
    """ADV-07: Ensure conflict cannot be repeatedly forwarded if not in_review."""
    res = client.get("/api/driver/conflicts", headers=auth_headers)
    conf_id = res.json()[0]["id"]

    # First forward succeeds (or already forwarded)
    client.post(f"/api/driver/conflicts/{conf_id}/forward", json={"note": "Forward 1"}, headers=auth_headers)

    # Second forward on forwarded conflict must be rejected
    res_retry = client.post(f"/api/driver/conflicts/{conf_id}/forward", json={"note": "Forward 2"}, headers=auth_headers)
    assert res_retry.status_code == 400
