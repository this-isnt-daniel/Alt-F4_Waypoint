"""
Focused regression tests for Issue 1 (Alembic schema check) and Issue 2 (Planning routes security).
"""
import subprocess
import sys
import pytest
from datetime import date
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
from app.adapters.optimizer_adapter import get_reference_data, resolve_real_data_dir


@pytest.fixture
def plan_security_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    ref = get_reference_data()

    # Seed depot
    depot = Depot(
        depot_id="Peliyagoda",
        name="Peliyagoda Central Depot",
        lat=6.9654,
        lng=79.8801,
    )
    db.add(depot)

    # Seed users
    dispatcher = User(
        user_id="U-DISP-SEC",
        name="Lead Dispatcher",
        username="dispatcher_sec",
        hashed_pw=get_password_hash("pass123"),
        role="dispatcher",
        depot_id="Peliyagoda",
    )
    store_manager = User(
        user_id="U-SM-SEC",
        name="Store Manager",
        username="sm_sec",
        hashed_pw=get_password_hash("pass123"),
        role="store_manager",
        depot_id="Peliyagoda",
    )
    driver = User(
        user_id="U-DRV-SEC",
        name="Platform Driver",
        username="drv_sec",
        hashed_pw=get_password_hash("pass123"),
        role="driver",
        depot_id="Peliyagoda",
    )
    db.add_all([dispatcher, store_manager, driver])

    # Seed real products
    p1 = Product(
        product_id="PROD-SEC-1",
        name="Fresh Milk 1L",
        brand="fresh",
        category="Dairy",
        temp_req="ambient",
        unit="crate",
        unit_wt_kg=10.0,
        unit_vol_m3=0.02,
        active=True,
    )
    db.add(p1)

    # Seed outlets
    out1 = Outlet(
        outlet_id="OUT004",
        name="Cargills Food City Wattala",
        brand="fresh",
        district="Gampaha",
        depot_id="Peliyagoda",
        dock_type="normal",
        park_constraint="none",
        lat=6.985,
        lng=79.891,
    )
    out2 = Outlet(
        outlet_id="OUT006",
        name="Keells Super Grandpass",
        brand="fresh",
        district="Colombo",
        depot_id="Peliyagoda",
        dock_type="normal",
        park_constraint="none",
        lat=6.951,
        lng=79.876,
    )
    db.add_all([out1, out2])

    # Seed fleet
    for v in ref.vehicles:
        if v.depot == "Peliyagoda":
            db.add(
                Vehicle(
                    vehicle_id=v.vehicle_id,
                    depot_id=v.depot,
                    type=v.type.value,
                    temp=v.temp.value,
                    weight_cap_kg=v.weight_cap_kg,
                    vol_cap_m3=v.volume_cap_m3,
                    fuel_type="diesel",
                    km_per_l=4.5,
                    fuel_quota_l=int(v.weekly_fuel_quota_l or 250),
                    plate=f"WP-{v.vehicle_id}",
                    status="available",
                )
            )

    # Seed confirmed order
    today = date(2026, 10, 2)
    o1 = Order(
        order_id="ORD-SEC-001",
        outlet_id="OUT004",
        created_by="U-SM-SEC",
        brand="fresh",
        temp_req="ambient",
        order_date=today,
        status="confirmed",
        order_units=15,
        order_wt_kg=150.0,
        order_vol_m3=0.3,
        window_open="06:00",
        window_close="10:00",
    )
    db.add(o1)
    db.flush()

    db.add(
        OrderLine(
            line_item_id="LI-SEC-001",
            order_id="ORD-SEC-001",
            product_id="PROD-SEC-1",
            quantity=15,
        )
    )
    db.commit()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(plan_security_db):
    def override_get_db():
        try:
            yield plan_security_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_1_alembic_check_passes():
    """Requirement 1: alembic check passes with 0 exit code."""
    import os
    env = os.environ.copy()
    env.pop("DATABASE_URL", None)

    res = subprocess.run(
        [sys.executable, "-m", "alembic", "check"],
        cwd=r"D:\Alt-F4_Waypoint\apps\backend",
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"alembic check failed:\n{res.stdout}\n{res.stderr}"
    assert "No new upgrade operations detected" in (res.stdout + res.stderr)


def test_2_and_3_unauthenticated_planning_rejected(client):
    """Requirements 2 & 3: Unauthenticated plan generation and approval are rejected (401)."""
    # 2. Unauthenticated plan generation
    res_gen1 = client.post("/api/v1/dispatcher/plans/draft", json={})
    assert res_gen1.status_code == 401
    assert "Not authenticated" in res_gen1.text

    res_gen2 = client.post("/api/v1/plans/generate", json={})
    assert res_gen2.status_code == 401

    res_gen3 = client.post("/dispatcher/plans/draft", json={})
    assert res_gen3.status_code == 401

    # 3. Unauthenticated plan approval
    res_app1 = client.post("/api/v1/dispatcher/plans/PLAN-123/approve", json={})
    assert res_app1.status_code == 401

    res_app2 = client.post("/api/v1/plans/PLAN-123/approve", json={})
    assert res_app2.status_code == 401

    res_app3 = client.post("/dispatcher/plans/PLAN-123/approve", json={})
    assert res_app3.status_code == 401


def test_4_and_5_non_dispatcher_rejected(client):
    """Requirements 4 & 5: Non-dispatcher roles are rejected with 403 Forbidden."""
    sm_token = create_platform_access_token({"sub": "U-SM-SEC", "role": "store_manager", "depot_id": "Peliyagoda"})
    drv_token = create_platform_access_token({"sub": "U-DRV-SEC", "role": "driver", "depot_id": "Peliyagoda"})

    for token in [sm_token, drv_token]:
        headers = {"Authorization": f"Bearer {token}"}

        # 4. Non-dispatcher plan generation rejected
        res_gen = client.post("/api/v1/dispatcher/plans/draft", headers=headers, json={})
        assert res_gen.status_code == 403, f"Expected 403, got {res_gen.status_code}"
        assert "Operation not permitted" in res_gen.text

        res_gen_alias = client.post("/api/v1/plans/generate", headers=headers, json={})
        assert res_gen_alias.status_code == 403

        # 5. Non-dispatcher plan approval rejected
        res_app = client.post("/api/v1/dispatcher/plans/PLAN-123/approve", headers=headers, json={})
        assert res_app.status_code == 403

        res_app_alias = client.post("/api/v1/plans/PLAN-123/approve", headers=headers, json={})
        assert res_app_alias.status_code == 403


def test_6_and_7_dispatcher_workflow(client, plan_security_db):
    """Requirements 6 & 7: Dispatcher can generate draft and approve valid draft."""
    disp_token = create_platform_access_token({"sub": "U-DISP-SEC", "role": "dispatcher", "depot_id": "Peliyagoda"})
    headers = {"Authorization": f"Bearer {disp_token}"}

    # 6. Dispatcher can generate a draft
    res_gen = client.post(
        "/api/v1/dispatcher/plans/draft",
        headers=headers,
        json={"depot_id": "Peliyagoda", "target_date": "2026-10-02", "enable_targeted_cpsat": True},
    )
    assert res_gen.status_code == 200, res_gen.text
    plan_dict = res_gen.json()
    plan_id = plan_dict["plan_id"]
    assert plan_dict["status"] == "FEASIBLE"
    assert plan_dict["validation"]["valid"] is True

    # Persisted ONLY as draft
    db_plan = plan_security_db.query(DraftPlan).filter(DraftPlan.plan_id == plan_id).first()
    assert db_plan is not None
    assert db_plan.status == "draft"

    # 7. Dispatcher can approve valid draft
    res_app = client.post(
        f"/api/v1/dispatcher/plans/{plan_id}/approve",
        headers=headers,
        json={"client_op_id": "OP-SEC-APP-001"},
    )
    assert res_app.status_code == 200, res_app.text
    app_data = res_app.json()
    assert app_data["status"] == "approved"
    assert app_data["trips_created"] >= 1

    plan_security_db.refresh(db_plan)
    assert db_plan.status == "approved"


def test_8_duplicate_route_aliases_identical_auth(client):
    """Requirement 8: Duplicate route aliases have identical authorization behavior."""
    routes = [
        ("POST", "/api/v1/dispatcher/plans/draft"),
        ("POST", "/dispatcher/plans/draft"),
        ("POST", "/api/v1/plans/generate"),
        ("POST", "/api/v1/plans/draft"),
        ("GET", "/api/v1/dispatcher/plans/PLAN-TEST"),
        ("GET", "/dispatcher/plans/PLAN-TEST"),
        ("GET", "/api/v1/plans/PLAN-TEST"),
        ("POST", "/api/v1/dispatcher/plans/PLAN-TEST/edit"),
        ("POST", "/dispatcher/plans/PLAN-TEST/edit"),
        ("POST", "/api/v1/plans/PLAN-TEST/edit"),
        ("POST", "/api/v1/dispatcher/plans/PLAN-TEST/approve"),
        ("POST", "/dispatcher/plans/PLAN-TEST/approve"),
        ("POST", "/api/v1/plans/PLAN-TEST/approve"),
    ]

    sm_token = create_platform_access_token({"sub": "U-SM-SEC", "role": "store_manager", "depot_id": "Peliyagoda"})
    sm_headers = {"Authorization": f"Bearer {sm_token}"}

    for method, path in routes:
        # Unauthenticated -> 401
        res_unauth = client.request(method, path, json={})
        assert res_unauth.status_code == 401, f"{path} expected 401 unauth, got {res_unauth.status_code}"

        # Store manager -> 403
        res_sm = client.request(method, path, headers=sm_headers, json={})
        assert res_sm.status_code == 403, f"{path} expected 403 forbidden, got {res_sm.status_code}"


def test_9_optimizer_integration_canonical_paths():
    """Requirement 9: Optimizer integration references canonical data directory."""
    resolved_path = resolve_real_data_dir()
    assert "apps\\backend\\data" in str(resolved_path) or "apps/backend/data" in str(resolved_path)
    ref = get_reference_data()
    assert len(ref.outlets) == 120
    assert len(ref.vehicles) == 60


def test_10_draft_edit_and_breakdown_flow(client, plan_security_db):
    """Requirement 10: Draft-edit and breakdown-recovery flows still pass under auth."""
    disp_token = create_platform_access_token({"sub": "U-DISP-SEC", "role": "dispatcher", "depot_id": "Peliyagoda"})
    headers = {"Authorization": f"Bearer {disp_token}"}

    # Generate draft
    res_gen = client.post(
        "/api/v1/dispatcher/plans/draft",
        headers=headers,
        json={"depot_id": "Peliyagoda", "target_date": "2026-10-02", "enable_targeted_cpsat": True},
    )
    assert res_gen.status_code == 200
    plan_data = res_gen.json()
    plan_id = plan_data["plan_id"]

    # Edit draft
    res_edit = client.post(
        f"/api/v1/dispatcher/plans/{plan_id}/edit",
        headers=headers,
        json={
            "actions": [
                {
                    "action_type": "defer_whole_order",
                    "order_ref": "ORD-SEC-001",
                    "reason": "MANUAL_TEST",
                }
            ]
        },
    )
    assert res_edit.status_code == 200
    edited = res_edit.json()
    assert edited["validation"]["valid"] is True
    assert len(edited["deferred_orders"]) == 1

    # Breakdown recovery
    assigned_v = plan_data["trips"][0]["vehicle_id"] if plan_data.get("trips") else "V001"
    res_bd = client.post(
        f"/api/v1/dispatcher/breakdowns/{assigned_v}/reallocate",
        headers=headers,
        json={"plan_id": plan_id, "current_time_iso": "2026-10-02T09:00:00+05:30"},
    )
    assert res_bd.status_code == 200
    bd_data = res_bd.json()
    assert "recovery_summary" in bd_data or "trips" in bd_data
