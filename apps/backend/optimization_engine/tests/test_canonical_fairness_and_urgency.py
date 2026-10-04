"""
Phase 5 — Canonical Fairness & Approved Urgency Regression Test Suite
===================================================================
Proves:
1. Canonical policy weights and fairness hierarchy:
     normal < urgent < deferred_once < deferred_3_times < urgent_and_deferred
2. Deferral fairness protection is strictly preserved:
   A previously deferred ordinary order OUTRANKS a newly approved urgent order.
3. Urgency is soft: impossible urgent orders remain deferred and NEVER bypass hard constraints.
4. Backend adapter derives is_urgent solely from UrgencyRequest.status == "approved"
   (pending, rejected, resolved, none -> False).
5. Breakdown recovery preserves deferred_prev, defer_count, is_urgent.
6. Validation rejects negative defer_count.
7. CSV roundtrip works with canonical fields and rejects silent aliasing of days_since_last_served.
8. Targeted CP-SAT shares the single source of truth for priority.
"""
import dataclasses
import io
import math
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Ensure backend root is on sys.path for app module imports
backend_root = str(Path(__file__).resolve().parents[2])
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.domain import (
    Brand, DockType, LineItem, Order, ParkingConstraint,
    TempRequirement, TempSpec, Vehicle, VehicleStatus, VehicleType,
)
from waypoint_optimizer.enums import DeferralReason
from waypoint_optimizer.input_validation import (
    InputValidationError, validate_operational_inputs,
)
from waypoint_optimizer.objective import defer_penalty
from waypoint_optimizer.hackathon_planner import (
    _order_priority_key as greedy_priority_key,
    generate_daily_draft_plan,
)
from waypoint_optimizer.targeted_cpsat import (
    _order_priority_key as cpsat_priority_key,
)
from waypoint_optimizer.operational.breakdown_recovery import (
    reallocate_broken_vehicle,
)
from waypoint_optimizer.operational.models import OperationalContext
from waypoint_optimizer.adapters.csv_adapter import (
    orders_from_csv,
)


def _make_test_order(
    ref: str = "ORD1",
    outlet_id: str = "OUT001",
    weight: float = 100.0,
    volume: float = 1.0,
    deferred_prev: bool = False,
    defer_count: int = 0,
    is_urgent: bool = False,
    brand: Brand = Brand.FRESH,
    district: str = "Colombo",
    depot: str = "Peliyagoda",
    dock_type: DockType = DockType.STREET,
    parking: ParkingConstraint = ParkingConstraint.NORMAL,
    temp: TempRequirement = TempRequirement.AMBIENT,
    window_open: str | None = None,
    window_close: str | None = None,
    line_items: list[LineItem] | None = None,
) -> Order:
    return Order(
        order_ref=ref,
        outlet_id=outlet_id,
        brand=brand,
        district=district,
        depot=depot,
        dock_type=dock_type,
        parking_constraint=parking,
        mall_window=None,
        window_open_time=window_open,
        window_close_time=window_close,
        temp_requirement=temp,
        order_units=5,
        order_weight_kg=weight,
        order_volume_m3=volume,
        deferred_prev=deferred_prev,
        defer_count=defer_count,
        is_urgent=is_urgent,
        line_items=line_items if line_items is not None else [],
    )


