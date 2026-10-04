import os
os.environ["DATABASE_URL"] = "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint"

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

db_url = "postgresql://postgres:postgres@localhost:5432/waypoint"

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

def test_golden_e2e(client, pg_conn):
    cursor = pg_conn.cursor()
    
    # 1. Setup E2E data using raw psycopg2
    cursor.execute("INSERT INTO depot (depot_id, name, lat, lng) VALUES ('DEP-E2E', 'E2E Depot', 0, 0) ON CONFLICT DO NOTHING;")
    cursor.execute("INSERT INTO outlet (outlet_id, depot_id, brand, name, lat, lng) VALUES ('OUT-999', 'DEP-E2E', 'fresh', 'E2E Outlet', 0, 0) ON CONFLICT DO NOTHING;")
    cursor.execute("INSERT INTO vehicle (vehicle_id, depot_id, type, temp, weight_cap_kg, vol_cap_m3, status) VALUES ('VEH-999', 'DEP-E2E', 'truck', 'reefer', 1000, 10, 'available') ON CONFLICT DO NOTHING;")
    
    # We need a product
    cursor.execute("INSERT INTO product (product_id, brand, temp_req, name, unit, unit_wt_kg, unit_vol_m3, active) VALUES ('PROD-E2E', 'fresh', 'reefer', 'E2E Product', 'EA', 1, 0.1, true) ON CONFLICT DO NOTHING;")

    # Password hash for 'pass' is generated here
    from app.core.security import get_password_hash
    pw_hash = get_password_hash("pass")
    cursor.execute(f"INSERT INTO \"user\" (user_id, username, hashed_pw, role, depot_id, outlet_id, name) VALUES ('U-E2E-SM', 'sm999', '{pw_hash}', 'store_manager', NULL, 'OUT-999', 'SM') ON CONFLICT (user_id) DO UPDATE SET hashed_pw='{pw_hash}';")
    cursor.execute(f"INSERT INTO \"user\" (user_id, username, hashed_pw, role, depot_id, outlet_id, name) VALUES ('U-E2E-DISP', 'disp999', '{pw_hash}', 'dispatcher', 'DEP-E2E', NULL, 'Disp') ON CONFLICT (user_id) DO UPDATE SET hashed_pw='{pw_hash}';")
    cursor.execute(f"INSERT INTO \"user\" (user_id, username, hashed_pw, role, depot_id, outlet_id, name) VALUES ('U-E2E-LOAD', 'load999', '{pw_hash}', 'loader', 'DEP-E2E', NULL, 'Load') ON CONFLICT (user_id) DO UPDATE SET hashed_pw='{pw_hash}';")
    cursor.execute(f"INSERT INTO \"user\" (user_id, username, hashed_pw, role, depot_id, outlet_id, name) VALUES ('U-E2E-DRIV', 'driv999', '{pw_hash}', 'driver', 'DEP-E2E', NULL, 'Driv') ON CONFLICT (user_id) DO UPDATE SET hashed_pw='{pw_hash}';")
    
    # 2. Authentication
    sm_token = get_token(client, "sm999")
    disp_token = get_token(client, "disp999")
    load_token = get_token(client, "load999")
    driv_token = get_token(client, "driv999")
    
    # 3. Store Manager Creates Order
    order_date = str(date.today())
    res = client.post("/api/v1/store-manager/orders", headers={"Authorization": f"Bearer {sm_token}"}, json={
        "outlet_id": "OUT-999",
        "brand": "fresh",
        "temp_req": "reefer",
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
    trip = next(t for t in trips if any(s["outlet_id"] == "OUT-999" for s in t["stops"]))
    trip_id = trip["trip_id"]
    stop_id = trip["stops"][0]["stop_id"]
    
    # Dispatcher assigns driver to the trip
    res = client.post(f"/api/v1/dispatcher/trips/{trip_id}/assign-driver", headers={"Authorization": f"Bearer {disp_token}"}, json={"driver_id": "U-E2E-DRIV"})
    assert res.status_code == 200, res.text

    # 5. Loader workflow
    res = client.post(f"/api/v1/loader/trips/{trip_id}/start", headers={"Authorization": f"Bearer {load_token}"})
    assert res.status_code == 200, res.text
    
    # Complete stop for loading
    res = client.post(f"/api/v1/loader/trips/{trip_id}/complete-stop/{stop_id}", headers={"Authorization": f"Bearer {load_token}"})
    assert res.status_code == 200, res.text
    
    # Submit load
    res = client.post(f"/api/v1/loader/trips/{trip_id}/load", headers={"Authorization": f"Bearer {load_token}"}, json={
        "vehicle_id": "VEH-999",
        "seal_no": "SEAL-001"
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
            "payload": {"stop_id": stop_id, "delivered_at": datetime.now().isoformat(), "base_row_version": 2, "pin": "0000", "items": []}
        }]
    })
    assert res.status_code == 200, res.text
    
    # Submit outcome
    res = client.post("/api/v1/driver-platform/events/sync", headers={"Authorization": f"Bearer {driv_token}"}, json={
        "events": [{
            "kind": "stop.outcome.submitted",
            "client_event_id": "e2e-outcome-1",
            "payload": {"stop_id": stop_id, "finished_at": datetime.now().isoformat(), "base_row_version": 3}
        }]
    })
    assert res.status_code == 200, res.text
    
    # Complete trip
    res = client.post("/api/v1/driver-platform/events/sync", headers={"Authorization": f"Bearer {driv_token}"}, json={
        "events": [{
            "kind": "trip.completed",
            "client_event_id": "e2e-complete-1",
            "payload": {"trip_id": trip_id, "returned_at": datetime.now().isoformat(), "base_row_version": 3}
        }]
    })
    assert res.status_code == 200, res.text
    
    # 7. Final assertion using psycopg
    cursor.execute(f"SELECT status FROM orders WHERE order_id = '{order_id}';")
    final_status = cursor.fetchone()[0]
    assert final_status == 'delivered', f"Order status is {final_status}, expected 'delivered'"
