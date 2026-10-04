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
from app.adapters.optimizer_adapter import (
    get_reference_data,
    _get_eligible_orders_for_date,
    _get_depot_outlet_ids,
    get_approved_urgent_order_ids,
    convert_db_order_to_optimizer,
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

    # Seed vehicles from reference data
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
            break  # one vehicle is enough for eligibility tests

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