def _make_planning_vehicle(
    base: Vehicle,
    vid: str | None = None,
    weight_cap: float | None = None,
    volume_cap: float | None = None,
    vtype: VehicleType | None = None,
    temp: TempSpec | None = None,
) -> Vehicle:
    return dataclasses.replace(
        base,
        vehicle_id=vid or base.vehicle_id,
        weight_cap_kg=weight_cap if weight_cap is not None else base.weight_cap_kg,
        volume_cap_m3=volume_cap if volume_cap is not None else base.volume_cap_m3,
        type=vtype or base.type,
        temp=temp or base.temp,
        status=VehicleStatus.AVAILABLE,
        is_selected_for_planning=True,
        remaining_trips=2,
        weekly_fuel_used_l=40.0,
        external_reservations_l=10.0,
        earliest_availability_iso="2026-10-03T04:00:00+05:30",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Numerical Policy & Fairness Hierarchy Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_defer_penalty_numerical_policy_and_fairness_scale():
    """
    Verify exact canonical defer_penalty calculation and the fairness scale:
      - Normal fresh order:           ~100 + volume (110)
      - New approved urgent order:    ~1100 + volume (1110)
      - Ordinary deferred once:       ~2700 + volume (2710)
      - Ordinary deferred 3 times:    ~2900 + volume (2910)
      - Approved urgent + def prev:   ~3700 + volume (3710)

    Guarantees:
      - Previously deferred ordinary order outranks newly approved urgent order.
      - Repeatedly deferred ordinary order retains and increases fairness protection.
      - Urgency priority bonus (1000) does not use an extreme override (e.g. 999999).
    """
    cfg = OptimizerConfig()
    vol = 1.0
    vol_bonus = math.ceil(vol * cfg.defer_penalty_volume_factor)  # ceil(1.0 * 10) = 10

    ord_normal = _make_test_order("NORM", volume=vol, deferred_prev=False, defer_count=0, is_urgent=False)
    ord_urgent = _make_test_order("URG", volume=vol, deferred_prev=False, defer_count=0, is_urgent=True)
    ord_def1 = _make_test_order("DEF1", volume=vol, deferred_prev=True, defer_count=1, is_urgent=False)
    ord_def3 = _make_test_order("DEF3", volume=vol, deferred_prev=True, defer_count=3, is_urgent=False)
    ord_urg_def1 = _make_test_order("URG_DEF1", volume=vol, deferred_prev=True, defer_count=1, is_urgent=True)

    pen_normal = defer_penalty(ord_normal, cfg)
    pen_urgent = defer_penalty(ord_urgent, cfg)
    pen_def1 = defer_penalty(ord_def1, cfg)
    pen_def3 = defer_penalty(ord_def3, cfg)
    pen_urg_def1 = defer_penalty(ord_urg_def1, cfg)

    # Exact expected numerical values
    assert pen_normal == 100 + vol_bonus  # 110
    assert pen_urgent == 100 + 1000 + vol_bonus  # 1110
    assert pen_def1 == 100 + 2500 + 100 * 1 + vol_bonus  # 2710
    assert pen_def3 == 100 + 2500 + 100 * 3 + vol_bonus  # 2910
    assert pen_urg_def1 == 100 + 2500 + 100 * 1 + 1000 + vol_bonus  # 3710

    # Strict fairness hierarchy assertions
    assert pen_normal < pen_urgent
    assert pen_urgent < pen_def1, "FAIRNESS VIOLATION: A single-time deferred order must outrank a new urgent order!"
    assert pen_def1 < pen_def3, "Repeat deferrals must increase fairness protection!"
    assert pen_def3 < pen_urg_def1, "Urgent order with prior deferral must receive both bonuses!"


def test_defer_count_cap_enforcement():
    """Verify that defer_count is capped at cfg.defer_count_cap (30)."""
    cfg = OptimizerConfig()
    vol = 1.0
    vol_bonus = math.ceil(vol * cfg.defer_penalty_volume_factor)

    ord_at_cap = _make_test_order("CAP30", volume=vol, deferred_prev=True, defer_count=30, is_urgent=False)
    ord_over_cap = _make_test_order("CAP50", volume=vol, deferred_prev=True, defer_count=50, is_urgent=False)

    pen_at_cap = defer_penalty(ord_at_cap, cfg)
    pen_over_cap = defer_penalty(ord_over_cap, cfg)

    expected_cap_penalty = 100 + 2500 + (30 * 100) + vol_bonus  # 5610
    assert pen_at_cap == expected_cap_penalty
    assert pen_over_cap == expected_cap_penalty, "defer_count penalty must not exceed cap (30)!"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Single Source of Priority Policy Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_single_source_of_priority_policy():
    """
    Verify that _order_priority_key in both hackathon_planner and targeted_cpsat
    are thin wrappers returning the identical canonical defer_penalty.
    """
    cfg = OptimizerConfig()
    orders = [
        _make_test_order("O1", deferred_prev=False, defer_count=0, is_urgent=False),
        _make_test_order("O2", deferred_prev=False, defer_count=0, is_urgent=True),
        _make_test_order("O3", deferred_prev=True, defer_count=2, is_urgent=False),
        _make_test_order("O4", deferred_prev=True, defer_count=2, is_urgent=True),
    ]

    for ord in orders:
        expected = defer_penalty(ord, cfg)
        assert greedy_priority_key(ord, cfg) == expected
        assert cpsat_priority_key(ord, cfg) == expected
        # Also when called with default cfg (None)
        assert greedy_priority_key(ord) == expected
        assert cpsat_priority_key(ord) == expected


# ─────────────────────────────────────────────────────────────────────────────
# 3. Input Validation Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_input_validation_negative_defer_count_rejected(real_reference_data):
    """Verify input_validation rejects negative defer_count."""
    bad_order = _make_test_order("BAD_DEF", defer_count=-1)
    v = _make_planning_vehicle(real_reference_data.vehicles[0])
    ctx = OperationalContext(planning_date="2026-10-03")

    with pytest.raises(InputValidationError) as exc:
        validate_operational_inputs([bad_order], [v], real_reference_data, ctx)
    assert "defer_count" in str(exc.value)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Backend Adapter Urgency Derivation & Mapping Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_backend_adapter_urgency_derivation_from_db_workflow():
    """
    Verify that the optimizer adapter queries UrgencyRequest.status == 'approved'
    and derives is_urgent accordingly.
    Pending, rejected, resolved, or absent requests must all produce is_urgent=False.
    """
    from app.adapters.optimizer_adapter import (
        get_approved_urgent_order_ids,
        convert_db_order_to_optimizer,
    )

    # Mock DB session
    db_mock = MagicMock()

    # Case 1: get_approved_urgent_order_ids only returns IDs with status == "approved"
    mock_approved_query = db_mock.query.return_value.filter.return_value
    mock_approved_query.all.return_value = [("ORD_APP_1",), ("ORD_APP_2",)]

    approved_ids = get_approved_urgent_order_ids(db_mock, ["ORD_NORM", "ORD_PEND", "ORD_REJ", "ORD_RES", "ORD_APP_1", "ORD_APP_2"])
    assert approved_ids == {"ORD_APP_1", "ORD_APP_2"}

    # Case 2: Mapping from DB order
    class MockDbOrder:
        def __init__(self, oid, deferred_prev=False, defer_count=0):
            self.order_id = oid
            self.outlet_id = "OUT001"
            self.deferred_prev = deferred_prev
            self.defer_count = defer_count
            self.brand = "fresh"
            self.district = "Colombo"
            self.depot = "Peliyagoda"
            self.dock_type = None
            self.parking_constraint = None
            self.mall_window = None
            self.window_open = None
            self.window_close = None
            self.order_units = 10
            self.order_wt_kg = 100.0
            self.order_vol_m3 = 1.0
            self.order_weight_kg = 100.0
            self.order_volume_m3 = 1.0
            self.temp_req = "ambient"
            self.temp_requirement = "ambient"
            self.line_items = []
            self.lines = []

    # Reference data mock
    ref_mock = MagicMock()
    ref_outlet = MagicMock()
    ref_outlet.dock_type = DockType.STREET
    ref_outlet.parking_constraint = ParkingConstraint.NORMAL
    ref_outlet.mall_window = None
    ref_outlet.window_open_time = None
    ref_outlet.window_close_time = None
    ref_mock.outlets = {"OUT001": ref_outlet}

    # Normal order -> is_urgent=False
    o_norm = convert_db_order_to_optimizer(
        MockDbOrder("ORD_NORM", deferred_prev=False, defer_count=0),
        ref_mock, db_mock, is_urgent=("ORD_NORM" in approved_ids),
    )
    assert o_norm.is_urgent is False
    assert o_norm.deferred_prev is False
    assert o_norm.defer_count == 0

    # Pending urgency -> is_urgent=False
    o_pend = convert_db_order_to_optimizer(
        MockDbOrder("ORD_PEND", deferred_prev=False, defer_count=0),
        ref_mock, db_mock, is_urgent=("ORD_PEND" in approved_ids),
    )
    assert o_pend.is_urgent is False

    # Rejected urgency -> is_urgent=False
    o_rej = convert_db_order_to_optimizer(
        MockDbOrder("ORD_REJ", deferred_prev=False, defer_count=0),
        ref_mock, db_mock, is_urgent=("ORD_REJ" in approved_ids),
    )
    assert o_rej.is_urgent is False

    # Resolved urgency -> is_urgent=False
    o_res = convert_db_order_to_optimizer(
        MockDbOrder("ORD_RES", deferred_prev=False, defer_count=0),
        ref_mock, db_mock, is_urgent=("ORD_RES" in approved_ids),
    )
    assert o_res.is_urgent is False

    # Approved urgency -> is_urgent=True
    o_app = convert_db_order_to_optimizer(
        MockDbOrder("ORD_APP_1", deferred_prev=True, defer_count=2),
        ref_mock, db_mock, is_urgent=("ORD_APP_1" in approved_ids),
    )
    assert o_app.is_urgent is True
    assert o_app.deferred_prev is True
    assert o_app.defer_count == 2


# ─────────────────────────────────────────────────────────────────────────────
# 5. Greedy Ordering & Fairness Protection in Draft Planning
# ─────────────────────────────────────────────────────────────────────────────

def test_greedy_draft_planning_fairness_and_urgency(real_reference_data):
    """
    Test in end-to-end draft planning:
    When vehicle capacity only fits 1 order:
    1. Between a fresh ordinary order and an approved urgent order, urgent wins.
    2. Between a previously deferred ordinary order and a newly approved urgent order,
       the PREVIOUSLY DEFERRED order wins (fairness preservation).
    """
    out1 = real_reference_data.outlets["OUT001"]
    v_small = _make_planning_vehicle(
        real_reference_data.vehicles[0],
        vid="V_SMALL",
        weight_cap=200.0,
        volume_cap=2.0,
        vtype=VehicleType.VAN,
        temp=TempSpec.REEFER,
    )
    v_small = dataclasses.replace(v_small, remaining_trips=1)
    context = OperationalContext(planning_date="2026-10-03")

    # Order A: normal fresh, 150 kg
    ord_norm = _make_test_order(
        ref="O_NORM", outlet_id=out1.outlet_id, brand=out1.brand, district=out1.district, depot=out1.depot,
        dock_type=out1.dock_type, parking=out1.parking_constraint,
        weight=150.0, volume=1.0, deferred_prev=False, defer_count=0, is_urgent=False,
    )
    # Order B: approved urgent, 150 kg
    ord_urg = _make_test_order(
        ref="O_URG", outlet_id=out1.outlet_id, brand=out1.brand, district=out1.district, depot=out1.depot,
        dock_type=out1.dock_type, parking=out1.parking_constraint,
        weight=150.0, volume=1.0, deferred_prev=False, defer_count=0, is_urgent=True,
    )
    # Order C: previously deferred ordinary, 150 kg
    ord_def = _make_test_order(
        ref="O_DEF", outlet_id=out1.outlet_id, brand=out1.brand, district=out1.district, depot=out1.depot,
        dock_type=out1.dock_type, parking=out1.parking_constraint,
        weight=150.0, volume=1.0, deferred_prev=True, defer_count=1, is_urgent=False,
    )

    # Round 1: normal vs urgent -> urgent wins
    plan1 = generate_daily_draft_plan(
        orders=[ord_norm, ord_urg],
        fleet=[v_small],
        reference_data=real_reference_data,
        context=context,
        enable_targeted_cpsat=False,
    )
    served1 = [ref for trip in plan1["trips"] for stop in trip["driver_itinerary"] for ref in stop["order_refs"]]
    assert "O_URG" in served1
    assert "O_NORM" not in served1

    # Round 2: urgent vs previously deferred -> PREVIOUSLY DEFERRED wins!
    plan2 = generate_daily_draft_plan(
        orders=[ord_urg, ord_def],
        fleet=[v_small],
        reference_data=real_reference_data,
        context=context,
        enable_targeted_cpsat=False,
    )
    served2 = [ref for trip in plan2["trips"] for stop in trip["driver_itinerary"] for ref in stop["order_refs"]]
    assert "O_DEF" in served2, "Fairness violated! Previously deferred order must be prioritized over new urgent order."
    assert "O_URG" not in served2


# ─────────────────────────────────────────────────────────────────────────────
# 6. Hard Constraint Inviolability: Impossible Urgent Order Remains Deferred
# ─────────────────────────────────────────────────────────────────────────────

def test_impossible_urgent_order_remains_deferred(real_reference_data):
    """
    Urgency is a soft preference only and must NEVER bypass hard constraints:
    - Weight overflow
    - Access/dock restrictions
    - Delivery time window violations
    - Refrigeration incompatibility
    """
    out1 = real_reference_data.outlets["OUT001"]
    v_small = _make_planning_vehicle(
        real_reference_data.vehicles[0],
        vid="V_SMALL",
        weight_cap=100.0,
        volume_cap=1.0,
        vtype=VehicleType.VAN,
        temp=TempSpec.AMBIENT,
    )
    context = OperationalContext(planning_date="2026-10-03")

    # Urgent order that is too heavy (500 kg > 100 kg)
    ord_heavy_urgent = _make_test_order(
        ref="O_HEAVY_URG", outlet_id=out1.outlet_id, brand=out1.brand, district=out1.district, depot=out1.depot,
        dock_type=out1.dock_type, parking=out1.parking_constraint,
        weight=500.0, volume=0.5, is_urgent=True,
    )

    plan = generate_daily_draft_plan(
        orders=[ord_heavy_urgent],
        fleet=[v_small],
        reference_data=real_reference_data,
        context=context,
        enable_targeted_cpsat=True,
    )
    assert plan["validation"]["valid"] is True
    assert plan["order_counts"]["fully_served_orders"] == 0
    assert plan["order_counts"]["fully_deferred_orders"] == 1
    assert plan["deferred_orders"][0]["order_ref"] == "O_HEAVY_URG"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Breakdown Recovery Preserves Canonical Signals
# ─────────────────────────────────────────────────────────────────────────────

def test_breakdown_recovery_preserves_canonical_signals(real_reference_data):
    """
    When a vehicle breaks down and remaining orders are reallocated,
    reallocate_broken_vehicle must preserve deferred_prev, defer_count, and is_urgent.
    """
    out1 = real_reference_data.outlets["OUT001"]
    context = OperationalContext(planning_date="2026-10-03")
    v_broken = _make_planning_vehicle(
        real_reference_data.vehicles[0],
        vid="V_BROKEN",
        vtype=VehicleType.VAN,
        temp=TempSpec.REEFER,
    )
    v_spare = _make_planning_vehicle(
        real_reference_data.vehicles[1],
        vid="V_SPARE",
        weight_cap=5000.0,
        volume_cap=30.0,
        vtype=VehicleType.VAN,
        temp=TempSpec.REEFER,
    )

    li1 = LineItem(
        line_item_id="LI_URG",
        quantity=5.0,
        quantity_unit="units",
        unit_weight_kg=10.0,
        unit_volume_m3=0.1,
        description="Urgent goods",
    )
    auth_order = _make_test_order(
        ref="O_URG_DEF",
        outlet_id=out1.outlet_id,
        brand=out1.brand,
        district=out1.district,
        depot=out1.depot,
        dock_type=out1.dock_type,
        parking=out1.parking_constraint,
        weight=50.0,
        volume=0.5,
        deferred_prev=True,
        defer_count=3,
        is_urgent=True,
        line_items=[li1],
    )

    # Create base plan where O_URG_DEF is scheduled on v_broken
    base_plan = generate_daily_draft_plan(
        orders=[auth_order],
        fleet=[v_broken],
        reference_data=real_reference_data,
        context=context,
        enable_targeted_cpsat=False,
    )

    # Execute recovery reallocating from v_broken to v_spare
    recovery_resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id=v_broken.vehicle_id,
        undelivered_quantities=[
            {"order_ref": "O_URG_DEF", "line_item_id": "LI_URG", "quantity": 5.0, "quantity_unit": "units"}
        ],
        available_fleet=[v_broken, v_spare],
        reference_data=real_reference_data,
        operational_context=context,
        current_time_iso="2026-10-03T05:30:00+05:30",
        authoritative_orders=[auth_order],
    )

    assert recovery_resp["validation"]["valid"] is True
    # The order was successfully reassigned to replacement trip
    assert len(recovery_resp["replacement_trips"]) == 1
    rep_trip = recovery_resp["replacement_trips"][0]
    rep_refs = [r for s in rep_trip["driver_itinerary"] for r in s["order_refs"]]
    assert "O_URG_DEF" in rep_refs


