import pytest
import uuid
from fastapi.testclient import TestClient
from datetime import datetime, date, timezone, timedelta
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.product import Product
from app.models.depot import Depot
from app.models.outlet import Outlet
from app.models.order import Order, OrderLine
from app.models.deferral import Deferral
from app.models.urgency import UrgencyRequest


@pytest.fixture
def urgency_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # 1. Depots
    depot1 = Depot(depot_id="DEP100", name="Peliyagoda Central", lat=6.95, lng=79.88)
    depot2 = Depot(depot_id="DEP200", name="Kandy Depot", lat=7.29, lng=80.63)
    db.add_all([depot1, depot2])

    # 2. Outlets
    outlet1 = Outlet(
        outlet_id="OUT100",
        name="Fresh Colombo 01",
        brand="fresh",
        district="Colombo",
        depot_id="DEP100",
        window_open="08:00",
        window_close="12:00",
        dock_type="rear_dock",
        park_constraint="normal",
    )
    outlet2 = Outlet(
        outlet_id="OUT200",
        name="Fresh Colombo 02",
        brand="fresh",
        district="Colombo",
        depot_id="DEP100",
        window_open="09:00",
        window_close="13:00",
        dock_type="street",
        park_constraint="normal",
    )
    outlet3 = Outlet(
        outlet_id="OUT300",
        name="Fresh Kandy 01",
        brand="fresh",
        district="Kandy",
        depot_id="DEP200",  # Different depot
        window_open="10:00",
        window_close="14:00",
        dock_type="rear_dock",
        park_constraint="normal",
    )
    db.add_all([outlet1, outlet2, outlet3])

    # 3. Users
    pw_hash = get_password_hash("password123")
    sm1 = User(
        user_id="U_SM1",
        name="Store Manager 1",
        username="sm1",
        hashed_pw=pw_hash,
        role="store_manager",
        outlet_id="OUT100",
    )
    sm2 = User(
        user_id="U_SM2",
        name="Store Manager 2",
        username="sm2",
        hashed_pw=pw_hash,
        role="store_manager",
        outlet_id="OUT200",
    )
    disp1 = User(
        user_id="U_DISP1",
        name="Dispatcher Depot 1",
        username="disp1",
        hashed_pw=pw_hash,
        role="dispatcher",
        depot_id="DEP100",
    )
    disp2 = User(
        user_id="U_DISP2",
        name="Dispatcher Depot 2",
        username="disp2",
        hashed_pw=pw_hash,
        role="dispatcher",
        depot_id="DEP200",
    )
    driver1 = User(
        user_id="U_DRV1",
        name="Driver 1",
        username="driver1",
        hashed_pw=pw_hash,
        role="driver",
        depot_id="DEP100",
    )
    db.add_all([sm1, sm2, disp1, disp2, driver1])

    # 4. Products
    p1 = Product(
        product_id="P100",
        name="Fresh Milk 1L",
        brand="fresh",
        temp_req="chilled",
        unit="CTN",
        unit_wt_kg=1.2,
        unit_vol_m3=0.002,
        active=True,
    )
    db.add(p1)

    # 5. Orders in different statuses
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    today = date.today()

    def make_order(order_id, outlet_id, status, day_offset=0, defer_count=0, deferred_prev=False, temp_req="chilled"):
        ord_obj = Order(
            order_id=order_id,
            outlet_id=outlet_id,
            created_by="U_SM1",
            order_date=today + timedelta(days=day_offset),
            brand="fresh",
            temp_req=temp_req,
            status=status,
            defer_count=defer_count,
            deferred_prev=deferred_prev,
            window_open="08:00",
            window_close="12:00",
            order_wt_kg=24.0,
            order_vol_m3=0.04,
            submitted_at=now,
        )
        db.add(ord_obj)
        line = OrderLine(
            line_item_id=f"LINE-{order_id}",
            order_id=order_id,
            product_id="P100",
            quantity=20,
        )
        db.add(line)
        return ord_obj

    # Orders for OUT100 (DEP100) - each on unique date to respect uix_order_outlet_date_temp
    make_order("ORD-CONF-1", "OUT100", "confirmed", day_offset=1)
    make_order("ORD-CONF-2", "OUT100", "confirmed", day_offset=2)
    make_order("ORD-DEF-1", "OUT100", "deferred", day_offset=3, defer_count=1, deferred_prev=True)
    make_order("ORD-DRAFT-1", "OUT100", "draft", day_offset=4)
    make_order("ORD-PLAN-1", "OUT100", "planned", day_offset=5)
    make_order("ORD-LOAD-1", "OUT100", "loaded", day_offset=6)
    make_order("ORD-OFD-1", "OUT100", "out_for_delivery", day_offset=7)
    make_order("ORD-DEL-1", "OUT100", "delivered", day_offset=8)

    # Order for OUT200 (DEP100)
    make_order("ORD-OUT2-CONF", "OUT200", "confirmed", day_offset=1)

    # Order for OUT300 (Foreign DEP200)
    make_order("ORD-DEP2-CONF", "OUT300", "confirmed", day_offset=1)

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
def client(urgency_test_db):
    return TestClient(app)


