"""
Tests for the Validator module.
Every hard constraint must be independently verified.

These tests exercise the Validator directly, without going through the optimizer.
They construct both valid and deliberately invalid plans to check detection.
"""
import pytest
from waypoint_optimizer.domain import (
    DistrictTravel, DeferredOrder, Order, OrderAssignment,
    ServiceAllowance, TripResult, Vehicle,
)
from waypoint_optimizer.enums import (
    Brand, DeferralReason, DockType, ParkingConstraint,
    TempRequirement, TempSpec, VehicleStatus, VehicleType,
)
from waypoint_optimizer.trip_math import build_allowance_index, build_travel_index
from waypoint_optimizer.validator import validate
from waypoint_optimizer.config import OptimizerConfig


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

DEPOT = "Peliyagoda"

@pytest.fixture
def travel() -> list[DistrictTravel]:
    return [
        DistrictTravel(
            district="Colombo", depot=DEPOT, road_class="A",
            free_flow_kmh=50.0, depot_to_district_km=12.0,
            depot_to_district_freeflow_min=24.0,
            inter_stop_km=3.0, inter_stop_freeflow_min=8.0,
        ),
        DistrictTravel(
            district="Gampaha", depot=DEPOT, road_class="A",
            free_flow_kmh=60.0, depot_to_district_km=37.0,
            depot_to_district_freeflow_min=37.0,
            inter_stop_km=4.5, inter_stop_freeflow_min=9.0,
        ),
    ]


@pytest.fixture
def allowances() -> list[ServiceAllowance]:
    return [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0),
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.STREET, service_allowance_min=16.0),
        ServiceAllowance(brand=Brand.STYLE, dock_type=DockType.REAR_DOCK, service_allowance_min=20.0),
        ServiceAllowance(brand=Brand.TECH, dock_type=DockType.REAR_DOCK, service_allowance_min=25.0),
    ]


@pytest.fixture
def t_idx(travel):
    return build_travel_index(travel)


@pytest.fixture
def a_idx(allowances):
    return build_allowance_index(allowances)


def mk_order(ref, brand=Brand.FRESH, district="Colombo", depot=DEPOT,
             temp=TempRequirement.AMBIENT, parking=ParkingConstraint.NORMAL,
             weight=100.0, volume=1.0, dock=DockType.REAR_DOCK):
    return Order(
        order_ref=ref, outlet_id="OUT1",
        brand=brand, district=district, depot=depot,
        dock_type=dock, parking_constraint=parking,
        mall_window=None, window_open_time=None, window_close_time=None,
        temp_requirement=temp, order_units=5,
        order_weight_kg=weight, order_volume_m3=volume,
        deferred_prev=False, defer_count=0, is_urgent=False,
    )


def mk_vehicle(vid="VH001", status=VehicleStatus.AVAILABLE,
               vtype=VehicleType.TRUCK, temp=TempSpec.AMBIENT,
               depot=DEPOT, weight_cap=5000.0, volume_cap=30.0):
    return Vehicle(
        vehicle_id=vid, status=status, type=vtype, temp=temp,
        weight_cap_kg=weight_cap, volume_cap_m3=volume_cap, depot=depot,
    )


