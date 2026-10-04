"""
Waypoint Optimizer — Multi-Start Greedy Portfolio
===================================================
Runs multiple Greedy instances with different ordering strategies and
selects the best valid result.

DESIGN PRINCIPLE:
  Different ordering strategies are SEARCH STRATEGIES, not different
  business policies. All strategies:
    1. Generate a candidate plan using the same Greedy allocator
    2. Validate it with the independent Validator
    3. Score it using the SAME objective function
  Only the ordering of orders before the Greedy pass differs.

  This distinction matters: the objective and constraints are the same
  for every candidate. Only the path through the search space differs.

Strategies:
  priority_first     — process orders with highest deferral penalty first
                       (TEAM-DEFINED penalty, not official formula)
  scarcity_first     — orders with fewest compatible vehicles first
  compatibility_first — restrictive orders (chilled, van_only) first
  large_first        — heaviest/most voluminous orders first
  random_{seed}      — randomised orderings with fixed seeds

The best VALID candidate is selected by lexicographic objective:
  (penalty, -served_count, canonical_signature)
"""
from __future__ import annotations

import random
import time
from typing import Sequence

from waypoint_optimizer.compatibility import count_compatible_vehicles
from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.domain import (
    DistrictTravel, Order, OptimizationResult, ServiceAllowance, Vehicle,
)
from waypoint_optimizer.enums import (
    EngineMode, ParkingConstraint, SolverStatus, TempRequirement,
)
from waypoint_optimizer.greedy import greedy_allocate
from waypoint_optimizer.objective import plan_score


# ──────────────────────────────────────────────────────────────────────────────
# Ordering strategies
# ──────────────────────────────────────────────────────────────────────────────

def _sort_priority_first(
    orders: list[Order],
    cfg: OptimizerConfig,
) -> list[Order]:
    """
    TEAM-DEFINED: sort by deferral penalty (highest first).

    Interpretation: protect the most costly-to-defer orders first.
    Uses the team-defined penalty function — NOT an official formula.
    """
    from waypoint_optimizer.objective import defer_penalty
    return sorted(orders, key=lambda o: defer_penalty(o, cfg), reverse=True)


def _sort_scarcity_first(
    orders: list[Order],
    vehicles: list[Vehicle],
) -> list[Order]:
    """
    PLANNING HEURISTIC: sort by number of compatible vehicles (fewest first).

    Orders with fewer compatible vehicles (reefer-only, van-only, specific depot)
    are placed first while more vehicles are still free.

    This is a planning diagnostic converted into an ordering strategy.
    """
    scarcity = {o.order_ref: count_compatible_vehicles(o, vehicles) for o in orders}
    return sorted(orders, key=lambda o: scarcity[o.order_ref])


def _sort_compatibility_first(orders: list[Order]) -> list[Order]:
    """
    Sort restrictive orders first: chilled → van_only → normal.

    Prioritises orders with the most restrictive vehicle requirements,
    placing them when more vehicles are still available.
    """
    def restriction_key(o: Order) -> int:
        score = 0
        if o.temp_requirement == TempRequirement.CHILLED:
            score += 10
        if o.parking_constraint == ParkingConstraint.VAN_ONLY:
            score += 5
        return -score  # most restrictive → lowest key → sorted first

    return sorted(orders, key=restriction_key)


def _sort_large_first(orders: list[Order]) -> list[Order]:
    """
    Sort by order size (largest by weight + normalised volume first).

    Large orders are harder to pack; placing them early avoids wasting
    the largest available space.

    ASSUMPTION: weight and volume are normalised equally by their maximums.
    This is a heuristic, not an official rule.
    """
    max_w = max((o.order_weight_kg for o in orders), default=1.0)
    max_v = max((o.order_volume_m3 for o in orders), default=1.0)

    def size_key(o: Order) -> float:
        return -(o.order_weight_kg / max_w + o.order_volume_m3 / max_v)

    return sorted(orders, key=size_key)


def _sort_random(orders: list[Order], seed: int) -> list[Order]:
    """
    Randomised ordering with a fixed seed for reproducibility.

    Same seed always produces the same permutation (deterministic).
    """
    lst = list(orders)
    random.Random(seed).shuffle(lst)
    return lst


# ──────────────────────────────────────────────────────────────────────────────
# Portfolio runner
# ──────────────────────────────────────────────────────────────────────────────

def run_portfolio(
    orders: list[Order],
    vehicles: list[Vehicle],
    travel_data: list[DistrictTravel],
    service_allowances: list[ServiceAllowance],
    cfg: OptimizerConfig = OptimizerConfig(),
    engine_mode: EngineMode = EngineMode.TASK2B_EXACT,
) -> tuple[OptimizationResult | None, list[OptimizationResult]]:
    """
    Run the Multi-start Greedy portfolio and return the best valid result.

    Each strategy generates an independent candidate. Only VALID candidates
    (Validator.valid == True) are considered for selection.

    Selection uses the lexicographic objective:
      PRIMARY   : minimise total deferral penalty
      SECONDARY : maximise served orders
      TERTIARY  : canonical signature tie-break

    Args:
        orders:            All input orders.
        vehicles:          Fleet of vehicles.
        travel_data:       District travel records.
        service_allowances:Service allowances.
        cfg:               Optimizer configuration.
        engine_mode:       Task2B exact or Hackathon operational mode.

    Returns:
        (best_result, all_candidates)
        best_result is None if NO valid candidate was found.
    """
    # Build ordered sequences for each strategy
    strategies: dict[str, list[Order]] = {
        "priority_first": _sort_priority_first(orders, cfg),
        "scarcity_first": _sort_scarcity_first(orders, vehicles),
        "compatibility_first": _sort_compatibility_first(orders),
        "large_first": _sort_large_first(orders),
    }

    # Fixed-seed random restarts
    base_seed = cfg.random_seed
    for i in range(cfg.greedy_random_restarts):
        strategies[f"random_{base_seed + i}"] = _sort_random(orders, base_seed + i)

    all_candidates: list[OptimizationResult] = []
    best_result: OptimizationResult | None = None
    best_score: tuple[float, int, str] | None = None

    for strategy_name, sequence in strategies.items():
        candidate = greedy_allocate(
            orders=orders,
            vehicles=vehicles,
            travel_data=travel_data,
            service_allowances=service_allowances,
            order_sequence=sequence,
            cfg=cfg,
            engine_mode=engine_mode,
        )
        # Tag which strategy produced this candidate
        candidate = _retag(candidate, f"greedy[{strategy_name}]")
        all_candidates.append(candidate)

        # ENGINE SAFETY RULE: only accept valid candidates
        if not candidate.validation.valid:
            continue

        score = plan_score(
            candidate.served_assignments,
            candidate.deferred_orders,
            orders,
            cfg,
        )

        if best_score is None or score < best_score:
            best_score = score
            best_result = candidate

    return best_result, all_candidates


def _retag(result: OptimizationResult, engine_name: str) -> OptimizationResult:
    """Return a new OptimizationResult with a different engine_name."""
    # OptimizationResult is frozen; reconstruct with new name
    return OptimizationResult(
        status=result.status,
        engine_name=engine_name,
        engine_mode=result.engine_mode,
        trips=result.trips,
        served_assignments=result.served_assignments,
        deferred_orders=result.deferred_orders,
        metrics=result.metrics,
        validation=result.validation,
        runtime_seconds=result.runtime_seconds,
        objective_value=result.objective_value,
        cpsat_improvements_accepted=result.cpsat_improvements_accepted,
        cpsat_solver_status=result.cpsat_solver_status,
    )