def auth_headers(client, username):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password123"},
    )
    assert res.status_code == 200, f"Login failed for {username}: {res.json()}"
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


_order_offset_counter = 100


def create_and_confirm_order_helper(client, sm_hdr, outlet_id="OUT100", brand="fresh", temp_req="chilled"):
    global _order_offset_counter
    _order_offset_counter += 1
    create_res = client.post(
        "/api/v1/store-manager/orders",
        headers=sm_hdr,
        json={
            "outlet_id": outlet_id,
            "brand": brand,
            "temp_req": temp_req,
            "order_date": str(date.today() + timedelta(days=_order_offset_counter)),
            "items": [{"product_id": "P100", "quantity": 10}],
        },
    )
    assert create_res.status_code == 200, f"Create order failed: {create_res.json()}"
    order_id = create_res.json()["order_id"]
    confirm_res = client.post(f"/api/v1/store-manager/orders/{order_id}/confirm", headers=sm_hdr)
    assert confirm_res.status_code == 200, f"Confirm order failed: {confirm_res.json()}"
    return order_id


# ==============================================================================
# Phase 3: Store Manager Urgency Request Tests
# ==============================================================================

def test_sm_can_request_urgency_for_confirmed_order(client, urgency_test_db):
    sm1_hdr = auth_headers(client, "sm1")
    payload = {
        "reason_code": "stockout_risk",
        "reason_text": "Store running critically low on milk inventory.",
    }
    res = client.post(
        "/api/v1/store-manager/orders/ORD-CONF-1/urgency-request",
        headers=sm1_hdr,
        json=payload,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["order_id"] == "ORD-CONF-1"
    assert data["outlet_id"] == "OUT100"
    assert data["reported_by"] == "U_SM1"
    assert data["reason_code"] == "stockout_risk"
    assert data["status"] == "pending"
    assert data["reviewed_by"] is None
    assert data["reviewed_at"] is None
    assert data["decision_note"] is None
    assert data["urgency_request_id"].startswith("URG-")

    # Verify invariants: deferral counts untouched
    order = urgency_test_db.query(Order).filter(Order.order_id == "ORD-CONF-1").first()
    assert order.deferred_prev is False
    assert order.defer_count == 0


def test_sm_can_request_urgency_for_deferred_order(client, urgency_test_db):
    sm1_hdr = auth_headers(client, "sm1")
    payload = {
        "reason_code": "chilled_shortage",
        "reason_text": "Chilled inventory deferred from prior cycle urgently required.",
    }
    res = client.post(
        "/api/v1/store-manager/orders/ORD-DEF-1/urgency-request",
        headers=sm1_hdr,
        json=payload,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["order_id"] == "ORD-DEF-1"
    assert data["status"] == "pending"

    # Verify invariants: defer_count and deferred_prev preserved
    order = urgency_test_db.query(Order).filter(Order.order_id == "ORD-DEF-1").first()
    assert order.deferred_prev is True
    assert order.defer_count == 1
    assert order.order_id == "ORD-DEF-1"


@pytest.mark.parametrize(
    "invalid_order_id,expected_status",
    [
        ("ORD-DRAFT-1", "draft"),
        ("ORD-PLAN-1", "planned"),
        ("ORD-LOAD-1", "loaded"),
        ("ORD-OFD-1", "out_for_delivery"),
        ("ORD-DEL-1", "delivered"),
    ],
)
def test_sm_request_rejected_for_invalid_order_statuses(
    client, invalid_order_id, expected_status
):
    sm1_hdr = auth_headers(client, "sm1")
    payload = {
        "reason_code": "store_operation_impact",
        "reason_text": "Requesting urgency on ineligible status order.",
    }
    res = client.post(
        f"/api/v1/store-manager/orders/{invalid_order_id}/urgency-request",
        headers=sm1_hdr,
        json=payload,
    )
    assert res.status_code == 409
    assert expected_status in res.json()["detail"]


def test_sm_foreign_outlet_blocked(client):
    sm1_hdr = auth_headers(client, "sm1")
    payload = {
        "reason_code": "time_bound_event",
        "reason_text": "Attempting to request urgency for OUT200 order.",
    }
    # sm1 belongs to OUT100; tries to request urgency for OUT200's order
    res = client.post(
        "/api/v1/store-manager/orders/ORD-OUT2-CONF/urgency-request",
        headers=sm1_hdr,
        json=payload,
    )
    assert res.status_code == 403
    assert "own outlet" in res.json()["detail"].lower()


def test_sm_duplicate_request_blocked(client):
    sm1_hdr = auth_headers(client, "sm1")
    payload = {
        "reason_code": "stockout_risk",
        "reason_text": "First urgency submission for ORD-CONF-2.",
    }
    res1 = client.post(
        "/api/v1/store-manager/orders/ORD-CONF-2/urgency-request",
        headers=sm1_hdr,
        json=payload,
    )
    assert res1.status_code == 201

    # Second submission without client_op_id
    payload2 = {
        "reason_code": "store_operation_impact",
        "reason_text": "Second submission for the same order should fail.",
    }
    res2 = client.post(
        "/api/v1/store-manager/orders/ORD-CONF-2/urgency-request",
        headers=sm1_hdr,
        json=payload2,
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_sm_client_op_id_retry_is_idempotent(client):
    sm1_hdr = auth_headers(client, "sm1")

    # Create fresh order using helper with unique date
    fresh_order_id = create_and_confirm_order_helper(client, sm1_hdr)

    # Now test client_op_id idempotency on fresh_order_id
    idemp_payload = {
        "reason_code": "stockout_risk",
        "reason_text": "Fresh order urgent request transmission.",
        "client_op_id": "op-idemp-12345",
    }
    first_res = client.post(
        f"/api/v1/store-manager/orders/{fresh_order_id}/urgency-request",
        headers=sm1_hdr,
        json=idemp_payload,
    )
    assert first_res.status_code == 201
    first_data = first_res.json()

    # Retry identical request with same client_op_id
    retry_res = client.post(
        f"/api/v1/store-manager/orders/{fresh_order_id}/urgency-request",
        headers=sm1_hdr,
        json=idemp_payload,
    )
    assert retry_res.status_code in (200, 201)
    retry_data = retry_res.json()
    assert retry_data["urgency_request_id"] == first_data["urgency_request_id"]
    assert retry_data["client_op_id"] == "op-idemp-12345"

    # 2. Retry with different client_op_id on same order -> 409
    diff_payload = {
        "reason_code": "stockout_risk",
        "reason_text": "Different request on same order should be rejected.",
        "client_op_id": "op-idemp-different",
    }
    diff_res = client.post(
        f"/api/v1/store-manager/orders/{fresh_order_id}/urgency-request",
        headers=sm1_hdr,
        json=diff_payload,
    )
    assert diff_res.status_code == 409

    # 3. Same client_op_id on DIFFERENT order -> 409 Conflict
    second_order_id = create_and_confirm_order_helper(client, sm1_hdr)
    reuse_op_diff_order = {
        "reason_code": "stockout_risk",
        "reason_text": "Reusing client_op_id for a different order.",
        "client_op_id": "op-idemp-12345",
    }
    diff_order_res = client.post(
        f"/api/v1/store-manager/orders/{second_order_id}/urgency-request",
        headers=sm1_hdr,
        json=reuse_op_diff_order,
    )
    assert diff_order_res.status_code == 409
    assert "different order" in diff_order_res.json()["detail"].lower()

    # 4. Same client_op_id attempted by ANOTHER outlet/user -> 403 Forbidden without leaking
    sm2_hdr = auth_headers(client, "sm2")
    sm2_order_id = create_and_confirm_order_helper(client, sm2_hdr, outlet_id="OUT200")
    sm2_res = client.post(
        f"/api/v1/store-manager/orders/{sm2_order_id}/urgency-request",
        headers=sm2_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "SM2 trying to reuse SM1's client_op_id.",
            "client_op_id": "op-idemp-12345",
        },
    )
    assert sm2_res.status_code == 403
    assert "not authorized" in sm2_res.json()["detail"].lower()


def test_sm_invalid_reason_or_short_text_rejected(client):
    sm1_hdr = auth_headers(client, "sm1")
    # Invalid reason code
    bad_reason = {
        "reason_code": "invalid_reason_xyz",
        "reason_text": "Valid length explanation text here.",
    }
    res1 = client.post(
        "/api/v1/store-manager/orders/ORD-CONF-1/urgency-request",
        headers=sm1_hdr,
        json=bad_reason,
    )
    assert res1.status_code == 422

    # Reason text too short (< 10 chars)
    short_text = {
        "reason_code": "stockout_risk",
        "reason_text": "Short",
    }
    res2 = client.post(
        "/api/v1/store-manager/orders/ORD-CONF-1/urgency-request",
        headers=sm1_hdr,
        json=short_text,
    )
    assert res2.status_code == 422


def test_sm_get_urgency_request(client):
    sm1_hdr = auth_headers(client, "sm1")
    sm2_hdr = auth_headers(client, "sm2")

    # Create an order specifically for GET tests
    new_ord = create_and_confirm_order_helper(client, sm1_hdr)

    # 404 before urgency request exists
    res_none = client.get(
        f"/api/v1/store-manager/orders/{new_ord}/urgency-request",
        headers=sm1_hdr,
    )
    assert res_none.status_code == 404

    # Create urgency request
    client.post(
        f"/api/v1/store-manager/orders/{new_ord}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Inventory is zero; need delivery today.",
        },
    )

    # Owner SM can retrieve
    res_get = client.get(
        f"/api/v1/store-manager/orders/{new_ord}/urgency-request",
        headers=sm1_hdr,
    )
    assert res_get.status_code == 200
    assert res_get.json()["order_id"] == new_ord

    # Foreign Store Manager blocked from viewing (403)
    res_foreign = client.get(
        f"/api/v1/store-manager/orders/{new_ord}/urgency-request",
        headers=sm2_hdr,
    )
    assert res_foreign.status_code == 403


# ==============================================================================
# Phase 4: Dispatcher Urgency Review Tests
# ==============================================================================

def test_dispatcher_list_is_depot_scoped(client):
    sm1_hdr = auth_headers(client, "sm1")
    disp1_hdr = auth_headers(client, "disp1")
    disp2_hdr = auth_headers(client, "disp2")

    # OUT100 (in DEP100) requests urgency
    client.post(
        "/api/v1/store-manager/orders/ORD-CONF-1/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Store running critically low on milk inventory.",
        },
    )

    disp1_res = client.get("/api/v1/dispatcher/urgency-requests?status=pending", headers=disp1_hdr)
    assert disp1_res.status_code == 200
    disp1_list = disp1_res.json()
    assert len(disp1_list) >= 1
    # Check enriched fields
    item = disp1_list[0]
    assert "urgency_request_id" in item
    assert "outlet_name" in item
    assert "order_status" in item
    assert "defer_count" in item
    assert "deferred_prev" in item
    assert "window_open" in item
    assert "window_close" in item
    assert "order_wt_kg" in item
    assert "order_vol_m3" in item

    # disp2 (DEP200) should NOT see DEP100's urgency requests
    disp2_res = client.get("/api/v1/dispatcher/urgency-requests?status=pending", headers=disp2_hdr)
    assert disp2_res.status_code == 200
    disp2_list = disp2_res.json()
    depot1_ids = [it["outlet_id"] for it in disp2_list]
    assert "OUT100" not in depot1_ids
    assert "OUT200" not in depot1_ids


