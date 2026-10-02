"""
Waypoint Optimizer — Deferral Explanations
============================================
Structured logic for determining WHY an order was deferred.

The explanations module provides human-readable context for each deferred
order. It is used by the Greedy allocator and CP-SAT solver.

IMPORTANT:
  - Reason codes describe why the order was not placed in THIS plan.
  - They do NOT prove the deferral was mathematically unavoidable.
  - Use language such as "Could not be placed because..." not
    "It was impossible to serve because...".
"""
from __future__ import annotations

from waypoint_optimizer.domain import DeferredOrder, Order
from waypoint_optimizer.enums import DeferralReason


def make_deferred(
    order: Order,
    reason: DeferralReason,
    detail: str = "",
) -> DeferredOrder:
    """
    Create a DeferredOrder with a structured reason and human-readable detail.

    Args:
        order:  The order that could not be placed.
        reason: Structured reason code.
        detail: Additional human-readable context.
    """
    if not detail:
        detail = _default_detail(order, reason)
    return DeferredOrder(
        order_ref=order.order_ref,
        reason=reason,
        detail=detail,
    )


def _default_detail(order: Order, reason: DeferralReason) -> str:
    """Return a default human-readable explanation for the given reason code."""
    templates = {
        DeferralReason.NO_COMPATIBLE_VEHICLE: (
            f"Order {order.order_ref!r} could not be placed: no available vehicle "
            f"in the fleet is compatible with its constraints "
            f"(brand={order.brand!r}, district={order.district!r}, "
            f"temp={order.temp_requirement!r}, parking={order.parking_constraint!r})."
        ),
        DeferralReason.REEFER_CAPACITY_EXHAUSTED: (
            f"Order {order.order_ref!r} requires chilled transport but all reefer "
            f"vehicles for district={order.district!r} are at capacity or time limit."
        ),
        DeferralReason.VAN_CAPACITY_EXHAUSTED: (
            f"Order {order.order_ref!r} requires van-only access but all compatible "
            f"vans for district={order.district!r} are at capacity or trip limit."
        ),
        DeferralReason.WEIGHT_CAPACITY: (
            f"Order {order.order_ref!r} ({order.order_weight_kg:.1f} kg) could not "
            f"be placed: no compatible trip has sufficient remaining weight capacity."
        ),
        DeferralReason.VOLUME_CAPACITY: (
            f"Order {order.order_ref!r} ({order.order_volume_m3:.3f} m³) could not "
            f"be placed: no compatible trip has sufficient remaining volume capacity."
        ),
        DeferralReason.TRIP_LIMIT: (
            f"Order {order.order_ref!r} could not be placed: all compatible vehicles "
            f"have already reached the maximum of 2 trips."
        ),
        DeferralReason.FRESH_TIME_BUDGET: (
            f"Order {order.order_ref!r} (brand=fresh) could not be placed: adding it "
            f"would exceed the 270-minute Fresh daily time budget for available vehicles."
        ),
        DeferralReason.STYLE_TECH_TIME_BUDGET: (
            f"Order {order.order_ref!r} (brand={order.brand!r}) could not be placed: "
            f"adding it would exceed the 480-minute Style+Tech daily time budget."
        ),
        DeferralReason.LOWER_PRIORITY_THAN_SELECTED_ORDERS: (
            f"Order {order.order_ref!r} was not selected in this plan because "
            f"higher-priority orders occupied the available capacity."
        ),
        DeferralReason.NOT_SELECTED_BY_HEURISTIC: (
            f"Order {order.order_ref!r} was not selected within available fleet capacity "
            f"under the greedy heuristic; global infeasibility is not proven."
        ),
        DeferralReason.OTHER_CAPACITY_LIMIT: (
            f"Order {order.order_ref!r} could not be placed due to a combination "
            f"of capacity constraints."
        ),
    }
    return templates.get(reason, f"Order {order.order_ref!r} was deferred.")


def classify_deferral(
    order: Order,
    no_compatible_vehicle: bool,
    reefer_exhausted: bool = False,
    van_exhausted: bool = False,
    weight_full: bool = False,
    volume_full: bool = False,
    trip_limit_reached: bool = False,
    fresh_budget_full: bool = False,
    style_tech_budget_full: bool = False,
) -> DeferralReason:
    """
    Classify the most specific deferral reason for an order.

    Priority order (most specific first):
      1. No compatible vehicle at all (HC2/HC3/HC4)
      2. Specific reefer or van exhaustion
      3. Weight / volume full
      4. Trip limit
      5. Time budget
      6. Generic capacity

    Returns the single most specific DeferralReason.
    """
    if no_compatible_vehicle:
        return DeferralReason.NO_COMPATIBLE_VEHICLE
    if reefer_exhausted:
        return DeferralReason.REEFER_CAPACITY_EXHAUSTED
    if van_exhausted:
        return DeferralReason.VAN_CAPACITY_EXHAUSTED
    if weight_full:
        return DeferralReason.WEIGHT_CAPACITY
    if volume_full:
        return DeferralReason.VOLUME_CAPACITY
    if trip_limit_reached:
        return DeferralReason.TRIP_LIMIT
    if fresh_budget_full:
        return DeferralReason.FRESH_TIME_BUDGET
    if style_tech_budget_full:
        return DeferralReason.STYLE_TECH_TIME_BUDGET
    return DeferralReason.OTHER_CAPACITY_LIMIT
