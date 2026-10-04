from receipt_fixture import record_delivery
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timezone, timedelta
import uuid

from app.main import app
from app.db.session import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.product import Product
from app.models.depot import Depot
from app.models.outlet import Outlet
from app.models.order import Order, OrderLine
from app.models.deferral import Deferral


@pytest.fixture
def store_manager_db():
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
    
    # Seed data
    depot = Depot(depot_id="DEP100", name="Peliyagoda Central", lat=6.95, lng=79.88)
    db.add(depot)
    
    outlet1 = Outlet(
        outlet_id="OUT100",
        name="Fresh Colombo 01",
        brand="fresh",
        district="Colombo",
        depot_id="DEP100",
        window_open="03:30",
        window_close="08:00",
        dock_type="rear_dock",
        park_constraint="normal"
    )
    outlet2 = Outlet(
        outlet_id="OUT200",
        name="Style Kandy 01",
        brand="style",
        district="Kandy",
        depot_id="DEP100",
        window_open="08:00",
        window_close="18:00",
        dock_type="street",
        park_constraint="van_only"
    )
    db.add_all([outlet1, outlet2])
    
    sm_user1 = User(
        user_id="U100",
        name="Store Manager 1",
        username="sm1",
        hashed_pw=get_password_hash("password123"),
        role="store_manager",
        outlet_id="OUT100"
    )
    sm_user2 = User(
        user_id="U200",
        name="Store Manager 2",
        username="sm2",
        hashed_pw=get_password_hash("password123"),
        role="store_manager",
        outlet_id="OUT200"
    )
    db.add_all([sm_user1, sm_user2])
    
    p1 = Product(product_id="P100", name="Fresh Milk 1L", brand="fresh", temp_req="chilled", unit="CTN", unit_wt_kg=1.2, unit_vol_m3=0.002, active=True)
    p2 = Product(product_id="P200", name="Dry Biscuits Pack", brand="fresh", temp_req="ambient", unit="BOX", unit_wt_kg=0.5, unit_vol_m3=0.001, active=True)
    p3 = Product(product_id="P300", name="Denim Jeans", brand="style", temp_req="ambient", unit="EA", unit_wt_kg=0.8, unit_vol_m3=0.003, active=True)
    db.add_all([p1, p2, p3])
    
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
def client(store_manager_db):
    return TestClient(app)


def get_auth_header(client, username, password="password123"):
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.json()}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_confirm_order(client, store_manager_db):
    headers = get_auth_header(client, "sm1")
    
    # 1. Create draft order
    create_payload = {
        "outlet_id": "OUT100",
        "brand": "fresh",
        "temp_req": "chilled",
        "order_date": str(date.today() + timedelta(days=7)),
        "items": [
            {"product_id": "P100", "quantity": 50},
            {"product_id": "P200", "quantity": 20}
        ]
    }
    res = client.post("/api/v1/store-manager/orders", headers=headers, json=create_payload)
    assert res.status_code == 200, res.json()
    order_data = res.json()
    assert order_data["status"] == "draft"
    assert order_data["outlet_id"] == "OUT100"
    assert len(order_data["items"]) == 2
    order_id = order_data["order_id"]
    
    # 2. Confirm order
    confirm_res = client.post(f"/api/v1/store-manager/orders/{order_id}/confirm", headers=headers)
    assert confirm_res.status_code == 200, confirm_res.json()
    confirmed_data = confirm_res.json()
    assert confirmed_data["status"] == "confirmed"
    assert confirmed_data["order_units"] == 70
    assert confirmed_data["order_wt_kg"] == 70.0  # (50*1.2) + (20*0.5) = 60 + 10 = 70.0
    assert confirmed_data["order_vol_m3"] == 0.12  # (50*0.002) + (20*0.001) = 0.10 + 0.02 = 0.12


def test_create_order_wrong_outlet_forbidden(client, store_manager_db):
    headers = get_auth_header(client, "sm1")
    
    # sm1 belongs to OUT100, trying to create for OUT200
    create_payload = {
        "outlet_id": "OUT200",
        "brand": "fresh",
        "temp_req": "chilled",
        "order_date": str(date.today() + timedelta(days=7)),
        "items": [{"product_id": "P100", "quantity": 10}]
    }
    res = client.post("/api/v1/store-manager/orders", headers=headers, json=create_payload)
    assert res.status_code == 403


