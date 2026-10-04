"""
Regression tests for Phase 2: greedy new-trip time-budget calculations.
Verifies the fix for first-order double-counting, budget boundaries,
configuration propagation, and rejection of unsupported configurations.
"""
import pytest
from waypoint_optimizer.compatibility import (
    can_add_order_to_trip,
    can_open_new_trip,
    check_fresh_time_budget,
    check_style_tech_time_budget,
)
from waypoint_optimizer.config import (
    FRESH_DAILY_BUDGET_MIN,
    OptimizerConfig,
    STYLE_TECH_DAILY_BUDGET_MIN,
)
from waypoint_optimizer.domain import (
    DistrictTravel,
    Order,
    ServiceAllowance,
    Trip,
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
)
from waypoint_optimizer.greedy import greedy_allocate, validate_greedy_config
from waypoint_optimizer.trip_math import build_allowance_index, build_travel_index


DEPOT = "Peliyagoda"


def make_order(
    ref: str,
    brand: Brand = Brand.FRESH,
    district: str = "Colombo",
    weight: float = 100.0,
    volume: float = 1.0,
    dock: DockType = DockType.REAR_DOCK,
) -> Order:
    return Order(
        order_ref=ref,
        outlet_id="OUT1",
        brand=brand,
        district=district,
        depot=DEPOT,
        dock_type=dock,
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=1,
        order_weight_kg=weight,
        order_volume_m3=volume,
        deferred_prev=False,
        defer_count=0,
        is_urgent=False,
    )


def make_vehicle(vid: str = "V1", weight_cap: float = 5000.0, volume_cap: float = 30.0) -> Vehicle:
    return Vehicle(
        vehicle_id=vid,
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.TRUCK,
        temp=TempSpec.REEFER,
        weight_cap_kg=weight_cap,
        volume_cap_m3=volume_cap,
        depot=DEPOT,
    )


def test_independently_calculated_case_allowed_not_doubled():
    """
    Independently calculated specification case:
      outbound = 250 minutes
      inter-stop = 10 minutes
      one order's allowance = 15 minutes
      Fresh budget = 270 minutes

    Correct duration:
      250 + (1 - 1) * 10 + 15 = 265 minutes <= 270 minutes -> ALLOWED.
    The previous buggy doubled calculation:
      250 + (2 - 1) * 10 + 2 * 15 = 290 minutes > 270 minutes -> was REJECTED.
    """
    travel = [
        DistrictTravel(
            district="Colombo",
            depot=DEPOT,
            road_class="A",
            free_flow_kmh=50.0,
            depot_to_district_km=50.0,
            depot_to_district_freeflow_min=250.0,
            inter_stop_km=5.0,
            inter_stop_freeflow_min=10.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0)
    ]
    t_idx = build_travel_index(travel)
    a_idx = build_allowance_index(allowances)

    order = make_order("O1", Brand.FRESH, "Colombo", dock=DockType.REAR_DOCK)
    vehicle = make_vehicle("V1")

    can_open, reasons = can_open_new_trip(order, vehicle, [], t_idx, a_idx)
    assert can_open, f"Expected opening trip to be allowed with 265 min duration. Reasons: {reasons}"
    assert reasons == []


def test_one_order_new_trip_budget_boundaries():
    """
    Single order new trip: exactly at budget is accepted; 0.1 over is rejected.
    outbound = 100, allowance = 20 -> duration = 120 min.
    """
    travel = [
        DistrictTravel(
            district="Colombo",
            depot=DEPOT,
            road_class="A",
            free_flow_kmh=50.0,
            depot_to_district_km=50.0,
            depot_to_district_freeflow_min=100.0,
            inter_stop_km=5.0,
            inter_stop_freeflow_min=15.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=20.0)
    ]
    t_idx = build_travel_index(travel)
    a_idx = build_allowance_index(allowances)

    order = make_order("O1", Brand.FRESH, "Colombo")
    vehicle = make_vehicle("V1")

    # Exact boundary: 120.0 min budget
    cfg_exact = OptimizerConfig(fresh_daily_budget_min=120)
    can_open_exact, reasons_exact = can_open_new_trip(order, vehicle, [], t_idx, a_idx, cfg=cfg_exact)
    assert can_open_exact, f"120 min trip at 120 min budget must be accepted. Reasons: {reasons_exact}"

    # Over boundary: 119.0 min budget
    cfg_over = OptimizerConfig(fresh_daily_budget_min=119)
    can_open_over, reasons_over = can_open_new_trip(order, vehicle, [], t_idx, a_idx, cfg=cfg_over)
    assert not can_open_over
    assert any("exceeding" in r for r in reasons_over)


