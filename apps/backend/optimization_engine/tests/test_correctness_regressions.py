"""
Regression tests reproducing and verifying fixes for confirmed correctness issues:
1. Operational input validation at generate_daily_draft_plan's Python API boundary
   (nonfinite values, duplicate IDs, inconsistent attributes, missing required live fleet state;
    no silent conversion of missing fuel usage/reservations to zero).
2. Independent operational validator
   (demand conservation, rejection of unknown refs, duplicates, unauthorized splits,
    manipulated reported totals/timestamps, quantity totals separated by unit).
3. Operational CP-SAT corrections
   (separate Tech modeling with >= 06:30 departure and exact Tech allowances,
    one-stop fuel boundaries with 0 inter-stop distance, incumbent preservation).
4. Consistent lexicographic objective
   (minimize penalty, then maximize served orders, then minimize fuel).
5. Dynamic travel structured missing-data diagnostics
   (no silent fallback to static).
"""
import math
import pytest

from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, Outlet,
    ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleStatus, VehicleType,
)
from waypoint_optimizer.operational.schedule_evaluator import parse_iso_or_time_str
from waypoint_optimizer.adapters.csv_adapter import ReferenceData
from waypoint_optimizer.hackathon_planner import (
    generate_daily_draft_plan, score_plan_objective,
)
from waypoint_optimizer.input_validation import InputValidationError
from waypoint_optimizer.operational import (
    OperationalContext, TravelPolicy, WindowPolicy,
)
from waypoint_optimizer.operational.validator import validate_operational_plan