def test_update_and_cancel_draft_order(client, store_manager_db):
    headers = get_auth_header(client, "sm1")
    
    # Create draft
    create_res = client.post("/api/v1/store-manager/orders", headers=headers, json={
        "outlet_id": "OUT100",
        "brand": "fresh",
        "temp_req": "ambient",
        "order_date": str(date.today() + timedelta(days=7)),
        "items": [{"product_id": "P200", "quantity": 10}]
    })
    assert create_res.status_code == 200
    order_id = create_res.json()["order_id"]
    
    # Update draft items
    update_res = client.put(f"/api/v1/store-manager/orders/{order_id}", headers=headers, json={
        "items": [{"product_id": "P200", "quantity": 25}]
    })
    assert update_res.status_code == 200
    assert update_res.json()["items"][0]["quantity"] == 25
    
    # Cancel draft order
    cancel_res = client.delete(f"/api/v1/store-manager/orders/{order_id}", headers=headers)
    assert cancel_res.status_code == 200
    
    # Verify order is gone
    get_res = client.get(f"/api/v1/store-manager/orders/{order_id}", headers=headers)
    assert get_res.status_code == 404


def test_list_products_and_outlet_details(client, store_manager_db):
    headers = get_auth_header(client, "sm1")
    
    # List products
    products_res = client.get("/api/v1/store-manager/products?brand=fresh", headers=headers)
    assert products_res.status_code == 200
    products = products_res.json()
    assert len(products) == 2
    assert all(p["brand"] == "fresh" for p in products)
    
    # Get outlet details
    outlet_res = client.get("/api/v1/store-manager/outlet", headers=headers)
    assert outlet_res.status_code == 200
    outlet = outlet_res.json()
    assert outlet["outlet_id"] == "OUT100"
    assert outlet["name"] == "Fresh Colombo 01"
    assert outlet["dock_type"] == "rear_dock"


def test_confirm_receipt_and_discrepancies(client, store_manager_db):
    headers = get_auth_header(client, "sm1")
    
    # Create & confirm order
    res = client.post("/api/v1/store-manager/orders", headers=headers, json={
        "outlet_id": "OUT100",
        "brand": "fresh",
        "temp_req": "chilled",
        "order_date": str(date.today() + timedelta(days=7)),
        "items": [{"product_id": "P100", "quantity": 10}]
    })
    order_id = res.json()["order_id"]
    client.post(f"/api/v1/store-manager/orders/{order_id}/confirm", headers=headers)
    
    record_delivery(store_manager_db, order_id, "POD-999")

    # Confirm receipt with discrepancy
    receipt_payload = {
        "client_op_id": f"op-{uuid.uuid4().hex[:6]}",
        "pod_id": "POD-999",
        "items_ok": False,
        "discrepancies": [
            {
                "product_id": "P100",
                "expected_qty": 10,
                "actual_qty": 8,
                "reason_code": "missing",
                "note": "2 cartons missing from delivery"
            }
        ]
    }
    rec_res = client.post(f"/api/v1/store-manager/orders/{order_id}/receipt", headers=headers, json=receipt_payload)
    assert rec_res.status_code == 200, rec_res.json()
    assert rec_res.json()["status"] == "success"
    
    # Check order status changed to delivered
    get_order_res = client.get(f"/api/v1/store-manager/orders/{order_id}", headers=headers)
    assert get_order_res.status_code == 200
    assert get_order_res.json()["status"] == "delivered"
    
    # Check discrepancy record in DB
    from app.models.delivery import Discrepancy
    disc = store_manager_db.query(Discrepancy).filter_by(order_id=order_id).first()
    assert disc is not None
    assert disc.type == "missing"


def test_get_order_eta_and_deferrals(client, store_manager_db):
    headers = get_auth_header(client, "sm1")
    
    # Create order
    res = client.post("/api/v1/store-manager/orders", headers=headers, json={
        "outlet_id": "OUT100",
        "brand": "fresh",
        "temp_req": "chilled",
        "order_date": str(date.today() + timedelta(days=7)),
        "items": [{"product_id": "P100", "quantity": 10}]
    })
    order_id = res.json()["order_id"]
    
    # Get ETA
    eta_res = client.get(f"/api/v1/store-manager/orders/{order_id}/eta", headers=headers)
    assert eta_res.status_code == 200
    eta_data = eta_res.json()
    assert eta_data["order_id"] == order_id
    assert eta_data["window_open"] == "03:30"
    
    # Get deferrals list (should be empty initially)
    def_res = client.get("/api/v1/store-manager/deferrals", headers=headers)
    assert def_res.status_code == 200
    assert isinstance(def_res.json(), list)


