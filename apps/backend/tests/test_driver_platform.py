"""Canonical Driver API tests (/api/v1/driver-platform) on the shared SQLAlchemy schema.

Covers authorization / IDOR, the full trip + stop lifecycle, POD, partial / failed delivery,
returns + depot confirmation, trip unlock, idempotency, offline sync, row_version conflicts
and their resolution, and Dispatcher route-change integration.
"""

import json
import os
import uuid
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_platform_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import (
    Conflict,
    Depot,
    DriverEvent,
    LoadCheck,
    LoadCheckItem,
    Order,
    OrderLine,
    Outlet,
    Product,
    ReturnCustody,
    Trip,
    TripStop,
    TripStopItem,
    User,
    Vehicle,
)

API = "/api/v1/driver-platform"
TODAY = date(2026, 10, 3)


@pytest.fixture
def db():
    # Set TEST_DATABASE_URL=postgresql+psycopg2://... to run against a real (disposable) PostgreSQL.
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        engine = create_engine(url)
        Base.metadata.drop_all(bind=engine)
    else:
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()

    session.add_all([
        Depot(depot_id="DEP1", name="Kandy hub"),
        Depot(depot_id="DEP2", name="Peliyagoda"),
        Outlet(outlet_id="OUT1", name="Kandy City", brand="fresh", district="Kandy", depot_id="DEP1",
               lat=7.29, lng=80.63),
        Outlet(outlet_id="OUT2", name="Peradeniya", brand="fresh", district="Kandy", depot_id="DEP1"),
        Product(product_id="P1", name="Milk", brand="fresh", temp_req="ambient", unit="crate"),
        Product(product_id="P2", name="Bread", brand="fresh", temp_req="ambient", unit="tray"),
        Vehicle(vehicle_id="V1", depot_id="DEP1", type="van", temp="ambient", weight_cap_kg=1000,
                vol_cap_m3=10, plate="WP-1234"),
        Vehicle(vehicle_id="V2", depot_id="DEP1", type="van", temp="ambient", weight_cap_kg=1000, vol_cap_m3=10),
    ])
    session.add_all([
        User(user_id="U_DRV1", username="driver1", name="Daniru", role="driver", depot_id="DEP1", hashed_pw="x"),
        User(user_id="U_DRV2", username="driver2", name="Other Driver", role="driver", depot_id="DEP1", hashed_pw="x"),
        User(user_id="U_DISP", username="disp1", name="Dispatcher", role="dispatcher", depot_id="DEP1", hashed_pw="x"),
        User(user_id="U_DISP2", username="disp2", name="Far Dispatcher", role="dispatcher", depot_id="DEP2", hashed_pw="x"),
        User(user_id="U_LOAD", username="loader1", name="Loader", role="loader", depot_id="DEP1", hashed_pw="x"),
        User(user_id="U_SM", username="sm1", name="Manager", role="store_manager", outlet_id="OUT1", hashed_pw="x"),
    ])
    session.commit()

    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.pop(get_db, None)
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    return TestClient(app)


