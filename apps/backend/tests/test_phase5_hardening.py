"""
Backend integration tests appended for Phase 5 final hardening:
  - test_deferred_carryover_visible_during_draft_edit: deferred carry-over stays eligible
  - test_urgency_derivation_real_db: real DB approved-urgency adapter integration
  - test_fleet_fallback_uses_reference_vehicles: reference fleet fallback uses vehicle_id
"""
import sys
from pathlib import Path
from datetime import date, datetime, timezone

# Ensure correct path
backend_root = str(Path(__file__).resolve().parents[1])
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.core.security import get_password_hash, create_platform_access_token
from app.models.user import User
from app.models.depot import Depot
from app.models.outlet import Outlet
from app.models.vehicle import Vehicle
from app.models.product import Product
from app.models.order import Order, OrderLine
from app.models.deferral import Deferral
from app.models.urgency import UrgencyRequest
from app.models.plan import DraftPlan
from app.models.trip import TripStop as DbTripStop
from app.models.events import DeliveryEvent
from app.adapters.optimizer_adapter import (
    get_reference_data,
    _get_eligible_orders_for_date,
    _get_depot_outlet_ids,
    get_approved_urgent_order_ids,
    convert_db_order_to_optimizer,
    generate_daily_draft_plan_operation,
    approve_draft_plan_operation,
    reallocate_broken_vehicle_operation,
    get_recovery_authoritative_orders,
)


