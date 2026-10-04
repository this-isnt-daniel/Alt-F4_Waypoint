import pytest
from datetime import datetime, timezone, date
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.models.urgency import UrgencyRequest
from app.models.deferral import Deferral
from app.models.order import Order, OrderLine
from app.models.outlet import Outlet
from app.models.user import User
from app.schemas.enums import UrgencyRequestStatus, UrgencyReason
from app.schemas.urgency import (
    CreateUrgencyRequest,
    UrgencyDecisionRequest,
    UrgencyRequestResponse,
    DispatcherUrgencyListItemResponse,
)
from app.schemas.shared import OrderResponse as SharedOrderResponse


# ==============================================================================
# 1. Pydantic Schema Tests
# ==============================================================================

def test_urgency_reason_enums():
    """Verify all 6 canonical reason codes exist."""
    expected = {
        "stockout_risk",
        "store_operation_impact",
        "chilled_shortage",
        "time_bound_event",
        "recovery_after_failed_delivery",
        "other",
    }
    actual = {r.value for r in UrgencyReason}
    assert actual == expected


def test_urgency_status_enums():
    """Verify all 4 canonical status values exist."""
    expected = {"pending", "approved", "rejected", "resolved"}
    actual = {s.value for s in UrgencyRequestStatus}
    assert actual == expected


def test_create_urgency_request_valid():
    """Valid CreateUrgencyRequest passes validation."""
    req = CreateUrgencyRequest(
        reason_code=UrgencyReason.stockout_risk,
        reason_text="Critically low on milk stock before evening peak",
        client_op_id="op-123",
    )
    assert req.reason_code == UrgencyReason.stockout_risk
    assert req.client_op_id == "op-123"


def test_create_urgency_request_invalid_reason():
    """Invalid reason code raises ValidationError."""
    with pytest.raises(ValidationError):
        CreateUrgencyRequest(
            reason_code="invalid_reason",  # type: ignore
            reason_text="Critically low on milk stock before evening peak",
        )


def test_create_urgency_request_text_too_short():
    """Reason text under 10 characters raises ValidationError."""
    with pytest.raises(ValidationError):
        CreateUrgencyRequest(
            reason_code=UrgencyReason.other,
            reason_text="Too short",
        )


def test_create_urgency_request_text_too_long():
    """Reason text over 500 characters raises ValidationError."""
    with pytest.raises(ValidationError):
        CreateUrgencyRequest(
            reason_code=UrgencyReason.other,
            reason_text="x" * 501,
        )


def test_urgency_decision_request_approved():
    """Approved decision does not require a decision_note."""
    req = UrgencyDecisionRequest(status=UrgencyRequestStatus.approved)
    assert req.status == UrgencyRequestStatus.approved
    assert req.decision_note is None

    req_with_note = UrgencyDecisionRequest(
        status=UrgencyRequestStatus.approved,
        decision_note="Capacity available on truck V001",
    )
    assert req_with_note.decision_note == "Capacity available on truck V001"


def test_urgency_decision_request_rejected_requires_note():
    """Rejected decision strictly requires a non-empty decision_note."""
    with pytest.raises(ValidationError) as exc:
        UrgencyDecisionRequest(status=UrgencyRequestStatus.rejected)
    assert "decision_note is mandatory when rejecting" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        UrgencyDecisionRequest(status=UrgencyRequestStatus.rejected, decision_note="   ")
    assert "decision_note is mandatory when rejecting" in str(exc.value)

    req = UrgencyDecisionRequest(
        status=UrgencyRequestStatus.rejected,
        decision_note="Depot reefer capacity fully exhausted today",
    )
    assert req.status == UrgencyRequestStatus.rejected
    assert req.decision_note == "Depot reefer capacity fully exhausted today"


def test_urgency_decision_request_disallows_other_statuses():
    """Decision endpoint must only accept approved or rejected."""
    with pytest.raises(ValidationError):
        UrgencyDecisionRequest(status=UrgencyRequestStatus.pending)  # type: ignore

    with pytest.raises(ValidationError):
        UrgencyDecisionRequest(status=UrgencyRequestStatus.resolved)  # type: ignore