def test_insertion_into_existing_trip_budget_boundaries():
    """
    Existing trip with O1: outbound = 100, inter_stop = 20, O1 allowance = 15 -> 115 min.
    Adding O2 (allowance = 15):
      new duration = 100 + (2 - 1)*20 + 15 + 15 = 150 min.
    Budget = 150 -> accepted; Budget = 149 -> rejected.
    """
    travel = [
        DistrictTravel(
            district="Colombo",
            depot=DEPOT,
            road_class="A",
            free_flow_kmh=50.0,
            depot_to_district_km=50.0,
            depot_to_district_freeflow_min=100.0,
            inter_stop_km=5.0,
            inter_stop_freeflow_min=20.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0)
    ]
    t_idx = build_travel_index(travel)
    a_idx = build_allowance_index(allowances)

    o1 = make_order("O1", Brand.FRESH, "Colombo")
    o2 = make_order("O2", Brand.FRESH, "Colombo")
    vehicle = make_vehicle("V1")

    existing_trip = Trip(
        vehicle_id="V1",
        trip_number=1,
        brand=Brand.FRESH,
        district="Colombo",
        orders=[o1],
    )

    # Exact boundary
    cfg_exact = OptimizerConfig(fresh_daily_budget_min=150)
    can_add_exact, reasons_exact = can_add_order_to_trip(
        o2, existing_trip, vehicle, [existing_trip], t_idx, a_idx, cfg=cfg_exact
    )
    assert can_add_exact, f"150 min combined trip at 150 min budget must be accepted. Reasons: {reasons_exact}"

    # Over boundary
    cfg_over = OptimizerConfig(fresh_daily_budget_min=149)
    can_add_over, reasons_over = can_add_order_to_trip(
        o2, existing_trip, vehicle, [existing_trip], t_idx, a_idx, cfg=cfg_over
    )
    assert not can_add_over
    assert any("exceeding" in r for r in reasons_over)


def test_aggregate_time_across_two_trips():
    """
    Trip 1: 100 + 0 + 15 = 115 min.
    Trip 2: 100 + 0 + 15 = 115 min.
    Aggregate Fresh time = 230 min.
    Fresh budget = 230 -> Trip 2 accepted.
    Fresh budget = 229 -> Trip 2 rejected.
    """
    travel = [
        DistrictTravel(
            district="Colombo",
            depot=DEPOT,
            road_class="A",
            free_flow_kmh=50.0,
            depot_to_district_km=50.0,
            depot_to_district_freeflow_min=100.0,
            inter_stop_km=5.0,
            inter_stop_freeflow_min=10.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0)
    ]
    t_idx = build_travel_index(travel)
    a_idx = build_allowance_index(allowances)

    o1 = make_order("O1", Brand.FRESH, "Colombo")
    o2 = make_order("O2", Brand.FRESH, "Colombo")
    vehicle = make_vehicle("V1")

    trip1 = Trip(
        vehicle_id="V1",
        trip_number=1,
        brand=Brand.FRESH,
        district="Colombo",
        orders=[o1],
    )

    # Budget 230 min
    cfg_exact = OptimizerConfig(fresh_daily_budget_min=230)
    can_open_exact, reasons_exact = can_open_new_trip(
        o2, vehicle, [trip1], t_idx, a_idx, cfg=cfg_exact
    )
    assert can_open_exact, f"230 min total across 2 trips at 230 min budget must be accepted. Reasons: {reasons_exact}"

    # Budget 229 min
    cfg_over = OptimizerConfig(fresh_daily_budget_min=229)
    can_open_over, reasons_over = can_open_new_trip(
        o2, vehicle, [trip1], t_idx, a_idx, cfg=cfg_over
    )
    assert not can_open_over
    assert any("exceeding" in r for r in reasons_over)


