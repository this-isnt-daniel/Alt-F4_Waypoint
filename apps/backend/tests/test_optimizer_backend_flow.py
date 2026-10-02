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
from app.models.vehicle import Vehicle
from app.models.product import Product
from app.models.order import Order, OrderLine
from app.models.plan import DraftPlan
from app.models.trip import Trip, TripStop
from app.adapters.optimizer_adapter import get_reference_data


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

    # Seed real reference data matching outlets.csv and vehicles.csv
    ref = get_reference_data()

    # Seed user (Dispatcher at DEP1 - Peliyagoda)
    dispatcher = User(
        user_id="U-DISP-1",
        name="Lead Dispatcher",
        username="dispatcher_lead",
        hashed_pw=get_password_hash("securepass123"),
        role="dispatcher",
        depot_id="Peliyagoda",
    )
    db.add(dispatcher)

    # Seed real products
    p1 = Product(
        product_id="PROD-FRESH-1",
        name="Fresh Pasteurized Milk 1L",
        brand="fresh",
        category="Dairy",
        temp_req="ambient",
        unit="crate",
        unit_wt_kg=12.0,
        unit_vol_m3=0.03,
        active=True,
    )
    p2 = Product(
        product_id="PROD-FRESH-2",
        name="Fresh Farm Butter 500g",
        brand="fresh",
        category="Dairy",
        temp_req="ambient",
        unit="box",
        unit_wt_kg=6.0,
        unit_vol_m3=0.015,
        active=True,
    )
    db.add_all([p1, p2])

    # Seed vehicles from real reference data (Peliyagoda depot)
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

    # Seed confirmed orders for OUT004 and OUT006 (Peliyagoda, Colombo, Fresh)
    today = date(2026, 10, 2)

    o1 = Order(
        order_id="ORD-REAL-001",
        outlet_id="OUT004",
        created_by="U-DISP-1",
        brand="fresh",
        temp_req="ambient",
        order_date=today,
        submitted_at=datetime.now(timezone.utc),
        status="confirmed",
        order_units=50,
        order_wt_kg=600.0,
        order_vol_m3=1.5,
        window_open="08:00",
        window_close="18:00",
        deferred_prev=False,
        defer_count=0,
    )
    o1_line = OrderLine(
        line_item_id="LI-001-1",
        order_id=o1.order_id,
        product_id=p1.product_id,
        quantity=50,
    )
    o1.lines.append(o1_line)

    o2 = Order(
        order_id="ORD-REAL-002",
        outlet_id="OUT006",
        created_by="U-DISP-1",
        brand="fresh",
        temp_req="ambient",
        order_date=today,
        submitted_at=datetime.now(timezone.utc),
        status="confirmed",
        order_units=40,
        order_wt_kg=480.0,
        order_vol_m3=1.2,
        window_open="09:00",
        window_close="17:00",
        deferred_prev=False,
        defer_count=0,
    )
    o2_line = OrderLine(
        line_item_id="LI-002-1",
        order_id=o2.order_id,
        product_id=p1.product_id,
        quantity=40,
    )
    o2.lines.append(o2_line)

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


