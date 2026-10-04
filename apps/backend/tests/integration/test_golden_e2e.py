import os
import pytest
import psycopg2
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.adapters.optimizer_adapter import get_reference_data

try:
    get_reference_data()
except FileNotFoundError:
    pytest.skip("Reference data missing, skipping module", allow_module_level=True)

raw_url = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint_test")
db_url = raw_url.replace("postgresql+psycopg2://", "postgresql://")


@pytest.fixture(scope="module")
def pg_conn():
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    yield conn
    conn.close()

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def get_token(client, username):
    res = client.post("/api/v1/auth/login", json={"username": username, "password": "pass"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]

def _cleanup_e2e_data(cursor):
    e2e_orders = "SELECT order_id FROM \"order\" WHERE created_by = 'U-E2E-SM'"
    e2e_trips = "SELECT trip_id FROM trip WHERE dispatcher_id = 'U-E2E-DISP' OR driver_id = 'U-E2E-DRIV'"
    e2e_stops = f"SELECT stop_id FROM trip_stop WHERE trip_id IN ({e2e_trips}) OR order_id IN ({e2e_orders})"
    e2e_checks = f"SELECT check_id FROM load_check WHERE trip_id IN ({e2e_trips})"

    cursor.execute("DELETE FROM driver_events WHERE driver_id = 'U-E2E-DRIV';")
    cursor.execute(f"DELETE FROM delivery_event WHERE order_id IN ({e2e_orders}) OR actor_id IN ('U-E2E-SM', 'U-E2E-DISP', 'U-E2E-LOAD', 'U-E2E-DRIV');")
    cursor.execute(f"DELETE FROM discrepancy WHERE raised_by IN ('U-E2E-SM', 'U-E2E-DISP', 'U-E2E-LOAD', 'U-E2E-DRIV') OR order_id IN ({e2e_orders});")
    cursor.execute(f"DELETE FROM receipt_confirmation WHERE order_id IN ({e2e_orders}) OR confirmed_by IN ('U-E2E-SM', 'U-E2E-DISP', 'U-E2E-LOAD', 'U-E2E-DRIV');")
    cursor.execute(f"DELETE FROM proof_of_delivery WHERE order_id IN ({e2e_orders}) OR delivered_by = 'U-E2E-DRIV' OR stop_id IN ({e2e_stops});")
    cursor.execute(f"DELETE FROM load_check_item WHERE check_id IN ({e2e_checks}) OR line_item_id IN (SELECT line_item_id FROM order_line WHERE order_id IN ({e2e_orders}));")
    cursor.execute(f"DELETE FROM load_check WHERE trip_id IN ({e2e_trips}) OR checked_by = 'U-E2E-LOAD';")
    cursor.execute(f"DELETE FROM trip_stop_item WHERE stop_id IN ({e2e_stops});")
    cursor.execute(f"DELETE FROM trip_stop WHERE trip_id IN ({e2e_trips}) OR order_id IN ({e2e_orders});")
    cursor.execute(f"DELETE FROM deferral WHERE order_id IN ({e2e_orders}) OR created_by = 'U-E2E-DISP';")
    cursor.execute(f"DELETE FROM order_line WHERE order_id IN ({e2e_orders}) OR product_id = 'PROD-E2E';")
    cursor.execute(f"DELETE FROM \"order\" WHERE created_by = 'U-E2E-SM';")
    cursor.execute(f"DELETE FROM trip WHERE dispatcher_id = 'U-E2E-DISP' OR driver_id = 'U-E2E-DRIV';")
    cursor.execute("DELETE FROM draft_plan WHERE created_by = 'U-E2E-DISP' OR approved_by = 'U-E2E-DISP';")

def test_golden_e2e(client, pg_conn):
    cursor = pg_conn.cursor()
    order_date = str(date.today())

    # 0. Narrowly clean up prior E2E runs without deleting broad canonical data
    _cleanup_e2e_data(cursor)

    # 1. Setup E2E data using raw psycopg2
    cursor.execute("INSERT INTO depot (depot_id, name, lat, lng) VALUES ('Peliyagoda', 'Peliyagoda Central', 6.96, 79.88) ON CONFLICT DO NOTHING;")
    cursor.execute("INSERT INTO outlet (outlet_id, depot_id, brand, name, lat, lng, dock_type, park_constraint, window_open, window_close) VALUES ('OUT001', 'Peliyagoda', 'fresh', 'Colpetty Fresh', 6.96, 79.88, 'street', 'van_only', '05:00', '07:30') ON CONFLICT DO NOTHING;")
    cursor.execute("INSERT INTO vehicle (vehicle_id, depot_id, type, temp, weight_cap_kg, vol_cap_m3, status) VALUES ('VEH035', 'Peliyagoda', 'van', 'reefer', 1040, 7.0, 'available') ON CONFLICT (vehicle_id) DO UPDATE SET status='available';")
    
    # We need a product with temp_req="chilled"
    cursor.execute("INSERT INTO product (product_id, brand, temp_req, name, unit, unit_wt_kg, unit_vol_m3, active) VALUES ('PROD-E2E', 'fresh', 'chilled', 'E2E Product', 'EA', 1, 0.1, true) ON CONFLICT (product_id) DO UPDATE SET temp_req='chilled';")

    # Password hash for 'pass' is generated here
    from app.core.security import get_password_hash
    pw_hash = get_password_hash("pass")
    cursor.execute(f"INSERT INTO \"user\" (user_id, username, hashed_pw, role, depot_id, outlet_id, name) VALUES ('U-E2E-SM', 'sm999', '{pw_hash}', 'store_manager', NULL, 'OUT001', 'SM') ON CONFLICT (user_id) DO UPDATE SET hashed_pw='{pw_hash}', outlet_id='OUT001';")
    cursor.execute(f"INSERT INTO \"user\" (user_id, username, hashed_pw, role, depot_id, outlet_id, name) VALUES ('U-E2E-DISP', 'disp999', '{pw_hash}', 'dispatcher', 'Peliyagoda', NULL, 'Disp') ON CONFLICT (user_id) DO UPDATE SET hashed_pw='{pw_hash}', depot_id='Peliyagoda';")
    cursor.execute(f"INSERT INTO \"user\" (user_id, username, hashed_pw, role, depot_id, outlet_id, name) VALUES ('U-E2E-LOAD', 'load999', '{pw_hash}', 'loader', 'Peliyagoda', NULL, 'Load') ON CONFLICT (user_id) DO UPDATE SET hashed_pw='{pw_hash}', depot_id='Peliyagoda';")
    cursor.execute(f"INSERT INTO \"user\" (user_id, username, hashed_pw, role, depot_id, outlet_id, name) VALUES ('U-E2E-DRIV', 'driv999', '{pw_hash}', 'driver', 'Peliyagoda', NULL, 'Driv') ON CONFLICT (user_id) DO UPDATE SET hashed_pw='{pw_hash}', depot_id='Peliyagoda';")
    
    # 2. Authentication
    sm_token = get_token(client, "sm999")
    disp_token = get_token(client, "disp999")
    load_token = get_token(client, "load999")
    driv_token = get_token(client, "driv999")
    
    # 3. Store Manager Creates Order with temp_req="chilled"
    order_date = str(date.today())
    res = client.post("/api/v1/store-manager/orders", headers={"Authorization": f"Bearer {sm_token}"}, json={
        "outlet_id": "OUT001",
        "brand": "fresh",
        "temp_req": "chilled",
        "order_date": order_date,
        "items": [{"product_id": "PROD-E2E", "quantity": 10}]
    })
    assert res.status_code == 200, res.text
    order_id = res.json()["order_id"]
    
    # Store Manager Confirms Order
    res = client.post(f"/api/v1/store-manager/orders/{order_id}/confirm", headers={"Authorization": f"Bearer {sm_token}"})
    assert res.status_code == 200, res.text
    
    # 4. Dispatcher runs optimization
    res = client.post("/api/v1/dispatcher/plans/draft", headers={"Authorization": f"Bearer {disp_token}"}, json={
        "target_date": order_date
    })
    assert res.status_code == 200, res.text
    draft_plan = res.json()
    plan_id = draft_plan.get("plan_id") or draft_plan.get("run_id")
    assert plan_id, "Missing plan_id"
    
    # Dispatcher Approves Plan
    res = client.post(f"/api/v1/dispatcher/plans/{plan_id}/approve", headers={"Authorization": f"Bearer {disp_token}"}, json={})
    assert res.status_code == 200, res.text
    
    # Fetch active trips to get trip ID
    res = client.get("/api/v1/dispatcher/trips/active", headers={"Authorization": f"Bearer {disp_token}"})
    assert res.status_code == 200, res.text
    trips = res.json()
    trip = next(t for t in trips if any(s["outlet_id"] == "OUT001" for s in t["stops"]))
    trip_id = trip["trip_id"]
    stop_id = trip["stops"][0]["stop_id"]
    
    # Dispatcher assigns driver to the trip
    res = client.post(f"/api/v1/dispatcher/trips/{trip_id}/assign-driver", headers={"Authorization": f"Bearer {disp_token}"}, json={"driver_id": "U-E2E-DRIV"})
    assert res.status_code == 200, res.text

    # 5. Loader workflow
    res = client.post(f"/api/v1/loader/trips/{trip_id}/start", headers={"Authorization": f"Bearer {load_token}"})
    assert res.status_code == 200, res.text
    
    # Verify items in workbench
    res = client.get(f"/api/v1/loader/trips/{trip_id}/workbench", headers={"Authorization": f"Bearer {load_token}"})
    assert res.status_code == 200, res.text
    wb = res.json()
    items_to_submit = []
    for s in wb.get("stops", []):
        for it in s.get("items", []):
            res = client.patch(
                f"/api/v1/loader/trips/{trip_id}/items/{it['line_item_id']}",
                headers={"Authorization": f"Bearer {load_token}"},
                json={"loaded_qty": it["assigned_qty"], "status": "verified"}
            )
            assert res.status_code == 200, res.text
            items_to_submit.append({"line_item_id": it["line_item_id"], "loaded_qty": it["assigned_qty"], "status": "verified"})

    # Complete stop for loading
    res = client.post(f"/api/v1/loader/trips/{trip_id}/complete-stop/{stop_id}", headers={"Authorization": f"Bearer {load_token}"})
    assert res.status_code == 200, res.text
    
    # Submit load
    res = client.post(f"/api/v1/loader/trips/{trip_id}/load", headers={"Authorization": f"Bearer {load_token}"}, json={
        "client_op_id": "e2e-load-1",
        "items": items_to_submit
    })
    assert res.status_code == 200, res.text
    
    # 6. Driver workflow
    # Depart trip
    res = client.post("/api/v1/driver-platform/events/sync", headers={"Authorization": f"Bearer {driv_token}"}, json={
        "events": [{
            "kind": "trip.departed",
            "client_event_id": "e2e-depart-1",
            "payload": {"trip_id": trip_id, "departed_at": datetime.now().isoformat(), "base_row_version": 1}
        }]
    })
    assert res.status_code == 200, res.text
    
    # Arrive stop
    res = client.post("/api/v1/driver-platform/events/sync", headers={"Authorization": f"Bearer {driv_token}"}, json={
        "events": [{
            "kind": "stop.arrived",
            "client_event_id": "e2e-arrive-1",
            "payload": {"stop_id": stop_id, "arrived_at": datetime.now().isoformat(), "base_row_version": 1, "lat": 0, "lng": 0}
        }]
    })
    assert res.status_code == 200, res.text
    
    # Submit POD
    res = client.post("/api/v1/driver-platform/events/sync", headers={"Authorization": f"Bearer {driv_token}"}, json={
        "events": [{
            "kind": "pod.submitted",
            "client_event_id": "e2e-pod-1",
            "payload": {"stop_id": stop_id, "order_id": order_id, "delivered_at": datetime.now().isoformat()}
        }]
    })
    assert res.status_code == 200, res.text
    assert res.json()["results"][0]["status"] == "applied", res.json()
    
    # Submit outcome
    res = client.post("/api/v1/driver-platform/events/sync", headers={"Authorization": f"Bearer {driv_token}"}, json={
        "events": [{
            "kind": "stop.outcome.submitted",
            "client_event_id": "e2e-outcome-1",
            "payload": {"stop_id": stop_id, "finished_at": datetime.now().isoformat(), "base_row_version": 2, "outcome": "delivered"}
        }]
    })
    assert res.status_code == 200, res.text
    assert res.json()["results"][0]["status"] == "applied", res.json()
    
    # Complete trip
    res = client.post("/api/v1/driver-platform/events/sync", headers={"Authorization": f"Bearer {driv_token}"}, json={
        "events": [{
            "kind": "trip.completed",
            "client_event_id": "e2e-complete-1",
            "payload": {"trip_id": trip_id, "returned_at": datetime.now().isoformat()}
        }]
    })
    assert res.status_code == 200, res.text
    assert res.json()["results"][0]["status"] == "applied", res.json()
    
    # 7. Final assertion using psycopg
    cursor.execute(f"SELECT status FROM \"order\" WHERE order_id = '{order_id}';")
    final_status = cursor.fetchone()[0]
    assert final_status == 'delivered', f"Order status is {final_status}, expected 'delivered'"