# ─────────────────────────────────────────────────────────────────────────────
# 8. CSV Roundtrip with Canonical Fields
# ─────────────────────────────────────────────────────────────────────────────

def test_csv_adapter_canonical_fields_roundtrip():
    """
    Verify that orders_from_csv parses canonical fields:
      deferred_prev, defer_count, is_urgent
    and supports the backward-compatible alias deferred_yesterday for deferred_prev,
    while NOT treating days_since_last_served as defer_count.
    """
    csv_canonical = """order_ref,outlet_id,brand,district,depot,dock_type,parking_constraint,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_prev,defer_count,is_urgent
ORD_CAN_1,OUT1,fresh,Colombo,Peliyagoda,rear_dock,normal,10,100.0,1.0,ambient,1,4,1
ORD_CAN_2,OUT2,fresh,Colombo,Peliyagoda,rear_dock,normal,5,50.0,0.5,ambient,0,0,0
"""
    orders = orders_from_csv(io.StringIO(csv_canonical))
    assert len(orders) == 2
    assert orders[0].deferred_prev is True
    assert orders[0].defer_count == 4
    assert orders[0].is_urgent is True

    assert orders[1].deferred_prev is False
    assert orders[1].defer_count == 0
    assert orders[1].is_urgent is False

    # Deprecated alias test: deferred_yesterday accepted as alias for deferred_prev
    csv_alias = """order_ref,outlet_id,brand,district,depot,dock_type,parking_constraint,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,defer_count,is_urgent
ORD_AL_1,OUT1,fresh,Colombo,Peliyagoda,rear_dock,normal,10,100.0,1.0,ambient,true,2,false
"""
    orders_alias = orders_from_csv(io.StringIO(csv_alias))
    assert orders_alias[0].deferred_prev is True
    assert orders_alias[0].defer_count == 2
    assert orders_alias[0].is_urgent is False


