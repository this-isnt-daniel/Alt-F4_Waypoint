import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timezone
from app.main import app

# We use the test client. To mock authentication, we need to bypass or mock the JWT.
from app.core.security import create_platform_access_token # just in case
from app.models.user import User
from app.models.order import Order
from app.db.session import get_db

@pytest.fixture
def override_db():
    # Setup test DB (borrowed from Phase 2 test setup)
    from sqlalchemy import create_engine, StaticPool
    from sqlalchemy.orm import sessionmaker
    from app.db.base import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # Seed users and products
    from app.core.security import get_password_hash
    from app.models.product import Product
    from app.models.depot import Depot
    from app.models.outlet import Outlet
    from app.models.vehicle import Vehicle
    from app.models.order import Order
    
    depots = [Depot(depot_id="DEP1", name="Test Depot", lat=0.0, lng=0.0)]
    db.add_all(depots)
    
    outlets = [
        Outlet(outlet_id="OUT1", name="Test Outlet", brand="fresh", lat=0.0, lng=0.0)
    ]
    db.add_all(outlets)
    
    vehicles = [Vehicle(vehicle_id="V1", depot_id="DEP1", type="truck", temp="ambient", vol_cap_m3=10.0, weight_cap_kg=1000.0, plate="TEST", status="available")]
    db.add_all(vehicles)
    
    users = [
        User(user_id="U1", name="Manager One", username="manager1", hashed_pw=get_password_hash("pass"), role="store_manager", outlet_id="OUT1"),
        User(user_id="U2", name="Dispatcher One", username="disp1", hashed_pw=get_password_hash("pass"), role="dispatcher", depot_id="DEP1"),
        User(user_id="U3", name="Loader One", username="loader1", hashed_pw=get_password_hash("pass"), role="loader", depot_id="DEP1"),
        User(user_id="U4", name="Driver One", username="driver1", hashed_pw=get_password_hash("pass"), role="driver")
    ]
    db.add_all(users)
    
    products = [
        Product(product_id="P1", name="Product 1", brand="fresh", temp_req="ambient", unit="EA", unit_wt_kg=1.0, unit_vol_m3=0.1)
    ]
    db.add_all(products)
    
    db.commit()
    
    def _override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = _override_get_db
    yield db
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    db.close()

@pytest.fixture
def client(override_db):
    return TestClient(app)

def get_token(client, username):
    res = client.post("/api/v1/auth/login", json={"username": username, "password": "pass"})
    return res.json()["access_token"]

