"""
Waypoint Optimizer — Targeted CP-SAT Improvement Hardening Tests
================================================================
Focuses on the preserved targeted CP-SAT improvement stage:
  - Brand and district homogeneity on new trip slots.
  - Insertion of deferred orders into existing trips.
  - Rejection of candidates violating time budgets and incumbent preservation.
  - Fractional precision and capacity boundary enforcement.
  - Verification that targeted CP-SAT operates strictly as insertion-only.
"""
from __future__ import annotations

import pytest

from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.domain import (
    DistrictTravel,
    OptimizationResult,
    Order,
    OrderAssignment,
    PlanMetrics,
    ServiceAllowance,
    TripResult,
    ValidationResult,
    Vehicle,
)
from waypoint_optimizer.enums import (
    Brand,
    DeferralReason,
    DockType,
    EngineMode,
    ParkingConstraint,
    SolverStatus,
    TempRequirement,
    TempSpec,
    VehicleStatus,
    VehicleType,
)
from waypoint_optimizer.explanations import make_deferred
from waypoint_optimizer.objective import defer_penalty
from waypoint_optimizer.targeted_cpsat import targeted_cpsat_improve


DEPOT = "Peliyagoda"


def make_order(
    ref: str,
    brand: Brand = Brand.FRESH,
    district: str = "Colombo",
    weight: float = 100.0,
    volume: float = 1.0,
    dock: DockType = DockType.REAR_DOCK,
    units: int = 1,
    deferred_yesterday: bool = False,
    days_since: int = 0,
) -> Order:
    return Order(
        order_ref=ref,
        outlet_id=f"OUT_{ref}",
        brand=brand,
        district=district,
        depot=DEPOT,
        dock_type=dock,
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time=None,
        window_close_time=None,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=units,
        order_weight_kg=weight,
        order_volume_m3=volume,
        deferred_yesterday=deferred_yesterday,
        days_since_last_served=days_since,
    )


def make_vehicle(
    vid: str = "V1",
    weight_cap: float = 5000.0,
    volume_cap: float = 30.0,
    vtype: VehicleType = VehicleType.TRUCK,
    temp: TempSpec = TempSpec.REEFER,
) -> Vehicle:
    return Vehicle(
        vehicle_id=vid,
        status=VehicleStatus.AVAILABLE,
        type=vtype,
        temp=temp,
        weight_cap_kg=weight_cap,
        volume_cap_m3=volume_cap,
        depot=DEPOT,
    )


def test_targeted_cpsat_mixed_brands_districts_slot_homogeneity():
    """
    Targeted CP-SAT: empty trip slot must enforce brand/district homogeneity.
    If 2 deferred orders of different brands compete for the same slot,
    they must NEVER be placed in the same trip.
    """
    travel = [
        DistrictTravel(
            district="Colombo", depot=DEPOT, road_class="A",
            free_flow_kmh=50.0, depot_to_district_km=10.0,
            depot_to_district_freeflow_min=24.0,
            inter_stop_km=3.0, inter_stop_freeflow_min=8.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0),
        ServiceAllowance(brand=Brand.STYLE, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0),
    ]
    o_fresh = make_order("O_FRESH", Brand.FRESH, "Colombo")
    o_style = make_order("O_STYLE", Brand.STYLE, "Colombo")
    vehicle = make_vehicle("V1")

    base_trip = TripResult(
        vehicle_id="V1", trip_number=1, brand=Brand.FRESH, district="Colombo",
        order_refs=("O_BASE",), stop_sequence=("O_BASE",),
        total_weight_kg=100.0, total_volume_m3=1.0, trip_minutes=39.0,
        remaining_weight_kg=4900.0, remaining_volume_m3=29.0,
    )
    o_base = make_order("O_BASE", Brand.FRESH, "Colombo")
    all_orders = [o_base, o_fresh, o_style]

    base_plan = OptimizationResult(
        status=SolverStatus.FEASIBLE,
        engine_name="greedy",
        engine_mode=EngineMode.TASK2B_EXACT,
        trips=[base_trip],
        served_assignments=[OrderAssignment("O_BASE", "V1", 1)],
        deferred_orders=[
            make_deferred(o_fresh, DeferralReason.OTHER_CAPACITY_LIMIT),
            make_deferred(o_style, DeferralReason.OTHER_CAPACITY_LIMIT),
        ],
        metrics=PlanMetrics(
            total_orders=3, served_count=1, deferred_count=2,
            total_deferral_penalty=500.0, reefer_vehicles_used=1, van_vehicles_used=0,
            vehicles_used=1, trips_created=1, fresh_time_used_by_vehicle={"V1": 39.0},
            style_tech_time_used_by_vehicle={},
        ),
        validation=ValidationResult(True, [], 1, 2, 500.0),
        runtime_seconds=0.01,
        objective_value=500.0,
    )

    improved = targeted_cpsat_improve(
        base_plan=base_plan,
        orders=all_orders,
        vehicles=[vehicle],
        travel_data=travel,
        service_allowances=allowances,
        cfg=OptimizerConfig(targeted_cpsat_time_limit_s=2.0),
    )

    assert improved.validation.valid
    # Cannot place both O_FRESH and O_STYLE in Trip 2 (different brands)
    for tr in improved.trips:
        brands = {o.brand for o in [o_base, o_fresh, o_style] if o.order_ref in tr.order_refs}
        assert len(brands) == 1, f"Trip {tr.trip_number} mixed brands: {brands}"


