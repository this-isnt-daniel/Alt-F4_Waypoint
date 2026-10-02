
"""
Waypoint Optimizer — Unit Tests for Hackathon H1 Operational Scheduling & Feasibility
======================================================================================
Tests:
  1. Early arrival with waiting until window open.
  2. Exact window boundaries and late service under different WindowPolicy settings.
  3. Multiple orders at one outlet consolidated into a single physical stop.
  4. Consecutive trip overlap vs feasible turnaround.
  5. Cumulative weekly fuel across multiple trips and quota exhaustion.
  6. Missing travel and fuel efficiency data reporting.
  7. Date coverage boundaries (strict missing data on dynamic policy vs static freeflow).
  8. Demand classification per line item without incompatible unit summing.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import pytest

from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, OrderAllocationStatus,
    Outlet, ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleStatus, VehicleType, classify_order_allocation,
)
from waypoint_optimizer.operational import (
    ESTIMATED_DEPOT_TURNAROUND_MIN, EvaluatedTripSchedule, OperationalContext,
    OperationalMissingData, OperationalViolation, TravelPolicy, WindowPolicy,
    consolidate_orders_to_stops, evaluate_trip_schedule,
    evaluate_vehicle_timeline, validate_operational_plan,
)


def make_test_order(
    order_ref: str,
    outlet_id: str,
    brand: Brand = Brand.FRESH,
    district: str = "Colombo",
    depot: str = "Peliyagoda",
    dock_type: DockType = DockType.STREET,
    parking_constraint: ParkingConstraint = ParkingConstraint.NORMAL,
    temp_requirement: TempRequirement = TempRequirement.AMBIENT,
    order_units: int = 10,
    order_weight_kg: float = 100.0,
    order_volume_m3: float = 1.0,
    mall_window: str | None = None,
    window_open_time: str | None = None,
    window_close_time: str | None = None,
    deferred_yesterday: bool = False,
    days_since_last_served: int = 1,
    line_items: list[LineItem] | None = None,
) -> Order:
    return Order(
        order_ref=order_ref,
        outlet_id=outlet_id,
        brand=brand,
        district=district,
        depot=depot,
        dock_type=dock_type,
        parking_constraint=parking_constraint,
        mall_window=mall_window,
        window_open_time=window_open_time,
        window_close_time=window_close_time,
        temp_requirement=temp_requirement,
        order_units=order_units,
        order_weight_kg=order_weight_kg,
        order_volume_m3=order_volume_m3,
        deferred_yesterday=deferred_yesterday,
        days_since_last_served=days_since_last_served,
        line_items=line_items or [],
    )


@pytest.fixture
def colombo_travel() -> dict[tuple[str, str], DistrictTravel]:
    return {
        ("Colombo", "Peliyagoda"): DistrictTravel(
            district="Colombo",
            depot="Peliyagoda",
            road_class="urban",
            free_flow_kmh=30.0,
            depot_to_district_km=12.0,
            depot_to_district_freeflow_min=24.0,
            inter_stop_km=4.0,
            inter_stop_freeflow_min=8.0,
        )
    }


@pytest.fixture
def allowances() -> dict[tuple[Brand, DockType], float]:
    return {
        (Brand.FRESH, DockType.STREET): 16.0,
        (Brand.FRESH, DockType.REAR_DOCK): 15.0,
        (Brand.STYLE, DockType.STREET): 46.0,
    }


@pytest.fixture
def outlets() -> dict[str, Outlet]:
    return {
        "OUT001": Outlet(
            outlet_id="OUT001",
            brand=Brand.FRESH,
            district="Colombo",
            depot="Peliyagoda",
            dock_type=DockType.STREET,
            parking_constraint=ParkingConstraint.VAN_ONLY,
            window_open_time="05:00",
            window_close_time="07:30",
        ),
        "OUT002": Outlet(
            outlet_id="OUT002",
            brand=Brand.FRESH,
            district="Colombo",
            depot="Peliyagoda",
            dock_type=DockType.STREET,
            parking_constraint=ParkingConstraint.NORMAL,
            window_open_time="05:30",
            window_close_time="08:00",
        ),
    }


@pytest.fixture
def reefer_van() -> Vehicle:
    return Vehicle(
        vehicle_id="VEH001",
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.VAN,
        temp=TempSpec.REEFER,
        weight_cap_kg=2000.0,
        volume_cap_m3=12.0,
        depot="Peliyagoda",
        km_per_l=8.0,
        weekly_fuel_quota_l=200.0,
        weekly_fuel_used_l=50.0,
        external_reservations_l=20.0,
        remaining_trips=2,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 1. Early Arrival with Waiting
# ──────────────────────────────────────────────────────────────────────────────

def test_early_arrival_with_waiting(colombo_travel, allowances, outlets, reefer_van):
    """
    Departure at 04:00. Outbound travel is 24 min.
    Arrival at OUT001 is 04:24. Window opens at 05:00.
    Must wait 36 minutes. Service start must be 05:00.
    Service duration is 16 min. Departure must be 05:16.
    """
    order = make_test_order(
        order_ref="ORD001",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=150.0,
        order_volume_m3=1.2,
    )

    ctx = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    schedule = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=1,
        orders=[order],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T04:00:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx,
    )

    assert schedule.is_feasible
    assert len(schedule.stops) == 1
    stop = schedule.stops[0]

    assert "04:24:00" in stop.arrival_time_iso
    assert stop.waiting_duration_min == 36.0
    assert "05:00:00" in stop.service_start_time_iso
    assert stop.service_duration_min == 16.0
    assert "05:16:00" in stop.departure_time_iso
    assert stop.window_compliant

    # Depot return: 05:16 + 24 min = 05:40
    assert "05:40:00" in schedule.depot_return_arrival_iso
    # Next available: 05:40 + 30 min turnaround = 06:10
    assert "06:10:00" in schedule.vehicle_next_available_iso

    # Distance: 12 (outbound) + 0 (inter-stop) + 12 (return) = 24 km
    assert schedule.total_distance_km == 24.0
    # Fuel: 24 km / 8.0 km/L = 3.0 L
    assert schedule.fuel_consumed_l == 3.0
    # Cumulative: 50 used + 20 reserved + 3 = 73 L <= 200 quota
    assert schedule.cumulative_fuel_used_l == 73.0
    assert schedule.fuel_compliant


# ──────────────────────────────────────────────────────────────────────────────
# 2. Window Policy Semantics: Arrival vs Service End Boundaries
# ──────────────────────────────────────────────────────────────────────────────

def test_window_boundary_policies(colombo_travel, allowances, outlets, reefer_van):
    """
    Depart at 06:50. Outbound travel = 24 min.
    Arrival at OUT001 = 07:14 (Window closes at 07:30).
    Service start = 07:14 (window open 05:00).
    Service duration = 20 min (hypothetical custom allowance).
    Departure / service completion = 07:34 (after 07:30 window close!).

    - ARRIVAL_BEFORE_CLOSE: Compliant (arrived at 07:14 <= 07:30).
    - SERVICE_END_BEFORE_CLOSE: Non-compliant (service finishes at 07:34 > 07:30).
    """
    order = make_test_order(
        order_ref="ORD001",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=100.0,
        order_volume_m3=1.0,
    )
    custom_allowances = {(Brand.FRESH, DockType.STREET): 20.0}

    # Policy 1: ARRIVAL_BEFORE_CLOSE
    ctx_arrival = OperationalContext(
        planning_date="2026-10-03",
        window_policy=WindowPolicy.ARRIVAL_BEFORE_CLOSE,
    )
    sched_arrival = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=1,
        orders=[order],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T06:50:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=custom_allowances,
        context=ctx_arrival,
    )
    assert sched_arrival.windows_compliant
    assert sched_arrival.stops[0].window_compliant

    # Policy 2: SERVICE_END_BEFORE_CLOSE
    ctx_end = OperationalContext(
        planning_date="2026-10-03",
        window_policy=WindowPolicy.SERVICE_END_BEFORE_CLOSE,
    )
    sched_end = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=1,
        orders=[order],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T06:50:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=custom_allowances,
        context=ctx_end,
    )
    assert not sched_end.windows_compliant
    assert not sched_end.stops[0].window_compliant
    assert any(v.rule == "DELIVERY_WINDOW_VIOLATION" for v in sched_end.violations)


# ──────────────────────────────────────────────────────────────────────────────
# 3. Multiple Orders at One Outlet Consolidation
# ──────────────────────────────────────────────────────────────────────────────

def test_multiple_orders_single_physical_stop(colombo_travel, allowances, outlets, reefer_van):
    """
    Two orders for the same outlet OUT001:
      - ORD001: Ambient dry goods, 10 units.
      - ORD002: Chilled dairy, 5 units.
    Should produce exactly ONE physical stop in the schedule, containing both orders,
    applying a single docking service allowance (16 min).
    """
    o1 = make_test_order(
        order_ref="ORD001",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=10,
        order_weight_kg=100.0,
        order_volume_m3=0.8,
        line_items=[
            LineItem("ITEM-1", 10, "crates", 10.0, 0.08, "Dry Groceries")
        ],
    )
    o2 = make_test_order(
        order_ref="ORD002",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.CHILLED,
        order_units=5,
        order_weight_kg=60.0,
        order_volume_m3=0.5,
        line_items=[
            LineItem("ITEM-2", 5, "crates", 12.0, 0.1, "Fresh Milk")
        ],
    )

    ctx = OperationalContext(planning_date="2026-10-03")
    schedule = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=1,
        orders=[o1, o2],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T04:00:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx,
    )

    assert len(schedule.stops) == 1
    stop = schedule.stops[0]
    assert stop.outlet_id == "OUT001"
    assert stop.order_refs == ["ORD001", "ORD002"]
    assert len(stop.line_items_delivered) == 2
    assert stop.service_duration_min == 16.0  # Single docking service allowance


# ──────────────────────────────────────────────────────────────────────────────
# 4. Consecutive Trip Chronology and Turnaround Overlap
# ──────────────────────────────────────────────────────────────────────────────

def test_consecutive_trip_chronology(colombo_travel, allowances, outlets, reefer_van):
    """
    Trip 1 departs at 04:00.
    Stops: OUT001. Arrives 04:24, waits until 05:00, departs 05:16.
    Returns to depot at 05:40.
    Turnaround = 30 min. Next available = 06:10.

    Case A: Trip 2 departs at 06:00 (10 min before vehicle ready). Overlap!
    Case B: Trip 2 departs at 06:30 (20 min after vehicle ready). Feasible!
    """
    order1 = make_test_order(
        order_ref="ORD001",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=100.0,
        order_volume_m3=1.0,
    )
    order2 = make_test_order(
        order_ref="ORD002",
        outlet_id="OUT002",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.NORMAL,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=100.0,
        order_volume_m3=1.0,
    )

    ctx = OperationalContext(
        planning_date="2026-10-03",
        depot_turnaround_duration_min=30.0,
    )

    trip1 = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=1,
        orders=[order1],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T04:00:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx,
    )

    # Case A: Overlap (Departs 06:00 < 06:10)
    trip2_overlap = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=2,
        orders=[order2],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T06:00:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx,
    )

    timeline_bad = evaluate_vehicle_timeline(reefer_van, [trip1, trip2_overlap], ctx)
    assert not timeline_bad.chronology_valid
    assert any(v.rule == "CONSECUTIVE_TRIP_OVERLAP" for v in timeline_bad.violations)

    # Case B: Feasible (Departs 06:30 >= 06:10)
    trip2_feasible = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=2,
        orders=[order2],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T06:30:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx,
    )

    timeline_good = evaluate_vehicle_timeline(reefer_van, [trip1, trip2_feasible], ctx)
    assert timeline_good.chronology_valid
    assert not any(v.rule == "CONSECUTIVE_TRIP_OVERLAP" for v in timeline_good.violations)


# ──────────────────────────────────────────────────────────────────────────────
# 5. Cumulative Weekly Fuel Across Two Trips & Quota Exhaustion
# ──────────────────────────────────────────────────────────────────────────────

def test_cumulative_weekly_fuel_quota(colombo_travel, allowances, outlets):
    """
    Vehicle: weekly_fuel_quota_l = 60.0 L
    Prior used: 40.0 L
    External reservations: 10.0 L
    Remaining before draft = 10.0 L.

    Trip 1: 24 km / 4.0 km/L = 6.0 L -> Cumulative = 56.0 L <= 60.0 (Feasible).
    Trip 2: 24 km / 4.0 km/L = 6.0 L -> Cumulative = 62.0 L > 60.0 (Exceeds Quota!).
    """
    tight_vehicle = Vehicle(
        vehicle_id="VEH099",
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.VAN,
        temp=TempSpec.REEFER,
        weight_cap_kg=2000.0,
        volume_cap_m3=12.0,
        depot="Peliyagoda",
        km_per_l=4.0,
        weekly_fuel_quota_l=60.0,
        weekly_fuel_used_l=40.0,
        external_reservations_l=10.0,
        remaining_trips=2,
    )

    o1 = make_test_order(
        order_ref="ORD001",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=100.0,
        order_volume_m3=1.0,
    )
    o2 = make_test_order(
        order_ref="ORD002",
        outlet_id="OUT002",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.NORMAL,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=100.0,
        order_volume_m3=1.0,
    )

    ctx = OperationalContext(planning_date="2026-10-03")

    trip1 = evaluate_trip_schedule(
        vehicle=tight_vehicle,
        trip_number=1,
        orders=[o1],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T04:00:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx,
    )

    trip2 = evaluate_trip_schedule(
        vehicle=tight_vehicle,
        trip_number=2,
        orders=[o2],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T06:30:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx,
    )

    timeline = evaluate_vehicle_timeline(tight_vehicle, [trip1, trip2], ctx)
    assert not timeline.weekly_fuel_valid
    assert timeline.cumulative_fuel_l == 62.0  # 40 + 10 + 6 + 6
    assert any(v.rule == "CUMULATIVE_WEEKLY_FUEL_EXCEEDED" for v in timeline.violations)


# ──────────────────────────────────────────────────────────────────────────────
# 6. Missing Travel & Fuel Data
# ──────────────────────────────────────────────────────────────────────────────

def test_missing_data_reporting(allowances, outlets, reefer_van):
    """
    Missing district travel record for Galle -> Peliyagoda.
    Must return a structured OperationalMissingData item, not crash.
    """
    order = make_test_order(
        order_ref="ORD001",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        district="Galle",
        depot="Peliyagoda",
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=100.0,
        order_volume_m3=1.0,
    )

    ctx = OperationalContext(planning_date="2026-10-03")
    schedule = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=1,
        orders=[order],
        brand=Brand.FRESH,
        district="Galle",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T04:00:00+05:30",
        travel_data={},  # Empty travel data
        outlets=outlets,
        allowances=allowances,
        context=ctx,
    )

    assert not schedule.is_feasible
    assert len(schedule.missing_data) >= 1
    assert any(m.field == "district_travel" for m in schedule.missing_data)


# ──────────────────────────────────────────────────────────────────────────────
# 7. Date Coverage Boundaries: Strict Missing Data vs Static Freeflow
# ──────────────────────────────────────────────────────────────────────────────

def test_date_coverage_dynamic_vs_static(colombo_travel, allowances, outlets, reefer_van):
    """
    Planning date 2026-10-03 is outside reference coverage (ends 2026-06-28).
    - If travel_policy == DYNAMIC_CONDITIONS: must return structured missing data error!
    - If travel_policy == STATIC_FREEFLOW: evaluates cleanly with static freeflow estimate.
    """
    order = make_test_order(
        order_ref="ORD001",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=100.0,
        order_volume_m3=1.0,
    )

    # Dynamic conditions outside coverage -> Missing Data
    ctx_dynamic = OperationalContext(
        planning_date="2026-10-03",
        travel_policy=TravelPolicy.DYNAMIC_CONDITIONS,
    )
    sched_dynamic = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=1,
        orders=[order],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T04:00:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx_dynamic,
    )
    assert not sched_dynamic.is_feasible
    assert any(m.field == "planning_date" for m in sched_dynamic.missing_data)

    # Static freeflow outside dynamic coverage -> Feasible with explicit notice
    ctx_static = OperationalContext(
        planning_date="2026-10-03",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )
    sched_static = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=1,
        orders=[order],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T04:00:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx_static,
    )
    assert sched_static.is_feasible
    assert not any(m.field == "planning_date" for m in sched_static.missing_data)
    assert "static district averages" in sched_static.travel_model_notice


# ──────────────────────────────────────────────────────────────────────────────
# 8. Demand Conservation & Order Classification per Line Item
# ──────────────────────────────────────────────────────────────────────────────

def test_line_item_order_classification():
    """
    Ensure order status is evaluated per line item and incompatible units are never summed.
    """
    order = make_test_order(
        order_ref="ORD001",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.CHILLED,
        order_units=15,
        order_weight_kg=150.0,
        order_volume_m3=1.5,
        line_items=[
            LineItem("ITEM-A", 10, "crates", 10.0, 0.1, "Dairy"),
            LineItem("ITEM-B", 5, "kg", 10.0, 0.1, "Cheese"),
        ],
    )

    # Case 1: Fully Served
    assigned_full = {"ITEM-A": 10.0, "ITEM-B": 5.0}
    assert classify_order_allocation(order, assigned_full) == OrderAllocationStatus.FULLY_SERVED

    # Case 2: Partially Served (1 item served, 1 deferred)
    assigned_partial = {"ITEM-A": 10.0, "ITEM-B": 0.0}
    assert classify_order_allocation(order, assigned_partial) == OrderAllocationStatus.PARTIALLY_SERVED

    # Case 3: Fully Deferred (0 assigned)
    assigned_none = {"ITEM-A": 0.0, "ITEM-B": 0.0}
    assert classify_order_allocation(order, assigned_none) == OrderAllocationStatus.FULLY_DEFERRED


# ──────────────────────────────────────────────────────────────────────────────
# 9. Complete Plan Validation Integration
# ──────────────────────────────────────────────────────────────────────────────

def test_validate_operational_plan_integration(colombo_travel, allowances, outlets, reefer_van):
    """
    Test overall plan validation: demand conservation, vehicle timelines, and order counts.
    """
    o1 = make_test_order(
        order_ref="ORD001",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.VAN_ONLY,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=100.0,
        order_volume_m3=1.0,
        line_items=[LineItem("ITEM-A", 10, "crates", 10.0, 0.1, "Milk")],
    )
    o2 = make_test_order(
        order_ref="ORD002",
        outlet_id="OUT002",
        brand=Brand.FRESH,
        dock_type=DockType.STREET,
        parking_constraint=ParkingConstraint.NORMAL,
        temp_requirement=TempRequirement.CHILLED,
        order_units=5,
        order_weight_kg=50.0,
        order_volume_m3=0.5,
        line_items=[LineItem("ITEM-B", 5, "crates", 10.0, 0.1, "Yogurt")],
    )

    ctx = OperationalContext(planning_date="2026-10-03")

    trip1 = evaluate_trip_schedule(
        vehicle=reefer_van,
        trip_number=1,
        orders=[o1, o2],
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        departure_time_iso="2026-10-03T04:00:00+05:30",
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
        context=ctx,
    )

    timeline = evaluate_vehicle_timeline(reefer_van, [trip1], ctx)
    result = validate_operational_plan(
        orders=[o1, o2],
        timelines=[timeline],
        context=ctx,
        fleet=[reefer_van],
        travel_data=colombo_travel,
        outlets=outlets,
        allowances=allowances,
    )

    assert result.valid
    assert result.is_dispatch_ready
    assert result.order_counts["total_orders"] == 2
    assert result.order_counts["fully_served_orders"] == 2
    assert result.order_counts["partially_served_orders"] == 0
    assert result.order_counts["fully_deferred_orders"] == 0
    assert result.quantity_totals["requested_units"] == 15.0
    assert result.quantity_totals["assigned_units"] == 15.0
    assert result.quantity_totals["deferred_units"] == 0.0