def mk_trip_result(vehicle_id, trip_num, brand, district, order_refs,
                   total_weight, total_volume, trip_minutes,
                   rem_weight=4000.0, rem_volume=20.0):
    refs = tuple(sorted(order_refs))
    return TripResult(
        vehicle_id=vehicle_id, trip_number=trip_num,
        brand=brand, district=district,
        order_refs=refs, stop_sequence=refs,
        total_weight_kg=total_weight, total_volume_m3=total_volume,
        trip_minutes=trip_minutes,
        remaining_weight_kg=rem_weight, remaining_volume_m3=rem_volume,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Baseline: a valid plan should pass
# ──────────────────────────────────────────────────────────────────────────────

class TestValidPlan:
    def test_simple_valid_plan_passes(self, t_idx, a_idx):
        """A correctly constructed plan should pass validation."""
        orders = [mk_order("O1"), mk_order("O2")]
        vehicles = [mk_vehicle()]
        vehicles_by_id = {"VH001": vehicles[0]}

        # Trip 1: 2 orders → 24 + 8*(2-1) + 15+15 = 24+8+30 = 62 min
        trip = mk_trip_result(
            "VH001", 1, Brand.FRESH, "Colombo",
            ["O1", "O2"],
            total_weight=200.0, total_volume=2.0,
            trip_minutes=62.0, rem_weight=4800.0, rem_volume=28.0,
        )

        served = [
            OrderAssignment(order_ref="O1", vehicle_id="VH001", trip_number=1),
            OrderAssignment(order_ref="O2", vehicle_id="VH001", trip_number=1),
        ]
        deferred = []

        result = validate(
            orders=orders, vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=served, deferred_orders=deferred,
            trip_results=[trip],
        )
        assert result.valid, f"Expected valid. Errors: {result.errors}"

    def test_deferred_order_valid_plan(self, t_idx, a_idx):
        """All deferred plan should also be valid."""
        orders = [mk_order("O1")]
        vehicles = [mk_vehicle()]
        vehicles_by_id = {"VH001": vehicles[0]}

        served = []
        deferred = [DeferredOrder(order_ref="O1", reason=DeferralReason.NO_COMPATIBLE_VEHICLE, detail="test")]

        result = validate(
            orders=orders, vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=served, deferred_orders=deferred,
            trip_results=[],
        )
        assert result.valid, f"Expected valid all-deferred. Errors: {result.errors}"


# ──────────────────────────────────────────────────────────────────────────────
# Coverage violations
# ──────────────────────────────────────────────────────────────────────────────

class TestCoverageViolations:
    def test_missing_order_from_plan(self, t_idx, a_idx):
        """Orders not in served or deferred should fail validation."""
        orders = [mk_order("O1"), mk_order("O2")]
        vehicles_by_id = {"VH001": mk_vehicle()}
        # O2 is missing from the plan
        result = validate(
            orders=orders, vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[OrderAssignment("O1", "VH001", 1)],
            deferred_orders=[],
            trip_results=[mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                         ["O1"], 100.0, 1.0, 39.0)],
        )
        assert not result.valid
        assert any("O2" in e.detail for e in result.errors)

    def test_served_order_missing_vehicle(self, t_idx, a_idx):
        """Served order with empty vehicle_id should fail."""
        orders = [mk_order("O1")]
        vehicles_by_id = {"VH001": mk_vehicle()}
        result = validate(
            orders=orders, vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[OrderAssignment("O1", "", 1)],
            deferred_orders=[],
            trip_results=[],
        )
        assert not result.valid
        assert any(e.rule == "SERVED_MISSING_VEHICLE" for e in result.errors)

    def test_duplicate_assignment_rejected(self, t_idx, a_idx):
        """Same order assigned twice should fail."""
        orders = [mk_order("O1")]
        vehicles_by_id = {"VH001": mk_vehicle()}
        result = validate(
            orders=orders, vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[
                OrderAssignment("O1", "VH001", 1),
                OrderAssignment("O1", "VH001", 1),
            ],
            deferred_orders=[],
            trip_results=[mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                         ["O1"], 100.0, 1.0, 39.0)],
        )
        assert not result.valid
        assert any(e.rule == "DUPLICATE_ASSIGNMENT" for e in result.errors)


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle violations
# ──────────────────────────────────────────────────────────────────────────────

class TestVehicleViolations:
    def test_workshop_vehicle_rejected(self, t_idx, a_idx):
        """Allocating a workshop vehicle should fail validation."""
        orders = [mk_order("O1")]
        workshop_vehicle = mk_vehicle(status=VehicleStatus.IN_WORKSHOP)
        vehicles_by_id = {"VH001": workshop_vehicle}
        result = validate(
            orders=orders, vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[OrderAssignment("O1", "VH001", 1)],
            deferred_orders=[],
            trip_results=[mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                         ["O1"], 100.0, 1.0, 39.0)],
        )
        assert not result.valid
        assert any(e.rule == "VEHICLE_IN_WORKSHOP" for e in result.errors)

    def test_too_many_trips_rejected(self, t_idx, a_idx):
        """Vehicle with 3 trips should fail (max 2)."""
        orders = [mk_order(f"O{i}") for i in range(3)]
        vehicles_by_id = {"VH001": mk_vehicle()}
        result = validate(
            orders=orders, vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[OrderAssignment(f"O{i}", "VH001", i+1) for i in range(3)],
            deferred_orders=[],
            trip_results=[
                mk_trip_result("VH001", 1, Brand.FRESH, "Colombo", ["O0"], 100.0, 1.0, 39.0),
                mk_trip_result("VH001", 2, Brand.FRESH, "Colombo", ["O1"], 100.0, 1.0, 39.0),
                mk_trip_result("VH001", 3, Brand.FRESH, "Colombo", ["O2"], 100.0, 1.0, 39.0),
            ],
        )
        assert not result.valid
        assert any(e.rule == "TOO_MANY_TRIPS" for e in result.errors)