def test_dispatcher_approve_pending_urgency_request(client, urgency_test_db):
    sm1_hdr = auth_headers(client, "sm1")
    disp1_hdr = auth_headers(client, "disp1")

    # Create fresh order & urgency request
    ord_id = create_and_confirm_order_helper(client, sm1_hdr)

    urg_res = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "store_operation_impact",
            "reason_text": "Production halted unless this shipment arrives.",
        },
    )
    urg_id = urg_res.json()["urgency_request_id"]

    # Dispatcher approves
    approve_res = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/approve",
        headers=disp1_hdr,
        json={"decision_note": "Approved due to operational impact."},
    )
    assert approve_res.status_code == 200
    app_data = approve_res.json()
    assert app_data["status"] == "approved"
    assert app_data["reviewed_by"] == "U_DISP1"
    assert app_data["reviewed_at"] is not None
    assert app_data["decision_note"] == "Approved due to operational impact."

    # Invariants check
    order = urgency_test_db.query(Order).filter(Order.order_id == ord_id).first()
    assert order.status == "confirmed"
    assert order.defer_count == 0
    assert order.deferred_prev is False


def test_dispatcher_reject_pending_urgency_request_with_mandatory_note(client):
    sm1_hdr = auth_headers(client, "sm1")
    disp1_hdr = auth_headers(client, "disp1")

    # Create fresh order & urgency request
    ord_id = create_and_confirm_order_helper(client, sm1_hdr)

    urg_id = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "other",
            "reason_text": "Special marketing event today at store.",
        },
    ).json()["urgency_request_id"]

    # Rejection without note or empty note must fail with 422
    rej_no_note = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/reject",
        headers=disp1_hdr,
        json={"decision_note": ""},
    )
    assert rej_no_note.status_code == 422

    rej_whitespace = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/reject",
        headers=disp1_hdr,
        json={"decision_note": "   "},
    )
    assert rej_whitespace.status_code == 422

    # Rejection with note succeeds
    rej_ok = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/reject",
        headers=disp1_hdr,
        json={"decision_note": "Fleet capacity full; cannot accommodate priority."},
    )
    assert rej_ok.status_code == 200
    data = rej_ok.json()
    assert data["status"] == "rejected"
    assert data["reviewed_by"] == "U_DISP1"
    assert data["decision_note"] == "Fleet capacity full; cannot accommodate priority."