def test_receipt_confirmation_idempotency_hardened(client, store_manager_db):
    headers_sm1 = get_auth_header(client, "sm1")
    headers_sm2 = get_auth_header(client, "sm2")
    
    # 1. Create & confirm Order 1 for OUT100 (SM1)
    res1 = client.post("/api/v1/store-manager/orders", headers=headers_sm1, json={
        "outlet_id": "OUT100",
        "brand": "fresh",
        "temp_req": "chilled",
        "order_date": str(date.today() + timedelta(days=20)),
        "items": [{"product_id": "P100", "quantity": 5}]
    })
    order1_id = res1.json()["order_id"]
    client.post(f"/api/v1/store-manager/orders/{order1_id}/confirm", headers=headers_sm1)
    
    record_delivery(store_manager_db, order1_id, "POD-IDEMP-001")

    # First receipt confirmation with client_op_id
    op_id = "op-rec-idemp-1"
    receipt_payload1 = {
        "client_op_id": op_id,
        "pod_id": "POD-IDEMP-001",
        "items_ok": True
    }
    rec1_res = client.post(f"/api/v1/store-manager/orders/{order1_id}/receipt", headers=headers_sm1, json=receipt_payload1)
    assert rec1_res.status_code == 200
    confirm_id_1 = rec1_res.json()["confirm_id"]
    
    # Case 1: Same client_op_id + same order_id + same Store Manager/outlet -> return existing receipt
    rec1_retry = client.post(f"/api/v1/store-manager/orders/{order1_id}/receipt", headers=headers_sm1, json=receipt_payload1)
    assert rec1_retry.status_code == 200
    assert rec1_retry.json()["confirm_id"] == confirm_id_1
    
    # Case 2: Same client_op_id + different order_id -> 409 Conflict
    res2 = client.post("/api/v1/store-manager/orders", headers=headers_sm1, json={
        "outlet_id": "OUT100",
        "brand": "fresh",
        "temp_req": "chilled",
        "order_date": str(date.today() + timedelta(days=21)),
        "items": [{"product_id": "P100", "quantity": 5}]
    })
    order2_id = res2.json()["order_id"]
    client.post(f"/api/v1/store-manager/orders/{order2_id}/confirm", headers=headers_sm1)
    
    rec2_res = client.post(f"/api/v1/store-manager/orders/{order2_id}/receipt", headers=headers_sm1, json={
        "client_op_id": op_id,
        "pod_id": "POD-IDEMP-002",
        "items_ok": True
    })
    assert rec2_res.status_code == 409
    assert "different order" in rec2_res.json()["detail"].lower()
    
    # Case 3: Same client_op_id + receipt belonging to another outlet/user -> 403 Forbidden without leaking
    res3 = client.post("/api/v1/store-manager/orders", headers=headers_sm2, json={
        "outlet_id": "OUT200",
        "brand": "style",
        "temp_req": "ambient",
        "order_date": str(date.today() + timedelta(days=22)),
        "items": [{"product_id": "P300", "quantity": 5}]
    })
    order3_id = res3.json()["order_id"]
    client.post(f"/api/v1/store-manager/orders/{order3_id}/confirm", headers=headers_sm2)
    
    rec3_res = client.post(f"/api/v1/store-manager/orders/{order3_id}/receipt", headers=headers_sm2, json={
        "client_op_id": op_id,
        "pod_id": "POD-IDEMP-003",
        "items_ok": True
    })
    assert rec3_res.status_code == 403
    assert "not authorized" in rec3_res.json()["detail"].lower()
    
    # Case 4: Non-existent order -> 404
    rec_404 = client.post("/api/v1/store-manager/orders/NON-EXISTENT-ORD/receipt", headers=headers_sm1, json={
        "client_op_id": op_id,
        "pod_id": "POD-IDEMP-004",
        "items_ok": True
    })
    assert rec_404.status_code == 404
    
    # Case 5: Foreign order -> 403 before idempotency
    rec_foreign = client.post(f"/api/v1/store-manager/orders/{order3_id}/receipt", headers=headers_sm1, json={
        "client_op_id": op_id,
        "pod_id": "POD-IDEMP-005",
        "items_ok": True
    })
    assert rec_foreign.status_code == 403