def headers(user_id, role="driver"):
    token = create_platform_access_token({"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


DRV1 = headers("U_DRV1")
DRV2 = headers("U_DRV2")
DISP = headers("U_DISP", "dispatcher")
DISP2 = headers("U_DISP2", "dispatcher")
LOADER = headers("U_LOAD", "loader")

_counter = {"n": 0}


def make_trip(db, *, driver_id="U_DRV1", trip_no=1, vehicle_id="V1", status="loaded",
              stops=(("OUT1", {"P1": 10, "P2": 4}),), loaded=None, materialize=True,
              window=("03:30", "23:59")):
    """Create a trip with one order per stop. `loaded` maps product → loader-recorded qty."""
    _counter["n"] += 1
    n = _counter["n"]
    trip = Trip(trip_id=f"T{n}", depot_id="DEP1", vehicle_id=vehicle_id, driver_id=driver_id,
                dispatcher_id="U_DISP", trip_date=TODAY, trip_no=trip_no, brand="fresh", status=status)
    db.add(trip)
    db.flush()
    check = None
    if loaded:
        check = LoadCheck(check_id=f"LC{n}", trip_id=trip.trip_id, checked_by="U_LOAD",
                          checked_at=datetime.now(timezone.utc), status="shortfall")
        db.add(check)
        db.flush()
    stop_ids = []
    for seq, (outlet_id, lines) in enumerate(stops, start=1):
        order = Order(order_id=f"ORD{n}-{seq}", outlet_id=outlet_id, created_by="U_SM", brand="fresh",
                      temp_req="ambient", order_date=date(2026, 10, n % 28 + 1), status="loaded",
                      trip_id=trip.trip_id, stop_seq=seq, order_units=sum(lines.values()),
                      window_open=window[0], window_close=window[1])
        db.add(order)
        db.flush()
        stop = TripStop(stop_id=f"S{n}-{seq}", trip_id=trip.trip_id, outlet_id=outlet_id, order_id=order.order_id,
                        stop_seq=seq, temp_req="ambient", status="upcoming")
        db.add(stop)
        db.flush()
        for product_id, qty in lines.items():
            line = OrderLine(line_item_id=f"L{n}-{seq}-{product_id}", order_id=order.order_id,
                             product_id=product_id, quantity=qty)
            db.add(line)
            db.flush()
            if materialize:
                db.add(TripStopItem(item_id=f"I{n}-{seq}-{product_id}", stop_id=stop.stop_id,
                                    line_item_id=line.line_item_id, qty_assigned=qty, unit="crate", sku=product_id))
            if check:
                db.add(LoadCheckItem(chk_item_id=f"CI{n}-{seq}-{product_id}", check_id=check.check_id,
                                     line_item_id=line.line_item_id, exp_qty=qty,
                                     loaded_qty=loaded.get(product_id, qty), status="ok"))
        stop_ids.append(stop.stop_id)
    db.commit()
    return trip.trip_id, stop_ids


def eid():
    return f"evt-{uuid.uuid4().hex[:10]}"


def stop_version(db, stop_id):
    db.expire_all()
    return db.query(TripStop).filter(TripStop.stop_id == stop_id).one().row_version


def depart(client, trip_id, h=DRV1, **extra):
    return client.post(f"{API}/trips/{trip_id}/depart", headers=h, json={"client_event_id": eid(), **extra})


def arrive(client, db, stop_id, h=DRV1, **extra):
    body = {"client_event_id": eid(), "base_row_version": stop_version(db, stop_id), **extra}
    return client.post(f"{API}/stops/{stop_id}/arrive", headers=h, json=body)


def pod(client, db, stop_id, h=DRV1, order_id=None):
    order_id = order_id or db.query(TripStop).filter(TripStop.stop_id == stop_id).one().order_id
    return client.post(f"{API}/stops/{stop_id}/pod", headers=h, json={"client_event_id": eid(), "order_id": order_id})


def outcome(client, db, stop_id, outcome_kind, h=DRV1, **extra):
    body = {"client_event_id": eid(), "base_row_version": stop_version(db, stop_id), "outcome": outcome_kind, **extra}
    return client.post(f"{API}/stops/{stop_id}/outcome", headers=h, json=body)


def deliver(client, db, stop_id):
    assert arrive(client, db, stop_id).status_code == 200
    assert pod(client, db, stop_id).status_code == 200
    res = outcome(client, db, stop_id, "delivered")
    assert res.status_code == 200, res.text
    return res


def complete(client, trip_id, h=DRV1):
    return client.post(f"{API}/trips/{trip_id}/complete", headers=h, json={"client_event_id": eid()})


# ═══════════════════════════════════════════════════════════════════════════
# Authentication / authorization
# ═══════════════════════════════════════════════════════════════════════════

def test_requires_authentication_and_driver_role(client, db):
    trip_id, _ = make_trip(db)
    assert client.get(f"{API}/trips/today").status_code in (401, 403)
    assert client.get(f"{API}/trips/today", headers=LOADER).status_code == 403
    assert client.get(f"{API}/trips/today", headers=DISP).status_code == 403
    assert depart(client, trip_id, h=LOADER).status_code == 403
    bad = {"Authorization": "Bearer not-a-jwt"}
    assert client.get(f"{API}/trips/today", headers=bad).status_code == 401


def test_today_trips_only_returns_assigned_trips_with_lock_flag(client, db):
    t1, _ = make_trip(db, trip_no=1)
    t2, _ = make_trip(db, trip_no=2)
    other, _ = make_trip(db, driver_id="U_DRV2", vehicle_id="V2")

    res = client.get(f"{API}/trips/today", headers=DRV1, params={"date": str(TODAY)})
    assert res.status_code == 200
    body = res.json()
    assert body["driver_name"] == "Daniru"
    assert [t["trip_id"] for t in body["trips"]] == [t1, t2]
    assert [t["locked"] for t in body["trips"]] == [False, True]
    assert body["trips"][0]["vehicle_plate"] == "WP-1234"
    assert other not in json.dumps(body)

    res = client.get(f"{API}/trips/today", headers=DRV2, params={"date": str(TODAY)})
    assert [t["trip_id"] for t in res.json()["trips"]] == [other]


def test_trip_detail_returns_stops_and_manifest(client, db):
    trip_id, (stop_id,) = make_trip(db, loaded={"P1": 8})
    res = client.get(f"{API}/trips/{trip_id}", headers=DRV1)
    assert res.status_code == 200
    stop = res.json()["stops"][0]
    assert stop["stop_id"] == stop_id
    assert stop["outlet_name"] == "Kandy City"
    assert stop["coords"] == {"lat": 7.29, "lng": 80.63}
    items = {item["product_id"]: item for item in stop["items"]}
    assert items["P1"]["qty_assigned"] == 10
    assert items["P1"]["qty_expected"] == 8  # loader shortfall flows through
    assert items["P2"]["qty_expected"] == 4


def test_driver_cannot_touch_another_drivers_trip_or_stop(client, db):
    trip_id, (stop_id,) = make_trip(db, driver_id="U_DRV2", status="out_for_delivery")

    assert client.get(f"{API}/trips/{trip_id}", headers=DRV1).status_code == 404
    assert depart(client, trip_id).status_code == 404
    assert complete(client, trip_id).status_code == 404
    assert arrive(client, db, stop_id).status_code == 404
    assert pod(client, db, stop_id).status_code == 404
    assert outcome(client, db, stop_id, "failed", reason="closed").status_code == 404
    assert client.post(f"{API}/stops/{stop_id}/pod/photo-intent", headers=DRV1).status_code == 404
    res = client.post(f"{API}/stops/{stop_id}/checklist", headers=DRV1,
                      json={"client_event_id": eid(), "base_row_version": 1,
                            "lines": [{"item_id": "x", "qty_delivered": 1}]})
    assert res.status_code == 404

    # Nothing changed, and every attempt is in the ledger as failed without a trip/stop link.
    db.expire_all()
    assert db.query(TripStop).filter(TripStop.stop_id == stop_id).one().status == "upcoming"
    failed = db.query(DriverEvent).filter(DriverEvent.driver_id == "U_DRV1").all()
    assert failed and all(e.status == "failed" and e.trip_id is None and e.stop_id is None for e in failed)


def test_offline_events_cannot_modify_another_drivers_stop(client, db):
    _, (stop_id,) = make_trip(db, driver_id="U_DRV2", status="out_for_delivery")
    res = client.post(f"{API}/events/sync", headers=DRV1, json={"events": [
        {"client_event_id": eid(), "kind": "stop.arrived", "payload": {"stop_id": stop_id, "base_row_version": 1}},
    ]})
    assert res.status_code == 200
    assert res.json()["results"][0]["status"] == "failed"
    assert stop_version(db, stop_id) == 1


# ═══════════════════════════════════════════════════════════════════════════
# Lifecycle
# ═══════════════════════════════════════════════════════════════════════════

def test_full_trip_lifecycle_and_trip_unlock(client, db):
    t1, (s1,) = make_trip(db, trip_no=1, materialize=False)
    t2, (s2,) = make_trip(db, trip_no=2)

    # Trip 2 is locked while trip 1 is open.
    res = depart(client, t2)
    assert res.status_code == 400 and "locked" in res.json()["detail"]

    res = depart(client, t1, load_confirmation=[{"stop_id": s1, "state": "flagged", "note": "1 crate short"}])
    assert res.status_code == 200, res.text
    assert res.json()["trip_status"] == "out_for_delivery"
    assert res.json()["flagged_count"] == 1
    db.expire_all()
    assert db.query(Order).filter(Order.order_id == "ORD%s-1" % t1[1:]).one().status == "out_for_delivery"
    stop = db.query(TripStop).filter(TripStop.stop_id == s1).one()
    assert stop.status == "upcoming"  # loader's 'loaded' normalised to the canonical enum
    assert db.query(TripStopItem).filter(TripStopItem.stop_id == s1).count() == 2  # manifest frozen

    res = arrive(client, db, s1, gps={"lat": 7.3, "lng": 80.6}, arrived_at="2026-10-03T04:00:00+00:00")
    assert res.status_code == 200, res.text
    assert res.json()["stop_status"] == "arrived"
    assert res.json()["new_row_version"] == 2
    assert res.json()["window_status"] == "on_time"
    db.expire_all()
    assert db.query(Order).filter(Order.trip_id == t1).one().actual_arrival == "09:30"  # Asia/Colombo

    items = {i.sku: i.item_id for i in db.query(TripStopItem).filter(TripStopItem.stop_id == s1)}
    res = client.post(f"{API}/stops/{s1}/checklist", headers=DRV1, json={
        "client_event_id": eid(), "base_row_version": 2,
        "lines": [{"item_id": items["P1"], "qty_delivered": 10}, {"item_id": items["P2"], "qty_delivered": 4}],
    })
    assert res.status_code == 200, res.text
    assert res.json()["new_row_version"] == 3

    intent = client.post(f"{API}/stops/{s1}/pod/photo-intent", headers=DRV1)
    assert intent.status_code == 200
    key = intent.json()["object_key"]
    assert key.startswith(f"pod/{s1}/")
    res = client.post(f"{API}/stops/{s1}/pod/photo-complete", headers=DRV1,
                      json={"client_event_id": eid(), "object_key": key})
    assert res.status_code == 200
    assert res.json()["pod"]["photo_url"] == key

    res = pod(client, db, s1)
    assert res.status_code == 200
    otp = res.json()["pod"]["otp_code"]
    assert len(otp) == 6 and otp.isdigit()
    assert res.json()["pod"]["pod_id"] == client.get(f"{API}/trips/{t1}", headers=DRV1).json()["stops"][0]["pod"]["pod_id"]

    res = outcome(client, db, s1, "delivered")
    assert res.status_code == 200, res.text
    assert res.json()["stop_status"] == "delivered"
    assert res.json()["return_id"] is None

    res = complete(client, t1)
    assert res.status_code == 200, res.text
    assert res.json()["trip_status"] == "completed"
    assert res.json()["unlocked_trip_id"] == t2

    trips = client.get(f"{API}/trips/today", headers=DRV1, params={"date": str(TODAY)}).json()["trips"]
    assert [t["locked"] for t in trips] == [False, False]
    assert depart(client, t2).status_code == 200


def test_invalid_state_transitions_are_rejected(client, db):
    trip_id, (s1, s2) = make_trip(db, stops=(("OUT1", {"P1": 5}), ("OUT2", {"P1": 3})))

    # Stop actions before departure.
    assert arrive(client, db, s1).status_code == 400
    assert depart(client, trip_id).status_code == 200
    assert depart(client, trip_id).status_code == 400  # already departed (new event id)

    res = client.post(f"{API}/stops/{s1}/checklist", headers=DRV1, json={
        "client_event_id": eid(), "base_row_version": 1, "lines": [{"item_id": "I-x", "qty_delivered": 5}]})
    assert res.status_code == 400  # before arrival
    assert outcome(client, db, s1, "delivered").status_code == 400  # before arrival
    assert complete(client, trip_id).status_code == 400  # stops still open

    assert arrive(client, db, s1).status_code == 200
    assert arrive(client, db, s1).status_code == 400  # second arrival, fresh version
    assert outcome(client, db, s1, "delivered").status_code == 400  # no POD yet
    assert pod(client, db, s1, order_id="ORD-of-someone-else").status_code == 400
    s2_order = db.query(TripStop).filter(TripStop.stop_id == s2).one().order_id
    assert pod(client, db, s1, order_id=s2_order).status_code == 400  # order of another stop
    res = client.post(f"{API}/stops/{s1}/pod/photo-complete", headers=DRV1,
                      json={"client_event_id": eid(), "object_key": f"pod/{s2}/stolen.jpg"})
    assert res.status_code == 400

    item = db.query(TripStopItem).filter(TripStopItem.stop_id == s1).one()
    res = client.post(f"{API}/stops/{s1}/checklist", headers=DRV1, json={
        "client_event_id": eid(), "base_row_version": stop_version(db, s1),
        "lines": [{"item_id": item.item_id, "qty_delivered": 4, "qty_returned": 0}]})
    assert res.status_code == 400 and "must equal" in res.json()["detail"]
    other_item = db.query(TripStopItem).filter(TripStopItem.stop_id == s2).one()
    res = client.post(f"{API}/stops/{s1}/checklist", headers=DRV1, json={
        "client_event_id": eid(), "base_row_version": stop_version(db, s1),
        "lines": [{"item_id": other_item.item_id, "qty_delivered": 3}]})
    assert res.status_code == 400

    assert outcome(client, db, s1, "partial").status_code == 400  # partial needs lines/checklist (and POD)
    assert outcome(client, db, s2, "failed").status_code == 400  # failed needs a reason


def test_partial_delivery_returns_and_depot_confirmation(client, db):
    trip_id, (stop_id,) = make_trip(db, loaded={"P1": 9})
    assert depart(client, trip_id).status_code == 200
    assert arrive(client, db, stop_id).status_code == 200
    assert pod(client, db, stop_id).status_code == 200
    items = {i.sku: i.item_id for i in db.query(TripStopItem).filter(TripStopItem.stop_id == stop_id)}

    res = outcome(client, db, stop_id, "partial", reason="damaged in transit", return_crate="R-04", lines=[
        {"item_id": items["P1"], "qty_delivered": 6, "qty_returned": 3},  # 9 on the van after loader shortfall
        {"item_id": items["P2"], "qty_delivered": 4},
    ])
    assert res.status_code == 200, res.text
    assert res.json()["stop_status"] == "delivered"
    return_id = res.json()["return_id"]
    assert return_id

    db.expire_all()
    p1 = db.query(TripStopItem).filter(TripStopItem.item_id == items["P1"]).one()
    assert (float(p1.qty_delivered), float(p1.qty_returned)) == (6, 3)
    record = db.query(ReturnCustody).filter(ReturnCustody.return_id == return_id).one()
    assert json.loads(record.items) == [{"item_id": items["P1"], "line_item_id": p1.line_item_id,
                                         "product_id": "P1", "qty": 3.0}]
    assert record.status == "pending" and record.driver_id == "U_DRV1"

    res = complete(client, trip_id)
    assert res.status_code == 400 and return_id in res.json()["detail"]

    confirm_body = {"client_event_id": eid(), "officer_name": "Kasun", "condition": "seal_intact"}
    # Driver 2's rejected attempt with the same client_event_id must not block driver 1.
    assert client.post(f"{API}/returns/{return_id}/depot-confirm", headers=DRV2, json=confirm_body).status_code == 404
    res = client.post(f"{API}/returns/{return_id}/depot-confirm", headers=DRV1, json=confirm_body)
    assert res.status_code == 200 and res.json()["return_status"] == "confirmed"
    res = client.post(f"{API}/returns/{return_id}/depot-confirm", headers=DRV1, json={**confirm_body, "client_event_id": eid()})
    assert res.status_code == 400  # already confirmed

    detail = client.get(f"{API}/trips/{trip_id}", headers=DRV1).json()
    assert detail["returns"][0]["status"] == "confirmed"
    assert detail["returns"][0]["officer_name"] == "Kasun"
    assert complete(client, trip_id).status_code == 200


def test_failed_delivery_skips_stop_and_returns_everything(client, db):
    trip_id, (stop_id,) = make_trip(db)
    assert depart(client, trip_id).status_code == 200
    res = outcome(client, db, stop_id, "failed", reason="outlet closed")
    assert res.status_code == 200, res.text
    assert res.json()["stop_status"] == "skipped"
    db.expire_all()
    stop = db.query(TripStop).filter(TripStop.stop_id == stop_id).one()
    assert stop.skip_reason == "outlet closed" and stop.completed_at is not None
    record = db.query(ReturnCustody).filter(ReturnCustody.return_id == res.json()["return_id"]).one()
    assert sorted(item["qty"] for item in json.loads(record.items)) == [4.0, 10.0]
    # A failed delivery cannot claim delivered units.
    trip2, (stop2,) = make_trip(db, vehicle_id="V2")
    assert depart(client, trip2).status_code == 200
    item = db.query(TripStopItem).filter(TripStopItem.stop_id == stop2, TripStopItem.sku == "P1").one()
    res = outcome(client, db, stop2, "failed", reason="x", lines=[{"item_id": item.item_id, "qty_delivered": 1}])
    assert res.status_code == 400


def test_explicit_return_after_delivery(client, db):
    trip_id, (stop_id,) = make_trip(db)
    assert depart(client, trip_id).status_code == 200
    deliver(client, db, stop_id)
    item = db.query(TripStopItem).filter(TripStopItem.stop_id == stop_id, TripStopItem.sku == "P2").one()

    body = {"client_event_id": eid(), "base_row_version": stop_version(db, stop_id),
            "items": [{"item_id": item.item_id, "qty": 5}], "reason": "rejected at door"}
    assert client.post(f"{API}/stops/{stop_id}/return", headers=DRV1, json=body).status_code == 400  # only 4 delivered

    body["items"][0]["qty"] = 2
    res = client.post(f"{API}/stops/{stop_id}/return", headers=DRV1, json=body)
    assert res.status_code == 200, res.text
    db.expire_all()
    item = db.query(TripStopItem).filter(TripStopItem.item_id == item.item_id).one()
    assert (float(item.qty_delivered), float(item.qty_returned)) == (2, 2)


# ═══════════════════════════════════════════════════════════════════════════
# Idempotency, offline sync, conflicts
# ═══════════════════════════════════════════════════════════════════════════

def test_rest_writes_are_idempotent(client, db):
    trip_id, (stop_id,) = make_trip(db)
    assert depart(client, trip_id).status_code == 200
    body = {"client_event_id": "arrive-once", "base_row_version": 1}
    first = client.post(f"{API}/stops/{stop_id}/arrive", headers=DRV1, json=body)
    second = client.post(f"{API}/stops/{stop_id}/arrive", headers=DRV1, json=body)
    assert first.json()["status"] == "applied"
    assert second.status_code == 200 and second.json()["status"] == "already_applied"
    assert second.json()["server_event_id"] == first.json()["server_event_id"]
    assert stop_version(db, stop_id) == 2

    # The legacy client_op_id name is accepted too.
    res = client.post(f"{API}/stops/{stop_id}/pod", headers=DRV1,
                      json={"client_op_id": "pod-once", "order_id": db.get(TripStop, stop_id).order_id})
    again = client.post(f"{API}/stops/{stop_id}/pod", headers=DRV1,
                        json={"client_op_id": "pod-once", "order_id": db.get(TripStop, stop_id).order_id})
    assert res.json()["status"] == "applied" and again.json()["status"] == "already_applied"

    # Another driver cannot reuse (or probe) someone else's client_event_id.
    trip2, (stop2,) = make_trip(db, driver_id="U_DRV2", vehicle_id="V2")
    res = client.post(f"{API}/trips/{trip2}/depart", headers=DRV2, json={"client_event_id": "arrive-once"})
    assert res.status_code == 409


def test_offline_sync_applies_batch_and_replay_is_safe(client, db):
    trip_id, (stop_id,) = make_trip(db)
    order_id = db.get(TripStop, stop_id).order_id
    events = [
        {"client_event_id": "e1", "kind": "trip.departed", "occurred_at": "2026-10-03T00:30:00Z",
         "payload": {"trip_id": trip_id}},
        {"client_event_id": "e2", "kind": "stop.arrived", "occurred_at": "2026-10-03T01:00:00Z",
         "payload": {"stop_id": stop_id, "base_row_version": 1}},
        {"client_event_id": "e3", "kind": "pod.submitted", "payload": {"stop_id": stop_id, "order_id": order_id}},
        {"client_event_id": "e4", "kind": "stop.outcome.submitted",
         "payload": {"stop_id": stop_id, "base_row_version": 2, "outcome": "delivered"}},
        {"client_event_id": "e5", "kind": "trip.completed", "payload": {"trip_id": trip_id}},
    ]
    res = client.post(f"{API}/events/sync", headers=DRV1, json={"device_id": "tab-7", "events": events})
    assert res.status_code == 200
    assert [r["status"] for r in res.json()["results"]] == ["applied"] * 5, res.json()

    db.expire_all()
    assert db.get(Trip, trip_id).status == "completed"
    stop = db.get(TripStop, stop_id)
    assert stop.status == "delivered" and stop.row_version == 3
    e2 = db.query(DriverEvent).filter(DriverEvent.client_event_id == "e2").one()
    assert (e2.device_id, e2.row_version_before, e2.row_version_after) == ("tab-7", 1, 2)
    from app.models import ProofOfDelivery
    assert db.query(ProofOfDelivery).filter(ProofOfDelivery.order_id == order_id).one().recorded_offline is True

    replay = client.post(f"{API}/events/sync", headers=DRV1, json={"device_id": "tab-7", "events": events})
    assert [r["status"] for r in replay.json()["results"]] == ["already_applied"] * 5
    assert stop_version(db, stop_id) == 3
    assert db.query(DriverEvent).count() == 5


def test_offline_sync_partial_batch_and_retry_of_failed_event(client, db):
    trip_id, (stop_id,) = make_trip(db)
    events = [
        {"client_event_id": "a1", "kind": "trip.departed", "payload": {"trip_id": trip_id}},
        {"client_event_id": "a2", "kind": "stop.teleported", "payload": {"stop_id": stop_id}},
        {"client_event_id": "a3", "kind": "stop.arrived", "payload": {"stop_id": stop_id}},  # missing version
        {"client_event_id": "a4", "kind": "stop.arrived", "payload": {"base_row_version": 1}},  # missing stop
        {"client_event_id": "a5", "kind": "stop.arrived", "payload": {"stop_id": stop_id, "base_row_version": 1}},
    ]
    results = client.post(f"{API}/events/sync", headers=DRV1, json={"events": events}).json()["results"]
    assert [r["status"] for r in results] == ["applied", "failed", "failed", "failed", "applied"]
    assert "Unknown event kind" in results[1]["error"]
    assert db.query(DriverEvent).filter(DriverEvent.client_event_id == "a3").one().status == "failed"

    # The device fixes the payload and retries the same client_event_id.
    retry = client.post(f"{API}/events/sync", headers=DRV1, json={"events": [
        {"client_event_id": "a3", "kind": "pod.submitted",
         "payload": {"stop_id": stop_id, "order_id": db.get(TripStop, stop_id).order_id}},
    ]}).json()["results"]
    assert retry[0]["status"] == "applied"
    db.expire_all()
    assert db.query(DriverEvent).filter(DriverEvent.client_event_id == "a3").one().status == "applied"


def test_stale_row_version_is_persisted_as_conflict(client, db):
    trip_id, (stop_id,) = make_trip(db)
    assert depart(client, trip_id).status_code == 200
    db.query(TripStop).filter(TripStop.stop_id == stop_id).update({"row_version": 5})  # e.g. dispatcher resequence
    db.commit()

    body = {"client_event_id": "stale-arrive", "base_row_version": 1}
    res = client.post(f"{API}/stops/{stop_id}/arrive", headers=DRV1, json=body)
    assert res.status_code == 409
    conflict_id = res.json()["conflict_id"]
    assert res.json()["status"] == "conflict"
    assert res.json()["system_record"]["row_version"] == 5

    db.expire_all()
    stop = db.get(TripStop, stop_id)
    assert stop.status == "upcoming" and stop.row_version == 5  # not applied
    conflict = db.get(Conflict, conflict_id)
    assert conflict.status == "in_review"
    assert json.loads(conflict.driver_json)["payload"]["base_row_version"] == 1
    assert db.get(DriverEvent, conflict.driver_event_id).status == "conflict"

    # Replaying the same event returns the same conflict, never applies it.
    again = client.post(f"{API}/stops/{stop_id}/arrive", headers=DRV1, json=body)
    assert again.status_code == 409 and again.json()["conflict_id"] == conflict_id

    listed = client.get(f"{API}/conflicts", headers=DRV1).json()
    assert [c["conflict_id"] for c in listed] == [conflict_id]
    assert listed[0]["kind"] == "stop.arrived" and listed[0]["trip_id"] == trip_id
    assert client.get(f"{API}/conflicts", headers=DRV2).json() == []


def _make_conflict(client, db, vehicle_id="V1"):
    trip_id, (stop_id,) = make_trip(db, vehicle_id=vehicle_id)
    assert depart(client, trip_id).status_code == 200
    db.query(TripStop).filter(TripStop.stop_id == stop_id).update({"row_version": 4})
    db.commit()
    res = client.post(f"{API}/events/sync", headers=DRV1, json={"events": [
        {"client_event_id": eid(), "kind": "stop.arrived", "payload": {"stop_id": stop_id, "base_row_version": 1}},
    ]})
    result = res.json()["results"][0]
    assert result["status"] == "conflict"
    return stop_id, result["conflict_id"]


def test_conflict_forward_and_resolve_accepting_driver_record(client, db):
    stop_id, conflict_id = _make_conflict(client, db)

    res = client.post(f"{API}/conflicts/{conflict_id}/forward", headers=DRV1, json={"note": "I was at the outlet"})
    assert res.status_code == 200 and res.json()["status"] == "forwarded"
    assert client.post(f"{API}/conflicts/{conflict_id}/forward", headers=DRV1).status_code == 400
    assert client.post(f"{API}/conflicts/{conflict_id}/forward", headers=DRV2).status_code == 404

    resolve = {"resolution": "accept_driver", "note": "GPS confirms arrival"}
    assert client.post(f"{API}/conflicts/{conflict_id}/resolve", headers=DRV1, json=resolve).status_code == 403
    assert client.post(f"{API}/conflicts/{conflict_id}/resolve", headers=DISP2, json=resolve).status_code == 404
    res = client.post(f"{API}/conflicts/{conflict_id}/resolve", headers=DISP, json=resolve)
    assert res.status_code == 200, res.text
    assert res.json()["conflict"]["status"] == "resolved"
    assert res.json()["applied"]["status"] == "applied"

    db.expire_all()
    stop = db.get(TripStop, stop_id)
    assert stop.status == "arrived" and stop.row_version == 5
    conflict = db.get(Conflict, conflict_id)
    assert (conflict.resolution, conflict.resolved_by, conflict.resolved_by_role) == ("accept_driver", "U_DISP", "dispatcher")
    assert client.post(f"{API}/conflicts/{conflict_id}/resolve", headers=DISP, json=resolve).status_code == 400


def test_conflict_keep_server_and_dismiss(client, db):
    stop_id, keep_id = _make_conflict(client, db)
    res = client.post(f"{API}/conflicts/{keep_id}/resolve", headers=DISP, json={"resolution": "keep_server"})
    assert res.status_code == 200 and res.json()["conflict"]["status"] == "resolved"
    assert res.json()["applied"] is None
    db.expire_all()
    assert db.get(TripStop, stop_id).status == "upcoming"

    _, dismiss_id = _make_conflict(client, db, vehicle_id="V2")
    res = client.post(f"{API}/conflicts/{dismiss_id}/resolve", headers=DISP, json={"resolution": "dismiss"})
    assert res.json()["conflict"]["status"] == "dismissed"


# ═══════════════════════════════════════════════════════════════════════════
# Dispatcher integration
# ═══════════════════════════════════════════════════════════════════════════

def test_route_change_retrieval_acknowledgement_and_resequence(client, db):
    trip_id, (s1, s2) = make_trip(db, stops=(("OUT1", {"P1": 1}), ("OUT2", {"P1": 1})))
    assert depart(client, trip_id).status_code == 200

    res = client.post(f"/api/v1/dispatcher/trips/{trip_id}/route-changes", headers=DISP, json={
        "change_type": "route.resequenced", "payload": {"new_sequence": [s2, s1]}})
    assert res.status_code == 200, res.text  # out_for_delivery trips accept route changes
    change_id = res.json()["change_id"]

    changes = client.get(f"{API}/changes", headers=DRV1, params={"pending_only": True}).json()
    assert [c["change_id"] for c in changes["changes"]] == [change_id]
    assert changes["changes"][0]["payload"] == {"new_sequence": [s2, s1]}
    assert client.get(f"{API}/changes", headers=DRV2).json()["changes"] == []
    later = client.get(f"{API}/changes", headers=DRV1, params={"since": changes["next_cursor"]}).json()
    assert later["changes"] == []

    assert client.post(f"{API}/changes/{change_id}/ack", headers=DRV2).status_code == 404
    res = client.post(f"{API}/changes/{change_id}/ack", headers=DRV1)
    assert res.status_code == 200 and res.json()["status"] == "applied"
    assert client.post(f"{API}/changes/{change_id}/ack", headers=DRV1).json()["status"] == "already_applied"
    res = client.post(f"{API}/changes/{change_id}/ack", headers=DRV1, json={"client_event_id": eid()})
    assert res.json()["status"] == "already_applied"

    db.expire_all()
    assert db.get(TripStop, s2).stop_seq == 1 and db.get(TripStop, s1).stop_seq == 2
    assert db.get(TripStop, s2).row_version == 2  # offline edits made on the old order now conflict
    assert db.query(Order).filter(Order.order_id == db.get(TripStop, s2).order_id).one().stop_seq == 1
    assert client.get(f"{API}/changes", headers=DRV1, params={"pending_only": True}).json()["changes"] == []

    seen = client.get(f"/api/v1/dispatcher/trips/{trip_id}/route-changes", headers=DISP).json()
    assert seen[0]["acknowledged"] is True and seen[0]["ack_at"]


def test_dispatcher_assigns_driver(client, db):
    trip_id, _ = make_trip(db, driver_id=None, status="planned")
    url = f"/api/v1/dispatcher/trips/{trip_id}/assign-driver"
    assert client.get(f"{API}/trips/{trip_id}", headers=DRV1).status_code == 404
    assert client.post(url, headers=DISP2, json={"driver_id": "U_DRV1"}).status_code == 404
    assert client.post(url, headers=DISP, json={"driver_id": "U_LOAD"}).status_code == 404
    assert client.post(url, headers=DRV1, json={"driver_id": "U_DRV1"}).status_code == 403
    res = client.post(url, headers=DISP, json={"driver_id": "U_DRV1"})
    assert res.status_code == 200 and res.json()["driver_id"] == "U_DRV1"
    assert client.get(f"{API}/trips/{trip_id}", headers=DRV1).status_code == 200

    clash_trip, _ = make_trip(db, driver_id=None, status="planned", vehicle_id="V2")
    res = client.post(f"/api/v1/dispatcher/trips/{clash_trip}/assign-driver", headers=DISP, json={"driver_id": "U_DRV1"})
    assert res.status_code == 409  # driver already has trip 1 that day

    gone, _ = make_trip(db, status="out_for_delivery", trip_no=2)
    res = client.post(f"/api/v1/dispatcher/trips/{gone}/assign-driver", headers=DISP, json={"driver_id": "U_DRV2"})
    assert res.status_code == 400


def test_dispatcher_timeline_shows_driver_events(client, db):
    trip_id, (stop_id,) = make_trip(db)
    assert depart(client, trip_id).status_code == 200
    assert arrive(client, db, stop_id).status_code == 200
    res = client.get("/api/v1/dispatcher/timeline", headers=DISP, params={"trip_id": trip_id})
    assert res.status_code == 200, res.text
    assert [e["kind"] for e in res.json()] == ["stop.arrived", "trip.departed"]
    assert res.json()[0]["status"] == "applied" and res.json()[0]["driver_id"] == "U_DRV1"