def test_dispatcher_authorization_checks(client):
    sm1_hdr = auth_headers(client, "sm1")
    disp1_hdr = auth_headers(client, "disp1")
    disp2_hdr = auth_headers(client, "disp2")
    driver_hdr = auth_headers(client, "driver1")

    # Order in OUT100 (DEP100)
    ord_id = create_and_confirm_order_helper(client, sm1_hdr)

    urg_id = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Need stock before weekend morning rush.",
        },
    ).json()["urgency_request_id"]

    # 1. Driver role blocked (403)
    res_drv = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/approve",
        headers=driver_hdr,
    )
    assert res_drv.status_code == 403

    # 2. Store Manager role blocked from dispatcher approve (403)
    res_sm = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/approve",
        headers=sm1_hdr,
    )
    assert res_sm.status_code == 403

    # 3. Foreign Depot Dispatcher blocked from approving (403)
    res_foreign_app = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/approve",
        headers=disp2_hdr,
    )
    assert res_foreign_app.status_code == 403
    assert "outside your depot" in res_foreign_app.json()["detail"].lower()

    # 4. Foreign Depot Dispatcher blocked from rejecting (403)
    res_foreign_rej = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/reject",
        headers=disp2_hdr,
        json={"decision_note": "Foreign rejection attempt"},
    )
    assert res_foreign_rej.status_code == 403
    assert "outside your depot" in res_foreign_rej.json()["detail"].lower()