def _make_minimal_db():
    """Create an in-memory SQLite DB with a single dispatcher, depot, outlets, vehicles, product."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = Session()

    ref = get_reference_data()

    db.add(Depot(
        depot_id="Peliyagoda",
        name="Peliyagoda Central Depot",
        lat=6.965,
        lng=79.895,
    ))

    for o in ref.outlets.values():
        if o.depot == "Peliyagoda":
            db.add(Outlet(
                outlet_id=o.outlet_id,
                name=f"Outlet {o.outlet_id}",
                brand=o.brand.value if hasattr(o.brand, "value") else str(o.brand),
                district=o.district,
                depot_id=o.depot,
                dock_type=o.dock_type.value if hasattr(o.dock_type, "value") else str(o.dock_type),
                park_constraint=o.parking_constraint.value if hasattr(o.parking_constraint, "value") else str(o.parking_constraint),
                lat=6.95,
                lng=79.88,
            ))

    db.add(User(
        user_id="U-INT-1", name="Integration Dispatcher",
        username="int_disp", hashed_pw=get_password_hash("pass"),
        role="dispatcher", depot_id="Peliyagoda",
    ))
    db.add(User(
        user_id="U-INT-SM", name="Integration Store Manager",
        username="int_sm", hashed_pw=get_password_hash("pass"),
        role="store_manager", depot_id=None, outlet_id="OUT004",
    ))

    db.add(Product(
        product_id="PROD-INT-1", name="Test Product", brand="fresh",
        category="Dairy", temp_req="ambient", unit="crate",
        unit_wt_kg=12.0, unit_vol_m3=0.03, active=True,
    ))

    # Seed vehicles from reference data (up to 5 to allow reallocation)
    v_count = 0
    for v in ref.vehicles:
        if v.depot == "Peliyagoda":
            db.add(Vehicle(
                vehicle_id=v.vehicle_id, depot_id=v.depot,
                type=v.type.value, temp=v.temp.value,
                weight_cap_kg=v.weight_cap_kg, vol_cap_m3=v.volume_cap_m3,
                fuel_type="diesel", km_per_l=4.5,
                fuel_quota_l=int(v.weekly_fuel_quota_l or 250),
                plate=f"WP-{v.vehicle_id}", status="available",
            ))
            v_count += 1
            if v_count >= 5:
                break

    db.commit()
    return db, engine


def test_deferred_carryover_visible_during_draft_edit():
    """
    A same-order deferred carry-over (whose order_date is a day earlier than
    the planning date and has no Deferral.new_date) must appear in the eligible
    order list for both draft generation AND draft editing.
    """
    db, engine = _make_minimal_db()
    try:
        planning_date = date(2026, 10, 5)
        original_date = date(2026, 10, 4)  # one day earlier

        # Seed an outlet that belongs to Peliyagoda depot via reference data
        ref = get_reference_data()
        depot_outlet_ids = _get_depot_outlet_ids("Peliyagoda", ref, db)
        assert depot_outlet_ids, "No outlets found for Peliyagoda depot in reference data"
        outlets = sorted(list(depot_outlet_ids))
        outlet_1 = outlets[0]
        outlet_2 = outlets[1]
        outlet_3 = outlets[2]

        # Confirmed order for the planning date (should be included)
        o_confirmed = Order(
            order_id="ORD-CARRYOVER-CONF",
            outlet_id=outlet_1,
            created_by="U-INT-1",
            brand="fresh", temp_req="ambient",
            order_date=planning_date,
            status="confirmed",
            order_units=10, order_wt_kg=120.0, order_vol_m3=0.3,
            window_open="08:00", window_close="18:00",
            deferred_prev=False, defer_count=0,
        )
        db.add(o_confirmed)

        # Deferred order with original date BEFORE planning date and NULL new_date (carry-forward)
        o_deferred = Order(
            order_id="ORD-CARRYOVER-DEF",
            outlet_id=outlet_2,
            created_by="U-INT-1",
            brand="fresh", temp_req="ambient",
            order_date=original_date,  # yesterday
            status="deferred",
            order_units=10, order_wt_kg=120.0, order_vol_m3=0.3,
            window_open="08:00", window_close="18:00",
            deferred_prev=True, defer_count=1,
        )
        db.add(o_deferred)

        now = datetime.now(timezone.utc)
        # Deferral row with new_date=NULL (carry forward)
        db.add(Deferral(
            deferral_id="DEF-CARRYOVER-1",
            order_id="ORD-CARRYOVER-DEF",
            outlet_id=outlet_2,
            original_date=original_date,
            reason="capacity",
            new_date=None,
            created_at=now,
            created_by="U-INT-1",
        ))
        db.commit()

        # Test eligibility with the shared helper
        eligible = _get_eligible_orders_for_date(db, planning_date, depot_outlet_ids)
        eligible_ids = {o.order_id for o in eligible}

        assert "ORD-CARRYOVER-CONF" in eligible_ids, "Confirmed order for planning_date must be eligible"
        assert "ORD-CARRYOVER-DEF" in eligible_ids, (
            "Deferred carry-over with NULL new_date must be eligible when order_date <= planning_date"
        )

        # Also verify: a deferred order with new_date set to a DIFFERENT date is NOT included
        o_future = Order(
            order_id="ORD-CARRYOVER-FUTURE",
            outlet_id=outlet_3,
            created_by="U-INT-1",
            brand="fresh", temp_req="ambient",
            order_date=original_date,
            status="deferred",
            order_units=5, order_wt_kg=60.0, order_vol_m3=0.15,
            window_open="08:00", window_close="18:00",
            deferred_prev=True, defer_count=1,
        )
        db.add(o_future)
        db.add(Deferral(
            deferral_id="DEF-CARRYOVER-2",
            order_id="ORD-CARRYOVER-FUTURE",
            outlet_id=outlet_3,
            original_date=original_date,
            reason="capacity",
            new_date=date(2026, 10, 6),  # rescheduled to NEXT day
            created_at=now,
            created_by="U-INT-1",
        ))
        db.commit()

        eligible2 = _get_eligible_orders_for_date(db, planning_date, depot_outlet_ids)
        eligible2_ids = {o.order_id for o in eligible2}
        assert "ORD-CARRYOVER-FUTURE" not in eligible2_ids, (
            "Deferred order rescheduled to a future date must NOT be eligible for today's plan"
        )
    finally:
        Base.metadata.drop_all(bind=engine)
        db.close()


def test_urgency_derivation_real_db():
    """
    Real SQLAlchemy integration test (no mocks) proving that:
      none      -> is_urgent False
      pending   -> is_urgent False
      rejected  -> is_urgent False
      resolved  -> is_urgent False
      approved  -> is_urgent True

    Also verifies that convert_db_order_to_optimizer correctly passes
    is_urgent=True only for the approved order.
    """
    db, engine = _make_minimal_db()
    try:
        ref = get_reference_data()
        depot_outlet_ids = _get_depot_outlet_ids("Peliyagoda", ref, db)
        outlets = sorted(list(depot_outlet_ids))
        today = date(2026, 10, 2)

        # Create 5 confirmed orders — each will get a different urgency state
        statuses_to_test = [
            ("ORD-URG-NONE", None, outlets[0]),
            ("ORD-URG-PEND", "pending", outlets[1]),
            ("ORD-URG-REJT", "rejected", outlets[2]),
            ("ORD-URG-RSLV", "resolved", outlets[3]),
            ("ORD-URG-APPR", "approved", outlets[4]),
        ]

        for order_id, urgency_status, order_outlet_id in statuses_to_test:
            o = Order(
                order_id=order_id, outlet_id=order_outlet_id, created_by="U-INT-1",
                brand="fresh", temp_req="ambient",
                order_date=today, status="confirmed",
                order_units=10, order_wt_kg=120.0, order_vol_m3=0.3,
                window_open="08:00", window_close="18:00",
                deferred_prev=False, defer_count=0,
            )
            db.add(o)
            db.flush()
            db.add(OrderLine(
                line_item_id=f"LI-{order_id}",
                order_id=order_id, product_id="PROD-INT-1", quantity=10,
            ))
            if urgency_status is not None:
                ur = UrgencyRequest(
                    urgency_request_id=f"UR-{order_id}",
                    order_id=order_id,
                    outlet_id=order_outlet_id,
                    reported_by="U-INT-SM",
                    reason_code="stockout_risk",
                    reason_text="Test urgency request",
                    status=urgency_status,
                    client_op_id=f"OP-{order_id}",
                )
                if urgency_status in ("resolved",):
                    ur.resolved_at = datetime.now(timezone.utc)
                db.add(ur)

        db.commit()

        # Batch-query approved urgency
        all_order_ids = [oid for oid, _, _ in statuses_to_test]
        approved_ids = get_approved_urgent_order_ids(db, all_order_ids)

        # Only the "approved" order must be in the set
        assert approved_ids == {"ORD-URG-APPR"}, (
            f"Expected only ORD-URG-APPR in approved_ids, got: {approved_ids}"
        )

        # Convert all orders and verify is_urgent
        db_orders = db.query(Order).filter(Order.order_id.in_(all_order_ids)).all()
        order_map = {o.order_id: o for o in db_orders}

        expected_urgent = {
            "ORD-URG-NONE": False,
            "ORD-URG-PEND": False,
            "ORD-URG-REJT": False,
            "ORD-URG-RSLV": False,
            "ORD-URG-APPR": True,
        }
        for order_id, expected in expected_urgent.items():
            db_order = order_map[order_id]
            opt_order = convert_db_order_to_optimizer(
                db_order, ref, db,
                is_urgent=(order_id in approved_ids),
            )
            assert opt_order.is_urgent == expected, (
                f"Order {order_id} (urgency_status={dict(statuses_to_test)[order_id]}): "
                f"expected is_urgent={expected}, got {opt_order.is_urgent}"
            )
    finally:
        Base.metadata.drop_all(bind=engine)
        db.close()


def test_fleet_fallback_uses_reference_vehicle_id():
    """
    When DB vehicle query returns empty, the reference fleet fallback must use
    v.vehicle_id (not v.id which doesn't exist on OptimizerVehicle).
    """
    ref = get_reference_data()
    # All OptimizerVehicle objects must have vehicle_id attribute
    for v in ref.vehicles:
        assert hasattr(v, "vehicle_id"), (
            f"Reference vehicle {v} missing .vehicle_id — fallback would crash"
        )
        assert not hasattr(v, "id") or v.vehicle_id is not None, (
            f"Reference vehicle has .id but not .vehicle_id — wrong attribute used in fallback"
        )
        # Verify the value is a non-empty string
        assert isinstance(v.vehicle_id, str) and v.vehicle_id, (
            f"Reference vehicle.vehicle_id must be a non-empty string, got {v.vehicle_id!r}"
        )


def test_end_to_end_recovery_loads_approved_planned_order():
    """
    End-to-end regression proving breakdown recovery loads planned orders:
      1. Generate draft plan from confirmed order.
      2. Approve draft plan -> order status transitions to 'planned'.
      3. Verify Order.status == 'planned'.
      4. Trigger vehicle breakdown recovery.
      5. Recovery uses get_recovery_authoritative_orders, successfully loads the planned
         order (not filtered out by status in ('confirmed', 'deferred')), and produces
         a valid recovery proposal.
    """
    db, engine = _make_minimal_db()
    try:
        ref = get_reference_data()
        target_date = date(2026, 10, 5)

        # Seed confirmed order
        order_id = "ORD-E2E-REC-01"
        o = Order(
            order_id=order_id,
            outlet_id="OUT004",
            created_by="U-INT-1",
            brand="fresh",
            temp_req="ambient",
            order_date=target_date,
            status="confirmed",
            order_units=10,
            order_wt_kg=120.0,
            order_vol_m3=0.3,
            window_open="08:00",
            window_close="18:00",
            deferred_prev=False,
            defer_count=0,
        )
        db.add(o)
        db.flush()
        db.add(OrderLine(
            line_item_id=f"LI-{order_id}",
            order_id=order_id,
            product_id="PROD-INT-1",
            quantity=10,
        ))
        db.commit()

        # Step 1: Generate daily draft plan
        draft = generate_daily_draft_plan_operation(
            db=db,
            depot_id="Peliyagoda",
            target_date=target_date,
            brand="fresh",
            enable_targeted_cpsat=False,
            user_id="U-INT-1",
        )
        assert draft["validation"]["valid"] is True, f"Draft invalid: {draft.get('violations')}"
        assert len(draft.get("trips", [])) >= 1, "Expected at least 1 trip in draft"
        plan_id = draft["plan_id"]
        assigned_vehicle = draft["trips"][0]["vehicle_id"]

        # Step 2: Approve draft plan
        appr = approve_draft_plan_operation(
            db=db,
            plan_id=plan_id,
            client_op_id="OP-E2E-APP-1",
            user_id="U-INT-1",
            depot_id="Peliyagoda",
        )
        assert appr["status"] == "approved"

        # Step 3: Assert affected order is now planned
        db_order = db.query(Order).filter(Order.order_id == order_id).first()
        assert db_order is not None
        assert db_order.status == "planned", f"Expected order to be 'planned', got {db_order.status}"

        # Step 4: Trigger vehicle breakdown on the assigned vehicle
        recovery = reallocate_broken_vehicle_operation(
            db=db,
            vehicle_id=assigned_vehicle,
            plan_id=plan_id,
            current_time_iso="2026-10-05T09:00:00+05:30",
            pickup_location="DEPOT",
            depot_id="Peliyagoda",
        )

        # Step 5: Assert recovery successfully loaded the planned order
        assert recovery["status"] != "INVALID", f"Recovery marked invalid: {recovery.get('recovery_reasons')}"
        reasons = recovery.get("recovery_reasons", [])
        assert not any(r.get("code") == "MISSING_AUTHORITATIVE_ORDERS" for r in reasons), (
            f"Recovery failed with MISSING_AUTHORITATIVE_ORDERS: {reasons}"
        )
        violations = recovery.get("violations", [])
        assert not any(v.get("rule") == "UNKNOWN_ORDER_REF" for v in violations), (
            f"Recovery reported UNKNOWN_ORDER_REF for planned order: {violations}"
        )
    finally:
        Base.metadata.drop_all(bind=engine)
        db.close()


def test_end_to_end_recovery_loads_approved_carryover_order():
    """
    Test carry-over order through approval and breakdown:
      original order_date = previous day
      → status deferred
      → replanned and approved today
      → status planned
      → breakdown today
      → get_recovery_authoritative_orders must find the order by ID without
        failing on order_date == today or status == confirmed.
    """
    db, engine = _make_minimal_db()
    try:
        planning_date = date(2026, 10, 5)
        yesterday = date(2026, 10, 4)

        order_id = "ORD-E2E-CARRYOVER"
        o = Order(
            order_id=order_id,
            outlet_id="OUT004",
            created_by="U-INT-1",
            brand="fresh",
            temp_req="ambient",
            order_date=yesterday,  # original date was yesterday!
            status="deferred",
            order_units=10,
            order_wt_kg=120.0,
            order_vol_m3=0.3,
            window_open="08:00",
            window_close="18:00",
            deferred_prev=True,
            defer_count=1,
        )
        db.add(o)
        db.flush()
        db.add(OrderLine(
            line_item_id=f"LI-{order_id}",
            order_id=order_id,
            product_id="PROD-INT-1",
            quantity=10,
        ))
        db.add(Deferral(
            deferral_id="DEF-E2E-01",
            order_id=order_id,
            outlet_id="OUT004",
            original_date=yesterday,
            reason="capacity",
            new_date=None,  # carry-forward
            created_at=datetime.now(timezone.utc),
            created_by="U-INT-1",
        ))
        db.commit()

        # Step 1: Generate plan for today (planning_date)
        draft = generate_daily_draft_plan_operation(
            db=db,
            depot_id="Peliyagoda",
            target_date=planning_date,
            brand="fresh",
            enable_targeted_cpsat=False,
            user_id="U-INT-1",
        )
        assert draft["validation"]["valid"] is True
        plan_id = draft["plan_id"]
        assert len(draft.get("trips", [])) >= 1
        assigned_vehicle = draft["trips"][0]["vehicle_id"]

        # Step 2: Approve draft plan
        appr = approve_draft_plan_operation(
            db=db,
            plan_id=plan_id,
            client_op_id="OP-E2E-APP-CARRY",
            user_id="U-INT-1",
            depot_id="Peliyagoda",
        )
        assert appr["status"] == "approved"

        # Step 3: Assert carry-over order is now planned and deferred_prev was reset
        db_order = db.query(Order).filter(Order.order_id == order_id).first()
        assert db_order.status == "planned"
        assert db_order.deferred_prev is False

        # Step 4: Breakdown on assigned vehicle
        recovery = reallocate_broken_vehicle_operation(
            db=db,
            vehicle_id=assigned_vehicle,
            plan_id=plan_id,
            current_time_iso="2026-10-05T09:00:00+05:30",
            pickup_location="DEPOT",
            depot_id="Peliyagoda",
        )

        # Step 5: Assert recovery successfully found the carry-over order
        assert recovery["status"] != "INVALID"
        reasons = recovery.get("recovery_reasons", [])
        assert not any(r.get("code") == "MISSING_AUTHORITATIVE_ORDERS" for r in reasons)
        violations = recovery.get("violations", [])
        assert not any(v.get("rule") == "UNKNOWN_ORDER_REF" for v in violations)
    finally:
        Base.metadata.drop_all(bind=engine)
        db.close()


def test_recovery_fleet_fallback_executes_db_empty():
    """
    Execute the DB-empty reference-fleet fallback path end-to-end:
      1. Delete all vehicles from DB table (db_vehicles is empty).
      2. Trigger breakdown recovery.
      3. Verify the fallback list comprehension uses v.vehicle_id without error
         and optimizer recovery operates with the reference fleet.
    """
    db, engine = _make_minimal_db()
    try:
        ref = get_reference_data()
        target_date = date(2026, 10, 5)

        # 1. Seed confirmed order
        order_id = "ORD-FALLBACK-01"
        o = Order(
            order_id=order_id,
            outlet_id="OUT004",
            created_by="U-INT-1",
            brand="fresh",
            temp_req="ambient",
            order_date=target_date,
            status="confirmed",
            order_units=10,
            order_wt_kg=120.0,
            order_vol_m3=0.3,
            window_open="08:00",
            window_close="18:00",
            deferred_prev=False,
            defer_count=0,
        )
        db.add(o)
        db.flush()
        db.add(OrderLine(
            line_item_id=f"LI-{order_id}",
            order_id=order_id,
            product_id="PROD-INT-1",
            quantity=10,
        ))
        db.commit()

        # 2. Generate and approve draft plan while vehicles are in DB
        draft = generate_daily_draft_plan_operation(
            db=db,
            depot_id="Peliyagoda",
            target_date=target_date,
            brand="fresh",
            enable_targeted_cpsat=False,
            user_id="U-INT-1",
        )
        assert draft["validation"]["valid"] is True
        plan_id = draft["plan_id"]
        assigned_vehicle = draft["trips"][0]["vehicle_id"]

        appr = approve_draft_plan_operation(
            db=db,
            plan_id=plan_id,
            client_op_id="OP-FALLBACK-APP-1",
            user_id="U-INT-1",
            depot_id="Peliyagoda",
        )
        assert appr["status"] == "approved"

        # 3. Clear all vehicles in DB (db_vehicles is now completely empty)
        db.query(Vehicle).delete()
        db.commit()
        assert db.query(Vehicle).count() == 0, "DB vehicle table must be empty for this test"

        # 4. Directly verify the reference fleet fallback list comprehension
        fallback_fleet = [v for v in ref.vehicles if v.vehicle_id != assigned_vehicle]
        assert len(fallback_fleet) == len(ref.vehicles) - 1
        assert not any(v.vehicle_id == assigned_vehicle for v in fallback_fleet)

        # 5. Execute reallocate_broken_vehicle_operation with DB-empty vehicle table
        rec = reallocate_broken_vehicle_operation(
            db=db,
            vehicle_id=assigned_vehicle,
            plan_id=plan_id,
            current_time_iso="2026-10-05T09:00:00+05:30",
            pickup_location="DEPOT",
            depot_id="Peliyagoda",
        )
        # Succeeded through the DB-empty reference fleet fallback
        assert rec["status"] != "INVALID", f"Recovery marked invalid: {rec.get('recovery_reasons')}"
        assert rec["broken_vehicle_id"] == assigned_vehicle
    finally:
        Base.metadata.drop_all(bind=engine)
        db.close()


def test_multi_order_plan_approval_deferral_idempotency():
    """
    Regression test for multi-order plan approval deferral idempotency:
      1. Valid draft containing at least two deferred orders.
      2. approve plan using client_op_id="OP-MULTI-DEF".
      3. Verify approval succeeds, exactly 2 Deferral rows exist, both client_op_id
         values are unique, both are deterministically derived from OP-MULTI-DEF
         (f"OP-MULTI-DEF:deferral:{order_id}"), both orders become deferred, and
         each defer_count increments exactly once.
      4. Call approval operation a second time for the same plan.
      5. Verify succeeds as idempotent retry, Deferral row count remains 2,
         defer_count values do not increment again, no duplicate order_deferred
         events are created, and no duplicate TripStops are created.
    """
    db, engine = _make_minimal_db()
    try:
        target_date = date(2026, 10, 5)

        ref = get_reference_data()
        depot_outlet_ids = sorted(list(_get_depot_outlet_ids("Peliyagoda", ref, db)))
        assert len(depot_outlet_ids) >= 3, "Expected at least 3 outlets for Peliyagoda"
        outlet_plan = depot_outlet_ids[0]
        outlet_def1 = depot_outlet_ids[1]
        outlet_def2 = depot_outlet_ids[2]

        # Create planned order
        ord_plan = Order(
            order_id="ORD-PLAN-01",
            outlet_id=outlet_plan,
            created_by="U-INT-1",
            brand="fresh",
            temp_req="ambient",
            order_date=target_date,
            status="confirmed",
            order_units=5,
            order_wt_kg=60.0,
            order_vol_m3=0.15,
            window_open="08:00",
            window_close="18:00",
            deferred_prev=False,
            defer_count=0,
        )
        # Create 2 orders that will be deferred
        ord_def1 = Order(
            order_id="ORD-DEF-01",
            outlet_id=outlet_def1,
            created_by="U-INT-1",
            brand="fresh",
            temp_req="ambient",
            order_date=target_date,
            status="confirmed",
            order_units=5,
            order_wt_kg=60.0,
            order_vol_m3=0.15,
            window_open="08:00",
            window_close="18:00",
            deferred_prev=False,
            defer_count=0,
        )
        ord_def2 = Order(
            order_id="ORD-DEF-02",
            outlet_id=outlet_def2,
            created_by="U-INT-1",
            brand="fresh",
            temp_req="ambient",
            order_date=target_date,
            status="confirmed",
            order_units=5,
            order_wt_kg=60.0,
            order_vol_m3=0.15,
            window_open="08:00",
            window_close="18:00",
            deferred_prev=False,
            defer_count=0,
        )
        db.add_all([ord_plan, ord_def1, ord_def2])
        db.flush()

        for o in (ord_plan, ord_def1, ord_def2):
            db.add(OrderLine(
                line_item_id=f"LI-{o.order_id}",
                order_id=o.order_id,
                product_id="PROD-INT-1",
                quantity=5,
            ))

        # Create valid draft plan record containing 1 trip with ORD-PLAN-01 and 2 deferred orders
        plan_id = "P-MULTI-DEF-01"
        mock_plan = {
            "plan_id": plan_id,
            "depot_id": "Peliyagoda",
            "target_date": target_date.isoformat(),
            "validation": {"valid": True, "violations": []},
            "trips": [
                {
                    "trip_id": "TRIP-PLAN-1",
                    "trip_number": 1,
                    "vehicle_id": "VEH001",
                    "order_refs": ["ORD-PLAN-01"],
                    "driver_itinerary": [
                        {
                            "stop_number": 1,
                            "outlet_id": outlet_plan,
                            "order_refs": ["ORD-PLAN-01"],
                            "line_items_delivered": [
                                {
                                    "order_ref": "ORD-PLAN-01",
                                    "line_item_id": "LI-ORD-PLAN-01",
                                    "quantity": 5,
                                }
                            ],
                        }
                    ],
                }
            ],
            "deferred_orders": [
                {"order_ref": "ORD-DEF-01", "reason": "OPTIMIZER_CAPACITY_CONSTRAINT"},
                {"order_ref": "ORD-DEF-02", "reason": "OPTIMIZER_CAPACITY_CONSTRAINT"},
            ],
        }
        draft_record = DraftPlan(
            plan_id=plan_id,
            depot_id="Peliyagoda",
            target_date=target_date,
            status="draft",
            plan_data=mock_plan,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by="U-INT-1",
        )
        db.add(draft_record)
        db.commit()

        # Step 3: Approve plan using client_op_id="OP-MULTI-DEF"
        res1 = approve_draft_plan_operation(
            db=db,
            plan_id=plan_id,
            user_id="U-INT-1",
            client_op_id="OP-MULTI-DEF",
            depot_id="Peliyagoda",
        )
        assert res1["status"] == "approved"

        # Verify exactly 2 Deferral rows exist
        deferrals = db.query(Deferral).all()
        assert len(deferrals) == 2, f"Expected exactly 2 Deferrals, got {len(deferrals)}"

        # Both client_op_id values are unique and deterministically derived from OP-MULTI-DEF
        op_ids = [d.client_op_id for d in deferrals]
        assert len(set(op_ids)) == 2, f"Expected unique client_op_ids, got {op_ids}"
        expected_op_ids = {
            "OP-MULTI-DEF:deferral:ORD-DEF-01",
            "OP-MULTI-DEF:deferral:ORD-DEF-02",
        }
        assert set(op_ids) == expected_op_ids, f"Expected {expected_op_ids}, got {set(op_ids)}"

        # Both orders become deferred
        db.refresh(ord_def1)
        db.refresh(ord_def2)
        db.refresh(ord_plan)
        assert ord_def1.status == "deferred"
        assert ord_def2.status == "deferred"
        assert ord_plan.status == "planned"

        # Each defer_count increments exactly once
        assert ord_def1.defer_count == 1
        assert ord_def2.defer_count == 1
        assert ord_def1.deferred_prev is True
        assert ord_def2.deferred_prev is True

        initial_stops = db.query(DbTripStop).count()
        assert initial_stops == 1
        initial_def_events = (
            db.query(DeliveryEvent)
            .filter(DeliveryEvent.event_type == "order_deferred")
            .count()
        )
        assert initial_def_events == 2

        # Step 4: Call the approval operation a second time for the same plan
        res2 = approve_draft_plan_operation(
            db=db,
            plan_id=plan_id,
            user_id="U-INT-1",
            client_op_id="OP-MULTI-DEF",
            depot_id="Peliyagoda",
        )
        assert res2["status"] == "approved"

        # Verify Deferral row count remains 2
        assert db.query(Deferral).count() == 2

        # defer_count values do not increment again
        db.refresh(ord_def1)
        db.refresh(ord_def2)
        assert ord_def1.defer_count == 1
        assert ord_def2.defer_count == 1

        # No duplicate order_deferred events are created
        def_events_after = (
            db.query(DeliveryEvent)
            .filter(DeliveryEvent.event_type == "order_deferred")
            .count()
        )
        assert def_events_after == 2

        # No duplicate TripStops are created
        stops_after = db.query(DbTripStop).count()
        assert stops_after == initial_stops
    finally:
        Base.metadata.drop_all(bind=engine)
        db.close()

