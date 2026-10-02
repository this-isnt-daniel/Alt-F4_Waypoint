"""
Waypoint Optimizer — Compatibility Module
==========================================
Small pure functions implementing each official hard constraint.

Every function is independently testable and has a clear docstring citing
the specific official rule it implements.

OFFICIAL HARD CONSTRAINTS IMPLEMENTED HERE:
  HC2  — Temperature compatibility (chilled → reefer only)
  HC3  — Access / parking compatibility (van_only → van only)
  HC4  — Home depot matching
  HC1  — Same brand + district per trip (trip-level check)
  HC6  — Weight and volume capacity per trip
  HC7  — Max 2 trips per vehicle
  HC2b — Reefer time-budget check (fresh / style+tech)

is_vehicle_compatible()  — checks HC2, HC3, HC4 for a (vehicle, order) pair
can_add_order_to_trip()  — checks HC1, HC6, and time budgets for insertion
"""
from __future__ import annotations

from typing import Sequence

from waypoint_optimizer.config import (
    FRESH_DAILY_BUDGET_MIN,
    MAX_TRIPS_PER_VEHICLE,
    STYLE_TECH_DAILY_BUDGET_MIN,
    VALID_TRIP_NUMBERS,
    OptimizerConfig,
)
from waypoint_optimizer.domain import (
    DistrictTravel, Order, ServiceAllowance, Trip, Vehicle,
)
from waypoint_optimizer.enums import (
    Brand, TempRequirement, TempSpec, VehicleStatus, VehicleType,
    ParkingConstraint,
)
from waypoint_optimizer.trip_math import (
    build_allowance_index, build_travel_index,
    calculate_trip_minutes, vehicle_fresh_time, vehicle_style_tech_time,
)


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle × Order compatibility (HC2, HC3, HC4)
# ──────────────────────────────────────────────────────────────────────────────

def check_temperature_compatibility(order: Order, vehicle: Vehicle) -> str | None:
    """
    HC2 — Temperature constraint.

    If order.temp_requirement == chilled, vehicle.temp MUST == reefer.
    A reefer vehicle MAY carry ambient orders.
    An ambient vehicle MUST NOT carry chilled orders.

    Returns None if compatible, or a human-readable error string.
    """
    if (
        order.temp_requirement == TempRequirement.CHILLED
        and vehicle.temp != TempSpec.REEFER
    ):
        return (
            f"order {order.order_ref!r} requires chilled/reefer transport but "
            f"vehicle {vehicle.vehicle_id!r} is ambient-only."
        )
    return None


def check_access_compatibility(order: Order, vehicle: Vehicle) -> str | None:
    """
    HC3 — Access / parking constraint.

    If order.parking_constraint == van_only, vehicle.type MUST == van.

    Note: parking_constraint == mall_dock is a different concept from
    dock_type == mall_bay. They must NOT be conflated.

    Returns None if compatible, or a human-readable error string.
    """
    if (
        order.parking_constraint == ParkingConstraint.VAN_ONLY
        and vehicle.type != VehicleType.VAN
    ):
        return (
            f"order {order.order_ref!r} requires van-only access but "
            f"vehicle {vehicle.vehicle_id!r} is type {vehicle.type!r}."
        )
    return None


def check_depot_compatibility(order: Order, vehicle: Vehicle) -> str | None:
    """
    HC4 — Home depot matching.

    vehicle.depot MUST equal order.depot.

    Returns None if compatible, or a human-readable error string.
    """
    if order.depot != vehicle.depot:
        return (
            f"order {order.order_ref!r} belongs to depot {order.depot!r} but "
            f"vehicle {vehicle.vehicle_id!r} is based at {vehicle.depot!r}."
        )
    return None


def check_vehicle_available(vehicle: Vehicle) -> str | None:
    """
    HC — Vehicle availability.

    Vehicles with status == in_workshop must NEVER be allocated.

    Returns None if available, or a human-readable error string.
    """
    if vehicle.status == VehicleStatus.IN_WORKSHOP:
        return f"vehicle {vehicle.vehicle_id!r} is in_workshop and cannot be allocated."
    return None


