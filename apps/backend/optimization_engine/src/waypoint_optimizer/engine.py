"""
Waypoint Optimizer — Main Engine Entry Point
=============================================
The main `optimize()` function. This is the single entry point that the
future Dispatcher backend will call.

Architecture:
  MULTI-START GREEDY
        ↓
  BEST VALID CANDIDATE
        ↓
  TARGETED CP-SAT IMPROVEMENT
        ↓
  INDEPENDENT VALIDATOR
        ↓
  FINAL PLAN

For benchmarking only (enable_full_cpsat_benchmark = True):
  FULL CP-SAT COLD

CONTRACT:
  - No database calls inside optimize().
  - No HTTP calls inside optimize().
  - No FastAPI objects in domain logic.
  - The backend converts its ORM objects to domain objects BEFORE calling this.

Usage:
    from waypoint_optimizer import optimize
    from waypoint_optimizer.config import OptimizerConfig

    result = optimize(orders, vehicles, district_travel, service_allowances)
    assert result.validation.valid
"""
from __future__ import annotations

from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.domain import (
    DistrictTravel, OptimizationResult, Order, ServiceAllowance, Vehicle,
)
from waypoint_optimizer.enums import EngineMode


def optimize(
    orders: list[Order],
    vehicles: list[Vehicle],
    district_travel: list[DistrictTravel],
    service_allowances: list[ServiceAllowance],
    config: OptimizerConfig | None = None,
    mode: EngineMode = EngineMode.TASK2B_EXACT,
) -> OptimizationResult:
    """
    Optimize fleet allocation for the given orders and vehicles.

    This is the primary API entry point for the optimization engine.

    Production pipeline:
      1. Multi-start Greedy portfolio → best valid incumbent
      2. Targeted CP-SAT improvement → accept only if strictly better and valid
      3. Independent Validator → confirm the result
      4. Return final plan

    Args:
        orders:            Confirmed delivery orders.
        vehicles:          Available fleet (engine filters in_workshop internally).
        district_travel:   Travel time/distance data per district.
        service_allowances:Service handling times per (brand, dock_type).
        config:            OptimizerConfig. Uses defaults if None.
        mode:              TASK2B_EXACT (default) or HACKATHON_OPERATIONAL.

    Returns:
        OptimizationResult with all trips, assignments, deferrals, metrics,
        and validation result.

    Guarantee:
        The returned result has been validated by the independent Validator.
        result.validation.valid == True means FEASIBLE (not globally optimal).
    """
    if config is None:
        config = OptimizerConfig()

    from waypoint_optimizer.input_validation import validate_inputs
    validate_inputs(orders, vehicles, district_travel, service_allowances, config)

    from waypoint_optimizer.portfolio import run_portfolio
    from waypoint_optimizer.targeted_cpsat import targeted_cpsat_improve

    # ── Step 1: Multi-start Greedy portfolio ─────────────────────────────────
    best_greedy, _all_candidates = run_portfolio(
        orders=orders,
        vehicles=vehicles,
        travel_data=district_travel,
        service_allowances=service_allowances,
        cfg=config,
        engine_mode=mode,
    )

    if best_greedy is None:
        # No valid Greedy candidate found — return an all-deferred plan that is valid.
        from waypoint_optimizer.explanations import make_deferred
        from waypoint_optimizer.enums import DeferralReason, SolverStatus
        from waypoint_optimizer.greedy import _build_plan_metrics
        from waypoint_optimizer.trip_math import build_allowance_index, build_travel_index
        from waypoint_optimizer.validator import validate

        deferred_orders = [make_deferred(o, DeferralReason.OTHER_CAPACITY_LIMIT) for o in orders]
        travel_index = build_travel_index(district_travel)
        allowance_index = build_allowance_index(service_allowances)
        vehicles_by_id = {v.vehicle_id: v for v in vehicles}

        validation = validate(
            orders=orders,
            vehicles=vehicles,
            travel_index=travel_index,
            allowance_index=allowance_index,
            served_assignments=[],
            deferred_orders=deferred_orders,
            trip_results=[],
            cfg=config,
        )
        metrics = _build_plan_metrics([], [], deferred_orders, orders, vehicles_by_id, config)

        return OptimizationResult(
            status=SolverStatus.INFEASIBLE,
            engine_name="greedy_fallback",
            engine_mode=mode,
            trips=[],
            served_assignments=[],
            deferred_orders=deferred_orders,
            metrics=metrics,
            validation=validation,
            runtime_seconds=time.perf_counter() - t_start,
            objective_value=metrics.total_deferral_penalty,
            diagnostic_message="All orders deferred: no feasible candidate placement found.",
        )

    if not config.enable_targeted_cpsat:
        return best_greedy

    # ── Step 2: Targeted CP-SAT improvement ──────────────────────────────────
    improved = targeted_cpsat_improve(
        base_plan=best_greedy,
        orders=orders,
        vehicles=vehicles,
        travel_data=district_travel,
        service_allowances=service_allowances,
        cfg=config,
        engine_mode=mode,
    )

    return improved


def benchmark(
    orders: list[Order],
    vehicles: list[Vehicle],
    district_travel: list[DistrictTravel],
    service_allowances: list[ServiceAllowance],
    config: OptimizerConfig | None = None,
    mode: EngineMode = EngineMode.TASK2B_EXACT,
) -> dict[str, OptimizationResult]:
    """
    Run baseline Greedy vs Multi-start Greedy + Targeted CP-SAT Hybrid.

    Returns:
        Dict mapping engine name to OptimizationResult ('greedy' and 'hybrid').
    """
    if config is None:
        config = OptimizerConfig()

    from waypoint_optimizer.input_validation import validate_inputs
    validate_inputs(orders, vehicles, district_travel, service_allowances, config)

    from waypoint_optimizer.greedy import greedy_allocate
    from waypoint_optimizer.portfolio import run_portfolio, _sort_priority_first
    from waypoint_optimizer.targeted_cpsat import targeted_cpsat_improve

    results: dict[str, OptimizationResult] = {}

    # Single Greedy (priority_first ordering)
    single_greedy = greedy_allocate(
        orders=orders,
        vehicles=vehicles,
        travel_data=district_travel,
        service_allowances=service_allowances,
        order_sequence=_sort_priority_first(orders, config),
        cfg=config,
        engine_mode=mode,
    )
    results["greedy"] = single_greedy

    # Hybrid: portfolio + targeted CP-SAT
    best_greedy, _ = run_portfolio(
        orders=orders,
        vehicles=vehicles,
        travel_data=district_travel,
        service_allowances=service_allowances,
        cfg=config,
        engine_mode=mode,
    )
    if best_greedy is not None and config.enable_targeted_cpsat:
        hybrid = targeted_cpsat_improve(
            base_plan=best_greedy,
            orders=orders,
            vehicles=vehicles,
            travel_data=district_travel,
            service_allowances=service_allowances,
            cfg=config,
            engine_mode=mode,
        )
    else:
        hybrid = best_greedy
    results["hybrid"] = hybrid

    return results

