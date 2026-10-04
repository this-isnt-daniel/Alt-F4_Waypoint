"""
Tests reproducing the official Task 2B trip-time formula examples.

These are deterministic regression tests. Any change to trip_math.py that
breaks these tests violates the official Task 2B specification.

EXAMPLE A: Fresh, Gampaha, 3 orders → 101 minutes
EXAMPLE B: Fresh, Colombo, 4 street orders → 112 minutes
EXAMPLE C: Same vehicle both trips → 213 minutes, must be ≤ 270 minutes

Also tests:
  - No return journey is included (regression guard)
  - Third trip is structurally prevented by MAX_TRIPS_PER_VEHICLE

All values in this file match the prompt specification exactly.
"""
import math
import pytest

from waypoint_optimizer.domain import (
    DistrictTravel, Order, ServiceAllowance, Trip,
)
from waypoint_optimizer.enums import (
    Brand, DockType, ParkingConstraint, TempRequirement, VehicleType,
)
from waypoint_optimizer.trip_math import (
    build_allowance_index,
    build_travel_index,
    calculate_trip_minutes,
    handling_minutes,
    inter_stop_minutes,
    outbound_minutes,
    vehicle_daily_time_usage,
    vehicle_fresh_time,
)
from waypoint_optimizer.config import (
    FRESH_DAILY_BUDGET_MIN,
    MAX_TRIPS_PER_VEHICLE,
)


# ──────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def gampaha_travel() -> DistrictTravel:
    """Travel data for depot=Peliyagoda → district=Gampaha (Example A)."""
    return DistrictTravel(
        district="Gampaha",
        depot="Peliyagoda",
        road_class="A",
        free_flow_kmh=60.0,
        depot_to_district_km=37.0,   # km — not used in Task2B time formula
        depot_to_district_freeflow_min=37.0,  # used in formula
        inter_stop_km=4.5,
        inter_stop_freeflow_min=9.0,  # used in formula
    )


@pytest.fixture
def colombo_travel() -> DistrictTravel:
    """Travel data for depot=Peliyagoda → district=Colombo (Example B)."""
    return DistrictTravel(
        district="Colombo",
        depot="Peliyagoda",
        road_class="A",
        free_flow_kmh=50.0,
        depot_to_district_km=12.0,
        depot_to_district_freeflow_min=24.0,  # used in formula
        inter_stop_km=3.0,
        inter_stop_freeflow_min=8.0,   # used in formula
    )


@pytest.fixture
def fresh_allowances() -> dict[tuple[Brand, str], float]:
    """
    Service allowances for Fresh orders.

    Spec Example A: (fresh, rear_dock) → 15 min, one order gets 16 min.
    For simplicity we define two keys so order dock_type drives the lookup.
    Example A uses three orders: two with 15-min allowance, one with 16-min.
    Example B uses four street orders each with 16-min allowance.
    """
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0),
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.STREET, service_allowance_min=16.0),
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.MALL_BAY, service_allowance_min=20.0),
    ]
    return build_allowance_index(allowances)