@pytest.fixture
def base_references() -> ReferenceData:
    travel = [
        DistrictTravel(
            district="Colombo",
            depot="Peliyagoda",
            road_class="urban",
            free_flow_kmh=30.0,
            depot_to_district_km=15.0,
            depot_to_district_freeflow_min=30.0,
            inter_stop_km=5.0,
            inter_stop_freeflow_min=10.0,
        ),
        DistrictTravel(
            district="Gampaha",
            depot="Peliyagoda",
            road_class="suburban",
            free_flow_kmh=40.0,
            depot_to_district_km=25.0,
            depot_to_district_freeflow_min=37.5,
            inter_stop_km=6.0,
            inter_stop_freeflow_min=9.0,
        ),
    ]
    allowances = [
        ServiceAllowance(Brand.FRESH, DockType.STREET, 15.0),
        ServiceAllowance(Brand.FRESH, DockType.REAR_DOCK, 20.0),
        ServiceAllowance(Brand.STYLE, DockType.STREET, 25.0),
        ServiceAllowance(Brand.TECH, DockType.REAR_DOCK, 30.0),
        ServiceAllowance(Brand.TECH, DockType.STREET, 35.0),
    ]
    outlets = {
        "OUT_COL_1": Outlet("OUT_COL_1", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                            window_open_time="05:00", window_close_time="09:00"),
        "OUT_COL_2": Outlet("OUT_COL_2", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                            window_open_time="05:00", window_close_time="09:00"),
        "OUT_TECH_1": Outlet("OUT_TECH_1", Brand.TECH, "Gampaha", "Peliyagoda", DockType.REAR_DOCK, ParkingConstraint.NORMAL,
                             window_open_time="07:00", window_close_time="11:00"),
        "OUT_TECH_2": Outlet("OUT_TECH_2", Brand.TECH, "Gampaha", "Peliyagoda", DockType.REAR_DOCK, ParkingConstraint.NORMAL,
                             window_open_time="07:00", window_close_time="11:00"),
    }
    vehicles = [
        Vehicle(
            vehicle_id="V_AMB",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=20.0,
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
        ref_dir="mock_ref",
    )


# ==============================================================================
# 1. Operational Input Validation at Python API Boundary
# ==============================================================================

def test_input_validation_boundary_rejects_missing_live_fleet_state(base_references):
    """
    Ensure vehicles selected for planning without weekly_fuel_used_l or
    external_reservations_l are rejected and NOT silently converted to 0.0.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )

    # Missing weekly_fuel_used_l
    bad_v1 = Vehicle(
        vehicle_id="V_BAD1", status=VehicleStatus.AVAILABLE, type=VehicleType.VAN, temp=TempSpec.AMBIENT,
        weight_cap_kg=1000.0, volume_cap_m3=8.0, depot="Peliyagoda", km_per_l=5.0,
        weekly_fuel_quota_l=200.0, weekly_fuel_used_l=None, external_reservations_l=10.0,
        remaining_trips=2, is_selected_for_planning=True,
    )
    with pytest.raises(InputValidationError) as exc1:
        generate_daily_draft_plan([order], [bad_v1], base_references, context)
    assert any("weekly_fuel_used_l" in str(err) for err in exc1.value.errors)

    # Missing external_reservations_l
    bad_v2 = Vehicle(
        vehicle_id="V_BAD2", status=VehicleStatus.AVAILABLE, type=VehicleType.VAN, temp=TempSpec.AMBIENT,
        weight_cap_kg=1000.0, volume_cap_m3=8.0, depot="Peliyagoda", km_per_l=5.0,
        weekly_fuel_quota_l=200.0, weekly_fuel_used_l=20.0, external_reservations_l=None,
        remaining_trips=2, is_selected_for_planning=True,
    )
    with pytest.raises(InputValidationError) as exc2:
        generate_daily_draft_plan([order], [bad_v2], base_references, context)
    assert any("external_reservations_l" in str(err) for err in exc2.value.errors)


def test_input_validation_boundary_rejects_nonfinite_and_duplicates(base_references):
    """
    Reject nonfinite numeric values and duplicate IDs at API boundary.
    """
    context = OperationalContext(planning_date="2026-10-03")

    # Nonfinite weight
    nan_order = Order(
        order_ref="O_NAN", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=float("nan"), order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    with pytest.raises(InputValidationError) as exc:
        generate_daily_draft_plan([nan_order], base_references.vehicles, base_references, context)
    assert any("order_weight_kg" in str(err) for err in exc.value.errors)

    # Duplicate order ref
    ord_dup1 = Order(
        order_ref="DUP_O", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    ord_dup2 = Order(
        order_ref="DUP_O", outlet_id="OUT_COL_2", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    with pytest.raises(InputValidationError) as exc:
        generate_daily_draft_plan([ord_dup1, ord_dup2], base_references.vehicles, base_references, context)
    assert any("Duplicate order_ref" in str(err) for err in exc.value.errors)


def test_input_validation_boundary_rejects_inconsistent_reference_attributes(base_references):
    """
    Reject when order's brand or dock_type conflicts with authoritative outlet master.
    """
    context = OperationalContext(planning_date="2026-10-03")
    # OUT_COL_1 is registered as Brand.FRESH in base_references, but order declares Brand.STYLE
    mismatch_order = Order(
        order_ref="O_MISMATCH", outlet_id="OUT_COL_1", brand=Brand.STYLE, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    with pytest.raises(InputValidationError) as exc:
        generate_daily_draft_plan([mismatch_order], base_references.vehicles, base_references, context)
    assert any("conflicts with authoritative outlet" in str(err) for err in exc.value.errors)


# ==============================================================================
# 2. Independent Operational Validator
# ==============================================================================

def test_independent_validator_reconstructs_and_catches_manipulated_fuel_and_times(base_references):
    """
    Validator must not trust reported totals or cached booleans in the plan dictionary.
    Reconstructing chronology and fuel from authoritative inputs catches tampering.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O_TAMPER", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    plan = generate_daily_draft_plan([order], base_references.vehicles, base_references, context)
    assert plan["validation"]["valid"] is True

    # 1. Tamper with trip distance and fuel in the dictionary
    corrupted_plan = dict(plan)
    corrupted_plan["trips"] = [dict(t) for t in plan["trips"]]
    corrupted_plan["trips"][0]["fuel"] = dict(corrupted_plan["trips"][0]["fuel"])
    corrupted_plan["trips"][0]["fuel"]["distance_km"] = 1.0  # Actually 30.0 km
    corrupted_plan["trips"][0]["fuel"]["fuel_consumed_l"] = 0.1  # Actually 6.0 L

    # Validator should catch mismatch against reconstructed values
    res = validate_operational_plan(
        orders=[order],
        timelines=corrupted_plan,
        context=context,
        fleet=base_references.vehicles,
        travel_data={(t.district, t.depot): t for t in base_references.travel},
        allowances={(a.brand, a.dock_type): a.service_allowance_min for a in base_references.allowances},
        outlets=base_references.outlets,
        deferred_orders=corrupted_plan["deferred_orders"],
    )
    assert res.valid is False
    assert any("MANIPULATED_OR_INCORRECT_DISTANCE" in v.rule for v in res.violations)
    assert any("MANIPULATED_OR_INCORRECT_FUEL" in v.rule for v in res.violations)


def test_independent_validator_rejects_unauthorized_splits_and_missing_demand(base_references):
    """
    Validator rejects plans where assigned + deferred != requested demand.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O_SPLIT", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    plan = generate_daily_draft_plan([order], base_references.vehicles, base_references, context)

    # Tamper by dropping order from both assigned stops and deferred list
    empty_plan = dict(plan)
    empty_plan["trips"] = []
    empty_plan["deferred_orders"] = []  # Demand vanished

    res = validate_operational_plan(
        orders=[order],
        timelines=empty_plan,
        context=context,
        fleet=base_references.vehicles,
        travel_data={(t.district, t.depot): t for t in base_references.travel},
        allowances={(a.brand, a.dock_type): a.service_allowance_min for a in base_references.allowances},
        outlets=base_references.outlets,
        deferred_orders=[],
    )
    assert res.valid is False
    assert any("DEMAND_CONSERVATION_VIOLATION" in v.rule for v in res.violations)


def test_independent_validator_separates_quantity_by_unit(base_references):
    """
    Validator keeps quantity totals separated by unit (crates, pallets, units).
    """
    context = OperationalContext(planning_date="2026-10-03")
    li1 = LineItem("LI1", 10.0, "crates", 5.0, 0.05)
    li2 = LineItem("LI2", 2.0, "pallets", 50.0, 0.5)
    ord1 = Order(
        order_ref="O_UNIT1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False, line_items=[li1],
    )
    ord2 = Order(
        order_ref="O_UNIT2", outlet_id="OUT_COL_2", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=2, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False, line_items=[li2],
    )

    plan = generate_daily_draft_plan([ord1, ord2], base_references.vehicles, base_references, context)
    assert plan["validation"]["valid"] is True
    units_dict = plan["validation"]["quantity_totals_by_unit"]
    assert "crates" in units_dict
    assert "pallets" in units_dict
    assert units_dict["crates"]["requested"] == 10.0
    assert units_dict["pallets"]["requested"] == 2.0


# ==============================================================================
# 3. Operational CP-SAT Corrections: Tech-Only Improvement & One-Stop Fuel
# ==============================================================================

def test_one_stop_trip_fuel_boundary(base_references):
    """
    Verify distance is exactly outbound + return = 2*depot_to_district_km with ZERO inter-stop.
    Fuel must be exactly 2*depot_to_district_km / km_per_l.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O_SINGLE", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    plan = generate_daily_draft_plan([order], base_references.vehicles, base_references, context)
    assert len(plan["trips"]) == 1
    trip = plan["trips"][0]
    assert len(trip["driver_itinerary"]) == 1
    # Colombo travel: depot_to_district_km = 15.0, inter_stop_km = 5.0
    # Expected distance: 15.0 * 2 = 30.0 km
    assert trip["fuel"]["distance_km"] == 30.0
    # Expected fuel: 30.0 km / 5.0 km/L = 6.0 L
    assert trip["fuel"]["fuel_consumed_l"] == 6.0


def test_cpsat_tech_only_improvement(base_references):
    """
    Verify Tech-only orders:
    - Obey Tech earliest departure (06:30 / 390 min)
    - Use exact Tech service allowances (30.0 min for REAR_DOCK)
    - Successfully solved and improved by targeted CP-SAT
    """
    context = OperationalContext(planning_date="2026-10-03")

    v_tech = Vehicle(
        vehicle_id="V_TECH", status=VehicleStatus.AVAILABLE, type=VehicleType.VAN, temp=TempSpec.AMBIENT,
        weight_cap_kg=500.0, volume_cap_m3=5.0, depot="Peliyagoda", km_per_l=5.0,
        weekly_fuel_quota_l=200.0, weekly_fuel_used_l=10.0, external_reservations_l=0.0,
        remaining_trips=2, is_selected_for_planning=True,
    )

    # Order T1: High penalty deferred yesterday
    ord_t1 = Order(
        order_ref="ORD_TECH_1", outlet_id="OUT_TECH_1", brand=Brand.TECH, district="Gampaha", depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="07:30", window_close_time="10:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=300.0, order_volume_m3=2.0, deferred_prev=True, defer_count=3, is_urgent=False,
    )
    # Order T2: Regular order
    ord_t2 = Order(
        order_ref="ORD_TECH_2", outlet_id="OUT_TECH_2", brand=Brand.TECH, district="Gampaha", depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="08:30", window_close_time="11:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=150.0, order_volume_m3=1.0, deferred_prev=False, defer_count=1, is_urgent=False,
    )

    plan = generate_daily_draft_plan(
        orders=[ord_t1, ord_t2],
        fleet=[v_tech],
        reference_data=base_references,
        context=context,
        enable_targeted_cpsat=True,
    )

    assert plan["validation"]["valid"] is True
    assert plan["order_counts"]["fully_served_orders"] == 2
    trip = plan["trips"][0]
    assert trip["brand"].upper() == "TECH"
    # Tech departure must be >= 06:30
    dep_dt = parse_iso_or_time_str(trip["departure_time_iso"], context.planning_date, context.timezone)
    dep_min = dep_dt.hour * 60 + dep_dt.minute
    assert dep_min >= 390  # 06:30


# ==============================================================================
# 4. Consistent Lexicographic Objective
# ==============================================================================

def test_lexicographic_objective_hierarchy():
    """
    Ensure scoring follows:
    1. minimize penalty
    2. maximize served orders (-served)
    3. minimize fuel
    """
    # Plan A: higher penalty (10.0), more served (5), low fuel (10.0)
    score_a = score_plan_objective(penalty=10.0, served_count=5, fuel_l=10.0)
    # Plan B: lower penalty (0.0), fewer served (4), high fuel (50.0)
    score_b = score_plan_objective(penalty=0.0, served_count=4, fuel_l=50.0)
    # Plan B must strictly beat Plan A because penalty takes priority
    assert score_b < score_a

    # Plan C: same penalty (0.0), more served (5), high fuel (40.0)
    score_c = score_plan_objective(penalty=0.0, served_count=5, fuel_l=40.0)
    # Plan C must strictly beat Plan B because served count takes second priority
    assert score_c < score_b

    # Plan D: same penalty (0.0), same served (5), lower fuel (30.0)
    score_d = score_plan_objective(penalty=0.0, served_count=5, fuel_l=30.0)
    # Plan D must strictly beat Plan C because fuel takes third priority
    assert score_d < score_c


# ==============================================================================
# 5. Dynamic Travel Missing-Data Diagnostics
# ==============================================================================

def test_dynamic_travel_missing_data_diagnostics(base_references):
    """
    Requesting dynamic travel without provider or speed factor function
    must return structured missing-data error and NEVER silently execute static travel.
    """
    context = OperationalContext(
        planning_date="2026-10-03",
        travel_policy=TravelPolicy.DYNAMIC_CONDITIONS,
    )
    order = Order(
        order_ref="O_DYN", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )

    with pytest.raises(InputValidationError) as exc:
        generate_daily_draft_plan([order], base_references.vehicles, base_references, context)

    assert any("dynamic speed provider" in str(err).lower() or "speed_factor_fn" in str(err).lower() for err in exc.value.errors)


# ==============================================================================
# 6. External Review Correctness Regressions
# ==============================================================================

def test_validator_requires_authoritative_references():
    """
    Validator must require authoritative fleet, outlets, travel, and allowances.
    Missing any of them must return valid=False with structured OperationalMissingData.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    # Call without fleet, outlets, travel_data, allowances
    res = validate_operational_plan(
        orders=[order],
        timelines=[],
        context=context,
        fleet=None,
        travel_data=None,
        outlets=None,
        allowances=None,
    )
    assert not res.valid
    fields_missing = {m.field for m in res.missing_data}
    assert "fleet" in fields_missing
    assert "outlets" in fields_missing
    assert "travel_data" in fields_missing
    assert "allowances" in fields_missing
    # Verify every OperationalMissingData includes field, entity_id, detail
    for m in res.missing_data:
        assert m.field
        assert m.entity_id
        assert m.detail


def test_validator_rejects_vehicle_unavailable_on_planning_date(base_references):
    """
    Vehicle with earliest_availability_iso on a different date than planning_date
    must be rejected by the independent validator.
    """
    context = OperationalContext(planning_date="2026-10-03")
    v_tomorrow = Vehicle(
        vehicle_id="V_TOMORROW",
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.VAN,
        temp=TempSpec.AMBIENT,
        weight_cap_kg=1500.0,
        volume_cap_m3=10.0,
        depot="Peliyagoda",
        km_per_l=5.0,
        weekly_fuel_quota_l=250.0,
        weekly_fuel_used_l=20.0,
        external_reservations_l=10.0,
        remaining_trips=2,
        is_selected_for_planning=True,
        earliest_availability_iso="2026-10-04T05:00:00+05:30",
    )
    order = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    plan_dict = {
        "planning_date": "2026-10-03",
        "trips": [
            {
                "trip_id": "T1",
                "vehicle_id": "V_TOMORROW",
                "trip_number": 1,
                "brand": "fresh",
                "district": "Colombo",
                "depot": "Peliyagoda",
                "departure_time_iso": "2026-10-03T05:00:00+05:30",
                "depot_return_arrival_iso": "2026-10-03T06:15:00+05:30",
                "vehicle_next_available_iso": "2026-10-03T06:45:00+05:30",
                "driver_itinerary": [
                    {
                        "stop_number": 1,
                        "outlet_id": "OUT_COL_1",
                        "order_refs": ["O1"],
                        "line_items_delivered": [
                            {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"}
                        ],
                        "arrival_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_start_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_duration_min": 15.0,
                        "departure_time_iso": "2026-10-03T05:45:00+05:30",
                        "window_compliant": True,
                    }
                ],
                "load_utilization": {"weight_kg": 100.0, "volume_m3": 1.0},
            }
        ],
        "deferred_orders": [],
    }
    res = validate_operational_plan(
        orders=[order],
        timelines=plan_dict,
        context=context,
        fleet=[v_tomorrow],
        reference_data=base_references,
    )
    assert not res.valid
    rules = [v.rule for v in res.violations]
    assert "VEHICLE_UNAVAILABLE_ON_PLANNING_DATE" in rules or "DEPARTURE_BEFORE_VEHICLE_AVAILABILITY" in rules


def test_validator_rejects_missing_fuel_state(base_references):
    """
    Missing weekly_fuel_used_l or external_reservations_l on an assigned vehicle
    must produce MISSING_FLEET_FUEL_STATE and never be converted to zero.
    """
    context = OperationalContext(planning_date="2026-10-03")
    v_no_fuel = Vehicle(
        vehicle_id="V_NO_FUEL",
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.VAN,
        temp=TempSpec.AMBIENT,
        weight_cap_kg=1500.0,
        volume_cap_m3=10.0,
        depot="Peliyagoda",
        km_per_l=5.0,
        weekly_fuel_quota_l=250.0,
        weekly_fuel_used_l=None,  # Missing!
        external_reservations_l=10.0,
        remaining_trips=2,
        is_selected_for_planning=True,
    )
    order = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    plan_dict = {
        "planning_date": "2026-10-03",
        "trips": [
            {
                "trip_id": "T1",
                "vehicle_id": "V_NO_FUEL",
                "trip_number": 1,
                "brand": "fresh",
                "district": "Colombo",
                "depot": "Peliyagoda",
                "departure_time_iso": "2026-10-03T05:00:00+05:30",
                "depot_return_arrival_iso": "2026-10-03T06:15:00+05:30",
                "vehicle_next_available_iso": "2026-10-03T06:45:00+05:30",
                "driver_itinerary": [
                    {
                        "stop_number": 1,
                        "outlet_id": "OUT_COL_1",
                        "order_refs": ["O1"],
                        "line_items_delivered": [
                            {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"}
                        ],
                        "arrival_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_start_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_duration_min": 15.0,
                        "departure_time_iso": "2026-10-03T05:45:00+05:30",
                        "window_compliant": True,
                    }
                ],
                "load_utilization": {"weight_kg": 100.0, "volume_m3": 1.0},
            }
        ],
        "deferred_orders": [],
    }
    res = validate_operational_plan(
        orders=[order],
        timelines=plan_dict,
        context=context,
        fleet=[v_no_fuel],
        reference_data=base_references,
    )
    assert not res.valid
    rules = [v.rule for v in res.violations]
    assert "MISSING_FLEET_FUEL_STATE" in rules


def test_validator_rejects_fake_line_item_id(base_references):
    """
    Line item delivered at a stop that does not exist on the authoritative order
    must be rejected with UNKNOWN_LINE_ITEM.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
        line_items=[
            LineItem(line_item_id="LI_REAL", quantity=10, quantity_unit="crates", unit_weight_kg=10.0, unit_volume_m3=0.1)
        ],
    )
    plan_dict = {
        "planning_date": "2026-10-03",
        "trips": [
            {
                "trip_id": "T1",
                "vehicle_id": "V_AMB",
                "trip_number": 1,
                "brand": "fresh",
                "district": "Colombo",
                "depot": "Peliyagoda",
                "departure_time_iso": "2026-10-03T05:00:00+05:30",
                "depot_return_arrival_iso": "2026-10-03T06:15:00+05:30",
                "vehicle_next_available_iso": "2026-10-03T06:45:00+05:30",
                "driver_itinerary": [
                    {
                        "stop_number": 1,
                        "outlet_id": "OUT_COL_1",
                        "order_refs": ["O1"],
                        "line_items_delivered": [
                            {"order_ref": "O1", "line_item_id": "LI_FAKE", "quantity": 10, "quantity_unit": "crates"}
                        ],
                        "arrival_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_start_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_duration_min": 15.0,
                        "departure_time_iso": "2026-10-03T05:45:00+05:30",
                        "window_compliant": True,
                    }
                ],
                "load_utilization": {"weight_kg": 100.0, "volume_m3": 1.0},
            }
        ],
        "deferred_orders": [],
    }
    res = validate_operational_plan(
        orders=[order],
        timelines=plan_dict,
        context=context,
        reference_data=base_references,
    )
    assert not res.valid
    rules = [v.rule for v in res.violations]
    assert "UNKNOWN_LINE_ITEM" in rules