def test_dispatcher_retry_and_conflict_state_transitions(client):
    sm1_hdr = auth_headers(client, "sm1")
    disp1_hdr = auth_headers(client, "disp1")

    # 1. Test approve retry safe & reject-after-approve 409
    ord1_id = create_and_confirm_order_helper(client, sm1_hdr)

    urg1_id = client.post(
        f"/api/v1/store-manager/orders/{ord1_id}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Order 1 urgent reason text for transition.",
        },
    ).json()["urgency_request_id"]

    # Initial approve
    app1 = client.post(f"/api/v1/dispatcher/urgency-requests/{urg1_id}/approve", headers=disp1_hdr)
    assert app1.status_code == 200
    assert app1.json()["status"] == "approved"

    # Retry approve is safe (200)
    app1_retry = client.post(f"/api/v1/dispatcher/urgency-requests/{urg1_id}/approve", headers=disp1_hdr)
    assert app1_retry.status_code == 200
    assert app1_retry.json()["status"] == "approved"

    # Reject after approve -> 409 Conflict
    rej_after_app = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg1_id}/reject",
        headers=disp1_hdr,
        json={"decision_note": "Trying to reject approved request."},
    )
    assert rej_after_app.status_code == 409
    assert "already approved" in rej_after_app.json()["detail"].lower()

    # 2. Test reject retry safe & approve-after-reject 409
    ord2_id = create_and_confirm_order_helper(client, sm1_hdr)

    urg2_id = client.post(
        f"/api/v1/store-manager/orders/{ord2_id}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Order 2 urgent reason text for transition.",
        },
    ).json()["urgency_request_id"]

    # Initial reject
    rej2 = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg2_id}/reject",
        headers=disp1_hdr,
        json={"decision_note": "Initial rejection reason."},
    )
    assert rej2.status_code == 200
    assert rej2.json()["status"] == "rejected"

    # Retry reject is safe (200)
    rej2_retry = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg2_id}/reject",
        headers=disp1_hdr,
        json={"decision_note": "Retry rejection reason."},
    )
    assert rej2_retry.status_code == 200
    assert rej2_retry.json()["status"] == "rejected"

    # Approve after reject -> 409 Conflict
    app_after_rej = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg2_id}/approve",
        headers=disp1_hdr,
    )
    assert app_after_rej.status_code == 409
    assert "already rejected" in app_after_rej.json()["detail"].lower()