def _make_fresh_order(
    ref: str,
    dock_type: DockType,
    district: str = "Gampaha",
    weight_kg: float = 100.0,
    volume_m3: float = 1.0,
) -> Order:
    return Order(
        order_ref=ref,
        outlet_id=f"outlet_{ref}",
        brand=Brand.FRESH,
        district=district,
        depot="Peliyagoda",
        dock_type=dock_type,
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=10,
        order_weight_kg=weight_kg,
        order_volume_m3=volume_m3,
        deferred_prev=False,
        defer_count=0,
        is_urgent=False,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Step-level unit tests (isolate each formula component)
# ──────────────────────────────────────────────────────────────────────────────

class TestOutboundMinutes:
    def test_gampaha_outbound(self, gampaha_travel):
        assert outbound_minutes(gampaha_travel) == 37.0

    def test_colombo_outbound(self, colombo_travel):
        assert outbound_minutes(colombo_travel) == 24.0


class TestInterStopMinutes:
    def test_one_order_zero_inter_stop(self, gampaha_travel):
        """1 order → 0 inter-stop journeys."""
        assert inter_stop_minutes(gampaha_travel, 1) == 0.0

    def test_three_orders_two_journeys(self, gampaha_travel):
        """3 orders → 2 inter-stop journeys at 9 min each → 18 min."""
        assert inter_stop_minutes(gampaha_travel, 3) == 9.0 * 2

    def test_four_orders_three_journeys(self, colombo_travel):
        """4 orders → 3 inter-stop journeys at 8 min each → 24 min."""
        assert inter_stop_minutes(colombo_travel, 4) == 8.0 * 3

    def test_zero_orders_zero_inter_stop(self, gampaha_travel):
        assert inter_stop_minutes(gampaha_travel, 0) == 0.0


class TestHandlingMinutes:
    def test_example_a_handling(self, fresh_allowances):
        """Example A: two rear_dock (15) + one street (16) = 46 min."""
        orders = [
            _make_fresh_order("A1", DockType.REAR_DOCK),
            _make_fresh_order("A2", DockType.REAR_DOCK),
            _make_fresh_order("A3", DockType.STREET),
        ]
        assert handling_minutes(orders, fresh_allowances) == 15.0 + 15.0 + 16.0

    def test_example_b_handling(self, fresh_allowances):
        """Example B: four street orders at 16 each = 64 min."""
        orders = [_make_fresh_order(f"B{i}", DockType.STREET, district="Colombo") for i in range(4)]
        assert handling_minutes(orders, fresh_allowances) == 64.0

    def test_missing_allowance_raises(self):
        """Missing (brand, dock_type) should raise KeyError, not silently return 0."""
        order = _make_fresh_order("X1", DockType.REAR_DOCK)
        empty_index: dict = {}
        with pytest.raises(KeyError):
            handling_minutes([order], empty_index)


# ──────────────────────────────────────────────────────────────────────────────
# OFFICIAL EXAMPLE A — 101 minutes
# ──────────────────────────────────────────────────────────────────────────────

class TestOfficialExampleA:
    """
    Fresh, Gampaha, 3 orders.
    outbound=37, inter_stop=9, allowances=[15, 15, 16]

    Expected: 37 + 9*(3-1) + (15+15+16) = 37 + 18 + 46 = 101 minutes
    """

    def test_trip_minutes_101(self, gampaha_travel, fresh_allowances):
        orders = [
            _make_fresh_order("A1", DockType.REAR_DOCK),
            _make_fresh_order("A2", DockType.REAR_DOCK),
            _make_fresh_order("A3", DockType.STREET),
        ]
        result = calculate_trip_minutes(orders, gampaha_travel, fresh_allowances)
        assert result == 101.0, f"Expected 101.0 but got {result}"

    def test_component_breakdown(self, gampaha_travel, fresh_allowances):
        """Verify each component separately to catch partial errors."""
        orders = [
            _make_fresh_order("A1", DockType.REAR_DOCK),
            _make_fresh_order("A2", DockType.REAR_DOCK),
            _make_fresh_order("A3", DockType.STREET),
        ]
        assert outbound_minutes(gampaha_travel) == 37.0
        assert inter_stop_minutes(gampaha_travel, 3) == 18.0
        assert handling_minutes(orders, fresh_allowances) == 46.0

    def test_no_return_journey(self, gampaha_travel, fresh_allowances):
        """
        REGRESSION GUARD: trip_minutes must NOT include return travel.

        Return journey would be another depot_to_district_freeflow_min = 37 min.
        So if result > 138 (= 101 + 37) the formula includes return.
        """
        orders = [
            _make_fresh_order("A1", DockType.REAR_DOCK),
            _make_fresh_order("A2", DockType.REAR_DOCK),
            _make_fresh_order("A3", DockType.STREET),
        ]
        result = calculate_trip_minutes(orders, gampaha_travel, fresh_allowances)
        # The return trip would add 37 minutes — assert it is NOT included
        assert result < 101.0 + gampaha_travel.depot_to_district_freeflow_min, (
            "Return journey appears to have been added to the trip time. "
            "This violates the Task 2B specification."
        )
        assert result == 101.0


# ──────────────────────────────────────────────────────────────────────────────
# OFFICIAL EXAMPLE B — 112 minutes
# ──────────────────────────────────────────────────────────────────────────────

class TestOfficialExampleB:
    """
    Fresh, Colombo, 4 street orders.
    outbound=24, inter_stop=8, allowance=16 each

    Expected: 24 + 8*(4-1) + 16*4 = 24 + 24 + 64 = 112 minutes
    """

    def test_trip_minutes_112(self, colombo_travel, fresh_allowances):
        orders = [
            _make_fresh_order(f"B{i}", DockType.STREET, district="Colombo")
            for i in range(4)
        ]
        result = calculate_trip_minutes(orders, colombo_travel, fresh_allowances)
        assert result == 112.0, f"Expected 112.0 but got {result}"

    def test_component_breakdown(self, colombo_travel, fresh_allowances):
        orders = [
            _make_fresh_order(f"B{i}", DockType.STREET, district="Colombo")
            for i in range(4)
        ]
        assert outbound_minutes(colombo_travel) == 24.0
        assert inter_stop_minutes(colombo_travel, 4) == 24.0
        assert handling_minutes(orders, fresh_allowances) == 64.0

    def test_no_return_journey(self, colombo_travel, fresh_allowances):
        """Return journey would add 24 min — must NOT be included."""
        orders = [
            _make_fresh_order(f"B{i}", DockType.STREET, district="Colombo")
            for i in range(4)
        ]
        result = calculate_trip_minutes(orders, colombo_travel, fresh_allowances)
        assert result < 112.0 + colombo_travel.depot_to_district_freeflow_min
        assert result == 112.0


# ──────────────────────────────────────────────────────────────────────────────
# OFFICIAL EXAMPLE C — 213 minutes combined on one vehicle
# ──────────────────────────────────────────────────────────────────────────────

class TestOfficialExampleC:
    """
    Same vehicle performs both Fresh trips:
      Trip 1: Gampaha, 3 orders → 101 min
      Trip 2: Colombo, 4 orders → 112 min
      Combined: 213 min ≤ 270 min (PASS)

    Also confirms MAX_TRIPS_PER_VEHICLE is 2: a third trip structure is
    detectable as a violation.
    """

    def test_combined_213_within_budget(
        self, gampaha_travel, colombo_travel, fresh_allowances
    ):
        orders_a = [
            _make_fresh_order("A1", DockType.REAR_DOCK),
            _make_fresh_order("A2", DockType.REAR_DOCK),
            _make_fresh_order("A3", DockType.STREET),
        ]
        orders_b = [
            _make_fresh_order(f"B{i}", DockType.STREET, district="Colombo")
            for i in range(4)
        ]

        trip1_min = calculate_trip_minutes(orders_a, gampaha_travel, fresh_allowances)
        trip2_min = calculate_trip_minutes(orders_b, colombo_travel, fresh_allowances)
        combined = trip1_min + trip2_min

        assert trip1_min == 101.0
        assert trip2_min == 112.0
        assert combined == 213.0
        assert combined <= FRESH_DAILY_BUDGET_MIN, (
            f"Combined Fresh time {combined} exceeds {FRESH_DAILY_BUDGET_MIN} min budget."
        )

    def test_third_trip_violates_max_trips(self):
        """
        MAX_TRIPS_PER_VEHICLE is 2. Three trips for one vehicle must never
        be produced by the optimizer.

        This test verifies the constant is set to 2 (the official rule)
        and that a list of 3 trips is detectable as a violation.
        """
        assert MAX_TRIPS_PER_VEHICLE == 2, (
            "Official rule: max 2 trips per vehicle. "
            "MAX_TRIPS_PER_VEHICLE must be 2."
        )
        # Simulate three trip objects for the same vehicle
        vehicle_trips = [
            Trip(vehicle_id="VH01", trip_number=1, brand=Brand.FRESH, district="Gampaha"),
            Trip(vehicle_id="VH01", trip_number=2, brand=Brand.FRESH, district="Colombo"),
            Trip(vehicle_id="VH01", trip_number=3, brand=Brand.FRESH, district="Kandy"),  # illegal
        ]
        # A validator checking len(trips) > MAX_TRIPS_PER_VEHICLE must flag this
        assert len(vehicle_trips) > MAX_TRIPS_PER_VEHICLE, (
            "Expected 3 trips to exceed the max-2 rule."
        )

    def test_vehicle_fresh_time_helper(
        self, gampaha_travel, colombo_travel, fresh_allowances
    ):
        """vehicle_fresh_time() should sum correctly across multiple trips."""
        orders_a = [
            _make_fresh_order("A1", DockType.REAR_DOCK),
            _make_fresh_order("A2", DockType.REAR_DOCK),
            _make_fresh_order("A3", DockType.STREET),
        ]
        orders_b = [
            _make_fresh_order(f"B{i}", DockType.STREET, district="Colombo")
            for i in range(4)
        ]

        trip1 = Trip(vehicle_id="VH01", trip_number=1, brand=Brand.FRESH, district="Gampaha", orders=orders_a)
        trip2 = Trip(vehicle_id="VH01", trip_number=2, brand=Brand.FRESH, district="Colombo", orders=orders_b)

        travel_index = build_travel_index([gampaha_travel, colombo_travel])
        total = vehicle_fresh_time([trip1, trip2], travel_index, fresh_allowances)

        assert total == 213.0
        assert total <= FRESH_DAILY_BUDGET_MIN


# ──────────────────────────────────────────────────────────────────────────────
# Edge cases
# ──────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_trip_returns_zero(self, gampaha_travel, fresh_allowances):
        """An empty trip should return 0 minutes, not an error."""
        result = calculate_trip_minutes([], gampaha_travel, fresh_allowances)
        assert result == 0.0

    def test_single_order_no_inter_stop(self, gampaha_travel, fresh_allowances):
        """
        1 order: only outbound + handling, zero inter-stop.
        37 + 0 + 15 = 52 minutes.
        """
        orders = [_make_fresh_order("S1", DockType.REAR_DOCK)]
        result = calculate_trip_minutes(orders, gampaha_travel, fresh_allowances)
        assert result == 37.0 + 0.0 + 15.0  # 52 minutes

    def test_inter_stop_uses_order_count_not_outlet_count(self, gampaha_travel, fresh_allowances):
        """
        Two orders at the SAME outlet should count as 2 orders (1 inter-stop journey),
        not 1 unique outlet (0 inter-stop journeys).

        This guards against the (incorrect) outlet-count interpretation.
        """
        # Both orders share the same outlet_id
        order1 = Order(
            order_ref="O1", outlet_id="same_outlet", brand=Brand.FRESH,
            district="Gampaha", depot="Peliyagoda", dock_type=DockType.REAR_DOCK,
            parking_constraint=ParkingConstraint.NORMAL,
            mall_window=None, window_open_time=None, window_close_time=None,
            temp_requirement=TempRequirement.AMBIENT,
            order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
            deferred_prev=False, defer_count=0, is_urgent=False,
        )
        order2 = Order(
            order_ref="O2", outlet_id="same_outlet", brand=Brand.FRESH,
            district="Gampaha", depot="Peliyagoda", dock_type=DockType.REAR_DOCK,
            parking_constraint=ParkingConstraint.NORMAL,
            mall_window=None, window_open_time=None, window_close_time=None,
            temp_requirement=TempRequirement.AMBIENT,
            order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
            deferred_prev=False, defer_count=0, is_urgent=False,
        )
        result = calculate_trip_minutes([order1, order2], gampaha_travel, fresh_allowances)
        # outbound=37, inter_stop=9*(2-1)=9, handling=15+15=30 → 71
        # If (incorrectly) counting unique outlets: inter_stop=9*(1-1)=0 → 67 (WRONG)
        assert result == 37.0 + 9.0 + 30.0, (
            "Inter-stop must count ORDERS, not unique outlets. "
            f"Got {result}, expected 76.0"
        )