def is_vehicle_compatible(order: Order, vehicle: Vehicle) -> tuple[bool, list[str]]:
    """
    Combined vehicle × order compatibility check (HC2, HC3, HC4, availability).

    Returns:
        (True, [])            — vehicle is compatible with this order
        (False, [reasons])    — vehicle is incompatible; reasons list non-empty
    """
    reasons: list[str] = []

    err = check_vehicle_available(vehicle)
    if err:
        reasons.append(err)

    err = check_temperature_compatibility(order, vehicle)
    if err:
        reasons.append(err)

    err = check_access_compatibility(order, vehicle)
    if err:
        reasons.append(err)

    err = check_depot_compatibility(order, vehicle)
    if err:
        reasons.append(err)

    return (len(reasons) == 0, reasons)


# ──────────────────────────────────────────────────────────────────────────────
# Trip-level compatibility (HC1, HC6, time budgets)
# ──────────────────────────────────────────────────────────────────────────────

def check_brand_district_consistency(trip: Trip, order: Order) -> str | None:
    """
    HC1 — Same brand and district within a trip.

    All orders in a trip must share exactly ONE brand and ONE district.

    Returns None if consistent, or a human-readable error string.
    """
    if trip.brand != order.brand:
        return (
            f"order {order.order_ref!r} has brand {order.brand!r} but trip "
            f"({trip.vehicle_id}, {trip.trip_number}) is brand {trip.brand!r}."
        )
    if trip.district != order.district:
        return (
            f"order {order.order_ref!r} is in district {order.district!r} but trip "
            f"({trip.vehicle_id}, {trip.trip_number}) serves district {trip.district!r}."
        )
    return None


def check_weight_capacity(trip: Trip, order: Order, vehicle: Vehicle) -> str | None:
    """
    HC6a — Weight capacity.

    sum(order_weight_kg) for all trip orders (including the candidate) must
    be ≤ vehicle.weight_cap_kg.

    Returns None if within capacity, or a human-readable error string.
    """
    new_weight = trip.total_weight_kg + order.order_weight_kg
    if new_weight > vehicle.weight_cap_kg:
        return (
            f"adding order {order.order_ref!r} ({order.order_weight_kg} kg) to trip "
            f"({trip.vehicle_id}, {trip.trip_number}) would give {new_weight:.1f} kg, "
            f"exceeding weight capacity of {vehicle.weight_cap_kg} kg."
        )
    return None


def check_volume_capacity(trip: Trip, order: Order, vehicle: Vehicle) -> str | None:
    """
    HC6b — Volume capacity.

    sum(order_volume_m3) ≤ vehicle.volume_cap_m3.

    Returns None if within capacity, or a human-readable error string.
    """
    new_volume = trip.total_volume_m3 + order.order_volume_m3
    if new_volume > vehicle.volume_cap_m3:
        return (
            f"adding order {order.order_ref!r} ({order.order_volume_m3} m³) to trip "
            f"({trip.vehicle_id}, {trip.trip_number}) would give {new_volume:.3f} m³, "
            f"exceeding volume capacity of {vehicle.volume_cap_m3} m³."
        )
    return None


def check_fresh_time_budget(
    candidate_trips: list[Trip],
    order: Order,
    trip_to_modify: Trip,
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
    budget_min: float = FRESH_DAILY_BUDGET_MIN,
) -> str | None:
    """
    HC — Fresh daily time budget.

    If order.brand == FRESH, adding it must keep total Fresh trip time ≤ budget_min.

    Simulates inserting the order into trip_to_modify and recalculates the
    total Fresh time across all candidate_trips for that vehicle.

    Returns None if within budget, or a human-readable error string.
    """
    if order.brand != Brand.FRESH:
        return None

    total_fresh = 0.0
    for trip in candidate_trips:
        if trip is trip_to_modify:
            if order in trip.orders:
                simulated_orders = list(trip.orders)
            else:
                simulated_orders = list(trip.orders) + [order]
        else:
            simulated_orders = list(trip.orders)

        if not simulated_orders:
            continue

        if trip.brand != Brand.FRESH:
            continue

        travel = travel_index.get((trip.district, simulated_orders[0].depot))
        if travel is None:
            continue
        total_fresh += calculate_trip_minutes(simulated_orders, travel, allowance_index)

    if total_fresh > budget_min:
        return (
            f"adding order {order.order_ref!r} (brand=fresh) would bring "
            f"total Fresh time to {total_fresh:.1f} min, exceeding "
            f"{budget_min} min budget."
        )
    return None


