"""
Regression tests for hardened plan validator and input validation gateway.
"""
import math
import pytest

from waypoint_optimizer.domain import (
    DistrictTravel,
    Order,
    OrderAssignment,
    DeferredOrder,
    ServiceAllowance,
    TripResult,
    Vehicle,
)
from waypoint_optimizer.enums import (
    Brand,
    DockType,
    ParkingConstraint,
    TempRequirement,
    TempSpec,
    VehicleStatus,
    VehicleType,
    DeferralReason,
)
from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.validator import validate
from waypoint_optimizer.input_validation import validate_inputs, InputValidationError


@pytest.fixture
def base_order():
    return Order(
        order_ref="O1",
        outlet_id="OUT1",
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK,
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=5,
        order_weight_kg=100.0,
        order_volume_m3=1.0,
        deferred_prev=False,
        defer_count=0,
        is_urgent=False,
    )


@pytest.fixture
def base_vehicle():
    return Vehicle(
        vehicle_id="V1",
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.TRUCK,
        temp=TempSpec.AMBIENT,
        weight_cap_kg=1000.0,
        volume_cap_m3=10.0,
        depot="Peliyagoda",
    )


@pytest.fixture
def travel_and_allowance():
    dt = DistrictTravel(
        district="Colombo",
        depot="Peliyagoda",
        road_class="A",
        free_flow_kmh=40.0,
        depot_to_district_km=20.0,
        depot_to_district_freeflow_min=24.0,
        inter_stop_km=2.0,
        inter_stop_freeflow_min=8.0,
    )
    t_idx = {("Colombo", "Peliyagoda"): dt}
    a_idx = {(Brand.FRESH, "rear_dock"): 15.0}
    return t_idx, a_idx, dt, ServiceAllowance(Brand.FRESH, DockType.REAR_DOCK, 15.0)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Validator Hardening Regression Tests
# ══════════════════════════════════════════════════════════════════════════════

def test_validator_rejects_assignment_trip_mismatch(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    # Assignment says Trip 2, but TripResult is Trip 1
    assignment = OrderAssignment("O1", "V1", 2)
    trip = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O1",), ("O1",), 100.0, 1.0, 39.0, 900.0, 9.0)
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [assignment], [], [trip])
    assert not res.valid
    rules = [e.rule for e in res.errors]
    assert "ASSIGNMENT_NOT_IN_TRIP" in rules or "TRIP_ORDER_NOT_SERVED" in rules


def test_validator_rejects_unknown_vehicle_in_assignment(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    assignment = OrderAssignment("O1", "V_GHOST", 1)
    trip = TripResult("V_GHOST", 1, Brand.FRESH, "Colombo", ("O1",), ("O1",), 100.0, 1.0, 39.0, 900.0, 9.0)
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [assignment], [], [trip])
    assert not res.valid
    assert any(e.rule == "VEHICLE_NOT_FOUND" for e in res.errors)


def test_validator_rejects_duplicate_trip_keys(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    assignment = OrderAssignment("O1", "V1", 1)
    trip1 = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O1",), ("O1",), 100.0, 1.0, 39.0, 900.0, 9.0)
    trip2 = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O1",), ("O1",), 100.0, 1.0, 39.0, 900.0, 9.0)
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [assignment], [], [trip1, trip2])
    assert not res.valid
    assert any(e.rule == "DUPLICATE_TRIP_KEY" for e in res.errors)


def test_validator_rejects_order_in_multiple_trips(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    assignment = OrderAssignment("O1", "V1", 1)
    trip1 = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O1",), ("O1",), 100.0, 1.0, 39.0, 900.0, 9.0)
    trip2 = TripResult("V1", 2, Brand.FRESH, "Colombo", ("O1",), ("O1",), 100.0, 1.0, 39.0, 900.0, 9.0)
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [assignment], [], [trip1, trip2])
    assert not res.valid
    assert any(e.rule == "ORDER_IN_MULTIPLE_TRIPS" for e in res.errors)


def test_validator_rejects_duplicate_deferred_records(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    d1 = DeferredOrder("O1", DeferralReason.OTHER_CAPACITY_LIMIT, "reason 1")
    d2 = DeferredOrder("O1", DeferralReason.OTHER_CAPACITY_LIMIT, "reason 2")
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [], [d1, d2], [])
    assert not res.valid
    assert any(e.rule == "DUPLICATE_DEFERRED" for e in res.errors)


def test_validator_rejects_trip_metadata_mismatch(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    assignment = OrderAssignment("O1", "V1", 1)
    # TripResult reports Brand.STYLE instead of Brand.FRESH
    trip = TripResult("V1", 1, Brand.STYLE, "Colombo", ("O1",), ("O1",), 100.0, 1.0, 39.0, 900.0, 9.0)
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [assignment], [], [trip])
    assert not res.valid
    assert any(e.rule == "TRIP_METADATA_MISMATCH" for e in res.errors)