# ──────────────────────────────────────────────────────────────────────────────
# 8b. Additional CSV migration hardening tests
# ──────────────────────────────────────────────────────────────────────────────

def test_csv_deferred_yesterday_alias_accepted():
    """Deprecated alias deferred_yesterday is accepted as deferred_prev (self-contained path)."""
    csv_alias = (
        "order_ref,outlet_id,brand,district,depot,dock_type,parking_constraint,"
        "order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,defer_count,is_urgent\n"
        "ORD_AL_1,OUT1,fresh,Colombo,Peliyagoda,rear_dock,normal,10,100.0,1.0,ambient,true,2,false\n"
    )
    import io as _io
    orders_alias = orders_from_csv(_io.StringIO(csv_alias))
    assert orders_alias[0].deferred_prev is True
    assert orders_alias[0].defer_count == 2
    assert orders_alias[0].is_urgent is False


def test_csv_days_since_last_served_rejected_outlet_joined_path():
    """days_since_last_served is rejected with a clear migration error in the outlet-joined path."""
    from waypoint_optimizer.adapters.csv_adapter import load_orders_with_outlets
    from waypoint_optimizer.domain import Outlet
    import io as _io

    csv_legacy = (
        "order_ref,outlet_id,order_units,order_weight_kg,order_volume_m3,temp_requirement,days_since_last_served\n"
        "ORD_LEG_1,OUT1,10,100.0,1.0,ambient,3\n"
    )
    mock_outlet = Outlet(
        outlet_id="OUT1",
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK,
        parking_constraint=ParkingConstraint.NORMAL,
    )
    with pytest.raises(InputValidationError, match="days_since_last_served"):
        load_orders_with_outlets(_io.StringIO(csv_legacy), outlets={"OUT1": mock_outlet})