def check_style_tech_time_budget(
    candidate_trips: list[Trip],
    order: Order,
    trip_to_modify: Trip,
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
    budget_min: float = STYLE_TECH_DAILY_BUDGET_MIN,
) -> str | None:
    """
    HC — Style+Tech combined daily time budget.

    If order.brand in (STYLE, TECH), adding it must keep total Style+Tech
    trip time ≤ budget_min.

    Returns None if within budget, or a human-readable error string.
    """
    if order.brand not in (Brand.STYLE, Brand.TECH):
        return None

    total_st = 0.0
    for trip in candidate_trips:
        if trip is trip_to_modify:
            if order in trip.orders:
                simulated_orders = list(trip.orders)
            else:
                simulated_orders = list(trip.orders) + [order]
        else:
            simulated_orders = list(trip.orders)

        if not simulated_orders:
            continue

        if trip.brand not in (Brand.STYLE, Brand.TECH):
            continue

        travel = travel_index.get((trip.district, simulated_orders[0].depot))
        if travel is None:
            continue
        total_st += calculate_trip_minutes(simulated_orders, travel, allowance_index)

    if total_st > budget_min:
        return (
            f"adding order {order.order_ref!r} (brand={order.brand.value!r}) would bring "
            f"total Style+Tech time to {total_st:.1f} min, exceeding "
            f"{budget_min} min budget."
        )
    return None


def can_add_order_to_trip(
    order: Order,
    trip: Trip,
    vehicle: Vehicle,
    all_vehicle_trips: list[Trip],
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
    cfg: OptimizerConfig | None = None,
) -> tuple[bool, list[str]]:
    """
    Check whether an order can be added to an existing trip.

    Checks in order:
      1. HC1  — same brand and district
      2. HC6a — weight capacity
      3. HC6b — volume capacity
      4. Time budget (Fresh or Style+Tech)

    Vehicle × order compatibility (HC2, HC3, HC4) must already have been
    checked before calling this function.

    Args:
        order:             The order to insert.
        trip:              The trip to insert into.
        vehicle:           The vehicle operating this trip.
        all_vehicle_trips: All trips currently assigned to this vehicle
                           (used for budget calculations).
        travel_index:      Pre-built travel lookup.
        allowance_index:   Pre-built service-allowance lookup.
        cfg:               Optional OptimizerConfig with customized rules/budgets.

    Returns:
        (True, [])         — insertion is feasible
        (False, [reasons]) — insertion is infeasible; reasons list non-empty
    """
    reasons: list[str] = []

    fresh_budget = cfg.fresh_daily_budget_min if cfg is not None else FRESH_DAILY_BUDGET_MIN
    style_tech_budget = cfg.style_tech_daily_budget_min if cfg is not None else STYLE_TECH_DAILY_BUDGET_MIN

    checks = [
        check_brand_district_consistency(trip, order),
        check_weight_capacity(trip, order, vehicle),
        check_volume_capacity(trip, order, vehicle),
        check_fresh_time_budget(
            all_vehicle_trips, order, trip, travel_index, allowance_index,
            budget_min=fresh_budget,
        ),
        check_style_tech_time_budget(
            all_vehicle_trips, order, trip, travel_index, allowance_index,
            budget_min=style_tech_budget,
        ),
    ]

    for result in checks:
        if result is not None:
            reasons.append(result)

    return (len(reasons) == 0, reasons)