def test_targeted_insertion_into_existing_trip():
    """
    Targeted CP-SAT: successfully inserts an eligible deferred order into an existing trip
    when capacity and time budget permit.
    """
    travel = [
        DistrictTravel(
            district="Colombo", depot=DEPOT, road_class="A",
            free_flow_kmh=50.0, depot_to_district_km=10.0,
            depot_to_district_freeflow_min=24.0,
            inter_stop_km=3.0, inter_stop_freeflow_min=8.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0)
    ]
    o1 = make_order("O1", Brand.FRESH, "Colombo", weight=100.0)
    o2 = make_order("O2", Brand.FRESH, "Colombo", weight=100.0)
    vehicle = make_vehicle("V1", weight_cap=500.0)

    trip1 = TripResult(
        vehicle_id="V1", trip_number=1, brand=Brand.FRESH, district="Colombo",
        order_refs=("O1",), stop_sequence=("O1",),
        total_weight_kg=100.0, total_volume_m3=1.0, trip_minutes=39.0,
        remaining_weight_kg=400.0, remaining_volume_m3=29.0,
    )
    p_o2 = defer_penalty(o2, OptimizerConfig())

    base_plan = OptimizationResult(
        status=SolverStatus.FEASIBLE,
        engine_name="greedy",
        engine_mode=EngineMode.TASK2B_EXACT,
        trips=[trip1],
        served_assignments=[OrderAssignment("O1", "V1", 1)],
        deferred_orders=[make_deferred(o2, DeferralReason.OTHER_CAPACITY_LIMIT)],
        metrics=PlanMetrics(
            total_orders=2, served_count=1, deferred_count=1,
            total_deferral_penalty=p_o2, reefer_vehicles_used=1, van_vehicles_used=0,
            vehicles_used=1, trips_created=1, fresh_time_used_by_vehicle={"V1": 39.0},
            style_tech_time_used_by_vehicle={},
        ),
        validation=ValidationResult(True, [], 1, 1, p_o2),
        runtime_seconds=0.01,
        objective_value=p_o2,
    )

    cfg_single = OptimizerConfig(max_trips_per_vehicle=1, valid_trip_numbers=frozenset({1}))

    improved = targeted_cpsat_improve(
        base_plan=base_plan,
        orders=[o1, o2],
        vehicles=[vehicle],
        travel_data=travel,
        service_allowances=allowances,
        cfg=cfg_single,
    )

    assert improved.validation.valid
    assert improved.metrics.served_count == 2
    assert improved.metrics.deferred_count == 0
    assert improved.cpsat_improvements_accepted == 1
    assert "O2" in improved.trips[0].order_refs
    assert abs(improved.trips[0].trip_minutes - 62.0) < 1e-4