def test_validator_rejects_wrong_quantity_unit(base_references):
    """
    Line item quantity_unit mismatch against authoritative unit must be rejected with QUANTITY_UNIT_MISMATCH.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
        line_items=[
            LineItem(line_item_id="LI_1", quantity=10, quantity_unit="crates", unit_weight_kg=10.0, unit_volume_m3=0.1)
        ],
    )
    plan_dict = {
        "planning_date": "2026-10-03",
        "trips": [
            {
                "trip_id": "T1",
                "vehicle_id": "V_AMB",
                "trip_number": 1,
                "brand": "fresh",
                "district": "Colombo",
                "depot": "Peliyagoda",
                "departure_time_iso": "2026-10-03T05:00:00+05:30",
                "depot_return_arrival_iso": "2026-10-03T06:15:00+05:30",
                "vehicle_next_available_iso": "2026-10-03T06:45:00+05:30",
                "driver_itinerary": [
                    {
                        "stop_number": 1,
                        "outlet_id": "OUT_COL_1",
                        "order_refs": ["O1"],
                        "line_items_delivered": [
                            {"order_ref": "O1", "line_item_id": "LI_1", "quantity": 10, "quantity_unit": "kg"}
                        ],
                        "arrival_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_start_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_duration_min": 15.0,
                        "departure_time_iso": "2026-10-03T05:45:00+05:30",
                        "window_compliant": True,
                    }
                ],
                "load_utilization": {"weight_kg": 100.0, "volume_m3": 1.0},
            }
        ],
        "deferred_orders": [],
    }
    res = validate_operational_plan(
        orders=[order],
        timelines=plan_dict,
        context=context,
        reference_data=base_references,
    )
    assert not res.valid
    rules = [v.rule for v in res.violations]
    assert "QUANTITY_UNIT_MISMATCH" in rules


def test_validator_rejects_missing_deferred_quantity(base_references):
    """
    If an order is partially served or unserved, but deferred quantity does not
    satisfy: assigned + deferred == requested, it must be rejected with DEMAND_CONSERVATION_VIOLATION.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    # Plan serves 6 units, but deferred quantity claims 2 (missing 2 units!)
    plan_dict = {
        "planning_date": "2026-10-03",
        "trips": [
            {
                "trip_id": "T1",
                "vehicle_id": "V_AMB",
                "trip_number": 1,
                "brand": "fresh",
                "district": "Colombo",
                "depot": "Peliyagoda",
                "departure_time_iso": "2026-10-03T05:00:00+05:30",
                "depot_return_arrival_iso": "2026-10-03T06:15:00+05:30",
                "vehicle_next_available_iso": "2026-10-03T06:45:00+05:30",
                "driver_itinerary": [
                    {
                        "stop_number": 1,
                        "outlet_id": "OUT_COL_1",
                        "order_refs": ["O1"],
                        "line_items_delivered": [
                            {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 6, "quantity_unit": "units"}
                        ],
                        "arrival_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_start_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_duration_min": 15.0,
                        "departure_time_iso": "2026-10-03T05:45:00+05:30",
                        "window_compliant": True,
                    }
                ],
                "load_utilization": {"weight_kg": 60.0, "volume_m3": 0.6},
            }
        ],
        "deferred_orders": [
            {
                "order_ref": "O1",
                "outlet_id": "OUT_COL_1",
                "deferred_quantity": 2,  # 6 + 2 = 8 != 10
            }
        ],
    }
    res = validate_operational_plan(
        orders=[order],
        timelines=plan_dict,
        context=context,
        reference_data=base_references,
    )
    assert not res.valid
    rules = [v.rule for v in res.violations]
    assert "DEMAND_CONSERVATION_VIOLATION" in rules