# ──────────────────────────────────────────────────────────────────────────────
# Trip hard constraint violations
# ──────────────────────────────────────────────────────────────────────────────

class TestTripViolations:
    def test_chilled_ambient_vehicle_rejected(self, t_idx, a_idx):
        """HC2: chilled order on ambient vehicle → validation fails."""
        chilled_order = mk_order("O1", temp=TempRequirement.CHILLED)
        ambient_vehicle = mk_vehicle(temp=TempSpec.AMBIENT)
        vehicles_by_id = {"VH001": ambient_vehicle}
        result = validate(
            orders=[chilled_order], vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[OrderAssignment("O1", "VH001", 1)],
            deferred_orders=[],
            trip_results=[mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                         ["O1"], 100.0, 1.0, 39.0)],
        )
        assert not result.valid
        assert any(e.rule == "TEMP_INCOMPATIBLE" for e in result.errors)

    def test_van_only_truck_rejected(self, t_idx, a_idx):
        """HC3: van_only order on truck → validation fails."""
        van_order = mk_order("O1", parking=ParkingConstraint.VAN_ONLY)
        truck = mk_vehicle(vtype=VehicleType.TRUCK)
        vehicles_by_id = {"VH001": truck}
        result = validate(
            orders=[van_order], vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[OrderAssignment("O1", "VH001", 1)],
            deferred_orders=[],
            trip_results=[mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                         ["O1"], 100.0, 1.0, 39.0)],
        )
        assert not result.valid
        assert any(e.rule == "ACCESS_INCOMPATIBLE" for e in result.errors)

    def test_depot_mismatch_rejected(self, t_idx, a_idx):
        """HC4: order and vehicle at different depots → validation fails."""
        order = mk_order("O1", depot="Kandy")
        vehicle = mk_vehicle(depot="Peliyagoda")
        vehicles_by_id = {"VH001": vehicle}
        result = validate(
            orders=[order], vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[OrderAssignment("O1", "VH001", 1)],
            deferred_orders=[],
            trip_results=[mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                         ["O1"], 100.0, 1.0, 39.0)],
        )
        assert not result.valid
        assert any(e.rule == "DEPOT_MISMATCH" for e in result.errors)

    def test_weight_overflow_rejected(self, t_idx, a_idx):
        """HC6a: trip exceeding weight capacity → validation fails."""
        heavy_order = mk_order("O1", weight=6000.0)
        vehicle = mk_vehicle(weight_cap=5000.0)
        vehicles_by_id = {"VH001": vehicle}
        # Declare the trip with excessive weight
        bad_trip = mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                  ["O1"], total_weight=6000.0, total_volume=1.0,
                                  trip_minutes=39.0, rem_weight=-1000.0)
        result = validate(
            orders=[heavy_order], vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[OrderAssignment("O1", "VH001", 1)],
            deferred_orders=[],
            trip_results=[bad_trip],
        )
        assert not result.valid
        assert any(e.rule == "WEIGHT_OVERFLOW" for e in result.errors)

    def test_volume_overflow_rejected(self, t_idx, a_idx):
        """HC6b: trip exceeding volume capacity → validation fails."""
        bulky_order = mk_order("O1", volume=40.0)
        vehicle = mk_vehicle(volume_cap=30.0)
        vehicles_by_id = {"VH001": vehicle}
        bad_trip = mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                  ["O1"], 100.0, 40.0, 39.0, rem_volume=-10.0)
        result = validate(
            orders=[bulky_order], vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[OrderAssignment("O1", "VH001", 1)],
            deferred_orders=[],
            trip_results=[bad_trip],
        )
        assert not result.valid
        assert any(e.rule == "VOLUME_OVERFLOW" for e in result.errors)

    def test_mixed_brand_rejected(self, t_idx, a_idx, allowances):
        """HC1: mixed brands in a trip → validation fails."""
        fresh_order = mk_order("O1", Brand.FRESH)
        style_order = mk_order("O2", Brand.STYLE)
        vehicle = mk_vehicle()
        vehicles_by_id = {"VH001": vehicle}
        # Claim trip has brand=FRESH but put both order_refs in it
        bad_trip = mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                  ["O1", "O2"], 200.0, 2.0, 62.0)
        result = validate(
            orders=[fresh_order, style_order], vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[
                OrderAssignment("O1", "VH001", 1),
                OrderAssignment("O2", "VH001", 1),
            ],
            deferred_orders=[],
            trip_results=[bad_trip],
        )
        assert not result.valid
        assert any(e.rule == "MIXED_BRAND" for e in result.errors)

    def test_mixed_district_rejected(self, t_idx, a_idx):
        """HC1: mixed districts in a trip → validation fails."""
        colombo_order = mk_order("O1", district="Colombo")
        gampaha_order = mk_order("O2", district="Gampaha")
        vehicle = mk_vehicle()
        vehicles_by_id = {"VH001": vehicle}
        bad_trip = mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                                  ["O1", "O2"], 200.0, 2.0, 62.0)
        result = validate(
            orders=[colombo_order, gampaha_order], vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=[
                OrderAssignment("O1", "VH001", 1),
                OrderAssignment("O2", "VH001", 1),
            ],
            deferred_orders=[],
            trip_results=[bad_trip],
        )
        assert not result.valid
        assert any(e.rule == "MIXED_DISTRICT" for e in result.errors)