def test_shared_order_response_has_deferred_prev():
    """Verify schemas/shared.py OrderResponse contains deferred_prev."""
    data = {
        "order_id": "ORD-1",
        "outlet_id": "OUT-1",
        "order_date": "2026-10-04",
        "status": "confirmed",
        "brand": "fresh",
        "temp_req": "chilled",
        "trip_id": None,
        "stop_seq": None,
        "defer_count": 2,
        "deferred_prev": True,
        "items": [],
    }
    resp = SharedOrderResponse.model_validate(data)
    assert resp.defer_count == 2
    assert resp.deferred_prev is True

    # Test default
    del data["deferred_prev"]
    resp_default = SharedOrderResponse.model_validate(data)
    assert resp_default.deferred_prev is False


# ==============================================================================
# 2. SQLAlchemy Model & Constraint Tests
# ==============================================================================

@pytest.fixture
def db_session():
    """Creates a fresh in-memory SQLite database for model validation."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_deferral_model_nullability_mismatch_fixes():
    """Verify Deferral.new_date is nullable=True and reason is nullable=False."""
    new_date_col = Deferral.__table__.columns["new_date"]
    reason_col = Deferral.__table__.columns["reason"]

    assert new_date_col.nullable is True, "Deferral.new_date must be nullable"
    assert reason_col.nullable is False, "Deferral.reason must be non-nullable"


def test_urgency_model_columns_and_constraints():
    """Verify table name, columns, and constraints on UrgencyRequest model."""
    table = UrgencyRequest.__table__
    assert table.name == "urgency_request"

    assert table.columns["urgency_request_id"].primary_key is True
    assert table.columns["order_id"].unique is True
    assert table.columns["order_id"].nullable is False
    assert table.columns["outlet_id"].nullable is False
    assert table.columns["reported_by"].nullable is False
    assert table.columns["reason_code"].nullable is False
    assert table.columns["reason_text"].nullable is False
    assert table.columns["status"].nullable is False
    assert table.columns["reviewed_by"].nullable is True
    assert table.columns["reviewed_at"].nullable is True
    assert table.columns["decision_note"].nullable is True
    assert table.columns["created_at"].nullable is False
    assert table.columns["resolved_at"].nullable is True
    assert table.columns["client_op_id"].unique is True


def test_urgency_request_creation_and_unique_order(db_session):
    """Verify creating UrgencyRequest and enforcing one request per order."""
    from app.models.depot import Depot
    now = datetime.now(timezone.utc)
    # Setup prerequisite entities
    depot = Depot(depot_id="DEPOT-1", name="Depot 1", lat=6.9, lng=79.9)
    outlet = Outlet(outlet_id="OUT-TEST-1", name="Outlet 1", brand="fresh", depot_id="DEPOT-1")
    user_sm = User(
        user_id="U-SM-1",
        username="sm1",
        name="SM One",
        hashed_pw="hash123",
        role="store_manager",
        outlet_id="OUT-TEST-1",
    )
    user_disp = User(
        user_id="U-DISP-1",
        username="disp1",
        name="Disp One",
        hashed_pw="hash123",
        role="dispatcher",
        depot_id="DEPOT-1",
    )
    order = Order(
        order_id="ORD-TEST-1",
        outlet_id="OUT-TEST-1",
        created_by="U-SM-1",
        brand="fresh",
        temp_req="ambient",
        order_date=date(2026, 10, 4),
        status="confirmed",
        deferred_prev=False,
        defer_count=0,
    )
    db_session.add_all([depot, outlet, user_sm, user_disp, order])
    db_session.commit()

    # Create urgency request
    urgency = UrgencyRequest(
        urgency_request_id="URG-001",
        order_id="ORD-TEST-1",
        outlet_id="OUT-TEST-1",
        reported_by="U-SM-1",
        reason_code=UrgencyReason.stockout_risk.value,
        reason_text="Expected empty shelves by noon",
        status=UrgencyRequestStatus.pending.value,
        created_at=now,
        client_op_id="op-unique-1",
    )
    db_session.add(urgency)
    db_session.commit()

    # Check relationships
    db_session.refresh(order)
    assert order.urgency_request is not None
    assert order.urgency_request.urgency_request_id == "URG-001"
    assert order.urgency_request.status == "pending"

    # Enforce one request per order: creating a second request with same order_id must fail
    duplicate_urgency = UrgencyRequest(
        urgency_request_id="URG-002",
        order_id="ORD-TEST-1",
        outlet_id="OUT-TEST-1",
        reported_by="U-SM-1",
        reason_code=UrgencyReason.chilled_shortage.value,
        reason_text="Duplicate request attempting bypass",
        status=UrgencyRequestStatus.pending.value,
        created_at=now,
        client_op_id="op-unique-2",
    )
    db_session.add(duplicate_urgency)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_urgency_lifecycle_transitions(db_session):
    """Verify pending -> approved -> resolved transitions on UrgencyRequest."""
    from app.models.depot import Depot
    now = datetime.now(timezone.utc)
    depot = Depot(depot_id="DEPOT-2", name="Depot 2", lat=6.9, lng=79.9)
    outlet = Outlet(outlet_id="OUT-TEST-2", name="Outlet 2", brand="fresh", depot_id="DEPOT-2")
    user_sm = User(
        user_id="U-SM-2",
        username="sm2",
        name="SM Two",
        hashed_pw="hash123",
        role="store_manager",
        outlet_id="OUT-TEST-2",
    )
    user_disp = User(
        user_id="U-DISP-2",
        username="disp2",
        name="Disp Two",
        hashed_pw="hash123",
        role="dispatcher",
        depot_id="DEPOT-2",
    )
    order = Order(
        order_id="ORD-TEST-2",
        outlet_id="OUT-TEST-2",
        created_by="U-SM-2",
        brand="fresh",
        temp_req="ambient",
        order_date=date(2026, 10, 4),
        status="confirmed",
        deferred_prev=False,
        defer_count=0,
    )
    db_session.add_all([depot, outlet, user_sm, user_disp, order])
    db_session.commit()

    # 1. Store Manager requests urgency (initially pending)
    urg = UrgencyRequest(
        urgency_request_id="URG-102",
        order_id="ORD-TEST-2",
        outlet_id="OUT-TEST-2",
        reported_by="U-SM-2",
        reason_code="time_bound_event",
        reason_text="Festival promotion requires early morning replenishment",
        status=UrgencyRequestStatus.pending.value,
        created_at=now,
    )
    db_session.add(urg)
    db_session.commit()
    assert urg.status == "pending"
    assert urg.reviewed_by is None

    # 2. Dispatcher approves urgency
    review_time = datetime.now(timezone.utc)
    urg.status = UrgencyRequestStatus.approved.value
    urg.reviewed_by = "U-DISP-2"
    urg.reviewed_at = review_time
    db_session.commit()
    assert urg.status == "approved"
    assert urg.reviewed_by == "U-DISP-2"

    # 3. Urgency does not modify fairness debt (deferred_prev and defer_count remain unchanged)
    assert order.deferred_prev is False
    assert order.defer_count == 0

    # 4. Delivery later resolves approved urgency
    delivery_time = datetime.now(timezone.utc)
    urg.status = UrgencyRequestStatus.resolved.value
    urg.resolved_at = delivery_time
    order.status = "delivered"
    db_session.commit()

    assert urg.status == "resolved"
    assert (urg.resolved_at.replace(tzinfo=timezone.utc) if urg.resolved_at.tzinfo is None else urg.resolved_at) == delivery_time
    assert order.status == "delivered"


def test_deferral_with_nullable_new_date(db_session):
    """Verify Deferral can be created with new_date=None."""
    from app.models.depot import Depot
    now = datetime.now(timezone.utc)
    depot = Depot(depot_id="DEPOT-3", name="Depot 3", lat=6.9, lng=79.9)
    outlet = Outlet(outlet_id="OUT-TEST-3", name="Outlet 3", brand="fresh", depot_id="DEPOT-3")
    user = User(
        user_id="U-DISP-3",
        username="disp3",
        name="Disp Three",
        hashed_pw="hash123",
        role="dispatcher",
        depot_id="DEPOT-3",
    )
    order = Order(
        order_id="ORD-TEST-3",
        outlet_id="OUT-TEST-3",
        created_by="U-DISP-3",
        brand="fresh",
        temp_req="ambient",
        order_date=date(2026, 10, 4),
        status="deferred",
        deferred_prev=True,
        defer_count=1,
    )
    db_session.add_all([depot, outlet, user, order])
    db_session.commit()

    deferral = Deferral(
        deferral_id="DEF-001",
        order_id="ORD-TEST-3",
        outlet_id="OUT-TEST-3",
        original_date=date(2026, 10, 4),
        new_date=None,  # Nullable until rescheduled!
        reason="NO_COMPATIBLE_VEHICLE",
        created_at=now,
        created_by="U-DISP-3",
    )
    db_session.add(deferral)
    db_session.commit()

    saved = db_session.query(Deferral).filter_by(deferral_id="DEF-001").first()
    assert saved is not None
    assert saved.new_date is None
    assert saved.reason == "NO_COMPATIBLE_VEHICLE"


# ==============================================================================
# 3. Real Integration Tests: Deferral Lifecycle & Replanning Flow
# ==============================================================================

def test_real_optimizer_deferral_lifecycle_and_replanning_flow(db_session):
    """
    Real integration test proving:
    - confirmed order -> optimizer can plan
    - optimizer deferral persists new_date=None
    - Store Manager does not recreate the order (409 Conflict)
    - deferred order -> next planning cycle can also be considered
    - deferred order -> planned uses same order_id
    - successful replanning resets deferred_prev=False
    - defer_count remains unchanged
    """
    from app.models.depot import Depot
    from app.models.vehicle import Vehicle
    from app.models.product import Product
    from app.models.plan import DraftPlan
    from app.adapters.optimizer_adapter import (
        generate_daily_draft_plan_operation,
        approve_draft_plan_operation,
        get_reference_data,
    )
    from app.services.order_service import create_or_update_draft_order
    from app.schemas.store_manager import (
        CreateOrderRequest as SMCreateOrderRequest,
        OrderItemInput,
    )
    from fastapi import HTTPException

    import pytest
    try:
        ref = get_reference_data()
    except FileNotFoundError:
        pytest.skip("Authoritative reference CSV directory not found")
    depot = Depot(depot_id="Peliyagoda", name="Peliyagoda Depot", lat=6.9632, lng=79.8837)
    outlet = Outlet(
        outlet_id="OUT004",
        name="Peliyagoda Fresh Store",
        brand="fresh",
        depot_id="Peliyagoda",
        lat=6.9632,
        lng=79.8837,
        dock_type="rear_dock",
        park_constraint="normal",
        window_open="08:00",
        window_close="18:00",
    )
    dispatcher = User(
        user_id="U-DISP-REAL",
        name="Main Dispatcher",
        username="disp_real",
        hashed_pw="hashed123",
        role="dispatcher",
        depot_id="Peliyagoda",
    )
    sm_user = User(
        user_id="U-SM-REAL",
        name="Store Manager",
        username="sm_real",
        hashed_pw="hashed123",
        role="store_manager",
        outlet_id="OUT004",
    )
    vehicle = Vehicle(
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
    product = Product(
        product_id="PROD-F1",
        name="Fresh Bread",
        brand="fresh",
        category="Bakery",
        temp_req="ambient",
        unit="crate",
        unit_wt_kg=5.0,
        unit_vol_m3=0.02,
        active=True,
    )
    db_session.add_all([depot, outlet, dispatcher, sm_user, vehicle, product])
    db_session.commit()

    target_date_1 = date(2026, 10, 4)

    # 1. Place and confirm order for target_date_1
    order = Order(
        order_id="ORD-FLOW-001",
        outlet_id="OUT004",
        created_by="U-SM-REAL",
        brand="fresh",
        temp_req="ambient",
        order_date=target_date_1,
        status="confirmed",
        order_units=20,
        order_wt_kg=100.0,
        order_vol_m3=0.4,
        window_open="08:00",
        window_close="18:00",
        deferred_prev=False,
        defer_count=0,
    )
    line = OrderLine(
        line_item_id="LI-FLOW-1",
        order_id="ORD-FLOW-001",
        product_id="PROD-F1",
        quantity=20,
    )
    order.lines.append(line)
    db_session.add(order)
    db_session.commit()

    # 2. Confirmed order -> optimizer can plan
    draft_1 = generate_daily_draft_plan_operation(
        db=db_session,
        depot_id="Peliyagoda",
        target_date=target_date_1,
        brand="fresh",
        user_id="U-DISP-REAL",
    )
    assert draft_1["status"] == "FEASIBLE"
    assert len(draft_1["trips"]) >= 1
    plan_id_1 = draft_1["plan_id"]

    # 3. Simulate operational deferral during plan finalization
    import copy
    db_plan = db_session.query(DraftPlan).filter_by(plan_id=plan_id_1).first()
    new_plan_data = copy.deepcopy(db_plan.plan_data)
    new_plan_data["trips"] = []
    new_plan_data["deferred_orders"] = [
        {"order_ref": "ORD-FLOW-001", "reason": "VOLUME_CAPACITY"}
    ]
    new_plan_data["validation"] = {"valid": True, "errors": []}
    db_plan.plan_data = new_plan_data
    db_session.commit()

    approve_draft_plan_operation(
        db=db_session,
        plan_id=plan_id_1,
        user_id="U-DISP-REAL",
        client_op_id="op-approve-deferral-1",
        depot_id="Peliyagoda",
    )

    db_session.refresh(order)
    assert order.status == "deferred"
    assert order.defer_count == 1
    assert order.deferred_prev is True

    # Check optimizer deferral persists new_date=None
    deferral_record = db_session.query(Deferral).filter_by(order_id="ORD-FLOW-001").first()
    assert deferral_record is not None
    assert deferral_record.new_date is None, "Optimizer deferral must persist new_date=None"
    assert deferral_record.original_date == target_date_1

    # 4. Store Manager cannot recreate the order (must get 409 Conflict)
    duplicate_request = SMCreateOrderRequest(
        outlet_id="OUT004",
        brand="fresh",
        temp_req="ambient",
        order_date=target_date_1,
        items=[OrderItemInput(product_id="PROD-F1", quantity=25)],
    )
    with pytest.raises(HTTPException) as exc_info:
        create_or_update_draft_order(
            db=db_session,
            request=duplicate_request,
            store_manager_outlet="OUT004",
            user_id="U-SM-REAL",
        )
    assert exc_info.value.status_code == 409
    assert db_session.query(Order).filter_by(order_id="ORD-FLOW-001").count() == 1

    # 5. Next planning cycle (target_date_2): deferred order is considered
    target_date_2 = date(2026, 10, 5)
    draft_2 = generate_daily_draft_plan_operation(
        db=db_session,
        depot_id="Peliyagoda",
        target_date=target_date_2,
        brand="fresh",
        user_id="U-DISP-REAL",
    )
    assert draft_2["status"] == "FEASIBLE"
    assert len(draft_2["trips"]) >= 1

    # The deferred order must be planned in the trips
    all_planned_refs = [
        o_ref
        for trip in draft_2["trips"]
        for stop in (trip.get("driver_itinerary") or trip.get("stops", []))
        for o_ref in stop.get("order_refs", [])
    ]
    assert "ORD-FLOW-001" in all_planned_refs, "Deferred order must be planned in the next cycle"

    # 6. Approve plan in cycle 2: deferred -> planned
    plan_id_2 = draft_2["plan_id"]
    approve_draft_plan_operation(
        db=db_session,
        plan_id=plan_id_2,
        user_id="U-DISP-REAL",
        client_op_id="op-approve-replan-2",
        depot_id="Peliyagoda",
    )

    db_session.refresh(order)
    # Proves: deferred order -> planned uses same order_id
    assert order.order_id == "ORD-FLOW-001"
    assert order.status == "planned"
    # Proves: successful replanning resets deferred_prev=False
    assert order.deferred_prev is False
    # Proves: defer_count remains unchanged
    assert order.defer_count == 1
    assert order.trip_id is not None


def test_planning_service_confirm_plan_accepts_deferred_order(db_session):
    """
    Tests planning_service.confirm_plan():
    - allows deferred -> planned transition
    - rejects invalid statuses (draft, loaded, out_for_delivery, delivered)
    - resets deferred_prev to False
    - preserves defer_count and order_id
    """
    from app.models.depot import Depot
    from app.services.planning_service import confirm_plan, _mock_planning_runs
    from app.schemas.dispatcher import ProposedPlanResponse, ProposedTrip, ProposedTripStop
    from fastapi import HTTPException

    depot = Depot(depot_id="DEPOT-CONFIRM", name="Confirm Depot", lat=6.9, lng=79.9)
    outlet = Outlet(outlet_id="OUT-CONFIRM", name="Outlet Confirm", brand="fresh", depot_id="DEPOT-CONFIRM")
    disp = User(
        user_id="U-DISP-C",
        username="disp_c",
        name="Dispatcher C",
        hashed_pw="h123",
        role="dispatcher",
        depot_id="DEPOT-CONFIRM",
    )
    # Order currently deferred
    order = Order(
        order_id="ORD-CONFIRM-1",
        outlet_id="OUT-CONFIRM",
        created_by="U-DISP-C",
        brand="fresh",
        temp_req="ambient",
        order_date=date(2026, 10, 4),
        status="deferred",
        deferred_prev=True,
        defer_count=2,
    )
    line = OrderLine(
        line_item_id="LI-CONFIRM-1",
        order_id="ORD-CONFIRM-1",
        product_id="P-C1",
        quantity=10,
    )
    order.lines.append(line)
    db_session.add_all([depot, outlet, disp, order])
    db_session.commit()

    # Setup mock planning run that plans ORD-CONFIRM-1
    run_id = "RUN-TEST-001"
    _mock_planning_runs[run_id] = ProposedPlanResponse(
        run_id=run_id,
        depot_id="DEPOT-CONFIRM",
        target_date=date(2026, 10, 5),
        trips=[
            ProposedTrip(
                vehicle_id="V-TEST-1",
                brand="fresh",
                temp_type="ambient",
                stops=[
                    ProposedTripStop(order_id="ORD-CONFIRM-1", sequence=1, expected_arrival="09:00")
                ],
            )
        ],
        deferred_orders=[],
    )

    # 1. Confirm plan with deferred order
    res = confirm_plan(
        db=db_session,
        run_id=run_id,
        client_op_id="op-confirm-plan-1",
        dispatcher_depot="DEPOT-CONFIRM",
        user_id="U-DISP-C",
    )
    assert res == {"status": "applied"}

    db_session.refresh(order)
    assert order.order_id == "ORD-CONFIRM-1"
    assert order.status == "planned"
    assert order.deferred_prev is False, "Replanning must reset deferred_prev to False"
    assert order.defer_count == 2, "Historical defer_count must be preserved"
    assert order.trip_id is not None

    # 2. Verify invalid statuses are rejected
    for idx, invalid_status in enumerate(["draft", "loaded", "out_for_delivery", "delivered"]):
        order.status = invalid_status
        db_session.commit()

        run_id_invalid = f"RUN-TEST-INV-{idx}"
        _mock_planning_runs[run_id_invalid] = ProposedPlanResponse(
            run_id=run_id_invalid,
            depot_id="DEPOT-CONFIRM",
            target_date=date(2026, 10, 5),
            trips=[
                ProposedTrip(
                    vehicle_id=f"V-TEST-INV-{idx}",
                    brand="fresh",
                    temp_type="ambient",
                    stops=[
                        ProposedTripStop(order_id="ORD-CONFIRM-1", sequence=1, expected_arrival="09:00")
                    ],
                )
            ],
            deferred_orders=[],
        )

        with pytest.raises(HTTPException) as exc_info:
            confirm_plan(
                db=db_session,
                run_id=run_id_invalid,
                client_op_id=f"op-invalid-{invalid_status}",
                dispatcher_depot="DEPOT-CONFIRM",
                user_id="U-DISP-C",
            )
        assert exc_info.value.status_code == 400
        assert f"is not in confirmed or deferred state (current: {invalid_status})" in exc_info.value.detail