def test_full_real_backend_optimizer_flow(client, test_db):
    """
    Tests the complete real backend flow required by Step 7:
    confirmed orders
    → hybrid optimizer
    → validated draft
    → database draft record
    → dispatcher edits
    → revalidation
    → dispatcher approval
    """
    token = create_platform_access_token({"sub": "U-DISP-1", "role": "dispatcher", "depot_id": "Peliyagoda"})
    headers = {"Authorization": f"Bearer {token}"}
    target_date = "2026-10-02"

    # Step A: POST /dispatcher/plans/draft (Confirmed orders -> Hybrid optimizer -> Draft plan)
    res = client.post(
        "/dispatcher/plans/draft",
        headers=headers,
        json={
            "depot_id": "Peliyagoda",
            "target_date": target_date,
            "enable_targeted_cpsat": True,
        },
    )
    assert res.status_code == 200, res.text
    draft_data = res.json()

    plan_id = draft_data["plan_id"]
    assert draft_data["status"] == "FEASIBLE"
    assert "trips" in draft_data
    assert len(draft_data["trips"]) >= 1
    assert draft_data["validation"]["valid"] is True
    assert draft_data["validation"]["is_dispatch_ready"] is False  # Must require dispatcher approval

    # Verify draft plan record exists in database
    db_plan = test_db.query(DraftPlan).filter(DraftPlan.plan_id == plan_id).first()
    assert db_plan is not None
    assert db_plan.status == "draft"
    assert db_plan.algorithm in ("hybrid_greedy_targeted_cpsat", "multistart_greedy_operational")

    # Step B: GET /dispatcher/plans/{plan_id}
    res_get = client.get(f"/dispatcher/plans/{plan_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["plan_id"] == plan_id

    # Step C: Dispatcher edits the draft (move whole order to V002)
    # Target vehicle V002 is also available at Peliyagoda
    edit_res = client.post(
        f"/dispatcher/plans/{plan_id}/edit",
        headers=headers,
        json={
            "actions": [
                {
                    "action_type": "move_whole_order",
                    "order_ref": "ORD-REAL-001",
                    "target_vehicle_id": "V002",
                    "target_trip_number": 1,
                }
            ]
        },
    )
    assert edit_res.status_code == 200, edit_res.text
    edited_data = edit_res.json()
    assert edited_data["validation"]["valid"] is True

    # Check updated database record
    test_db.refresh(db_plan)
    assert "ORD-REAL-001" in str(db_plan.plan_data)

    # Step D: Dispatcher approves the draft (approval boundary)
    approve_res = client.post(
        f"/dispatcher/plans/{plan_id}/approve",
        headers=headers,
        json={"client_op_id": "OP-APPROVE-1"},
    )
    assert approve_res.status_code == 200, approve_res.text
    approve_data = approve_res.json()
    assert approve_data["status"] == "approved"
    assert approve_data["trips_created"] >= 1

    # Step E: Verify database status changes after approval
    test_db.refresh(db_plan)
    assert db_plan.status == "approved"
    assert db_plan.approved_by == "U-DISP-1"

    # Confirmed orders must now be planned
    ord1 = test_db.query(Order).filter(Order.order_id == "ORD-REAL-001").first()
    ord2 = test_db.query(Order).filter(Order.order_id == "ORD-REAL-002").first()
    assert ord1.status == "planned"
    assert ord1.trip_id is not None
    assert ord2.status == "planned"
    assert ord2.trip_id is not None

    # Trip and TripStop rows must exist
    trips = test_db.query(Trip).all()
    assert len(trips) >= 1
    stops = test_db.query(TripStop).all()
    assert len(stops) >= 2


def test_vehicle_breakdown_reallocation_flow(client, test_db):
    """
    Tests vehicle breakdown recovery operation:
    POST /dispatcher/breakdowns/{vehicle_id}/reallocate
    """
    token = create_platform_access_token({"sub": "U-DISP-1", "role": "dispatcher", "depot_id": "Peliyagoda"})
    headers = {"Authorization": f"Bearer {token}"}
    target_date = "2026-10-02"

    # Generate and approve draft
    res = client.post(
        "/dispatcher/plans/draft",
        headers=headers,
        json={"depot_id": "Peliyagoda", "target_date": target_date},
    )
    assert res.status_code == 200
    plan_id = res.json()["plan_id"]
    assigned_v = res.json()["trips"][0]["vehicle_id"]

    # Trigger breakdown on the assigned vehicle
    breakdown_res = client.post(
        f"/dispatcher/breakdowns/{assigned_v}/reallocate",
        headers=headers,
        json={
            "plan_id": plan_id,
            "current_time_iso": "2026-10-02T10:00:00+05:30",
            "pickup_location": "DEPOT",
        },
    )
    assert breakdown_res.status_code == 200, breakdown_res.text
    recovery_data = breakdown_res.json()
    assert "recovery_reasons" in recovery_data or "trips" in recovery_data

    # Verify vehicle status is marked in_workshop in database
    v = test_db.query(Vehicle).filter(Vehicle.vehicle_id == assigned_v).first()
    assert v.status == "in_workshop"
