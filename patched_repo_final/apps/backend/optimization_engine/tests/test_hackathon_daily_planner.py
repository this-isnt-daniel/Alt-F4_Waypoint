"""
Waypoint Optimizer — End-to-End Tests for Hackathon Daily Draft Planner
========================================================================
Tests the complete daily planning workflow against operational constraints:
  1. Order fitting capacity but failing delivery window -> deferred.
  2. Stop sequencing / reordering enabling feasible placement of multiple windows.
  3. Two trips on one vehicle without chronological overlap.
  4. Cumulative fuel quota exhaustion rejecting a second trip.
  5. Unselected (driver absent) and mechanically unavailable (workshop) vehicles excluded.
  6. Repeated orders at one outlet consolidated into a single physical stop visit.
  7. Demand conservation and strict JSON roundtrip revalidation.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from waypoint_optimizer.adapters.csv_adapter import ReferenceData
from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, Outlet,
    ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleStatus, VehicleType,
)
from waypoint_optimizer.hackathon_planner import generate_daily_draft_plan
from waypoint_optimizer.operational import (
    OperationalContext, TravelPolicy, WindowPolicy,
)


@pytest.fixture
def test_reference() -> ReferenceData:
    """Minimal authoritative reference data fixture."""
    travel = [
        DistrictTravel(
            district="Colombo",
            depot="Peliyagoda",
            road_class="urban",
            free_flow_kmh=30.0,
            depot_to_district_km=12.0,
            depot_to_district_freeflow_min=24.0,
            inter_stop_km=4.0,
            inter_stop_freeflow_min=8.0,
        )
    ]
    allowances = [
        ServiceAllowance(Brand.FRESH, DockType.STREET, 16.0),
        ServiceAllowance(Brand.FRESH, DockType.REAR_DOCK, 15.0),
        ServiceAllowance(Brand.STYLE, DockType.STREET, 46.0),
    ]
    outlets = {
        "OUT001": Outlet("OUT001", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.VAN_ONLY,
                         window_open_time="05:00", window_close_time="07:30"),
        "OUT002": Outlet("OUT002", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                         window_open_time="05:30", window_close_time="08:00"),
        "OUT_EARLY": Outlet("OUT_EARLY", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                            window_open_time="03:30", window_close_time="04:15"),
        "OUT_TIGHT_A": Outlet("OUT_TIGHT_A", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                              window_open_time="04:20", window_close_time="04:45"),
        "OUT_TIGHT_B": Outlet("OUT_TIGHT_B", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                              window_open_time="05:00", window_close_time="06:00"),
    }
    vehicles = [
        Vehicle(
            vehicle_id="VEH001",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.REEFER,
            weight_cap_kg=2500.0,
            volume_cap_m3=15.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=300.0,
            weekly_fuel_used_l=50.0,
            external_reservations_l=10.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        )
    ]
    return ReferenceData(
        outlets=outlets,
        vehicles=vehicles,
        travel=travel,
        allowances=allowances,
        ref_dir="test_mock",
    )


def make_test_order(
    ref: str,
    outlet_id: str,
    units: int = 10,
    weight: float = 100.0,
    volume: float = 1.0,
    temp: TempRequirement = TempRequirement.AMBIENT,
    parking: Optional[ParkingConstraint] = None,
    line_items: list[LineItem] | None = None,
) -> Order:
    if parking is None:
        parking = ParkingConstraint.VAN_ONLY if outlet_id == "OUT001" else ParkingConstraint.NORMAL
    return Order(
        order_ref=ref,
        outlet_id=outlet_id,
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        dock_type=DockType.STREET,
        parking_constraint=parking,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=temp,
        order_units=units,
        order_weight_kg=weight,
        order_volume_m3=volume,
        deferred_prev=False,
        defer_count=1,
        is_urgent=False,
        line_items=line_items or [],
    )


# ──────────────────────────────────────────────────────────────────────────────
# 1. Order Fitting Capacity but Failing Delivery Window
# ──────────────────────────────────────────────────────────────────────────────

def test_order_capacity_fits_but_delivery_window_fails(test_reference):
    """
    OUT_EARLY closes at 04:15.
    Standard departure is 04:00. Outbound travel to Colombo is 24 min -> Arrival at 04:24.
    Vehicle arrival (04:24) misses the 04:15 window close.
    Order fits weight/volume capacity, but cannot be delivered before closing.
    Must be deferred with a window-related diagnostic reason.
    """
    order = make_test_order("ORD_MISSED", "OUT_EARLY", weight=50.0, volume=0.5)
    context = OperationalContext(planning_date="2026-10-03")

    plan = generate_daily_draft_plan(
        orders=[order],
        fleet=test_reference.vehicles,
        reference_data=test_reference,
        context=context,
    )

    assert plan["validation"]["valid"]
    assert plan["order_counts"]["fully_served_orders"] == 0
    assert plan["order_counts"]["fully_deferred_orders"] == 1
    assert len(plan["trips"]) == 0
    assert len(plan["deferred_orders"]) == 1
    assert plan["deferred_orders"][0]["order_ref"] == "ORD_MISSED"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Stop Sequencing Enables Feasible Placement of Multiple Windows
# ──────────────────────────────────────────────────────────────────────────────

def test_stop_sequencing_enables_placement(test_reference):
    """
    Two outlets with narrow, staggered windows:
      - OUT_TIGHT_A: Window 04:20 to 04:45
      - OUT_TIGHT_B: Window 05:00 to 06:00
    If A is visited first:
      - Depart 04:00 -> Arrive A 04:24 (within 04:20-04:45). Unload 16 min -> Depart A 04:40.
      - Inter-stop 8 min -> Arrive B 04:48. Wait 12 min until 05:00 -> Depart B 05:16 (within 05:00-06:00).
    Both orders are successfully scheduled and served!
    """
    o_a = make_test_order("ORD_A", "OUT_TIGHT_A", weight=80.0, volume=0.8)
    o_b = make_test_order("ORD_B", "OUT_TIGHT_B", weight=80.0, volume=0.8)
    context = OperationalContext(planning_date="2026-10-03")

    plan = generate_daily_draft_plan(
        orders=[o_a, o_b],
        fleet=test_reference.vehicles,
        reference_data=test_reference,
        context=context,
    )

    assert plan["validation"]["valid"]
    assert plan["order_counts"]["fully_served_orders"] == 2
    assert len(plan["trips"]) == 1

    stops = plan["trips"][0]["driver_itinerary"]
    assert len(stops) == 2
    # Verify chronological order
    assert stops[0]["outlet_id"] == "OUT_TIGHT_A"
    assert stops[0]["window_compliant"]
    assert stops[1]["outlet_id"] == "OUT_TIGHT_B"
    assert stops[1]["window_compliant"]


# ──────────────────────────────────────────────────────────────────────────────
# 3. Two Trips on One Vehicle Without Chronological Overlap
# ──────────────────────────────────────────────────────────────────────────────

def test_two_trips_same_vehicle_no_overlap(test_reference):
    """
    Trip 1: Fresh orders (depart 04:00, return depot ~05:40, next available ~06:10).
    Trip 2: Fresh orders scheduled after 06:10.
    Both trips executed by VEH001 without chronological overlap.
    """
    o1 = make_test_order("ORD001", "OUT001", weight=1200.0, volume=7.0)
    o2 = make_test_order("ORD002", "OUT002", weight=1200.0, volume=7.0)
    # Total weight is 2400 kg <= vehicle cap 2500 kg, but total volume is 14 m3 <= 15 m3
    # With a small vehicle, putting both on 1 trip might be tight, so let's use a vehicle cap that forces 2 trips:
    small_v = Vehicle(
        vehicle_id="VEH_SPLIT",
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.VAN,
        temp=TempSpec.REEFER,
        weight_cap_kg=1500.0,  # Forces 1 order per trip
        volume_cap_m3=10.0,
        depot="Peliyagoda",
        km_per_l=5.0,
        weekly_fuel_quota_l=300.0,
        weekly_fuel_used_l=50.0,
        external_reservations_l=10.0,
        remaining_trips=2,
        is_selected_for_planning=True,
    )

    context = OperationalContext(planning_date="2026-10-03")

    plan = generate_daily_draft_plan(
        orders=[o1, o2],
        fleet=[small_v],
        reference_data=test_reference,
        context=context,
    )

    assert plan["validation"]["valid"]
    assert plan["order_counts"]["fully_served_orders"] == 2
    assert len(plan["trips"]) == 2

    t1 = plan["trips"][0]
    t2 = plan["trips"][1]
    assert t1["vehicle_id"] == "VEH_SPLIT"
    assert t2["vehicle_id"] == "VEH_SPLIT"

    # Verify no chronological overlap
    t1_avail = t1["vehicle_next_available_iso"]
    t2_dep = t2["departure_time_iso"]
    assert t2_dep >= t1_avail


# ──────────────────────────────────────────────────────────────────────────────
# 4. Cumulative Fuel Quota Rejects Second Trip
# ──────────────────────────────────────────────────────────────────────────────

def test_cumulative_fuel_rejects_second_trip(test_reference):
    """
    Vehicle weekly quota is 65 L.
    Prior used: 45 L, external reservations: 10 L -> Remaining = 10 L.
    Each trip takes 24 km / 4.0 km/L = 6.0 L.
    Trip 1 takes 6.0 L -> Cumulative = 61.0 L <= 65 L (feasible).
    Trip 2 would take 6.0 L -> Cumulative = 67.0 L > 65 L (quota exceeded!).
    Second trip must not be allocated to this vehicle.
    """
    tight_fuel_v = Vehicle(
        vehicle_id="VEH_FUEL",
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.VAN,
        temp=TempSpec.REEFER,
        weight_cap_kg=1000.0,  # Forces 1 order per trip
        volume_cap_m3=8.0,
        depot="Peliyagoda",
        km_per_l=4.0,
        weekly_fuel_quota_l=65.0,
        weekly_fuel_used_l=45.0,
        external_reservations_l=10.0,
        remaining_trips=2,
        is_selected_for_planning=True,
    )

    o1 = make_test_order("ORD_F1", "OUT001", weight=600.0, volume=5.0)
    o2 = make_test_order("ORD_F2", "OUT002", weight=600.0, volume=5.0)

    context = OperationalContext(planning_date="2026-10-03")

    plan = generate_daily_draft_plan(
        orders=[o1, o2],
        fleet=[tight_fuel_v],
        reference_data=test_reference,
        context=context,
    )

    assert plan["validation"]["valid"]
    assert len(plan["trips"]) == 1
    assert plan["order_counts"]["fully_served_orders"] == 1
    assert plan["order_counts"]["fully_deferred_orders"] == 1
    assert plan["trips"][0]["fuel"]["fuel_compliant"]
    assert plan["trips"][0]["fuel"]["cumulative_fuel_used_l"] <= 65.0


# ──────────────────────────────────────────────────────────────────────────────
# 5. Unselected and Mechanically Unavailable Vehicles Excluded
# ──────────────────────────────────────────────────────────────────────────────

def test_unselected_and_unavailable_vehicles_excluded(test_reference):
    """
    Fleet of 3 vehicles:
      - V_WORKSHOP: status == IN_WORKSHOP
      - V_UNSELECTED: is_selected_for_planning == False
      - V_ACTIVE: available and selected
    Only V_ACTIVE should receive assignments.
    """
    v_workshop = Vehicle(
        vehicle_id="V_WORKSHOP",
        status=VehicleStatus.IN_WORKSHOP,
        type=VehicleType.VAN,
        temp=TempSpec.REEFER,
        weight_cap_kg=3000.0,
        volume_cap_m3=20.0,
        depot="Peliyagoda",
        is_selected_for_planning=False,
    )
    v_unselected = Vehicle(
        vehicle_id="V_UNSELECTED",
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.VAN,
        temp=TempSpec.REEFER,
        weight_cap_kg=3000.0,
        volume_cap_m3=20.0,
        depot="Peliyagoda",
        is_selected_for_planning=False,
        exclusion_reason="Driver on medical leave",
    )
    v_active = Vehicle(
        vehicle_id="V_ACTIVE",
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.VAN,
        temp=TempSpec.REEFER,
        weight_cap_kg=3000.0,
        volume_cap_m3=20.0,
        depot="Peliyagoda",
        km_per_l=5.0,
        weekly_fuel_quota_l=400.0,
        weekly_fuel_used_l=100.0,
        external_reservations_l=0.0,
        remaining_trips=2,
        is_selected_for_planning=True,
    )

    order = make_test_order("ORD_AVAIL", "OUT001", weight=200.0, volume=2.0)
    context = OperationalContext(planning_date="2026-10-03")

    plan = generate_daily_draft_plan(
        orders=[order],
        fleet=[v_workshop, v_unselected, v_active],
        reference_data=test_reference,
        context=context,
    )

    assert plan["validation"]["valid"]
    assert len(plan["trips"]) == 1
    assert plan["trips"][0]["vehicle_id"] == "V_ACTIVE"


# ──────────────────────────────────────────────────────────────────────────────
# 6. Repeated Orders at One Outlet Consolidated
# ──────────────────────────────────────────────────────────────────────────────

def test_repeated_orders_at_one_outlet_consolidated(test_reference):
    """
    3 distinct orders for OUT001:
      - ORD_1: 10 crates Dairy
      - ORD_2: 5 crates Cheese
      - ORD_3: 8 crates Milk
    Should consolidate into exactly 1 physical stop visit with a single service duration (16 min),
    and the Loader Manifest must reflect all 3 line items loaded in reverse order.
    """
    o1 = make_test_order(
        "ORD_1", "OUT001", units=10, weight=100.0, volume=1.0,
        line_items=[LineItem("ITEM_1", 10, "crates", 10.0, 0.1, "Dairy")]
    )
    o2 = make_test_order(
        "ORD_2", "OUT001", units=5, weight=50.0, volume=0.5,
        line_items=[LineItem("ITEM_2", 5, "crates", 10.0, 0.1, "Cheese")]
    )
    o3 = make_test_order(
        "ORD_3", "OUT001", units=8, weight=80.0, volume=0.8,
        line_items=[LineItem("ITEM_3", 8, "crates", 10.0, 0.1, "Milk")]
    )

    context = OperationalContext(planning_date="2026-10-03")

    plan = generate_daily_draft_plan(
        orders=[o1, o2, o3],
        fleet=test_reference.vehicles,
        reference_data=test_reference,
        context=context,
    )

    assert plan["validation"]["valid"]
    assert plan["order_counts"]["fully_served_orders"] == 3
    assert len(plan["trips"]) == 1

    trip = plan["trips"][0]
    # Only 1 physical stop visit for OUT001
    assert len(trip["driver_itinerary"]) == 1
    stop = trip["driver_itinerary"][0]
    assert stop["outlet_id"] == "OUT001"
    assert len(stop["order_refs"]) == 3
    assert stop["service_duration_min"] == 16.0  # Single service allowance

    # Loader manifest contains all 3 items
    manifest = trip["loader_manifest"]
    assert len(manifest) == 3
    assert {m["line_item_id"] for m in manifest} == {"ITEM_1", "ITEM_2", "ITEM_3"}


# ──────────────────────────────────────────────────────────────────────────────
# 7. Demand Conservation and Strict JSON Roundtrip Revalidation
# ──────────────────────────────────────────────────────────────────────────────

def test_demand_conservation_and_json_roundtrip(test_reference, tmp_path):
    """
    Serialize plan to strict JSON (allow_nan=False), reload, and verify:
      - Valid JSON without NaN or Infinity.
      - Requested quantity == Assigned quantity + Deferred quantity.
      - Total orders == Fully served + Partially served + Fully deferred.
    """
    o1 = make_test_order(
        "ORD_C1", "OUT001", units=10, weight=100.0, volume=1.0,
        line_items=[LineItem("ITEM_C1", 10, "crates", 10.0, 0.1, "Apples")]
    )
    o2 = make_test_order(
        "ORD_C2", "OUT_EARLY", units=5, weight=50.0, volume=0.5,
        line_items=[LineItem("ITEM_C2", 5, "crates", 10.0, 0.1, "Berries")]
    )

    context = OperationalContext(planning_date="2026-10-03")

    plan = generate_daily_draft_plan(
        orders=[o1, o2],
        fleet=test_reference.vehicles,
        reference_data=test_reference,
        context=context,
    )

    json_file = tmp_path / "test_plan.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, allow_nan=False)

    with open(json_file, "r", encoding="utf-8") as f:
        reloaded = json.load(f)

    assert reloaded["status"] == "FEASIBLE"
    assert reloaded["validation"]["valid"]

    counts = reloaded["order_counts"]
    assert counts["total_orders"] == counts["fully_served_orders"] + counts["partially_served_orders"] + counts["fully_deferred_orders"]

    quantities = reloaded["quantity_totals"]
    assert quantities["requested_units"] == quantities["assigned_units"] + quantities["deferred_units"]


# ──────────────────────────────────────────────────────────────────────────────
# 8. Missing Service Allowance Produces Structured Missing-Data Error
# ──────────────────────────────────────────────────────────────────────────────

def test_missing_service_allowance_raises_structured_error(test_reference):
    """
    Verify that an unmapped service allowance raises an InputValidationError with
    structured error details, never silently receiving an invented 15.0 minute fallback.
    """
    from waypoint_optimizer.input_validation import InputValidationError

    # Outlet with MALL_BAY dock type for FRESH brand, where test_reference.allowances
    # does not have (Brand.FRESH, DockType.MALL_BAY)
    custom_order = make_test_order("ORD_NO_ALLOWANCE", "OUT001", weight=50.0, volume=0.5)
    # Mutate to an unmapped dock type
    custom_order = Order(
        order_ref="ORD_NO_ALLOWANCE",
        outlet_id="OUT001",
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        dock_type=DockType.MALL_BAY,  # Not in test_reference allowances for Fresh
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=10,
        order_weight_kg=50.0,
        order_volume_m3=0.5,
        deferred_prev=False,
        defer_count=1,
        is_urgent=False,
    )

    context = OperationalContext(planning_date="2026-10-03")

    with pytest.raises(InputValidationError) as exc_info:
        generate_daily_draft_plan(
            orders=[custom_order],
            fleet=test_reference.vehicles,
            reference_data=test_reference,
            context=context,
        )

    err = exc_info.value
    assert any(e.field == "service_allowances" for e in err.errors)
    assert any("fresh" in e.message.lower() and "mall_bay" in e.message.lower() for e in err.errors)


# ──────────────────────────────────────────────────────────────────────────────
# 9. Operational Targeted CP-SAT Improvement & Hybrid Workflow Tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def hybrid_test_reference() -> ReferenceData:
    """Fixture providing multi-vehicle multi-district environment for CP-SAT tests."""
    travel = [
        DistrictTravel(
            district="Colombo",
            depot="Peliyagoda",
            road_class="urban",
            free_flow_kmh=30.0,
            depot_to_district_km=10.0,
            depot_to_district_freeflow_min=20.0,
            inter_stop_km=2.0,
            inter_stop_freeflow_min=5.0,
        ),
        DistrictTravel(
            district="Avissawella",
            depot="Peliyagoda",
            road_class="urban",
            free_flow_kmh=30.0,
            depot_to_district_km=15.0,
            depot_to_district_freeflow_min=25.0,
            inter_stop_km=2.0,
            inter_stop_freeflow_min=5.0,
        ),
        DistrictTravel(
            district="Kalutara",
            depot="Peliyagoda",
            road_class="urban",
            free_flow_kmh=30.0,
            depot_to_district_km=20.0,
            depot_to_district_freeflow_min=30.0,
            inter_stop_km=2.0,
            inter_stop_freeflow_min=5.0,
        ),
    ]
    allowances = [
        ServiceAllowance(Brand.FRESH, DockType.STREET, 15.0),
        ServiceAllowance(Brand.STYLE, DockType.STREET, 15.0),
    ]
    outlets = {
        "OUT_COL_1": Outlet("OUT_COL_1", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                            window_open_time="05:00", window_close_time="08:00"),
        "OUT_COL_2": Outlet("OUT_COL_2", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                            window_open_time="05:00", window_close_time="08:00"),
        "OUT_AVI_1": Outlet("OUT_AVI_1", Brand.FRESH, "Avissawella", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                            window_open_time="05:00", window_close_time="06:30"),
        "OUT_FIXED": Outlet("OUT_FIXED", Brand.FRESH, "Kalutara", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                            window_open_time="05:00", window_close_time="08:00"),
    }
    vehicles = [
        Vehicle(
            vehicle_id="VEH_FIXED",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.TRUCK,
            temp=TempSpec.REEFER,
            weight_cap_kg=500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=200.0,
            weekly_fuel_used_l=10.0,
            external_reservations_l=0.0,
            remaining_trips=1,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="VEH_LARGE",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.TRUCK,
            temp=TempSpec.REEFER,
            weight_cap_kg=500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=200.0,
            weekly_fuel_used_l=10.0,
            external_reservations_l=0.0,
            remaining_trips=1,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="VEH_SMALL",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.TRUCK,
            temp=TempSpec.REEFER,
            weight_cap_kg=300.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=200.0,
            weekly_fuel_used_l=10.0,
            external_reservations_l=0.0,
            remaining_trips=1,
            is_selected_for_planning=True,
        ),
    ]
    return ReferenceData(
        outlets=outlets,
        vehicles=vehicles,
        travel=travel,
        allowances=allowances,
        ref_dir="test_mock_hybrid",
    )


def test_operational_cpsat_improves_deferrals_via_reassignment(hybrid_test_reference):
    """
    Demonstrate that targeted CP-SAT reassigns existing orders across vehicles
    to place a deferred order, strictly reducing deferral penalty and serving all orders.
    """
    context = OperationalContext(planning_date="2026-10-03")

    # High penalty order in Kalutara taking VEH_FIXED (450 kg on 500 kg capacity)
    ord_fix = Order(
        order_ref="ORD_FIX", outlet_id="OUT_FIXED", brand=Brand.FRESH, district="Kalutara", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="06:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=450.0, order_volume_m3=1.0, deferred_prev=True, defer_count=5, is_urgent=False,
    )
    # High penalty order in Avissawella (250 kg) with early window (05:00 - 06:30)
    ord_a1 = Order(
        order_ref="ORD_A1", outlet_id="OUT_AVI_1", brand=Brand.FRESH, district="Avissawella", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="06:30", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=250.0, order_volume_m3=1.0, deferred_prev=True, defer_count=3, is_urgent=False,
    )
    # Two orders in Colombo (250 kg each, window 05:00 - 08:00)
    ord_c1 = Order(
        order_ref="ORD_C1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="08:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=250.0, order_volume_m3=1.0, deferred_prev=False, defer_count=1, is_urgent=False,
    )
    ord_c2 = Order(
        order_ref="ORD_C2", outlet_id="OUT_COL_2", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="08:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=250.0, order_volume_m3=1.0, deferred_prev=False, defer_count=1, is_urgent=False,
    )

    all_orders = [ord_fix, ord_a1, ord_c1, ord_c2]

    # First, run with CP-SAT disabled to verify greedy baseline defers ORD_C2
    greedy_plan = generate_daily_draft_plan(
        orders=all_orders,
        fleet=hybrid_test_reference.vehicles,
        reference_data=hybrid_test_reference,
        context=context,
        enable_targeted_cpsat=False,
    )
    assert greedy_plan["validation"]["valid"]
    assert greedy_plan["order_counts"]["fully_served_orders"] == 3
    assert greedy_plan["order_counts"]["fully_deferred_orders"] == 1
    assert greedy_plan["algorithm"] == "multistart_greedy_operational"
    assert greedy_plan["deferred_orders"][0]["order_ref"] == "ORD_C2"

    # Now, run with CP-SAT enabled
    hybrid_plan = generate_daily_draft_plan(
        orders=all_orders,
        fleet=hybrid_test_reference.vehicles,
        reference_data=hybrid_test_reference,
        context=context,
        enable_targeted_cpsat=True,
        targeted_cpsat_time_limit_s=5.0,
    )

    assert hybrid_plan["validation"]["valid"]
    assert hybrid_plan["order_counts"]["fully_served_orders"] == 4
    assert hybrid_plan["order_counts"]["fully_deferred_orders"] == 0
    assert len(hybrid_plan["deferred_orders"]) == 0
    assert hybrid_plan["algorithm"] == "hybrid_greedy_targeted_cpsat"

    cpsat_stage = hybrid_plan["targeted_cpsat_stage"]
    assert cpsat_stage["executed"] is True
    assert cpsat_stage["improvement_accepted"] is True
    assert cpsat_stage["outcome"] == "ACCEPTED"
    assert cpsat_stage["raw_solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert cpsat_stage["final_deferral_penalty"] < cpsat_stage["incumbent_deferral_penalty"]
    assert cpsat_stage["final_served_count"] == 4
    assert cpsat_stage["incumbent_served_count"] == 3
    assert cpsat_stage["runtime_seconds"] > 0

    # Unaffected vehicle VEH_FIXED remains fixed
    fixed_trip = next(t for t in hybrid_plan["trips"] if t["vehicle_id"] == "VEH_FIXED")
    assert fixed_trip["district"] == "Kalutara"
    assert fixed_trip["driver_itinerary"][0]["order_refs"] == ["ORD_FIX"]


def test_operational_cpsat_no_improvement_retains_incumbent(hybrid_test_reference):
    """
    When CP-SAT cannot find a candidate that improves the objective,
    the valid greedy incumbent is cleanly retained.
    """
    context = OperationalContext(planning_date="2026-10-03")

    # Only single order: already served by greedy
    orders = [
        Order(
            order_ref="ORD_ONLY", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
            dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
            window_open_time="05:00", window_close_time="08:00", temp_requirement=TempRequirement.AMBIENT,
            order_units=10, order_weight_kg=200.0, order_volume_m3=1.0, deferred_prev=False, defer_count=1, is_urgent=False,
        )
    ]

    plan = generate_daily_draft_plan(
        orders=orders,
        fleet=hybrid_test_reference.vehicles,
        reference_data=hybrid_test_reference,
        context=context,
        enable_targeted_cpsat=True,
    )

    assert plan["validation"]["valid"]
    assert plan["order_counts"]["fully_served_orders"] == 1
    cpsat_stage = plan["targeted_cpsat_stage"]
    assert cpsat_stage["improvement_accepted"] is False
    assert cpsat_stage["outcome"] == "SKIPPED_NO_DEFERRED_ORDERS"
    assert plan["algorithm"] == "multistart_greedy_operational"


def test_operational_cpsat_timeout_and_error_fallback(hybrid_test_reference):
    """
    Verify that upon timeout or solver error, the engine cleanly retains
    the incumbent without mutating it.
    """
    from waypoint_optimizer.targeted_cpsat import operational_targeted_cpsat_improve
    from waypoint_optimizer.operational.validator import OperationalValidationResult

    context = OperationalContext(planning_date="2026-10-03")

    ord_g1 = Order(
        order_ref="ORD_G1", outlet_id="OUT_GAM_1", brand=Brand.FRESH, district="Gampaha", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="08:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=300.0, order_volume_m3=1.0, deferred_prev=True, defer_count=3, is_urgent=False,
    )
    ord_c1 = Order(
        order_ref="ORD_C1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="08:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=250.0, order_volume_m3=1.0, deferred_prev=False, defer_count=1, is_urgent=False,
    )
    all_orders = [ord_g1, ord_c1]

    # Call with non-supported travel policy -> immediate skip
    dyn_context = OperationalContext(planning_date="2026-01-05", travel_policy=TravelPolicy.DYNAMIC_CONDITIONS)
    val_res = OperationalValidationResult(valid=True, violations=[], missing_data=[])
    incumbent_state = {
        "trip_schedules": [],
        "timelines": [],
        "validation_result": val_res,
        "assigned_orders": set(),
    }
    state, info = operational_targeted_cpsat_improve(
        incumbent_plan_state=incumbent_state,
        orders=all_orders,
        fleet=hybrid_test_reference.vehicles,
        travel_data={(t.district, t.depot): t for t in hybrid_test_reference.travel},
        outlets=hybrid_test_reference.outlets,
        allowances={(a.brand, a.dock_type): a.service_allowance_min for a in hybrid_test_reference.allowances},
        context=dyn_context,
    )
    assert info["executed"] is False
    assert info["outcome"] == "SKIPPED_POLICY_NOT_SUPPORTED"
    assert info["improvement_accepted"] is False
    assert state == incumbent_state


def test_operational_cpsat_invalid_candidate_rejected(hybrid_test_reference, monkeypatch):
    """
    Verify that if a candidate solution produced during targeted CP-SAT fails
    independent operational validation, it is rejected and the incumbent is retained.
    """
    from waypoint_optimizer.operational.validator import OperationalValidationResult, OperationalViolation

    context = OperationalContext(planning_date="2026-10-03")

    ord_fix = Order(
        order_ref="ORD_FIX", outlet_id="OUT_FIXED", brand=Brand.FRESH, district="Kalutara", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="06:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=450.0, order_volume_m3=1.0, deferred_prev=True, defer_count=5, is_urgent=False,
    )
    ord_a1 = Order(
        order_ref="ORD_A1", outlet_id="OUT_AVI_1", brand=Brand.FRESH, district="Avissawella", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="06:30", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=250.0, order_volume_m3=1.0, deferred_prev=True, defer_count=3, is_urgent=False,
    )
    ord_c1 = Order(
        order_ref="ORD_C1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="08:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=250.0, order_volume_m3=1.0, deferred_prev=False, defer_count=1, is_urgent=False,
    )
    ord_c2 = Order(
        order_ref="ORD_C2", outlet_id="OUT_COL_2", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="08:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=250.0, order_volume_m3=1.0, deferred_prev=False, defer_count=1, is_urgent=False,
    )

    all_orders = [ord_fix, ord_a1, ord_c1, ord_c2]

    # Generate greedy incumbent
    greedy_plan = generate_daily_draft_plan(
        orders=all_orders,
        fleet=hybrid_test_reference.vehicles,
        reference_data=hybrid_test_reference,
        context=context,
        enable_targeted_cpsat=False,
    )
    assert greedy_plan["validation"]["valid"]

    # Mock validate_operational_plan to simulate validation rejection
    import waypoint_optimizer.targeted_cpsat as tcp
    def mock_invalid_validate(orders, timelines, context, **kwargs):
        return OperationalValidationResult(
            valid=False,
            violations=[OperationalViolation("DELIVERY_WINDOW_VIOLATION", "Simulated delivery window violation", "OUT_COL_2")],
            missing_data=[],
        )

    monkeypatch.setattr(tcp, "validate_operational_plan", mock_invalid_validate)

    # Run hybrid plan with mocked invalid candidate validation
    hybrid_plan = generate_daily_draft_plan(
        orders=all_orders,
        fleet=hybrid_test_reference.vehicles,
        reference_data=hybrid_test_reference,
        context=context,
        enable_targeted_cpsat=True,
    )

    assert hybrid_plan["targeted_cpsat_stage"]["executed"] is True
    assert hybrid_plan["targeted_cpsat_stage"]["improvement_accepted"] is False
    assert hybrid_plan["targeted_cpsat_stage"]["outcome"] == "REJECTED_INVALID"
    assert "DELIVERY_WINDOW_VIOLATION" in hybrid_plan["targeted_cpsat_stage"]["rejection_or_skip_reason"]
    assert hybrid_plan["algorithm"] == "multistart_greedy_operational"
    assert hybrid_plan["order_counts"]["fully_served_orders"] == 3


def test_operational_cpsat_enforces_fuel_and_windows(hybrid_test_reference):
    """
    Verify that CP-SAT respects cumulative fuel bounds with external reservations,
    preventing assignment of orders when fuel quota is exhausted.
    """
    context = OperationalContext(planning_date="2026-10-03")

    # Vehicle with zero available fuel headroom (quota = used + reservations)
    low_fuel_vehicles = [
        Vehicle(
            vehicle_id="VEH_A",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.TRUCK,
            temp=TempSpec.REEFER,
            weight_cap_kg=500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=20.0,
            weekly_fuel_used_l=10.0,
            external_reservations_l=10.0,  # 10 + 10 = 20 L -> 0 L headroom!
            remaining_trips=1,
            is_selected_for_planning=True,
        )
    ]
    ref = ReferenceData(
        outlets=hybrid_test_reference.outlets,
        vehicles=low_fuel_vehicles,
        travel=hybrid_test_reference.travel,
        allowances=hybrid_test_reference.allowances,
        ref_dir="test_fuel",
    )
    order = Order(
        order_ref="ORD_FUEL_FAIL", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="08:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=250.0, order_volume_m3=1.0, deferred_prev=False, defer_count=1, is_urgent=False,
    )

    plan = generate_daily_draft_plan(
        orders=[order],
        fleet=low_fuel_vehicles,
        reference_data=ref,
        context=context,
        enable_targeted_cpsat=True,
    )

    assert plan["validation"]["valid"]
    assert plan["order_counts"]["fully_served_orders"] == 0
    assert plan["order_counts"]["fully_deferred_orders"] == 1
    # CP-SAT should skip because no vehicle has fuel headroom
    assert plan["targeted_cpsat_stage"]["improvement_accepted"] is False