def test_targeted_cpsat_rejects_candidate_violating_time_budget():
    """
    Targeted CP-SAT: candidate that would exceed time budget is rejected,
    preserving the valid incumbent plan.
    """
    travel = [
        DistrictTravel(
            district="Colombo", depot=DEPOT, road_class="A",
            free_flow_kmh=50.0, depot_to_district_km=10.0,
            depot_to_district_freeflow_min=100.0,  # 100 min outbound
            inter_stop_km=3.0, inter_stop_freeflow_min=50.0,   # 50 min inter
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=20.0)
    ]
    # Trip 1: 100 + 20 = 120 min.
    # Inserting O2: 120 + 50 + 20 = 190 min.
    # If Fresh budget is 150 min, O2 cannot fit.
    o1 = make_order("O1", Brand.FRESH, "Colombo", weight=50.0)
    o2 = make_order("O2", Brand.FRESH, "Colombo", weight=50.0)
    vehicle = make_vehicle("V1", weight_cap=500.0)

    trip1 = TripResult(
        vehicle_id="V1", trip_number=1, brand=Brand.FRESH, district="Colombo",
        order_refs=("O1",), stop_sequence=("O1",),
        total_weight_kg=50.0, total_volume_m3=1.0, trip_minutes=120.0,
        remaining_weight_kg=450.0, remaining_volume_m3=29.0,
    )
    p_o2 = defer_penalty(o2, OptimizerConfig())

    base_plan = OptimizationResult(
        status=SolverStatus.FEASIBLE,
        engine_name="greedy",
        engine_mode=EngineMode.TASK2B_EXACT,
        trips=[trip1],
        served_assignments=[OrderAssignment("O1", "V1", 1)],
        deferred_orders=[make_deferred(o2, DeferralReason.OTHER_CAPACITY_LIMIT)],
        metrics=PlanMetrics(
            total_orders=2, served_count=1, deferred_count=1,
            total_deferral_penalty=p_o2, reefer_vehicles_used=1, van_vehicles_used=0,
            vehicles_used=1, trips_created=1, fresh_time_used_by_vehicle={"V1": 120.0},
            style_tech_time_used_by_vehicle={},
        ),
        validation=ValidationResult(True, [], 1, 1, p_o2),
        runtime_seconds=0.01,
        objective_value=p_o2,
    )

    cfg = OptimizerConfig(
        fresh_daily_budget_min=150.0,  # 150 min cap prevents insertion (requires 190 min)
        max_trips_per_vehicle=1,
        valid_trip_numbers=frozenset({1}),
    )

    result = targeted_cpsat_improve(
        base_plan=base_plan,
        orders=[o1, o2],
        vehicles=[vehicle],
        travel_data=travel,
        service_allowances=allowances,
        cfg=cfg,
    )

    assert result.validation.valid
    # Must preserve base plan: O2 remains deferred
    assert result.metrics.served_count == 1
    assert result.metrics.deferred_count == 1
    assert result.cpsat_improvements_accepted == 0


def test_targeted_cpsat_fractional_capacity_boundary():
    """
    Verify conservative integer scaling handles fractional capacity boundaries:
    - Weight: 100.25 kg fits in 100.25 kg capacity.
    - Weight: 100.26 kg is rejected for 100.25 kg capacity.
    """
    travel = [
        DistrictTravel(
            district="Colombo", depot=DEPOT, road_class="A",
            free_flow_kmh=50.0, depot_to_district_km=10.0,
            depot_to_district_freeflow_min=24.0,
            inter_stop_km=3.0, inter_stop_freeflow_min=8.0,
        )
    ]
    allowances = [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0)
    ]
    o_over = make_order("O_OVER", Brand.FRESH, "Colombo", weight=100.26)
    v_cap = make_vehicle("V1", weight_cap=100.25)

    base_plan = OptimizationResult(
        status=SolverStatus.FEASIBLE,
        engine_name="greedy",
        engine_mode=EngineMode.TASK2B_EXACT,
        trips=[],
        served_assignments=[],
        deferred_orders=[make_deferred(o_over, DeferralReason.OTHER_CAPACITY_LIMIT)],
        metrics=PlanMetrics(1, 0, 1, 100.0, 0, 0, 0, 0, {}, {}),
        validation=ValidationResult(True, [], 0, 1, 100.0),
        runtime_seconds=0.01,
        objective_value=100.0,
    )

    res_over = targeted_cpsat_improve(
        base_plan=base_plan,
        orders=[o_over],
        vehicles=[v_cap],
        travel_data=travel,
        service_allowances=allowances,
    )
    assert res_over.validation.valid
    assert res_over.metrics.served_count == 0

    # Fits exactly: 100.25 kg
    o_fit = make_order("O_FIT", Brand.FRESH, "Colombo", weight=100.25)
    base_plan_fit = OptimizationResult(
        status=SolverStatus.FEASIBLE,
        engine_name="greedy",
        engine_mode=EngineMode.TASK2B_EXACT,
        trips=[],
        served_assignments=[],
        deferred_orders=[make_deferred(o_fit, DeferralReason.OTHER_CAPACITY_LIMIT)],
        metrics=PlanMetrics(1, 0, 1, 100.0, 0, 0, 0, 0, {}, {}),
        validation=ValidationResult(True, [], 0, 1, 100.0),
        runtime_seconds=0.01,
        objective_value=100.0,
    )

    res_fit = targeted_cpsat_improve(
        base_plan=base_plan_fit,
        orders=[o_fit],
        vehicles=[v_cap],
        travel_data=travel,
        service_allowances=allowances,
    )
    assert res_fit.validation.valid
    assert res_fit.metrics.served_count == 1
