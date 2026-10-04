"""
Waypoint Optimizer — Single Greedy Allocator
==============================================
A simple deterministic Greedy allocator. It is:
  1. A useful standalone baseline
  2. A debugging reference
  3. The foundation for the Multi-start portfolio
  4. A fallback if CP-SAT fails

The Greedy algorithm:
  For each order (in a configurable sort order):
    1. Try to insert it into an existing compatible trip.
    2. If no compatible trip exists, try to open a new trip on a
       compatible vehicle.
    3. If neither is possible, defer the order with a reason code.

IMPORTANT:
  - All candidates produced by Greedy are validated by the independent
    Validator before being returned.
  - A candidate that fails validation is NEVER accepted regardless of score.
  - The Greedy ordering strategy affects which orders are placed first, but
    ALL valid candidates use the SAME objective function for comparison.
    Different orderings are SEARCH STRATEGIES, not different business policies.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, Sequence

from waypoint_optimizer.compatibility import (
    can_add_order_to_trip,
    can_open_new_trip,
    count_compatible_vehicles,
    is_vehicle_compatible,
)
from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.domain import (
    DistrictTravel, DeferredOrder, Order, OrderAssignment,
    PlanMetrics, ServiceAllowance, Trip, TripResult, Vehicle,
    OptimizationResult, ValidationResult,
)
from waypoint_optimizer.enums import (
    Brand, DeferralReason, EngineMode, SolverStatus, TempSpec, VehicleType,
)
from waypoint_optimizer.explanations import classify_deferral, make_deferred
from waypoint_optimizer.objective import defer_penalty, plan_score
from waypoint_optimizer.trip_math import (
    build_allowance_index, build_travel_index, calculate_trip_minutes,
)
from waypoint_optimizer.validator import validate


# ──────────────────────────────────────────────────────────────────────────────
# Greedy core
# ──────────────────────────────────────────────────────────────────────────────

def _build_trip_result(
    trip: Trip,
    vehicle: Vehicle,
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
) -> TripResult:
    """Convert a mutable Trip into an immutable TripResult."""
    if not trip.orders:
        raise ValueError(f"Trip {trip.vehicle_id}:{trip.trip_number} has no orders.")

    depot = trip.orders[0].depot
    travel = travel_index[(trip.district, depot)]
    minutes = calculate_trip_minutes(trip.orders, travel, allowance_index)

    # Deterministic stop sequence: sorted by order_ref
    sorted_refs = tuple(sorted(o.order_ref for o in trip.orders))

    return TripResult(
        vehicle_id=trip.vehicle_id,
        trip_number=trip.trip_number,
        brand=trip.brand,
        district=trip.district,
        order_refs=sorted_refs,
        stop_sequence=sorted_refs,  # deterministic placeholder; NOT route-optimal
        total_weight_kg=trip.total_weight_kg,
        total_volume_m3=trip.total_volume_m3,
        trip_minutes=minutes,
        remaining_weight_kg=vehicle.weight_cap_kg - trip.total_weight_kg,
        remaining_volume_m3=vehicle.volume_cap_m3 - trip.total_volume_m3,
    )


def _build_plan_metrics(
    trip_results: list[TripResult],
    served_assignments: list[OrderAssignment],
    deferred_orders: list[DeferredOrder],
    all_orders: list[Order],
    vehicles_by_id: dict[str, Vehicle],
    cfg: OptimizerConfig,
) -> PlanMetrics:
    """Build PlanMetrics by aggregating trip results."""
    order_by_ref = {o.order_ref: o for o in all_orders}
    vehicles_used: set[str] = {tr.vehicle_id for tr in trip_results}

    reefer_used = sum(
        1 for vid in vehicles_used
        if vid in vehicles_by_id and vehicles_by_id[vid].temp == TempSpec.REEFER
    )
    van_used = sum(
        1 for vid in vehicles_used
        if vid in vehicles_by_id and vehicles_by_id[vid].type == VehicleType.VAN
    )

    # Time budget usage per vehicle
    fresh_time: dict[str, float] = defaultdict(float)
    style_tech_time: dict[str, float] = defaultdict(float)
    for tr in trip_results:
        if tr.brand == Brand.FRESH:
            fresh_time[tr.vehicle_id] += tr.trip_minutes
        elif tr.brand in (Brand.STYLE, Brand.TECH):
            style_tech_time[tr.vehicle_id] += tr.trip_minutes

    deferred_objs = [
        order_by_ref[d.order_ref]
        for d in deferred_orders
        if d.order_ref in order_by_ref
    ]
    penalty = sum(defer_penalty(o, cfg) for o in deferred_objs)

    return PlanMetrics(
        total_orders=len(all_orders),
        served_count=len(served_assignments),
        deferred_count=len(deferred_orders),
        total_deferral_penalty=penalty,
        reefer_vehicles_used=reefer_used,
        van_vehicles_used=van_used,
        vehicles_used=len(vehicles_used),
        trips_created=len(trip_results),
        fresh_time_used_by_vehicle=dict(fresh_time),
        style_tech_time_used_by_vehicle=dict(style_tech_time),
    )


def _attempt_deferral_classify(
    order: Order,
    compatible_vehicles: list[Vehicle],
    vehicles_by_id: dict[str, Vehicle],
    trips_by_vehicle: dict[str, list[Trip]],
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
    cfg: OptimizerConfig,
) -> DeferredOrder:
    """
    Attempt to classify the most specific deferral reason for this order.
    """
    if not compatible_vehicles:
        return make_deferred(order, DeferralReason.NO_COMPATIBLE_VEHICLE)

    # Check if specifically reefer or van vehicles are exhausted
    from waypoint_optimizer.enums import TempRequirement
    needs_reefer = order.temp_requirement == TempRequirement.CHILLED
    needs_van = order.parking_constraint.value == "van_only"

    reefer_exhausted = False
    van_exhausted = False
    weight_full = True
    volume_full = True
    trip_limit = True
    fresh_budget_full = False
    st_budget_full = False

    for v in compatible_vehicles:
        existing = trips_by_vehicle.get(v.vehicle_id, [])
        can_open, reasons = can_open_new_trip(
            order, v, existing, travel_index, allowance_index, cfg=cfg,
        )
        if can_open:
            # If can_open says True but we still deferred, this shouldn't happen
            # (the Greedy must have placed it). So classify generically.
            return make_deferred(order, DeferralReason.OTHER_CAPACITY_LIMIT)

        # Analyze reasons
        reasons_str = " ".join(reasons)
        if "trips" in reasons_str:
            trip_limit = True
        else:
            trip_limit = False  # at least one vehicle could open a trip
        if "weight" in reasons_str:
            weight_full = True
        else:
            weight_full = False
        if "volume" in reasons_str:
            volume_full = True
        if str(int(cfg.fresh_daily_budget_min)) in reasons_str or "fresh time" in reasons_str.lower():
            fresh_budget_full = True
        if str(int(cfg.style_tech_daily_budget_min)) in reasons_str or "style" in reasons_str.lower():
            st_budget_full = True

    if needs_reefer:
        reefer_exhausted = True
    if needs_van:
        van_exhausted = True

    reason = classify_deferral(
        order,
        no_compatible_vehicle=False,
        reefer_exhausted=reefer_exhausted and needs_reefer,
        van_exhausted=van_exhausted and needs_van,
        weight_full=weight_full,
        volume_full=volume_full,
        trip_limit_reached=trip_limit,
        fresh_budget_full=fresh_budget_full,
        style_tech_budget_full=st_budget_full,
    )
    return make_deferred(order, reason)


def validate_greedy_config(cfg: OptimizerConfig) -> None:
    """
    Validate that configuration options are supported by the greedy solver assumptions.
    Rejects unsupported configurations explicitly.
    """
    if cfg.max_trips_per_vehicle < 1:
        raise ValueError(f"max_trips_per_vehicle must be >= 1, got {cfg.max_trips_per_vehicle}.")
    if cfg.max_trips_per_vehicle > 2:
        raise ValueError(
            f"Greedy solver only supports up to 2 trips per vehicle; "
            f"got max_trips_per_vehicle={cfg.max_trips_per_vehicle}."
        )
    if not cfg.valid_trip_numbers:
        raise ValueError("valid_trip_numbers cannot be empty.")
    if 1 not in cfg.valid_trip_numbers:
        raise ValueError(
            f"Greedy solver requires trip number 1 in valid_trip_numbers; "
            f"got {cfg.valid_trip_numbers}."
        )
    unsupported_trips = set(cfg.valid_trip_numbers) - {1, 2}
    if unsupported_trips:
        raise ValueError(
            f"Greedy solver does not support trip numbers beyond {{1, 2}}; "
            f"got unsupported trip numbers {unsupported_trips}."
        )
    if cfg.fresh_daily_budget_min <= 0:
        raise ValueError(f"fresh_daily_budget_min must be positive, got {cfg.fresh_daily_budget_min}.")
    if cfg.style_tech_daily_budget_min <= 0:
        raise ValueError(f"style_tech_daily_budget_min must be positive, got {cfg.style_tech_daily_budget_min}.")


def greedy_allocate(
    orders: list[Order],
    vehicles: list[Vehicle],
    travel_data: list[DistrictTravel],
    service_allowances: list[ServiceAllowance],
    order_sequence: list[Order] | None = None,
    cfg: OptimizerConfig = OptimizerConfig(),
    engine_mode: EngineMode = EngineMode.TASK2B_EXACT,
) -> OptimizationResult:
    """
    Single-pass deterministic Greedy allocator.

    Args:
        orders:             All input orders.
        vehicles:           Fleet of vehicles.
        travel_data:        District travel records.
        service_allowances: Service time allowances.
        order_sequence:     Explicit ordering of orders. If None, uses input order.
        cfg:                Optimizer configuration.
        engine_mode:        Task2B exact or Hackathon operational mode.

    Returns:
        OptimizationResult (always validated before returning).
    """
    t_start = time.perf_counter()
    validate_greedy_config(cfg)

    # ── Precompute indices ────────────────────────────────────────────────────
    travel_index = build_travel_index(travel_data)
    allowance_index = build_allowance_index(service_allowances)
    vehicles_by_id: dict[str, Vehicle] = {v.vehicle_id: v for v in vehicles}

    # Available vehicles only
    available_vehicles = [v for v in vehicles if v.is_available]

    # ── State: trips per vehicle ──────────────────────────────────────────────
    # trips_by_vehicle: vehicle_id → list[Trip] (mutable, ordered)
    trips_by_vehicle: dict[str, list[Trip]] = defaultdict(list)

    served_assignments: list[OrderAssignment] = []
    deferred_orders: list[DeferredOrder] = []

    sequence = order_sequence if order_sequence is not None else orders

    # ── Main allocation loop ─────────────────────────────────────────────────
    for order in sequence:
        placed = False

        # ── Step 1: Try inserting into an existing compatible trip ────────────
        for vehicle in available_vehicles:
            existing_trips = trips_by_vehicle[vehicle.vehicle_id]
            compat_ok, _ = is_vehicle_compatible(order, vehicle)
            if not compat_ok:
                continue

            for trip in existing_trips:
                if trip.brand != order.brand or trip.district != order.district:
                    continue

                can_add, _ = can_add_order_to_trip(
                    order, trip, vehicle, existing_trips,
                    travel_index, allowance_index,
                    cfg=cfg,
                )
                if can_add:
                    trip.orders.append(order)
                    served_assignments.append(OrderAssignment(
                        order_ref=order.order_ref,
                        vehicle_id=vehicle.vehicle_id,
                        trip_number=trip.trip_number,
                    ))
                    placed = True
                    break

            if placed:
                break

        if placed:
            continue

        # ── Step 2: Try opening a new trip on a compatible vehicle ────────────
        for vehicle in available_vehicles:
            existing_trips = trips_by_vehicle[vehicle.vehicle_id]
            can_open, _ = can_open_new_trip(
                order, vehicle, existing_trips, travel_index, allowance_index,
                cfg=cfg,
            )
            if can_open:
                trip_number = len(existing_trips) + 1
                new_trip = Trip(
                    vehicle_id=vehicle.vehicle_id,
                    trip_number=trip_number,
                    brand=order.brand,
                    district=order.district,
                    orders=[order],
                )
                trips_by_vehicle[vehicle.vehicle_id].append(new_trip)
                served_assignments.append(OrderAssignment(
                    order_ref=order.order_ref,
                    vehicle_id=vehicle.vehicle_id,
                    trip_number=trip_number,
                ))
                placed = True
                break

        if placed:
            continue

        # ── Step 3: Defer with explanation ────────────────────────────────────
        compatible_vehicles = [
            v for v in available_vehicles
            if is_vehicle_compatible(order, v)[0]
        ]
        deferred = _attempt_deferral_classify(
            order, compatible_vehicles, vehicles_by_id,
            trips_by_vehicle, travel_index, allowance_index, cfg,
        )
        deferred_orders.append(deferred)

    # ── Build output ──────────────────────────────────────────────────────────
    trip_results: list[TripResult] = []
    for vehicle_id, trips in trips_by_vehicle.items():
        vehicle = vehicles_by_id[vehicle_id]
        for trip in trips:
            if trip.orders:
                trip_results.append(
                    _build_trip_result(trip, vehicle, travel_index, allowance_index)
                )

    # Sort trip_results deterministically
    trip_results.sort(key=lambda tr: (tr.vehicle_id, tr.trip_number))

    metrics = _build_plan_metrics(
        trip_results, served_assignments, deferred_orders,
        orders, vehicles_by_id, cfg,
    )

    # ── Independent validation ────────────────────────────────────────────────
    validation = validate(
        orders=orders,
        vehicles_by_id=vehicles_by_id,
        travel_index=travel_index,
        allowance_index=allowance_index,
        served_assignments=served_assignments,
        deferred_orders=deferred_orders,
        trip_results=trip_results,
        cfg=cfg,
    )

    penalty = metrics.total_deferral_penalty
    runtime = time.perf_counter() - t_start

    return OptimizationResult(
        status=SolverStatus.FEASIBLE,
        engine_name="greedy",
        engine_mode=engine_mode,
        trips=trip_results,
        served_assignments=served_assignments,
        deferred_orders=deferred_orders,
        metrics=metrics,
        validation=validation,
        runtime_seconds=runtime,
        objective_value=penalty,
        cpsat_improvements_accepted=None,
        cpsat_solver_status=None,
    )
