"""
Waypoint Optimizer — Trip Math
================================
Official Task 2B trip-time formula and related calculations.

OFFICIAL FORMULA (source: Task 2B specification):
─────────────────────────────────────────────────
  trip_minutes =
      outbound_travel                            ← depot_to_district_freeflow_min (once per trip)
    + inter_stop_travel                          ← inter_stop_freeflow_min × (n_orders − 1)
    + total_handling_time                        ← Σ service_allowance_min per order

KEY RULES (from the specification, enforced here):
  1. Outbound is added exactly ONCE per trip.
  2. Inter-stop journeys = (number_of_orders − 1), using ORDER COUNT not outlet count.
  3. NO return journey is added. The stated time budgets already account for return.
     Adding return travel would be a formula violation.
  4. Handling time is looked up from ServiceAllowance keyed by (brand, dock_type).

TEAM-DEFINED extensions (fuel, ETA) live in the operational/ package, NOT here.
"""
from __future__ import annotations

import math
from typing import Sequence

from waypoint_optimizer.domain import (
    DistrictTravel, Order, ServiceAllowance, Trip,
)
from waypoint_optimizer.enums import Brand


# ──────────────────────────────────────────────────────────────────────────────
# Lookup helpers
# ──────────────────────────────────────────────────────────────────────────────

def build_travel_index(
    travels: Sequence[DistrictTravel],
) -> dict[tuple[str, str], DistrictTravel]:
    """
    Return a dict keyed by (district, depot) for O(1) lookup.

    Args:
        travels: Iterable of DistrictTravel records.

    Returns:
        Mapping of (district, depot) → DistrictTravel.
    """
    return {(dt.district, dt.depot): dt for dt in travels}


def build_allowance_index(
    allowances: Sequence[ServiceAllowance],
) -> dict[tuple[Brand, str], float]:
    """
    Return a dict keyed by (brand, dock_type) for O(1) lookup.

    Args:
        allowances: Iterable of ServiceAllowance records.

    Returns:
        Mapping of (brand, dock_type_value) → service_allowance_min.
    """
    return {(sa.brand, sa.dock_type): sa.service_allowance_min for sa in allowances}


# ──────────────────────────────────────────────────────────────────────────────
# Core formula components (pure functions, easy to unit-test individually)
# ──────────────────────────────────────────────────────────────────────────────

def outbound_minutes(travel: DistrictTravel) -> float:
    """
    Step 1 of the official formula: outbound travel from depot to district.

    Uses depot_to_district_freeflow_min exactly once per trip.
    """
    return travel.depot_to_district_freeflow_min


def inter_stop_minutes(travel: DistrictTravel, n_orders: int) -> float:
    """
    Step 2 of the official formula: travel between consecutive stops.

    Journeys = (n_orders − 1), using ORDER count, not unique outlet count.

    Examples from the specification:
        1 order  → 0 inter-stop journeys
        3 orders → 2 inter-stop journeys
        4 orders → 3 inter-stop journeys

    Args:
        travel:   DistrictTravel record for the relevant (district, depot).
        n_orders: Number of orders in the trip (NOT outlet count).
    """
    if n_orders <= 0:
        return 0.0
    return travel.inter_stop_freeflow_min * (n_orders - 1)


def handling_minutes(
    orders: Sequence[Order],
    allowance_index: dict[tuple[Brand, str], float],
) -> float:
    """
    Step 3 of the official formula: sum of service allowances for all orders.

    Each order is looked up by (brand, dock_type). The dock_type is the
    delivery-point physical attribute of the order, NOT parking_constraint.

    Args:
        orders:          Orders in the trip.
        allowance_index: Pre-built index from build_allowance_index().

    Raises:
        KeyError: If a (brand, dock_type) combination is missing from the index.
                  Callers should pre-validate their input data.
    """
    total = 0.0
    for order in orders:
        key = (order.brand, order.dock_type)
        if key not in allowance_index:
            raise KeyError(
                f"No ServiceAllowance for brand={order.brand!r}, "
                f"dock_type={order.dock_type!r}. "
                f"order_ref={order.order_ref!r}"
            )
        total += allowance_index[key]
    return total


def calculate_trip_minutes(
    orders: Sequence[Order],
    travel: DistrictTravel,
    allowance_index: dict[tuple[Brand, str], float],
) -> float:
    """
    Official Task 2B trip-time formula.

    FORMULA:
        trip_minutes =
            outbound_travel                        (once per trip)
          + inter_stop_freeflow_min × (n − 1)      (n = number of orders)
          + Σ service_allowance_min                (per order)

    NO return journey is included. The time budgets stated in the Task 2B
    specification already account for return. Adding return travel here would
    be a specification violation.

    Args:
        orders:          All orders in the trip (must be non-empty).
        travel:          Travel data for the trip's (district, depot).
        allowance_index: Pre-built service-allowance lookup.

    Returns:
        Trip duration in minutes (float).
    """
    if not orders:
        return 0.0

    step1 = outbound_minutes(travel)
    step2 = inter_stop_minutes(travel, len(orders))
    step3 = handling_minutes(orders, allowance_index)

    return step1 + step2 + step3


# ──────────────────────────────────────────────────────────────────────────────
# Capacity helpers (used by Validator and compatibility checks)
# ──────────────────────────────────────────────────────────────────────────────

def trip_weight(orders: Sequence[Order]) -> float:
    """Total weight of all orders in a trip (kg)."""
    return sum(o.order_weight_kg for o in orders)


def trip_volume(orders: Sequence[Order]) -> float:
    """Total volume of all orders in a trip (m³)."""
    return sum(o.order_volume_m3 for o in orders)


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle daily time budget helpers
# ──────────────────────────────────────────────────────────────────────────────

def vehicle_fresh_time(
    trips: Sequence[Trip],
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
) -> float:
    """
    Total time (minutes) spent on Fresh trips for a vehicle on a given day.

    Must not exceed FRESH_DAILY_BUDGET_MIN (270).
    """
    from waypoint_optimizer.enums import Brand  # avoid circular at module level
    total = 0.0
    for trip in trips:
        if trip.brand == Brand.FRESH and trip.orders:
            travel = travel_index[(trip.district, trip.orders[0].depot)]
            total += calculate_trip_minutes(trip.orders, travel, allowance_index)
    return total


def vehicle_style_tech_time(
    trips: Sequence[Trip],
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
) -> float:
    """
    Total time (minutes) spent on Style and Tech trips for a vehicle.

    Must not exceed STYLE_TECH_DAILY_BUDGET_MIN (480).
    """
    total = 0.0
    for trip in trips:
        if trip.brand in (Brand.STYLE, Brand.TECH) and trip.orders:
            travel = travel_index[(trip.district, trip.orders[0].depot)]
            total += calculate_trip_minutes(trip.orders, travel, allowance_index)
    return total


def vehicle_daily_time_usage(
    trips: Sequence[Trip],
    travel_index: dict[tuple[str, str], DistrictTravel],
    allowance_index: dict[tuple[Brand, str], float],
) -> dict[str, float]:
    """
    Return a summary dict with fresh_min and style_tech_min for a vehicle's trips.
    Useful for diagnostics and validation.
    """
    return {
        "fresh_min": vehicle_fresh_time(trips, travel_index, allowance_index),
        "style_tech_min": vehicle_style_tech_time(trips, travel_index, allowance_index),
    }