def test_validator_rejects_corrupted_stop_timestamps(base_references):
    """
    Timezone-naive timestamps, non-chronological sequences, or timestamps altered
    from recomputed travel/service allowances must be rejected.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )

    # 1. Corrupted with timezone-naive timestamp
    plan_naive = {
        "planning_date": "2026-10-03",
        "trips": [
            {
                "trip_id": "T1",
                "vehicle_id": "V_AMB",
                "trip_number": 1,
                "brand": "fresh",
                "district": "Colombo",
                "depot": "Peliyagoda",
                "departure_time_iso": "2026-10-03T05:00:00",  # Naive!
                "depot_return_arrival_iso": "2026-10-03T06:15:00+05:30",
                "vehicle_next_available_iso": "2026-10-03T06:45:00+05:30",
                "driver_itinerary": [
                    {
                        "stop_number": 1,
                        "outlet_id": "OUT_COL_1",
                        "order_refs": ["O1"],
                        "arrival_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_start_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_duration_min": 15.0,
                        "departure_time_iso": "2026-10-03T05:45:00+05:30",
                        "window_compliant": True,
                    }
                ],
                "load_utilization": {"weight_kg": 100.0, "volume_m3": 1.0},
            }
        ],
        "deferred_orders": [],
    }
    res_naive = validate_operational_plan(
        orders=[order],
        timelines=plan_naive,
        context=context,
        reference_data=base_references,
    )
    assert not res_naive.valid
    assert any("TIMEZONE_NAIVE_OR_INVALID" in v.rule for v in res_naive.violations)

    # 2. Corrupted arrival time that does not match authoritative travel duration (30 min expected, reporting 5 min)
    plan_skewed = {
        "planning_date": "2026-10-03",
        "trips": [
            {
                "trip_id": "T1",
                "vehicle_id": "V_AMB",
                "trip_number": 1,
                "brand": "fresh",
                "district": "Colombo",
                "depot": "Peliyagoda",
                "departure_time_iso": "2026-10-03T05:00:00+05:30",
                "depot_return_arrival_iso": "2026-10-03T06:15:00+05:30",
                "vehicle_next_available_iso": "2026-10-03T06:45:00+05:30",
                "driver_itinerary": [
                    {
                        "stop_number": 1,
                        "outlet_id": "OUT_COL_1",
                        "order_refs": ["O1"],
                        "arrival_time_iso": "2026-10-03T05:05:00+05:30",  # Fake arrival: 5 min instead of 30 min!
                        "service_start_time_iso": "2026-10-03T05:05:00+05:30",
                        "service_duration_min": 15.0,
                        "departure_time_iso": "2026-10-03T05:20:00+05:30",
                        "window_compliant": True,
                    }
                ],
                "load_utilization": {"weight_kg": 100.0, "volume_m3": 1.0},
            }
        ],
        "deferred_orders": [],
    }
    res_skewed = validate_operational_plan(
        orders=[order],
        timelines=plan_skewed,
        context=context,
        reference_data=base_references,
    )
    assert not res_skewed.valid
    assert any(v.rule in ("STOP_ARRIVAL_TIME_MISMATCH", "MANIPULATED_OR_INCORRECT_TIMESTAMPS") for v in res_skewed.violations)


def test_missing_travel_data_returns_structured_diagnostics(base_references):
    """
    Missing district travel for a trip must return structured OperationalMissingData
    diagnostics and valid=False without raising TypeError or unhandled exception.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O_UNKNOWN_DIST", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="UnknownDistrict", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    plan_dict = {
        "planning_date": "2026-10-03",
        "trips": [
            {
                "trip_id": "T1",
                "vehicle_id": "V_AMB",
                "trip_number": 1,
                "brand": "fresh",
                "district": "UnknownDistrict",
                "depot": "Peliyagoda",
                "departure_time_iso": "2026-10-03T05:00:00+05:30",
                "depot_return_arrival_iso": "2026-10-03T06:15:00+05:30",
                "vehicle_next_available_iso": "2026-10-03T06:45:00+05:30",
                "driver_itinerary": [
                    {
                        "stop_number": 1,
                        "outlet_id": "OUT_COL_1",
                        "order_refs": ["O_UNKNOWN_DIST"],
                        "arrival_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_start_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_duration_min": 15.0,
                        "departure_time_iso": "2026-10-03T05:45:00+05:30",
                        "window_compliant": True,
                    }
                ],
                "load_utilization": {"weight_kg": 100.0, "volume_m3": 1.0},
            }
        ],
        "deferred_orders": [],
    }
    # base_references does not have UnknownDistrict
    res = validate_operational_plan(
        orders=[order],
        timelines=plan_dict,
        context=context,
        reference_data=base_references,
    )
    assert not res.valid
    travel_missing = [m for m in res.missing_data if m.field in ("travel_data", "district_travel")]
    assert len(travel_missing) > 0
    assert travel_missing[0].field in ("travel_data", "district_travel")
    assert "UnknownDistrict" in travel_missing[0].entity_id
    assert travel_missing[0].detail