def test_dispatcher_review_blocked_if_order_status_changed(client, urgency_test_db):
    sm1_hdr = auth_headers(client, "sm1")
    disp1_hdr = auth_headers(client, "disp1")

    # Create order & urgency request
    ord_id = create_and_confirm_order_helper(client, sm1_hdr)

    urg_id = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Urgency request while order is confirmed.",
        },
    ).json()["urgency_request_id"]

    # Now change order status directly in DB (simulating order cancelled / delivered / planned)
    order = urgency_test_db.query(Order).filter(Order.order_id == ord_id).first()
    order.status = "delivered"
    urgency_test_db.commit()

    # Attempt to approve -> 409 Conflict
    res_app = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/approve",
        headers=disp1_hdr,
    )
    assert res_app.status_code == 409
    assert "delivered" in res_app.json()["detail"].lower()

    # Attempt to reject -> 409 Conflict
    res_rej = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/reject",
        headers=disp1_hdr,
        json={"decision_note": "Rejection attempted after delivery."},
    )
    assert res_rej.status_code == 409
    assert "delivered" in res_rej.json()["detail"].lower()


# ==============================================================================
# Final Delivery Receipt Resolution Tests
# ==============================================================================

def test_receipt_delivery_resolves_approved_urgency(client, urgency_test_db):
    sm1_hdr = auth_headers(client, "sm1")
    disp1_hdr = auth_headers(client, "disp1")

    # 1. Create & confirm order
    ord_id = create_and_confirm_order_helper(client, sm1_hdr)

    # 2. Request urgency
    urg_res = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Approved urgency to be resolved upon delivery.",
        },
    )
    urg_id = urg_res.json()["urgency_request_id"]

    # 3. Dispatcher approves urgency
    app_res = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/approve",
        headers=disp1_hdr,
        json={"decision_note": "Approved for rush delivery."},
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved"

    # 4. Store Manager confirms receipt (final delivery transition)
    rec_payload = {
        "client_op_id": f"op-rec-{uuid.uuid4().hex[:6]}",
        "pod_id": "POD-RESOLVE-100",
        "items_ok": True,
    }
    rec_res = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/receipt",
        headers=sm1_hdr,
        json=rec_payload,
    )
    assert rec_res.status_code == 200, rec_res.json()

    # 5. Check order status -> delivered, invariants intact
    order = urgency_test_db.query(Order).filter(Order.order_id == ord_id).first()
    assert order.status == "delivered"
    assert order.deferred_prev is False
    assert order.defer_count == 0

    # 6. Check UrgencyRequest -> resolved, resolved_at populated
    urg_db = urgency_test_db.query(UrgencyRequest).filter(UrgencyRequest.urgency_request_id == urg_id).first()
    assert urg_db.status == "resolved"
    assert urg_db.resolved_at is not None