def test_style_tech_budget_path_exact_and_over():
    """
    Trip 1: Style order, 200 min outbound + 40 min allowance = 240 min.
    Trip 2: Tech order, 200 min outbound + 40 min allowance = 240 min.
    Total Style+Tech time = 480 min.
    Budget = 480 min -> accepted.
    Budget = 479 min -> rejected.
    """
    travel = [
        DistrictTravel(
            district="Colombo",
            depot=DEPOT,
            road_class="A",
            free_flow_kmh=50.0,
            depot_to_district_km=50.0,
            depot_to_district_freeflow_min=200.0,
            inter_stop_km=5.0,
            inter_stop_freeflow_min=10.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.STYLE, dock_type=DockType.REAR_DOCK, service_allowance_min=40.0),
        ServiceAllowance(brand=Brand.TECH, dock_type=DockType.REAR_DOCK, service_allowance_min=40.0),
    ]
    t_idx = build_travel_index(travel)
    a_idx = build_allowance_index(allowances)

    o_style = make_order("O_STYLE", Brand.STYLE, "Colombo")
    o_tech = make_order("O_TECH", Brand.TECH, "Colombo")
    vehicle = make_vehicle("V1")

    trip1 = Trip(
        vehicle_id="V1",
        trip_number=1,
        brand=Brand.STYLE,
        district="Colombo",
        orders=[o_style],
    )

    # Exact boundary: 480 min
    cfg_exact = OptimizerConfig(style_tech_daily_budget_min=480)
    can_open_exact, reasons_exact = can_open_new_trip(
        o_tech, vehicle, [trip1], t_idx, a_idx, cfg=cfg_exact
    )
    assert can_open_exact, f"480 min combined Style+Tech at 480 min budget must be accepted. Reasons: {reasons_exact}"

    # Over boundary: 479 min
    cfg_over = OptimizerConfig(style_tech_daily_budget_min=479)
    can_open_over, reasons_over = can_open_new_trip(
        o_tech, vehicle, [trip1], t_idx, a_idx, cfg=cfg_over
    )
    assert not can_open_over
    assert any("exceeding" in r for r in reasons_over)


def test_non_default_supported_budget_and_single_trip_policy():
    """
    Greedy allocator with non-default supported settings:
    max_trips_per_vehicle = 1, valid_trip_numbers = frozenset({1}).
    Orders that would need trip 2 must be deferred due to trip limit.
    """
    travel = [
        DistrictTravel(
            district="Colombo",
            depot=DEPOT,
            road_class="A",
            free_flow_kmh=50.0,
            depot_to_district_km=10.0,
            depot_to_district_freeflow_min=20.0,
            inter_stop_km=3.0,
            inter_stop_freeflow_min=5.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=10.0),
        ServiceAllowance(brand=Brand.STYLE, dock_type=DockType.REAR_DOCK, service_allowance_min=10.0),
    ]
    # Two orders of different brands (cannot share trip 1) and only 1 vehicle
    o1 = make_order("O1", Brand.FRESH, "Colombo")
    o2 = make_order("O2", Brand.STYLE, "Colombo")
    vehicle = make_vehicle("V1")

    cfg_single_trip = OptimizerConfig(
        max_trips_per_vehicle=1,
        valid_trip_numbers=frozenset({1}),
    )

    result = greedy_allocate([o1, o2], [vehicle], travel, allowances, cfg=cfg_single_trip)
    assert result.validation.valid
    assert result.metrics.served_count == 1
    assert result.metrics.deferred_count == 1
    assert len(result.trips) == 1
    assert result.trips[0].trip_number == 1


def test_unsupported_configuration_explicitly_rejected():
    """
    Greedy solver explicitly rejects configurations that conflict with solver assumptions:
    - max_trips_per_vehicle > 2
    - valid_trip_numbers missing trip 1 or containing trip numbers > 2
    - non-positive budgets
    """
    travel = [
        DistrictTravel(
            district="Colombo",
            depot=DEPOT,
            road_class="A",
            free_flow_kmh=50.0,
            depot_to_district_km=10.0,
            depot_to_district_freeflow_min=20.0,
            inter_stop_km=3.0,
            inter_stop_freeflow_min=5.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=10.0)
    ]
    orders = [make_order("O1")]
    vehicles = [make_vehicle("V1")]

    # max_trips_per_vehicle > 2
    with pytest.raises(ValueError, match="Greedy solver only supports up to 2 trips per vehicle"):
        greedy_allocate(orders, vehicles, travel, allowances, cfg=OptimizerConfig(max_trips_per_vehicle=3))

    # valid_trip_numbers missing 1
    with pytest.raises(ValueError, match="Greedy solver requires trip number 1"):
        greedy_allocate(orders, vehicles, travel, allowances, cfg=OptimizerConfig(valid_trip_numbers=frozenset({2})))

    # valid_trip_numbers containing trip 3
    with pytest.raises(ValueError, match="Greedy solver does not support trip numbers beyond"):
        greedy_allocate(orders, vehicles, travel, allowances, cfg=OptimizerConfig(valid_trip_numbers=frozenset({1, 2, 3})))

    # Non-positive budget
    with pytest.raises(ValueError, match="fresh_daily_budget_min must be positive"):
        greedy_allocate(orders, vehicles, travel, allowances, cfg=OptimizerConfig(fresh_daily_budget_min=0))