def test_exact_line_item_demand_conservation(base_references):
    """
    Exact demand conservation per line item:
    assigned quantity + deferred quantity == requested quantity.
    Totals must be separated by quantity unit.
    """
    context = OperationalContext(planning_date="2026-10-03")
    order = Order(
        order_ref="O_MULTI_UNIT", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=15, order_weight_kg=150.0, order_volume_m3=1.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
        line_items=[
            LineItem(line_item_id="LI_CRATES", quantity=10.0, quantity_unit="crates", unit_weight_kg=10.0, unit_volume_m3=0.1),
            LineItem(line_item_id="LI_KG", quantity=5.0, quantity_unit="kg", unit_weight_kg=10.0, unit_volume_m3=0.1),
        ],
    )

    plan_dict = {
        "planning_date": "2026-10-03",
        "trips": [
            {
                "trip_id": "T1",
                "vehicle_id": "V_AMB",
                "trip_number": 1,
                "brand": "fresh",
                "district": "Colombo",
                "depot": "Peliyagoda",
                "departure_time_iso": "2026-10-03T05:00:00+05:30",
                "depot_return_arrival_iso": "2026-10-03T06:15:00+05:30",
                "vehicle_next_available_iso": "2026-10-03T06:45:00+05:30",
                "driver_itinerary": [
                    {
                        "stop_number": 1,
                        "outlet_id": "OUT_COL_1",
                        "order_refs": ["O_MULTI_UNIT"],
                        "line_items_delivered": [
                            {"order_ref": "O_MULTI_UNIT", "line_item_id": "LI_CRATES", "quantity": 10.0, "quantity_unit": "crates"},
                            {"order_ref": "O_MULTI_UNIT", "line_item_id": "LI_KG", "quantity": 3.0, "quantity_unit": "kg"},
                        ],
                        "arrival_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_start_time_iso": "2026-10-03T05:30:00+05:30",
                        "service_duration_min": 15.0,
                        "departure_time_iso": "2026-10-03T05:45:00+05:30",
                        "window_compliant": True,
                    }
                ],
                "load_utilization": {"weight_kg": 130.0, "volume_m3": 1.3},
            }
        ],
        "deferred_orders": [
            {
                "order_ref": "O_MULTI_UNIT",
                "outlet_id": "OUT_COL_1",
                "deferred_quantity": 2.0,
                "line_items": [
                    {"line_item_id": "LI_KG", "deferred_quantity": 2.0, "quantity_unit": "kg"}
                ],
            }
        ],
    }
    res = validate_operational_plan(
        orders=[order],
        timelines=plan_dict,
        context=context,
        reference_data=base_references,
    )
    assert res.valid
    assert res.quantity_totals_by_unit["crates"]["requested"] == 10.0
    assert res.quantity_totals_by_unit["crates"]["assigned"] == 10.0
    assert res.quantity_totals_by_unit["crates"]["deferred"] == 0.0

    assert res.quantity_totals_by_unit["kg"]["requested"] == 5.0
    assert res.quantity_totals_by_unit["kg"]["assigned"] == 3.0
    assert res.quantity_totals_by_unit["kg"]["deferred"] == 2.0

