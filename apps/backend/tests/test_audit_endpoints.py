import pytest
from datetime import date, datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import get_password_hash, create_platform_access_token
from app.models.user import User
from app.models.depot import Depot
from app.models.outlet import Outlet
from app.models.product import Product
from app.models.vehicle import Vehicle
from app.models.order import Order, OrderLine
from app.models.plan import DraftPlan

try:
    from app.adapters.optimizer_adapter import get_reference_data
    get_reference_data()
except FileNotFoundError:
    pytest.skip("Reference data missing, skipping module", allow_module_level=True)


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Depot
    depot = Depot(
        depot_id="Peliyagoda",
        name="Peliyagoda Central Depot",
        lat=6.965,
        lng=79.895,
    )
    db.add(depot)

    # Outlets matching outlets.csv
    out1 = Outlet(
        outlet_id="OUT004",
        name="Cargills Food City Wattala",
        brand="fresh",
        district="Gampaha",
        depot_id="Peliyagoda",
        dock_type="street",
        park_constraint="normal",
        lat=6.985,
        lng=79.891,
    )
    out2 = Outlet(
        outlet_id="OUT006",
        name="Keells Super Grandpass",
        brand="fresh",
        district="Colombo",
        depot_id="Peliyagoda",
        dock_type="street",
        park_constraint="normal",
        lat=6.951,
        lng=79.876,
    )
    out3 = Outlet(
        outlet_id="OUT007",
        name="Keells Super Colombo 03",
        brand="fresh",
        district="Colombo",
        depot_id="Peliyagoda",
        dock_type="street",
        park_constraint="normal",
        lat=6.912,
        lng=79.852,
    )
    db.add_all([out1, out2, out3])

    # Users
    user = User(
        user_id="U-DISP-AUDIT",
        name="Audit Dispatcher",
        username="dispatcher_audit",
        hashed_pw=get_password_hash("testpass"),
        role="dispatcher",
        depot_id="Peliyagoda",
    )
    sm_user = User(
        user_id="U-SM-AUDIT",
        name="Audit Store Manager",
        username="sm_audit",
        hashed_pw=get_password_hash("testpass"),
        role="store_manager",
        outlet_id="OUT004",
        depot_id=None,
    )
    db.add_all([user, sm_user])

    # Product
    p = Product(
        product_id="PROD-AUDIT-1",
        name="Fresh Milk 1L",
        brand="fresh",
        category="Dairy",
        temp_req="ambient",
        unit="crate",
        unit_wt_kg=10.0,
        unit_vol_m3=0.02,
        active=True,
    )
    db.add(p)

    # Vehicles at Peliyagoda (matching outlets.csv depot)
    v1 = Vehicle(
        vehicle_id="V001",
        depot_id="Peliyagoda",
        type="truck",
        temp="ambient",
        weight_cap_kg=2500.0,
        vol_cap_m3=12.0,
        fuel_type="diesel",
        km_per_l=4.5,
        fuel_quota_l=250,
        plate="WP-CAD-1001",
        status="available",
    )
    v2 = Vehicle(
        vehicle_id="V002",
        depot_id="Peliyagoda",
        type="truck",
        temp="ambient",
        weight_cap_kg=2500.0,
        vol_cap_m3=12.0,
        fuel_type="diesel",
        km_per_l=4.5,
        fuel_quota_l=250,
        plate="WP-CAD-1002",
        status="available",
    )
    db.add_all([v1, v2])

    # Confirmed orders in Peliyagoda/Colombo
    today = date(2026, 10, 2)
    o1 = Order(
        order_id="ORD-AUDIT-001",
        outlet_id="OUT004",
        created_by="U-DISP-AUDIT",
        brand="fresh",
        temp_req="ambient",
        order_date=today,
        submitted_at=datetime.now(timezone.utc),
        status="confirmed",
        order_units=30,
        order_wt_kg=300.0,
        order_vol_m3=0.6,
        window_open="08:00",
        window_close="18:00",
        deferred_prev=False,
        defer_count=0,
    )
    o1.lines.append(OrderLine(line_item_id="LI-AUDIT-1", order_id=o1.order_id, product_id=p.product_id, quantity=30))

    o2 = Order(
        order_id="ORD-AUDIT-002",
        outlet_id="OUT006",
        created_by="U-DISP-AUDIT",
        brand="fresh",
        temp_req="ambient",
        order_date=today,
        submitted_at=datetime.now(timezone.utc),
        status="confirmed",
        order_units=25,
        order_wt_kg=250.0,
        order_vol_m3=0.5,
        window_open="08:00",
        window_close="18:00",
        deferred_prev=False,
        defer_count=0,
    )
    o2.lines.append(OrderLine(line_item_id="LI-AUDIT-2", order_id=o2.order_id, product_id=p.product_id, quantity=25))

    db.add_all([o1, o2])
    db.commit()

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    old_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_get_db
    yield db
    if old_override is not None:
        app.dependency_overrides[get_db] = old_override
    else:
        app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)
    db.close()


@pytest.fixture
def client(test_db):
    return TestClient(app)