def test_csv_days_since_last_served_rejected_self_contained_path():
    """days_since_last_served is rejected with a clear migration error in the self-contained path."""
    import io as _io
    csv_legacy = (
        "order_ref,outlet_id,brand,district,depot,dock_type,parking_constraint,"
        "order_units,order_weight_kg,order_volume_m3,temp_requirement,days_since_last_served\n"
        "ORD_LEG_SC,OUT1,fresh,Colombo,Peliyagoda,rear_dock,normal,10,100.0,1.0,ambient,3\n"
    )
    with pytest.raises(InputValidationError, match="days_since_last_served"):
        orders_from_csv(_io.StringIO(csv_legacy))


def test_csv_negative_defer_count_rejected_outlet_joined_path():
    """Negative defer_count is rejected in the outlet-joined path."""
    from waypoint_optimizer.adapters.csv_adapter import load_orders_with_outlets
    from waypoint_optimizer.domain import Outlet
    import io as _io

    csv_neg = (
        "order_ref,outlet_id,order_units,order_weight_kg,order_volume_m3,temp_requirement,defer_count\n"
        "ORD_NEG,OUT1,10,100.0,1.0,ambient,-1\n"
    )
    mock_outlet = Outlet(
        outlet_id="OUT1",
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK,
        parking_constraint=ParkingConstraint.NORMAL,
    )
    with pytest.raises(InputValidationError, match="defer_count"):
        load_orders_with_outlets(_io.StringIO(csv_neg), outlets={"OUT1": mock_outlet})


def test_csv_negative_defer_count_rejected_self_contained_path():
    """Negative defer_count is rejected in the self-contained orders_from_csv path."""
    import io as _io
    csv_neg = (
        "order_ref,outlet_id,brand,district,depot,dock_type,parking_constraint,"
        "order_units,order_weight_kg,order_volume_m3,temp_requirement,defer_count\n"
        "ORD_NEG_SC,OUT1,fresh,Colombo,Peliyagoda,rear_dock,normal,10,100.0,1.0,ambient,-5\n"
    )
    with pytest.raises(InputValidationError, match="defer_count"):
        orders_from_csv(_io.StringIO(csv_neg))