def can_open_new_trip(
    order: Order,
    vehicle: Vehicle,
    existing_trips: list[Trip],
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
    cfg: OptimizerConfig | None = None,
) -> tuple[bool, list[str]]:
    """
    Check whether a new trip can be opened on a vehicle for this order.

    Rules:
      - Vehicle must not already have max_trips trips (HC7).
      - Target trip number must be in supported valid_trip_numbers.
      - Vehicle must be compatible with the order (HC2, HC3, HC4).
      - The single-order trip time must fit within the relevant budget.

    Returns:
        (True, [])      — new trip can be opened
        (False, [...])  — cannot open; reasons list non-empty
    """
    reasons: list[str] = []

    max_trips = cfg.max_trips_per_vehicle if cfg is not None else MAX_TRIPS_PER_VEHICLE
    valid_trip_numbers = cfg.valid_trip_numbers if (cfg is not None and cfg.valid_trip_numbers) else VALID_TRIP_NUMBERS

    # HC7 — max trips
    if len(existing_trips) >= max_trips:
        reasons.append(
            f"vehicle {vehicle.vehicle_id!r} already has "
            f"{len(existing_trips)} trips (max {max_trips})."
        )
        return False, reasons

    # Supported trip number check
    trip_number = len(existing_trips) + 1
    if trip_number not in valid_trip_numbers:
        reasons.append(
            f"trip number {trip_number} for vehicle {vehicle.vehicle_id!r} is not in "
            f"valid_trip_numbers ({sorted(valid_trip_numbers)})."
        )
        return False, reasons

    # HC2, HC3, HC4
    compat_ok, compat_reasons = is_vehicle_compatible(order, vehicle)
    if not compat_ok:
        return False, compat_reasons

    # HC6a, HC6b — weight and volume capacity for the new trip
    if order.order_weight_kg > vehicle.weight_cap_kg:
        reasons.append(
            f"order {order.order_ref!r} weight {order.order_weight_kg:.1f} kg exceeds "
            f"vehicle {vehicle.vehicle_id!r} weight capacity of {vehicle.weight_cap_kg:.1f} kg."
        )
        return False, reasons

    if order.order_volume_m3 > vehicle.volume_cap_m3:
        reasons.append(
            f"order {order.order_ref!r} volume {order.order_volume_m3:.3f} m³ exceeds "
            f"vehicle {vehicle.vehicle_id!r} volume capacity of {vehicle.volume_cap_m3:.3f} m³."
        )
        return False, reasons

    # Time budget check for a single-order trip
    simulated_trip = Trip(
        vehicle_id=vehicle.vehicle_id,
        trip_number=trip_number,
        brand=order.brand,
        district=order.district,
        orders=[order],
    )
    all_trips = existing_trips + [simulated_trip]

    travel = travel_index.get((order.district, order.depot))
    if travel is None:
        reasons.append(
            f"No travel data for district={order.district!r}, depot={order.depot!r}."
        )
        return False, reasons

    fresh_budget = cfg.fresh_daily_budget_min if cfg is not None else FRESH_DAILY_BUDGET_MIN
    style_tech_budget = cfg.style_tech_daily_budget_min if cfg is not None else STYLE_TECH_DAILY_BUDGET_MIN

    if order.brand == Brand.FRESH:
        err = check_fresh_time_budget(
            all_trips, order, simulated_trip, travel_index, allowance_index,
            budget_min=fresh_budget,
        )
        if err:
            reasons.append(err)
    elif order.brand in (Brand.STYLE, Brand.TECH):
        err = check_style_tech_time_budget(
            all_trips, order, simulated_trip, travel_index, allowance_index,
            budget_min=style_tech_budget,
        )
        if err:
            reasons.append(err)

    return (len(reasons) == 0, reasons)


# ──────────────────────────────────────────────────────────────────────────────
# Scarcity diagnostics (used by Greedy portfolio, not hard constraints)
# ──────────────────────────────────────────────────────────────────────────────

def count_compatible_vehicles(order: Order, vehicles: Sequence[Vehicle]) -> int:
    """
    Return the number of available vehicles that are compatible with this order
    (HC2, HC3, HC4 — excludes trip-level and time-budget checks).

    Used by the scarcity_first Greedy ordering strategy.
    This is a PLANNING DIAGNOSTIC, not a hard feasibility check.
    """
    count = 0
    for v in vehicles:
        ok, _ = is_vehicle_compatible(order, v)
        if ok:
            count += 1
    return count