def test_audit_all_five_required_api_routes(client, test_db):
    """
    Verifies the 5 specific API routes requested:
      1. POST /api/v1/dispatcher/plans/draft
      2. POST /api/v1/dispatcher/plans/{plan_id}/edit
      3. Canonical Urgency Workflow (Store Manager request & Dispatcher review)
      4. POST /api/v1/dispatcher/plans/{plan_id}/approve
      5. POST /api/v1/vehicles/{vehicle_id}/breakdown
    """
    token = create_platform_access_token({"sub": "U-DISP-AUDIT", "role": "dispatcher", "depot_id": "Peliyagoda"})
    headers = {"Authorization": f"Bearer {token}"}
    target_date = "2026-10-02"

    # 1. POST /api/v1/dispatcher/plans/draft
    try:
        res_gen = client.post(
            "/api/v1/dispatcher/plans/draft",
            headers=headers,
            json={"depot_id": "Peliyagoda", "target_date": target_date, "enable_targeted_cpsat": True},
        )
        if res_gen.status_code == 500 and "FileNotFoundError" in res_gen.text:
            pytest.skip("Reference data missing, skipping audit")
        assert res_gen.status_code == 200, res_gen.text
        draft_data = res_gen.json()
        plan_id = draft_data.get("plan_id", "P-DUMMY")
    except Exception as e:
        if "FileNotFoundError" in str(e):
            pytest.skip("Reference data missing, skipping audit")
        raise
    assert "trips" in draft_data
    assert draft_data["validation"]["valid"] is True
    # Rule 8 check: Must create a DRAFT only; never automatically approve or lock a plan
    assert draft_data["validation"]["is_dispatch_ready"] is False

    db_plan = test_db.query(DraftPlan).filter(DraftPlan.plan_id == plan_id).first()
    assert db_plan is not None
    assert db_plan.status == "draft"

    # 2. POST /api/v1/dispatcher/plans/{plan_id}/edit
    res_edit = client.post(
        f"/api/v1/dispatcher/plans/{plan_id}/edit",
        headers=headers,
        json={
            "actions": [
                {
                    "action_type": "move_whole_order",
                    "order_ref": "ORD-AUDIT-001",
                    "target_vehicle_id": "V002",
                    "target_trip_number": 1,
                }
            ]
        },
    )
    assert res_edit.status_code == 200, res_edit.text
    edited_data = res_edit.json()
    assert edited_data["validation"]["valid"] is True

    # 3. Canonical Urgency Workflow (Store Manager request & Dispatcher review)
    sm_token = create_platform_access_token({"sub": "U-SM-AUDIT", "role": "store_manager", "outlet_id": "OUT004"})
    sm_headers = {"Authorization": f"Bearer {sm_token}"}

    # Store Manager requests urgency for confirmed order ORD-AUDIT-001
    res_urg = client.post(
        "/api/v1/store-manager/orders/ORD-AUDIT-001/urgency-request",
        headers=sm_headers,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Critical stockout risk at store",
            "client_op_id": "OP-AUDIT-URG-1",
        },
    )
    assert res_urg.status_code == 201, res_urg.text
    urg_data = res_urg.json()
    assert urg_data["status"] == "pending"
    assert urg_data["order_id"] == "ORD-AUDIT-001"
    urg_id = urg_data["urgency_request_id"]

    # Store Manager retrieves urgency request
    res_get_urg = client.get(
        "/api/v1/store-manager/orders/ORD-AUDIT-001/urgency-request",
        headers=sm_headers,
    )
    assert res_get_urg.status_code == 200, res_get_urg.text
    assert res_get_urg.json()["urgency_request_id"] == urg_id

    # Dispatcher lists urgency requests for depot
    res_disp_list = client.get(
        "/api/v1/dispatcher/urgency-requests",
        headers=headers,
    )
    assert res_disp_list.status_code == 200, res_disp_list.text
    assert any(item["urgency_request_id"] == urg_id for item in res_disp_list.json())

    # Dispatcher approves urgency request
    res_disp_appr = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/approve",
        headers=headers,
        json={"decision_note": "Approved by audit dispatcher"},
    )
    assert res_disp_appr.status_code == 200, res_disp_appr.text
    assert res_disp_appr.json()["status"] == "approved"

    # 4. POST /api/v1/dispatcher/plans/{plan_id}/approve
    res_approve = client.post(
        f"/api/v1/dispatcher/plans/{plan_id}/approve",
        headers=headers,
        json={"client_op_id": "OP-AUDIT-APPROVE-1"},
    )
    assert res_approve.status_code == 200, res_approve.text
    approve_data = res_approve.json()
    assert approve_data["status"] == "approved"
    assert approve_data["trips_created"] >= 1

    test_db.refresh(db_plan)
    assert db_plan.status == "approved"

    # 5. POST /api/v1/vehicles/{vehicle_id}/breakdown
    res_breakdown = client.post(
        "/api/v1/vehicles/V001/breakdown",
        headers=headers,
        json={
            "plan_id": plan_id,
            "current_time_iso": "2026-10-02T10:00:00+05:30",
            "pickup_location": "DEPOT",
        },
    )
    assert res_breakdown.status_code == 200, res_breakdown.text
    breakdown_data = res_breakdown.json()
    assert "trips" in breakdown_data or "recovery_reasons" in breakdown_data
