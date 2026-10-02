"""
Waypoint Optimizer — Objective / Priority Policy
==================================================
TEAM-DEFINED HEURISTICS — NOT OFFICIAL COMPETITION FORMULAS.

This module implements:
  1. defer_penalty()        — per-order penalty score for being deferred
  2. plan_objective()       — aggregate plan score (lower = better)
  3. is_plan_strictly_better() — lexicographic comparison of two valid plans

IMPORTANT:
  - These functions represent the TEAM'S priority policy.
  - Changing weights shifts which orders are prioritised but does NOT
    violate any official competition rule.
  - The penalty value is NOT money, NOT official competition scoring,
    and NOT a hard constraint.
  - Only VALID plans are compared; invalid plans are never selected
    regardless of their score.

The lexicographic selection order is:
  PRIMARY   : minimise total deferral penalty
  SECONDARY : maximise number of served orders
  TERTIARY  : deterministic stable tie-break (sorted canonical signature)
"""
from __future__ import annotations

import math
from typing import Sequence

from waypoint_optimizer.config import (
    DEFER_PENALTY_BASE,
    DEFER_PENALTY_DAYS_CAP,
    DEFER_PENALTY_DEFERRED_YESTERDAY,
    DEFER_PENALTY_PER_DAY,
    DEFER_PENALTY_VOLUME_FACTOR,
    OptimizerConfig,
)
from waypoint_optimizer.domain import (
    DeferredOrder, OptimizationResult, Order, OrderAssignment, TripResult,
)


def defer_penalty(order: Order, cfg: OptimizerConfig = OptimizerConfig()) -> float:
    """
    TEAM-DEFINED: compute the deferral penalty for a single order.

    Formula (team heuristic):
        penalty =
            base
          + deferred_yesterday_bonus  (if deferred_yesterday)
          + per_day × min(days_since_last_served, days_cap)
          + ceil(order_volume_m3 × volume_factor)

    Interpretation:
        Higher penalty → more undesirable to defer this order.

    This formula is configurable via OptimizerConfig. It is NOT:
        - money
        - an official competition scoring metric
        - a hard constraint

    Args:
        order: The order to score.
        cfg:   OptimizerConfig containing penalty weights.

    Returns:
        Non-negative float penalty (higher = worse to defer).
    """
    yesterday_bonus = (
        cfg.defer_penalty_deferred_yesterday if order.deferred_yesterday else 0
    )
    days_bonus = cfg.defer_penalty_per_day * min(
        order.days_since_last_served, cfg.defer_penalty_days_cap
    )
    volume_bonus = math.ceil(order.order_volume_m3 * cfg.defer_penalty_volume_factor)

    return cfg.defer_penalty_base + yesterday_bonus + days_bonus + volume_bonus


def total_penalty(
    deferred: Sequence[Order],
    cfg: OptimizerConfig = OptimizerConfig(),
) -> float:
    """
    Sum of defer_penalty over all deferred orders.

    Lower is better (fewer/less-critical deferrals).
    """
    return sum(defer_penalty(o, cfg) for o in deferred)


# ──────────────────────────────────────────────────────────────────────────────
# Plan objective (used for selecting the best valid candidate)
# ──────────────────────────────────────────────────────────────────────────────

def canonical_signature(
    assignments: Sequence[OrderAssignment],
    deferred: Sequence[DeferredOrder],
) -> str:
    """
    Deterministic string representation of a plan for stable tie-breaking.

    Does NOT use runtime, timestamps, or any random element.
    """
    served_part = ",".join(
        sorted(f"{a.order_ref}:{a.vehicle_id}:{a.trip_number}" for a in assignments)
    )
    deferred_part = ",".join(sorted(d.order_ref for d in deferred))
    return f"S[{served_part}]D[{deferred_part}]"


def plan_score(
    served_assignments: Sequence[OrderAssignment],
    deferred_orders: Sequence[DeferredOrder],
    all_orders: Sequence[Order],
    cfg: OptimizerConfig = OptimizerConfig(),
) -> tuple[float, int, str]:
    """
    Compute the lexicographic plan score for comparison.

    Returns a tuple:
        (total_penalty, -served_count, canonical_signature)

    Comparison is via standard Python tuple ordering:
        - Lower total_penalty wins (primary).
        - If equal, higher served_count wins (negative so lower tuple value wins).
        - If still equal, lower canonical_signature wins (deterministic).

    Only VALID plans should be compared — the optimizer must never use this
    to justify selecting an invalid plan.
    """
    order_by_ref = {o.order_ref: o for o in all_orders}

    deferred_order_objects = [
        order_by_ref[d.order_ref]
        for d in deferred_orders
        if d.order_ref in order_by_ref
    ]

    penalty = total_penalty(deferred_order_objects, cfg)
    served_count = len(served_assignments)
    sig = canonical_signature(served_assignments, deferred_orders)

    return (penalty, -served_count, sig)


def is_plan_strictly_better(
    candidate_score: tuple[float, int, str],
    incumbent_score: tuple[float, int, str],
) -> bool:
    """
    Return True if candidate is strictly better than incumbent.

    Lexicographic: (penalty, -served, signature).
    Lower tuple = better plan.
    """
    return candidate_score < incumbent_score