def test_validator_rejects_nan_and_infinite_duration(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    assignment = OrderAssignment("O1", "V1", 1)
    trip_nan = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O1",), ("O1",), 100.0, 1.0, float("nan"), 900.0, 9.0)
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [assignment], [], [trip_nan])
    assert not res.valid
    rules = [e.rule for e in res.errors]
    assert "NONFINITE_METRIC" in rules or "TRIP_TIME_MISMATCH" in rules


def test_validator_rejects_corrupted_stop_sequence(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    assignment = OrderAssignment("O1", "V1", 1)
    trip = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O1",), ("GHOST",), 100.0, 1.0, 39.0, 900.0, 9.0)
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [assignment], [], [trip])
    assert not res.valid
    assert any(e.rule == "INVALID_STOP_SEQUENCE" for e in res.errors)


def test_validator_rejects_mismatched_capacity_totals(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    assignment = OrderAssignment("O1", "V1", 1)
    # total_weight_kg claims 500.0, but base_order is 100.0
    trip = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O1",), ("O1",), 500.0, 1.0, 39.0, 900.0, 9.0)
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [assignment], [], [trip])
    assert not res.valid
    assert any(e.rule == "WEIGHT_REPORT_MISMATCH" for e in res.errors)


def test_validator_accepts_valid_boundary_plan(base_order, base_vehicle, travel_and_allowance):
    t_idx, a_idx, _, _ = travel_and_allowance
    assignment = OrderAssignment("O1", "V1", 1)
    # Trip time: 24 (outbound) + 0 (inter-stop for 1 order) + 15 (allowance) = 39.0
    trip = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O1",), ("O1",), 100.0, 1.0, 39.0, 900.0, 9.0)
    res = validate([base_order], {"V1": base_vehicle}, t_idx, a_idx, [assignment], [], [trip])
    assert res.valid
    assert len(res.errors) == 0


# ══════════════════════════════════════════════════════════════════════════════
# 2. Input Validation Gateway Tests
# ══════════════════════════════════════════════════════════════════════════════

def test_input_validation_duplicate_orders(base_order, base_vehicle, travel_and_allowance):
    _, _, dt, sa = travel_and_allowance
    o2 = Order(
        order_ref="O1",  # duplicate ref
        outlet_id="OUT2",
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK,
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=1,
        order_weight_kg=10.0,
        order_volume_m3=0.1,
        deferred_prev=False,
        defer_count=0,
        is_urgent=False,
    )
    with pytest.raises(InputValidationError) as exc:
        validate_inputs([base_order, o2], [base_vehicle], [dt], [sa])
    assert "Duplicate order_ref" in str(exc.value)


def test_input_validation_negative_or_nan(base_order, base_vehicle, travel_and_allowance):
    _, _, dt, sa = travel_and_allowance
    bad_order = Order(
        order_ref="O_BAD",
        outlet_id="OUT1",
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK,
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=1,
        order_weight_kg=-50.0,  # negative weight!
        order_volume_m3=float("nan"),  # NaN volume!
        deferred_prev=False,
        defer_count=0,
        is_urgent=False,
    )
    with pytest.raises(InputValidationError) as exc:
        validate_inputs([bad_order], [base_vehicle], [dt], [sa])
    assert "order_weight_kg" in str(exc.value)
    assert "order_volume_m3" in str(exc.value)


def test_input_validation_missing_travel_or_allowance(base_order, base_vehicle, travel_and_allowance):
    _, _, dt, sa = travel_and_allowance
    # Order for district="Kandy" where no travel record exists
    unmapped_order = Order(
        order_ref="O_UNMAPPED",
        outlet_id="OUT1",
        brand=Brand.FRESH,
        district="Kandy",  # no travel entry for (Kandy, Peliyagoda)
        depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK,
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=1,
        order_weight_kg=10.0,
        order_volume_m3=0.1,
        deferred_prev=False,
        defer_count=0,
        is_urgent=False,
    )
    with pytest.raises(InputValidationError) as exc:
        validate_inputs([unmapped_order], [base_vehicle], [dt], [sa])
    assert "requires district_travel" in str(exc.value)


def test_input_validation_zero_values_allowed_when_valid(base_order, base_vehicle, travel_and_allowance):
    _, _, dt, sa = travel_and_allowance
    # Zero units or zero days since last served are legitimate
    zero_order = Order(
        order_ref="O_ZERO",
        outlet_id="OUT1",
        brand=Brand.FRESH,
        district="Colombo",
        depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK,
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=0,  # zero units
        order_weight_kg=0.0,  # zero weight
        order_volume_m3=0.0,  # zero volume
        deferred_prev=False,
        defer_count=0,  # zero defer count
        is_urgent=False,
    )
    # Should NOT raise
    validate_inputs([zero_order], [base_vehicle], [dt], [sa])
