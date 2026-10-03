"""
Waypoint Optimizer — Independent Validator
============================================
The Validator is the most safety-critical module in the system.

It independently checks EVERY hard constraint WITHOUT trusting the optimizer.
Every plan produced by any optimizer (Greedy, Hybrid, CP-SAT) must pass this
validator before being accepted.

IMPORTANT:
  - Passing validation means the plan is FEASIBLE.
  - It does NOT prove GLOBAL OPTIMALITY.
  - A plan that fails validation is ALWAYS rejected, regardless of its score.

Constraints checked (in order):
  ┌─────────────────────────────────────────────────────────────┐
  │ Coverage checks                                             │
  │  1. Every input order appears exactly once in the result   │
  │  2. Every order is either served or deferred               │
  │  3. Served orders have vehicle_id and trip_number          │
  │  4. Deferred orders have no vehicle_id or trip_number      │
  │  5. No order appears in both served and deferred           │
  ├─────────────────────────────────────────────────────────────┤
  │ Vehicle checks                                             │
  │  6. Referenced vehicle exists in fleet                     │
  │  7. Vehicle is available (not in_workshop)                 │
  │  8. Trip number is 1 or 2                                  │
  │  9. No vehicle has > 2 trips                               │
  │ 10. No order assigned twice                               │
  ├─────────────────────────────────────────────────────────────┤
  │ Trip hard constraints                                      │
  │ 11. Same brand within trip (HC1)                          │
  │ 12. Same district within trip (HC1)                       │
  │ 13. Chilled only on reefer (HC2)                          │
  │ 14. van_only only on van (HC3)                            │
  │ 15. Correct depot (HC4)                                   │
  │ 16. Weight capacity (HC6a)                                │
  │ 17. Volume capacity (HC6b)                                │
  ├─────────────────────────────────────────────────────────────┤
  │ Time budget checks                                         │
  │ 18. Correct trip-time calculation (formula check)         │
  │ 19. Fresh ≤ 270 minutes (per vehicle)                     │
  │ 20. Style+Tech ≤ 480 minutes (per vehicle)                │
  └─────────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Sequence

from waypoint_optimizer.config import (
    FRESH_DAILY_BUDGET_MIN,
    MAX_TRIPS_PER_VEHICLE,
    STYLE_TECH_DAILY_BUDGET_MIN,
    VALID_TRIP_NUMBERS,
    OptimizerConfig,
)
from waypoint_optimizer.domain import (
    DistrictTravel, Order, OrderAssignment, DeferredOrder,
    ServiceAllowance, TripResult, ValidationError, ValidationResult,
)
from waypoint_optimizer.enums import (
    Brand, TempRequirement, TempSpec, VehicleStatus, VehicleType,
    ParkingConstraint,
)
from waypoint_optimizer.objective import total_penalty
from waypoint_optimizer.trip_math import (
    build_allowance_index, build_travel_index,
    calculate_trip_minutes,
)


def validate(
    orders: Sequence[Order],
    vehicles_by_id: dict[str, "Vehicle"],   # imported lazily to avoid circular
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
    served_assignments: Sequence[OrderAssignment],
    deferred_orders: Sequence[DeferredOrder],
    trip_results: Sequence[TripResult],
    cfg: OptimizerConfig = OptimizerConfig(),
) -> ValidationResult:
    """
    Independently validate a complete allocation plan.

    This function does NOT trust the optimizer. It recomputes every metric
    from scratch using the raw input data.

    Args:
        orders:             All input orders for this run.
        vehicles_by_id:     Fleet dict: vehicle_id → Vehicle.
        travel_index:       Pre-built (district, depot) → DistrictTravel.
        allowance_index:    Pre-built (brand, dock_type) → service_allowance_min.
        served_assignments: List of OrderAssignment from the optimizer.
        deferred_orders:    List of DeferredOrder from the optimizer.
        trip_results:       List of TripResult from the optimizer.
        cfg:                OptimizerConfig for objective calculation.

    Returns:
        ValidationResult with valid=True only if ALL checks pass.
    """
    from waypoint_optimizer.domain import Vehicle  # avoid circular at module top

    errors: list[ValidationError] = []

    # ── 1. Authoritative Lookups & Input Order Uniqueness ────────────────────
    order_by_ref: dict[str, Order] = {}
    for o in orders:
        if o.order_ref in order_by_ref:
            errors.append(ValidationError(
                rule="INPUT_DUPLICATE_ORDER",
                detail=f"Input orders contain duplicate order_ref {o.order_ref!r}.",
                order_ref=o.order_ref,
            ))
        order_by_ref[o.order_ref] = o
    all_order_refs: set[str] = set(order_by_ref)

    # ── 2. Coverage & Duplicate Assignment / Deferral Checks ──────────────────
    seen_served_refs: set[str] = set()
    served_refs_list: list[str] = []
    for a in served_assignments:
        if a.order_ref in seen_served_refs:
            errors.append(ValidationError(
                rule="DUPLICATE_ASSIGNMENT",
                detail=f"Order {a.order_ref!r} appears multiple times in served_assignments.",
                order_ref=a.order_ref,
                vehicle_id=a.vehicle_id,
            ))
        seen_served_refs.add(a.order_ref)
        served_refs_list.append(a.order_ref)

    seen_deferred_refs: set[str] = set()
    deferred_refs_list: list[str] = []
    for d in deferred_orders:
        if d.order_ref in seen_deferred_refs:
            errors.append(ValidationError(
                rule="DUPLICATE_DEFERRED",
                detail=f"Order {d.order_ref!r} appears multiple times in deferred_orders.",
                order_ref=d.order_ref,
            ))
        seen_deferred_refs.add(d.order_ref)
        deferred_refs_list.append(d.order_ref)

    # Missing orders (neither served nor deferred)
    missing = all_order_refs - (seen_served_refs | seen_deferred_refs)
    for ref in sorted(missing):
        errors.append(ValidationError(
            rule="COVERAGE_MISSING",
            detail=f"Order {ref!r} is not present in served or deferred output.",
            order_ref=ref,
        ))

    # Extra orders (not in authoritative input)
    extra = (seen_served_refs | seen_deferred_refs) - all_order_refs
    for ref in sorted(extra):
        errors.append(ValidationError(
            rule="COVERAGE_EXTRA",
            detail=f"Order {ref!r} appears in plan output but was not in the authoritative input.",
            order_ref=ref,
        ))

    # Overlap (both served and deferred)
    overlap = seen_served_refs & seen_deferred_refs
    for ref in sorted(overlap):
        errors.append(ValidationError(
            rule="SERVED_AND_DEFERRED",
            detail=f"Order {ref!r} appears in both served_assignments and deferred_orders.",
            order_ref=ref,
        ))

    # Assignment vehicle and trip number validity
    for a in served_assignments:
        if not a.vehicle_id:
            errors.append(ValidationError(
                rule="SERVED_MISSING_VEHICLE",
                detail=f"Served order {a.order_ref!r} has an empty vehicle_id.",
                order_ref=a.order_ref,
            ))
        elif a.vehicle_id not in vehicles_by_id:
            errors.append(ValidationError(
                rule="VEHICLE_NOT_FOUND",
                detail=f"Served order {a.order_ref!r} references unknown vehicle {a.vehicle_id!r}.",
                order_ref=a.order_ref,
                vehicle_id=a.vehicle_id,
            ))

        valid_trips = getattr(cfg, "valid_trip_numbers", VALID_TRIP_NUMBERS)
        if a.trip_number not in valid_trips:
            errors.append(ValidationError(
                rule="SERVED_INVALID_TRIP_NUMBER",
                detail=f"Served order {a.order_ref!r} has trip_number={a.trip_number} "
                       f"(must be in {valid_trips}).",
                order_ref=a.order_ref,
                vehicle_id=a.vehicle_id,
            ))

    # ── 3. TripResult Structure, Keys & 1-to-1 Correspondence ─────────────────
    seen_trip_keys: set[tuple[str, int]] = set()
    trip_by_key: dict[tuple[str, int], TripResult] = {}
    order_trip_map: dict[str, list[tuple[str, int]]] = defaultdict(list)

    for tr in trip_results:
        key = (tr.vehicle_id, tr.trip_number)
        if key in seen_trip_keys:
            errors.append(ValidationError(
                rule="DUPLICATE_TRIP_KEY",
                detail=f"Duplicate TripResult found for vehicle {tr.vehicle_id!r} trip {tr.trip_number}.",
                vehicle_id=tr.vehicle_id,
            ))
        else:
            seen_trip_keys.add(key)
            trip_by_key[key] = tr

        for ref in tr.order_refs:
            order_trip_map[ref].append(key)

    # Check for order appearing in multiple trips
    for ref, trip_keys in sorted(order_trip_map.items()):
        if len(trip_keys) > 1:
            errors.append(ValidationError(
                rule="ORDER_IN_MULTIPLE_TRIPS",
                detail=f"Order {ref!r} appears in multiple trips: {trip_keys}.",
                order_ref=ref,
            ))

    # Check served_assignments match TripResult exact membership
    for a in served_assignments:
        key = (a.vehicle_id, a.trip_number)
        tr = trip_by_key.get(key)
        if tr is None or a.order_ref not in tr.order_refs:
            errors.append(ValidationError(
                rule="ASSIGNMENT_NOT_IN_TRIP",
                detail=f"Order {a.order_ref!r} is assigned to vehicle {a.vehicle_id!r} trip {a.trip_number}, "
                       f"but is not in that TripResult's order_refs.",
                order_ref=a.order_ref,
                vehicle_id=a.vehicle_id,
            ))

    # Check TripResult order_refs match served_assignments
    assignment_map = {a.order_ref: a for a in served_assignments}
    for tr in trip_results:
        for ref in tr.order_refs:
            a = assignment_map.get(ref)
            if a is None or a.vehicle_id != tr.vehicle_id or a.trip_number != tr.trip_number:
                errors.append(ValidationError(
                    rule="TRIP_ORDER_NOT_SERVED",
                    detail=f"Order {ref!r} is in TripResult ({tr.vehicle_id}, {tr.trip_number}) "
                           f"but has mismatched or missing served_assignment ({a}).",
                    order_ref=ref,
                    vehicle_id=tr.vehicle_id,
                ))

    # ── 4. Vehicle Availability & Fleet Trip Count Checks ────────────────────
    trips_by_vehicle: dict[str, list[TripResult]] = defaultdict(list)
    for tr in trip_results:
        trips_by_vehicle[tr.vehicle_id].append(tr)

    for vehicle_id, vtrips in trips_by_vehicle.items():
        if vehicle_id not in vehicles_by_id:
            errors.append(ValidationError(
                rule="VEHICLE_NOT_FOUND",
                detail=f"Vehicle {vehicle_id!r} referenced in TripResult does not exist in fleet.",
                vehicle_id=vehicle_id,
            ))
            continue

        vehicle = vehicles_by_id[vehicle_id]

        if vehicle.status == VehicleStatus.IN_WORKSHOP:
            errors.append(ValidationError(
                rule="VEHICLE_IN_WORKSHOP",
                detail=f"Vehicle {vehicle_id!r} is in_workshop and must not be allocated.",
                vehicle_id=vehicle_id,
            ))

        max_trips = getattr(cfg, "max_trips_per_vehicle", MAX_TRIPS_PER_VEHICLE)
        if len(vtrips) > max_trips:
            errors.append(ValidationError(
                rule="TOO_MANY_TRIPS",
                detail=f"Vehicle {vehicle_id!r} has {len(vtrips)} trips "
                       f"(max allowed is {max_trips}).",
                vehicle_id=vehicle_id,
            ))

        valid_trips = getattr(cfg, "valid_trip_numbers", VALID_TRIP_NUMBERS)
        for tr in vtrips:
            if tr.trip_number not in valid_trips:
                errors.append(ValidationError(
                    rule="INVALID_TRIP_NUMBER",
                    detail=f"Vehicle {vehicle_id!r} trip has invalid trip_number={tr.trip_number}.",
                    vehicle_id=vehicle_id,
                ))

    # ── 5. Per-Trip Constraints, Metadata, and Recomputed Metrics ─────────────
    for tr in trip_results:
        vehicle = vehicles_by_id.get(tr.vehicle_id)
        trip_orders = [order_by_ref[ref] for ref in tr.order_refs if ref in order_by_ref]

        # Stop sequence contract check: must be a permutation of order_refs
        if sorted(tr.stop_sequence) != sorted(tr.order_refs):
            errors.append(ValidationError(
                rule="INVALID_STOP_SEQUENCE",
                detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} stop_sequence "
                       f"does not match order_refs.",
                vehicle_id=tr.vehicle_id,
            ))

        # Finite metrics check
        for field_name, metric_val in [
            ("trip_minutes", tr.trip_minutes),
            ("total_weight_kg", tr.total_weight_kg),
            ("total_volume_m3", tr.total_volume_m3),
            ("remaining_weight_kg", tr.remaining_weight_kg),
            ("remaining_volume_m3", tr.remaining_volume_m3),
        ]:
            if not math.isfinite(metric_val):
                errors.append(ValidationError(
                    rule="NONFINITE_METRIC",
                    detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} has non-finite {field_name}: {metric_val}.",
                    vehicle_id=tr.vehicle_id,
                ))

        if not trip_orders:
            continue

        # Metadata consistency: TripResult brand/district must match its orders
        expected_brand = trip_orders[0].brand
        expected_district = trip_orders[0].district

        if tr.brand != expected_brand:
            errors.append(ValidationError(
                rule="TRIP_METADATA_MISMATCH",
                detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} reports brand={tr.brand.value!r} "
                       f"but its orders belong to brand={expected_brand.value!r}.",
                vehicle_id=tr.vehicle_id,
            ))
        if tr.district != expected_district:
            errors.append(ValidationError(
                rule="TRIP_METADATA_MISMATCH",
                detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} reports district={tr.district!r} "
                       f"but its orders belong to district={expected_district!r}.",
                vehicle_id=tr.vehicle_id,
            ))

        # Brand & District homogeneity (HC1)
        brands = {o.brand for o in trip_orders}
        if len(brands) > 1:
            errors.append(ValidationError(
                rule="MIXED_BRAND",
                detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} has mixed brands: {brands}.",
                vehicle_id=tr.vehicle_id,
            ))
        districts = {o.district for o in trip_orders}
        if len(districts) > 1:
            errors.append(ValidationError(
                rule="MIXED_DISTRICT",
                detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} has mixed districts: {districts}.",
                vehicle_id=tr.vehicle_id,
            ))

        if vehicle is not None:
            # Temperature (HC2)
            for o in trip_orders:
                if o.temp_requirement == TempRequirement.CHILLED and vehicle.temp != TempSpec.REEFER:
                    errors.append(ValidationError(
                        rule="TEMP_INCOMPATIBLE",
                        detail=f"Order {o.order_ref!r} requires chilled but vehicle {tr.vehicle_id!r} is ambient.",
                        order_ref=o.order_ref,
                        vehicle_id=tr.vehicle_id,
                    ))

            # Access (HC3)
            for o in trip_orders:
                if o.parking_constraint == ParkingConstraint.VAN_ONLY and vehicle.type != VehicleType.VAN:
                    errors.append(ValidationError(
                        rule="ACCESS_INCOMPATIBLE",
                        detail=f"Order {o.order_ref!r} requires van_only access but vehicle {tr.vehicle_id!r} is type {vehicle.type!r}.",
                        order_ref=o.order_ref,
                        vehicle_id=tr.vehicle_id,
                    ))

            # Depot (HC4)
            for o in trip_orders:
                if o.depot != vehicle.depot:
                    errors.append(ValidationError(
                        rule="DEPOT_MISMATCH",
                        detail=f"Order {o.order_ref!r} depot={o.depot!r} but vehicle {tr.vehicle_id!r} depot={vehicle.depot!r}.",
                        order_ref=o.order_ref,
                        vehicle_id=tr.vehicle_id,
                    ))

            # Weight Capacity (HC6a)
            calc_weight = sum(o.order_weight_kg for o in trip_orders)
            if calc_weight > vehicle.weight_cap_kg + 1e-6:
                errors.append(ValidationError(
                    rule="WEIGHT_OVERFLOW",
                    detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} weight {calc_weight:.1f} kg "
                           f"exceeds capacity {vehicle.weight_cap_kg:.1f} kg.",
                    vehicle_id=tr.vehicle_id,
                ))
            if math.isfinite(tr.total_weight_kg) and abs(tr.total_weight_kg - calc_weight) > 0.05:
                errors.append(ValidationError(
                    rule="WEIGHT_REPORT_MISMATCH",
                    detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} reports weight {tr.total_weight_kg:.2f} kg "
                           f"but validator computes {calc_weight:.2f} kg.",
                    vehicle_id=tr.vehicle_id,
                ))

            # Volume Capacity (HC6b)
            calc_volume = sum(o.order_volume_m3 for o in trip_orders)
            if calc_volume > vehicle.volume_cap_m3 + 1e-6:
                errors.append(ValidationError(
                    rule="VOLUME_OVERFLOW",
                    detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} volume {calc_volume:.3f} m³ "
                           f"exceeds capacity {vehicle.volume_cap_m3:.3f} m³.",
                    vehicle_id=tr.vehicle_id,
                ))
            if math.isfinite(tr.total_volume_m3) and abs(tr.total_volume_m3 - calc_volume) > 0.005:
                errors.append(ValidationError(
                    rule="VOLUME_REPORT_MISMATCH",
                    detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} reports volume {tr.total_volume_m3:.3f} m³ "
                           f"but validator computes {calc_volume:.3f} m³.",
                    vehicle_id=tr.vehicle_id,
                ))


        # Recomputed Trip Duration
        travel_key = (expected_district, trip_orders[0].depot)
        if travel_key not in travel_index:
            errors.append(ValidationError(
                rule="MISSING_TRAVEL_DATA",
                detail=f"No travel data for district={expected_district!r}, depot={trip_orders[0].depot!r}.",
                vehicle_id=tr.vehicle_id,
            ))
        else:
            calc_minutes = calculate_trip_minutes(trip_orders, travel_index[travel_key], allowance_index)
            if not math.isfinite(tr.trip_minutes) or abs(calc_minutes - tr.trip_minutes) > 0.05:
                errors.append(ValidationError(
                    rule="TRIP_TIME_MISMATCH",
                    detail=f"Vehicle {tr.vehicle_id!r} trip {tr.trip_number} reports {tr.trip_minutes} min "
                           f"but validator computes {calc_minutes:.2f} min.",
                    vehicle_id=tr.vehicle_id,
                ))

    # ── 6. Recomputed Vehicle Daily Time Budgets ──────────────────────────────
    for vehicle_id, vtrips in trips_by_vehicle.items():
        fresh_min = 0.0
        style_tech_min = 0.0

        for tr in vtrips:
            trip_orders = [order_by_ref[ref] for ref in tr.order_refs if ref in order_by_ref]
            if not trip_orders:
                continue

            travel_key = (trip_orders[0].district, trip_orders[0].depot)
            if travel_key not in travel_index:
                continue
            t_min = calculate_trip_minutes(trip_orders, travel_index[travel_key], allowance_index)

            brand = trip_orders[0].brand
            if brand == Brand.FRESH:
                fresh_min += t_min
            elif brand in (Brand.STYLE, Brand.TECH):
                style_tech_min += t_min

        if fresh_min > cfg.fresh_daily_budget_min + 1e-6:
            errors.append(ValidationError(
                rule="FRESH_BUDGET_EXCEEDED",
                detail=f"Vehicle {vehicle_id!r} Fresh time {fresh_min:.1f} min "
                       f"exceeds {cfg.fresh_daily_budget_min} min budget.",
                vehicle_id=vehicle_id,
            ))

        if style_tech_min > cfg.style_tech_daily_budget_min + 1e-6:
            errors.append(ValidationError(
                rule="STYLE_TECH_BUDGET_EXCEEDED",
                detail=f"Vehicle {vehicle_id!r} Style+Tech time {style_tech_min:.1f} min "
                       f"exceeds {cfg.style_tech_daily_budget_min} min budget.",
                vehicle_id=vehicle_id,
            ))

    # ── Summary Metrics ───────────────────────────────────────────────────────
    deferred_order_objects = [
        order_by_ref[d.order_ref]
        for d in deferred_orders
        if d.order_ref in order_by_ref
    ]
    penalty = total_penalty(deferred_order_objects, cfg)

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        served_count=len(seen_served_refs - extra - overlap),
        deferred_count=len(seen_deferred_refs - extra - overlap),
        total_deferral_penalty=penalty,
    )