# ──────────────────────────────────────────────────────────────────────────────
# Time budget violations
# ──────────────────────────────────────────────────────────────────────────────

class TestTimeBudgets:
    def test_fresh_budget_exceeded(self, t_idx, a_idx):
        """Fresh >270 minutes should fail validation."""
        orders = [mk_order("O1")]
        vehicle = mk_vehicle()
        vehicles_by_id = {"VH001": vehicle}
        # Report trip minutes = 280 (exceeds 270 budget)
        # But the validator recomputes — so we need the formula to produce >270
        # We create a scenario with many orders to exceed 270 min
        # outbound=24, each order: 16 min handling + 8 inter_stop
        # Formula: 24 + 8*(n-1) + 16*n
        # For n=15: 24 + 8*14 + 16*15 = 24+112+240 = 376 > 270
        many_orders = [mk_order(f"O{i}", dock=DockType.STREET) for i in range(15)]
        served = [OrderAssignment(f"O{i}", "VH001", 1) for i in range(15)]
        refs = tuple(f"O{i}" for i in range(15))
        # Correct trip time for 15 orders: 24 + 8*14 + 16*15 = 376
        trip = mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                              list(refs), 1500.0, 15.0, 376.0,
                              rem_weight=3500.0, rem_volume=15.0)

        result = validate(
            orders=many_orders, vehicles_by_id={"VH001": mk_vehicle(weight_cap=50000, volume_cap=1000)},
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=served,
            deferred_orders=[],
            trip_results=[trip],
        )
        assert not result.valid
        assert any(e.rule == "FRESH_BUDGET_EXCEEDED" for e in result.errors), \
            f"Expected FRESH_BUDGET_EXCEEDED. Got: {[e.rule for e in result.errors]}"


# ──────────────────────────────────────────────────────────────────────────────
# Validator pass = FEASIBLE, not OPTIMAL
# ──────────────────────────────────────────────────────────────────────────────

class TestValidationMeaning:
    def test_valid_plan_is_feasible_not_optimal(self, t_idx, a_idx):
        """
        Explicitly test that a passing plan is labelled FEASIBLE.
        The Validator must never claim global optimality.
        """
        orders = [mk_order("O1")]
        vehicles_by_id = {"VH001": mk_vehicle()}
        served = [OrderAssignment("O1", "VH001", 1)]
        trip = mk_trip_result("VH001", 1, Brand.FRESH, "Colombo",
                              ["O1"], 100.0, 1.0, 39.0)
        result = validate(
            orders=orders, vehicles_by_id=vehicles_by_id,
            travel_index=t_idx, allowance_index=a_idx,
            served_assignments=served, deferred_orders=[],
            trip_results=[trip],
        )
        assert result.valid
        # The ValidationResult object does NOT have an "is_optimal" attribute.
        # This is intentional — validation only checks feasibility.
        assert not hasattr(result, "is_optimal")