def test_receipt_delivery_leaves_rejected_urgency_rejected(client, urgency_test_db):
    sm1_hdr = auth_headers(client, "sm1")
    disp1_hdr = auth_headers(client, "disp1")

    # 1. Create & confirm order
    ord_id = create_and_confirm_order_helper(client, sm1_hdr)

    # 2. Request urgency
    urg_res = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Urgency request that will be rejected.",
        },
    )
    urg_id = urg_res.json()["urgency_request_id"]

    # 3. Dispatcher rejects urgency
    rej_res = client.post(
        f"/api/v1/dispatcher/urgency-requests/{urg_id}/reject",
        headers=disp1_hdr,
        json={"decision_note": "Rejected due to capacity."},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"

    # 4. Store Manager confirms receipt (final delivery transition)
    rec_payload = {
        "client_op_id": f"op-rec-{uuid.uuid4().hex[:6]}",
        "pod_id": "POD-REJ-200",
        "items_ok": True,
    }
    rec_res = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/receipt",
        headers=sm1_hdr,
        json=rec_payload,
    )
    assert rec_res.status_code == 200

    # 5. Check order status -> delivered
    order = urgency_test_db.query(Order).filter(Order.order_id == ord_id).first()
    assert order.status == "delivered"

    # 6. Check UrgencyRequest -> remains rejected, resolved_at is None
    urg_db = urgency_test_db.query(UrgencyRequest).filter(UrgencyRequest.urgency_request_id == urg_id).first()
    assert urg_db.status == "rejected"
    assert urg_db.resolved_at is None


def test_receipt_delivery_leaves_pending_urgency_pending(client, urgency_test_db):
    sm1_hdr = auth_headers(client, "sm1")

    # 1. Create & confirm order
    ord_id = create_and_confirm_order_helper(client, sm1_hdr)

    # 2. Request urgency (remains pending)
    urg_res = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/urgency-request",
        headers=sm1_hdr,
        json={
            "reason_code": "stockout_risk",
            "reason_text": "Urgency request that remains pending.",
        },
    )
    urg_id = urg_res.json()["urgency_request_id"]

    # 3. Store Manager confirms receipt without prior review
    rec_payload = {
        "client_op_id": f"op-rec-{uuid.uuid4().hex[:6]}",
        "pod_id": "POD-PEND-300",
        "items_ok": True,
    }
    rec_res = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/receipt",
        headers=sm1_hdr,
        json=rec_payload,
    )
    assert rec_res.status_code == 200

    # 4. Check order status -> delivered
    order = urgency_test_db.query(Order).filter(Order.order_id == ord_id).first()
    assert order.status == "delivered"

    # 5. UrgencyRequest remains pending, resolved_at is None
    urg_db = urgency_test_db.query(UrgencyRequest).filter(UrgencyRequest.urgency_request_id == urg_id).first()
    assert urg_db.status == "pending"
    assert urg_db.resolved_at is None


def test_receipt_delivery_without_urgency_unaffected(client, urgency_test_db):
    sm1_hdr = auth_headers(client, "sm1")

    # 1. Create & confirm order without any urgency request
    ord_id = create_and_confirm_order_helper(client, sm1_hdr)

    # 2. Store Manager confirms receipt
    rec_payload = {
        "client_op_id": f"op-rec-{uuid.uuid4().hex[:6]}",
        "pod_id": "POD-NORMAL-400",
        "items_ok": True,
    }
    rec_res = client.post(
        f"/api/v1/store-manager/orders/{ord_id}/receipt",
        headers=sm1_hdr,
        json=rec_payload,
    )
    assert rec_res.status_code == 200

    # 3. Check order status -> delivered
    order = urgency_test_db.query(Order).filter(Order.order_id == ord_id).first()
    assert order.status == "delivered"
    assert order.deferred_prev is False
    assert order.defer_count == 0

    # 4. No urgency request exists
    urg_db = urgency_test_db.query(UrgencyRequest).filter(UrgencyRequest.order_id == ord_id).first()
    assert urg_db is None