def test_integration_flow(client, override_db):
    sm_token = get_token(client, "manager1")
    disp_token = get_token(client, "disp1")
    loader_token = get_token(client, "loader1")
    driver_token = get_token(client, "driver1")
    
    # FLOW 1: Store Manager creates draft
    sm_headers = {"Authorization": f"Bearer {sm_token}"}
    res = client.post("/api/v1/store-manager/orders", headers=sm_headers, json={
        "outlet_id": "OUT1",
        "brand": "fresh",
        "temp_req": "ambient",
        "order_date": str(date.today()),
        "items": [{"product_id": "P1", "quantity": 10}]
    })
    assert res.status_code == 200
    order = res.json()
    assert order["status"] == "draft"
    order_id = order["order_id"]
    
    # FLOW 2: Store Manager confirms
    res = client.post(f"/api/v1/store-manager/orders/{order_id}/confirm", headers=sm_headers)
    assert res.status_code == 200
    order = res.json()
    assert order["status"] == "confirmed"
    assert order["order_units"] == 10
    
    timeline_res = client.get(f"/api/v1/orders/{order_id}/timeline", headers=sm_headers)
    assert any(e["event_type"] == "order_confirmed" for e in timeline_res.json())
    
    # FLOW 3: Dispatcher plans
    disp_headers = {"Authorization": f"Bearer {disp_token}"}
    # Create plan
    plan_res = client.post("/api/v1/dispatcher/planning/optimize", headers=disp_headers, json={
        "depot_id": "DEP1",
        "target_date": str(date.today()),
    })
    assert plan_res.status_code == 200
    # The mock returns empty trips. For this test to proceed, we must mock the service return directly
    # because the optimizer is mocked. Let's just create a mock trip directly using the DB, or just assert the boundary works.
    run_id = plan_res.json()["run_id"]
    
    # Let's inject a trip into the mock planning run so confirm_plan works
    from app.services.planning_service import _mock_planning_runs
    _mock_planning_runs[run_id].trips = [
        type("Obj", (object,), {"vehicle_id": "V1", "brand": "fresh", "temp_type": "ambient", "stops": [
            type("Stop", (object,), {"order_id": order_id, "sequence": 1, "expected_arrival": "10:00"})
        ]})
    ]
    
    res = client.post(f"/api/v1/dispatcher/planning/runs/{run_id}/confirm", headers=disp_headers, json={"client_op_id": "plan1"})
    assert res.status_code == 200
    
    # Verify order is planned
    order_db = override_db.query(Order).filter(Order.order_id == order_id).first()
    assert order_db.status == "planned"
    trip_id = order_db.trip_id
    assert trip_id is not None
    
    # FLOW 4: Loader loads
    load_headers = {"Authorization": f"Bearer {loader_token}"}
    res = client.post(f"/api/v1/loader/trips/{trip_id}/load", headers=load_headers, json={
        "client_op_id": "load1",
        "items": [
            {"product_id": "P1", "expected_qty": 10, "loaded_qty": 10, "status": "ok"}
        ]
    })
    assert res.status_code == 200
    
    override_db.refresh(order_db)
    assert order_db.status == "loaded"
    
    # FLOW 5: Driver departs
    driver_headers = {"Authorization": f"Bearer {driver_token}"}
    res = client.post(f"/api/v1/driver-platform/trips/{trip_id}/depart", headers=driver_headers, json={
        "client_op_id": "dep1",
        "departed_at": datetime.now(timezone.utc).isoformat()
    })
    assert res.status_code == 200
    
    override_db.refresh(order_db)
    assert order_db.status == "out_for_delivery"
    
    # FLOW 6: Driver POD
    # Get stop ID
    from app.models.trip import TripStop
    stop = override_db.query(TripStop).filter(TripStop.trip_id == trip_id).first()
    
    res = client.post(f"/api/v1/driver-platform/stops/{stop.stop_id}/pod", headers=driver_headers, json={
        "client_op_id": "pod1",
        "order_id": order_id,
        "delivered_at": datetime.now(timezone.utc).isoformat()
    })
    assert res.status_code == 200
    
    override_db.refresh(order_db)
    assert order_db.status == "out_for_delivery" # POD doesn't transition order to delivered
    
    # FLOW 7: Store Manager confirms receipt
    res = client.post(f"/api/v1/store-manager/orders/{order_id}/receipt", headers=sm_headers, json={
        "client_op_id": "rec1",
        "pod_id": res.json()["pod_id"],
        "items_ok": True
    })
    assert res.status_code == 200
    
    override_db.refresh(order_db)
    assert order_db.status == "delivered"
    
    # FLOW 11: Unauthorized role (Loader trying to plan)
    res = client.post("/api/v1/dispatcher/planning/optimize", headers=load_headers, json={
        "depot_id": "DEP1",
        "target_date": str(date.today()),
    })
    assert res.status_code == 403
    
    # FLOW 13: Concurrency / Idempotency
    # Retry receipt confirmation with same client_op_id
    res = client.post(f"/api/v1/store-manager/orders/{order_id}/receipt", headers=sm_headers, json={
        "client_op_id": "rec1",
        "pod_id": "fake",
        "items_ok": True
    })
    assert res.status_code == 200 # Returns existing without failing
