"""
Waypoint Optimizer — Targeted CP-SAT Improvement
==================================================
After the Multi-start Greedy produces the best valid base plan, this module
uses OR-Tools CP-SAT to try to improve a TARGETED neighbourhood (insertion-only).

Design principles:
  - Preserves the valid incumbent unless a candidate is strictly better and passes validation.
  - Strict enforcement of brand/district homogeneity for existing and newly opened trips.
  - Complete time budget accounting for both Fresh and Style/Tech budgets across all trips
    (existing base duration + incremental time for inserted orders + activation for new trips).
  - Clear diagnostic reporting when improvement is skipped, times out, fails validation,
    or does not improve the incumbent.
"""
from __future__ import annotations

import math
import time
from collections import defaultdict
from typing import Optional, Sequence

from waypoint_optimizer.compatibility import is_vehicle_compatible
from waypoint_optimizer.config import (
    MAX_TRIPS_PER_VEHICLE,
    VALID_TRIP_NUMBERS,
    OptimizerConfig,
)
from waypoint_optimizer.domain import (
    DeferredOrder,
    DistrictTravel,
    DockType,
    OptimizationResult,
    Order,
    OrderAssignment,
    Outlet,
    ParkingConstraint,
    PlanMetrics,
    ServiceAllowance,
    TempRequirement,
    TempSpec,
    Trip,
    TripResult,
    Vehicle,
    VehicleType,
)
from waypoint_optimizer.enums import (
    Brand,
    DeferralReason,
    EngineMode,
    SolverStatus,
)
from waypoint_optimizer.input_validation import InputValidationError
from waypoint_optimizer.operational.models import (
    DEFAULT_FRESH_DEPARTURE_TIME,
    DEFAULT_STYLE_TECH_DEPARTURE_TIME,
    EvaluatedTripSchedule,
    OperationalContext,
    TravelPolicy,
    VehicleScheduleTimeline,
    WindowPolicy,
)
from waypoint_optimizer.operational.schedule_evaluator import (
    evaluate_trip_schedule,
    parse_iso_or_time_str,
)
from waypoint_optimizer.operational.timeline import evaluate_vehicle_timeline
from waypoint_optimizer.operational.validator import validate_operational_plan
from waypoint_optimizer.explanations import make_deferred
from waypoint_optimizer.greedy import (
    _build_plan_metrics,
    _build_trip_result,
    validate_greedy_config,
)
from waypoint_optimizer.objective import defer_penalty, plan_score
from waypoint_optimizer.trip_math import (
    build_allowance_index,
    build_travel_index,
)
from waypoint_optimizer.validator import validate


SCALE_TIME = 1000
SCALE_WEIGHT = 1000
SCALE_VOL = 10000
SCALE_PENALTY = 1000


def targeted_cpsat_improve(
    base_plan: OptimizationResult,
    orders: list[Order],
    vehicles: list[Vehicle],
    travel_data: list[DistrictTravel],
    service_allowances: list[ServiceAllowance],
    cfg: OptimizerConfig = OptimizerConfig(),
    engine_mode: EngineMode = EngineMode.TASK2B_EXACT,
) -> OptimizationResult:
    """
    Attempt to improve a base Greedy plan using targeted CP-SAT insertion.

    Returns:
        The improved plan if CP-SAT finds something strictly better and valid.
        Otherwise, returns the original base_plan unchanged with diagnostic message.
    """
    t_start = time.perf_counter()
    validate_greedy_config(cfg)

    # 1. Check incumbent validity
    if not base_plan.validation.valid:
        return _retain_base(
            base_plan,
            diag="Base plan is invalid; targeted CP-SAT cannot improve an invalid base plan.",
            elapsed=time.perf_counter() - t_start,
        )

    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return _retain_base(
            base_plan,
            diag="OR-Tools is not installed; targeted CP-SAT skipped.",
            elapsed=time.perf_counter() - t_start,
        )

    travel_index = build_travel_index(travel_data)
    allowance_index = build_allowance_index(service_allowances)
    vehicles_by_id = {v.vehicle_id: v for v in vehicles}
    order_by_ref = {o.order_ref: o for o in orders}
    available_vehicles = [v for v in vehicles if v.is_available]

    # 2. Select target deferred orders (highest penalty first, up to 30)
    deferred_refs = {d.order_ref for d in base_plan.deferred_orders}
    deferred_orders_sorted = sorted(
        [order_by_ref[r] for r in deferred_refs if r in order_by_ref],
        key=lambda o: defer_penalty(o, cfg),
        reverse=True,
    )

    MAX_NEIGHBOURHOOD = 30
    target_deferred = deferred_orders_sorted[:MAX_NEIGHBOURHOOD]
    if not target_deferred:
        return _retain_base(
            base_plan,
            diag="No deferred orders to improve.",
            elapsed=time.perf_counter() - t_start,
        )

    # 3. Categorize vehicle trip slots: existing vs new
    existing_trips_by_vid: dict[str, dict[int, TripResult]] = defaultdict(dict)
    for tr in base_plan.trips:
        existing_trips_by_vid[tr.vehicle_id][tr.trip_number] = tr

    trip_nums = sorted(t for t in cfg.valid_trip_numbers if t <= cfg.max_trips_per_vehicle)
    all_districts = sorted({o.district for o in orders})
    all_brands = sorted({o.brand for o in orders}, key=lambda b: b.value)

    # ── Build CP-SAT Model ────────────────────────────────────────────────────
    model = cp_model.CpModel()

    # x[oi, vi, t] = 1 if deferred order oi is inserted into vehicle vi trip t
    x: dict[int, dict[tuple[int, int], cp_model.IntVar]] = {
        i: {} for i in range(len(target_deferred))
    }

    # Y[vi, t, brand, district] for newly opened trips
    Y_new: dict[tuple[int, int, Brand, str], cp_model.IntVar] = {}
    open_new: dict[tuple[int, int], cp_model.IntVar] = {}

    for vi, vehicle in enumerate(available_vehicles):
        vid = vehicle.vehicle_id
        existing_on_v = existing_trips_by_vid.get(vid, {})

        for t in trip_nums:
            if t in existing_on_v:
                # Existing trip slot: brand and district are locked to existing trip
                ex_tr = existing_on_v[t]
                for oi, order in enumerate(target_deferred):
                    compat_ok, _ = is_vehicle_compatible(order, vehicle)
                    if not compat_ok:
                        continue
                    if order.brand != ex_tr.brand or order.district != ex_tr.district:
                        continue
                    # Check reference data exists
                    if (order.district, vehicle.depot) not in travel_index:
                        continue
                    if (order.brand, order.dock_type) not in allowance_index:
                        continue

                    var = model.new_bool_var(f"x_{oi}_{vi}_{t}")
                    x[oi][(vi, t)] = var

            else:
                # Unopened trip slot: only if vehicle has not reached max_trips
                if len(existing_on_v) >= cfg.max_trips_per_vehicle:
                    continue

                open_var = model.new_bool_var(f"open_new_{vi}_{t}")
                open_new[(vi, t)] = open_var
                group_vars: list[cp_model.IntVar] = []

                for brand in all_brands:
                    for district in all_districts:
                        travel = travel_index.get((district, vehicle.depot))
                        if travel is None:
                            continue

                        matching_orders = []
                        for oi, order in enumerate(target_deferred):
                            compat_ok, _ = is_vehicle_compatible(order, vehicle)
                            if not compat_ok:
                                continue
                            if order.brand != brand or order.district != district:
                                continue
                            if (order.brand, order.dock_type) not in allowance_index:
                                continue

                            var = model.new_bool_var(f"x_{oi}_{vi}_{t}")
                            x[oi][(vi, t)] = var
                            matching_orders.append(var)

                        if matching_orders:
                            y_var = model.new_bool_var(f"Y_new_{vi}_{t}_{brand.value}_{district}")
                            Y_new[(vi, t, brand, district)] = y_var
                            group_vars.append(y_var)

                            # Activation linkage
                            model.add(y_var <= sum(matching_orders))
                            for m_var in matching_orders:
                                model.add(m_var <= y_var)

                if group_vars:
                    model.add(sum(group_vars) == open_var)
                else:
                    model.add(open_var == 0)

    # 4. Each deferred order assigned to at most one slot
    for oi in range(len(target_deferred)):
        slots = list(x[oi].values())
        if slots:
            model.add(sum(slots) <= 1)

    # 5. Sequencing: if slot 2 is new and slot 1 is new, open_new[2] <= open_new[1]
    for vi in range(len(available_vehicles)):
        if (vi, 2) in open_new and (vi, 1) in open_new:
            model.add(open_new[(vi, 2)] <= open_new[(vi, 1)])

    # 6. Capacity constraints per trip slot
    for vi, vehicle in enumerate(available_vehicles):
        vid = vehicle.vehicle_id
        existing_on_v = existing_trips_by_vid.get(vid, {})

        for t in trip_nums:
            new_w_terms = [
                x[oi][(vi, t)] * int(math.ceil(target_deferred[oi].order_weight_kg * SCALE_WEIGHT))
                for oi in range(len(target_deferred))
                if (vi, t) in x[oi]
            ]
            new_v_terms = [
                x[oi][(vi, t)] * int(math.ceil(target_deferred[oi].order_volume_m3 * SCALE_VOL))
                for oi in range(len(target_deferred))
                if (vi, t) in x[oi]
            ]

            if not new_w_terms:
                continue

            if t in existing_on_v:
                ex_tr = existing_on_v[t]
                rem_w = max(0.0, vehicle.weight_cap_kg - ex_tr.total_weight_kg)
                rem_v = max(0.0, vehicle.volume_cap_m3 - ex_tr.total_volume_m3)
                model.add(sum(new_w_terms) <= int(math.floor(rem_w * SCALE_WEIGHT)))
                model.add(sum(new_v_terms) <= int(math.floor(rem_v * SCALE_VOL)))
            else:
                model.add(sum(new_w_terms) <= int(math.floor(vehicle.weight_cap_kg * SCALE_WEIGHT)))
                model.add(sum(new_v_terms) <= int(math.floor(vehicle.volume_cap_m3 * SCALE_VOL)))

    # 7. Time budgets per vehicle (Complete budget check: existing base + additions + new trips)
    fresh_budget_scaled = int(math.floor(cfg.fresh_daily_budget_min * SCALE_TIME))
    st_budget_scaled = int(math.floor(cfg.style_tech_daily_budget_min * SCALE_TIME))

    for vi, vehicle in enumerate(available_vehicles):
        vid = vehicle.vehicle_id
        existing_on_v = existing_trips_by_vid.get(vid, {})

        fresh_terms: list[cp_model.LinearExpr] = []
        st_terms: list[cp_model.LinearExpr] = []

        # (a) Base time from existing trips
        for ex_t, ex_tr in existing_on_v.items():
            base_time_scaled = int(math.ceil(ex_tr.trip_minutes * SCALE_TIME))
            if ex_tr.brand == Brand.FRESH:
                fresh_terms.append(base_time_scaled)
            elif ex_tr.brand in (Brand.STYLE, Brand.TECH):
                st_terms.append(base_time_scaled)

        # (b) Additions to existing trips: each added order adds inter_stop + allowance
        for ex_t, ex_tr in existing_on_v.items():
            travel = travel_index[(ex_tr.district, vehicle.depot)]
            for oi, order in enumerate(target_deferred):
                if (vi, ex_t) not in x[oi]:
                    continue
                allowance = allowance_index[(order.brand, order.dock_type)]
                added_time_scaled = int(math.ceil(
                    (travel.inter_stop_freeflow_min + allowance) * SCALE_TIME
                ))
                if order.brand == Brand.FRESH:
                    fresh_terms.append(added_time_scaled * x[oi][(vi, ex_t)])
                elif order.brand in (Brand.STYLE, Brand.TECH):
                    st_terms.append(added_time_scaled * x[oi][(vi, ex_t)])

        # (c) Time from newly opened trips: activation delta + per-order terms
        for t in trip_nums:
            if t in existing_on_v:
                continue

            for district in all_districts:
                travel = travel_index.get((district, vehicle.depot))
                if travel is None:
                    continue
                delta_scaled = int(math.ceil(
                    (travel.depot_to_district_freeflow_min - travel.inter_stop_freeflow_min) * SCALE_TIME
                ))

                y_fresh = Y_new.get((vi, t, Brand.FRESH, district))
                if y_fresh is not None:
                    fresh_terms.append(delta_scaled * y_fresh)

                for st_brand in (Brand.STYLE, Brand.TECH):
                    y_st = Y_new.get((vi, t, st_brand, district))
                    if y_st is not None:
                        st_terms.append(delta_scaled * y_st)

            for oi, order in enumerate(target_deferred):
                if (vi, t) not in x[oi]:
                    continue
                travel = travel_index[(order.district, vehicle.depot)]
                allowance = allowance_index[(order.brand, order.dock_type)]
                order_time_scaled = int(math.ceil(
                    (travel.inter_stop_freeflow_min + allowance) * SCALE_TIME
                ))
                if order.brand == Brand.FRESH:
                    fresh_terms.append(order_time_scaled * x[oi][(vi, t)])
                elif order.brand in (Brand.STYLE, Brand.TECH):
                    st_terms.append(order_time_scaled * x[oi][(vi, t)])

        if fresh_terms:
            model.add(sum(fresh_terms) <= fresh_budget_scaled)
        if st_terms:
            model.add(sum(st_terms) <= st_budget_scaled)

    # 8. Objective: Maximise total penalty of newly placed orders
    objective_terms: list[cp_model.LinearExpr] = []
    for oi, order in enumerate(target_deferred):
        penalty_i = int(round(defer_penalty(order, cfg) * SCALE_PENALTY))
        for (vi, t), var in x[oi].items():
            objective_terms.append(penalty_i * var)

    if not objective_terms:
        return _retain_base(
            base_plan,
            diag="No feasible insertion slots found for target deferred orders.",
            elapsed=time.perf_counter() - t_start,
        )

    model.maximize(sum(objective_terms))

    # ── Solve ─────────────────────────────────────────────────────────────────
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = cfg.targeted_cpsat_time_limit_s
    solver.parameters.num_search_workers = cfg.cpsat_num_workers
    solver.parameters.random_seed = cfg.random_seed

    status_code = solver.solve(model)

    status_map = {
        cp_model.OPTIMAL: SolverStatus.OPTIMAL,
        cp_model.FEASIBLE: SolverStatus.FEASIBLE,
        cp_model.INFEASIBLE: SolverStatus.INFEASIBLE,
        cp_model.UNKNOWN: SolverStatus.UNKNOWN,
    }
    raw_status = status_map.get(status_code, SolverStatus.UNKNOWN)

    if raw_status not in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
        return _retain_base(
            base_plan,
            diag=f"Targeted CP-SAT returned {raw_status.value}; retained base plan.",
            elapsed=time.perf_counter() - t_start,
            cpsat_status=raw_status,
        )

    # ── Extract candidate additions ───────────────────────────────────────────
    newly_placed: list[tuple[Order, str, int]] = []
    for oi, order in enumerate(target_deferred):
        for (vi, t), var in x[oi].items():
            if solver.value(var) == 1:
                vid = available_vehicles[vi].vehicle_id
                newly_placed.append((order, vid, t))
                break

    if not newly_placed:
        return _retain_base(
            base_plan,
            diag="Targeted CP-SAT found no improving placements; retained base plan.",
            elapsed=time.perf_counter() - t_start,
            cpsat_status=raw_status,
        )

    # ── Reconstruct Candidate Plan ────────────────────────────────────────────
    # Map vehicle trips
    candidate_trips: dict[tuple[str, int], list[Order]] = defaultdict(list)

    # Add existing orders from base_plan
    for tr in base_plan.trips:
        for ref in tr.order_refs:
            candidate_trips[(tr.vehicle_id, tr.trip_number)].append(order_by_ref[ref])

    # Add newly placed orders
    for order, vid, t in newly_placed:
        candidate_trips[(vid, t)].append(order)

    # Build updated assignments & deferred
    served_assignments: list[OrderAssignment] = []
    placed_refs: set[str] = set()

    for (vid, t), trip_orders in sorted(candidate_trips.items()):
        for o in trip_orders:
            served_assignments.append(OrderAssignment(
                order_ref=o.order_ref,
                vehicle_id=vid,
                trip_number=t,
            ))
            placed_refs.add(o.order_ref)

    deferred_orders: list[DeferredOrder] = [
        make_deferred(o, DeferralReason.LOWER_PRIORITY_THAN_SELECTED_ORDERS)
        for o in orders
        if o.order_ref not in placed_refs
    ]

    trip_results: list[TripResult] = []
    for (vid, trip_num), trip_orders in sorted(candidate_trips.items()):
        if not trip_orders:
            continue
        vehicle = vehicles_by_id[vid]
        trip_obj = Trip(
            vehicle_id=vid,
            trip_number=trip_num,
            brand=trip_orders[0].brand,
            district=trip_orders[0].district,
            orders=trip_orders,
        )
        trip_results.append(_build_trip_result(trip_obj, vehicle, travel_index, allowance_index))

    trip_results.sort(key=lambda tr: (tr.vehicle_id, tr.trip_number))

    # ── Independent Validation ────────────────────────────────────────────────
    candidate_validation = validate(
        orders=orders,
        vehicles_by_id=vehicles_by_id,
        travel_index=travel_index,
        allowance_index=allowance_index,
        served_assignments=served_assignments,
        deferred_orders=deferred_orders,
        trip_results=trip_results,
        cfg=cfg,
    )

    if not candidate_validation.valid:
        error_details = ", ".join(e.rule for e in candidate_validation.errors[:3])
        return _retain_base(
            base_plan,
            diag=f"Targeted CP-SAT candidate failed independent validation ({error_details}); retained base plan.",
            elapsed=time.perf_counter() - t_start,
            cpsat_status=raw_status,
        )

    # ── Score comparison under existing plan_score ────────────────────────────
    new_score = plan_score(served_assignments, deferred_orders, orders, cfg)
    incumbent_score = plan_score(
        base_plan.served_assignments, base_plan.deferred_orders, orders, cfg
    )

    # Must be strictly better (lower score)
    if new_score >= incumbent_score:
        return _retain_base(
            base_plan,
            diag=f"Targeted CP-SAT candidate score ({new_score}) not strictly better than incumbent ({incumbent_score}); retained base plan.",
            elapsed=time.perf_counter() - t_start,
            cpsat_status=raw_status,
        )

    # Accepted improvement!
    metrics = _build_plan_metrics(
        trip_results, served_assignments, deferred_orders, orders, vehicles_by_id, cfg
    )

    diag_msg = (
        f"Targeted CP-SAT accepted: placed {len(newly_placed)} additional order(s); "
        f"score improved from {incumbent_score[0]:.1f} to {new_score[0]:.1f}."
    )

    return OptimizationResult(
        status=SolverStatus.FEASIBLE,
        engine_name=base_plan.engine_name + "+cpsat",
        engine_mode=engine_mode,
        trips=trip_results,
        served_assignments=served_assignments,
        deferred_orders=deferred_orders,
        metrics=metrics,
        validation=candidate_validation,
        runtime_seconds=base_plan.runtime_seconds + (time.perf_counter() - t_start),
        objective_value=metrics.total_deferral_penalty,
        cpsat_improvements_accepted=len(newly_placed),
        cpsat_solver_status=raw_status,
        diagnostic_message=diag_msg,
    )


def _retain_base(
    base_plan: OptimizationResult,
    diag: str,
    elapsed: float,
    cpsat_status: Optional[SolverStatus] = None,
) -> OptimizationResult:
    """Return base_plan with diagnostic message and updated runtime."""
    return OptimizationResult(
        status=base_plan.status,
        engine_name=base_plan.engine_name,
        engine_mode=base_plan.engine_mode,
        trips=base_plan.trips,
        served_assignments=base_plan.served_assignments,
        deferred_orders=base_plan.deferred_orders,
        metrics=base_plan.metrics,
        validation=base_plan.validation,
        runtime_seconds=base_plan.runtime_seconds + elapsed,
        objective_value=base_plan.objective_value,
        cpsat_improvements_accepted=0,
        cpsat_solver_status=cpsat_status,
        diagnostic_message=diag,
    )


def _order_priority_key(order: Order, config: Optional[OptimizerConfig] = None) -> float:
    """Computes priority weighting for order deferral penalties."""
    weight = 0.0
    if order.deferred_yesterday:
        weight += 1000.0
    weight += order.days_since_last_served * 100.0
    if config:
        weight += defer_penalty(order, config)
    else:
        weight += float(order.order_units)
    return weight


def operational_targeted_cpsat_improve(
    incumbent_plan_state: dict[str, Any],
    orders: list[Order],
    fleet: list[Vehicle],
    travel_data: dict[tuple[str, str], DistrictTravel],
    outlets: dict[str, Outlet],
    allowances: dict[tuple[Brand, DockType], float],
    context: OperationalContext,
    time_limit_s: float = 5.0,
    config: Optional[OptimizerConfig] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Operational Targeted CP-SAT Improvement Stage (Hackathon).

    Preserves the independently valid multi-start greedy plan as the incumbent.
    Selects a bounded neighborhood consisting of:
      - Top high-penalty deferred orders.
      - Relevant compatible available vehicles at the depot.
      - Selected existing assignments on those vehicles.

    Allows whole-order reassignment within this neighborhood; keeps orders and
    commitments outside it strictly fixed. Recomputes complete affected schedules
    and validates the merged plan against authoritative inputs.
    """
    t_start = time.perf_counter()

    incumbent_assigned = incumbent_plan_state.get("assigned_orders", set())
    incumbent_penalty = sum(_order_priority_key(o, config) for o in orders if o.order_ref not in incumbent_assigned)
    incumbent_served = len(incumbent_assigned)

    # 1. Check Travel Policy (only static_freeflow supported for CP-SAT stage)
    if context.travel_policy != TravelPolicy.STATIC_FREEFLOW:
        return incumbent_plan_state, {
            "executed": False,
            "neighborhood_size": {"target_deferred_orders": 0, "neighborhood_orders": 0, "vehicles": 0, "vehicle_ids": []},
            "raw_solver_status": "SKIPPED",
            "outcome": "SKIPPED_POLICY_NOT_SUPPORTED",
            "improvement_accepted": False,
            "rejection_or_skip_reason": (
                f"Targeted CP-SAT improvement currently only supports static_freeflow travel policy (requested: {context.travel_policy.value})."
            ),
            "incumbent_deferral_penalty": round(incumbent_penalty, 2),
            "final_deferral_penalty": round(incumbent_penalty, 2),
            "incumbent_served_count": incumbent_served,
            "final_served_count": incumbent_served,
            "runtime_seconds": round(time.perf_counter() - t_start, 4),
        }

    # 2. Check OR-Tools dependency
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return incumbent_plan_state, {
            "executed": False,
            "neighborhood_size": {"target_deferred_orders": 0, "neighborhood_orders": 0, "vehicles": 0, "vehicle_ids": []},
            "raw_solver_status": "NOT_INSTALLED",
            "outcome": "SKIPPED_ORTOOLS_NOT_INSTALLED",
            "improvement_accepted": False,
            "rejection_or_skip_reason": "OR-Tools is not installed in the environment.",
            "incumbent_deferral_penalty": round(incumbent_penalty, 2),
            "final_deferral_penalty": round(incumbent_penalty, 2),
            "incumbent_served_count": incumbent_served,
            "final_served_count": incumbent_served,
            "runtime_seconds": round(time.perf_counter() - t_start, 4),
        }

    # 3. Check incumbent validity
    val_res = incumbent_plan_state.get("validation_result")
    if not val_res or not val_res.valid:
        return incumbent_plan_state, {
            "executed": False,
            "neighborhood_size": {"target_deferred_orders": 0, "neighborhood_orders": 0, "vehicles": 0, "vehicle_ids": []},
            "raw_solver_status": "SKIPPED",
            "outcome": "SKIPPED_INCUMBENT_INVALID",
            "improvement_accepted": False,
            "rejection_or_skip_reason": "Incumbent plan failed validation; cannot perform targeted improvement on invalid plan.",
            "incumbent_deferral_penalty": round(incumbent_penalty, 2),
            "final_deferral_penalty": round(incumbent_penalty, 2),
            "incumbent_served_count": incumbent_served,
            "final_served_count": incumbent_served,
            "runtime_seconds": round(time.perf_counter() - t_start, 4),
        }

    # 4. Check deferred orders
    deferred_orders = [o for o in orders if o.order_ref not in incumbent_assigned]
    if not deferred_orders:
        return incumbent_plan_state, {
            "executed": False,
            "neighborhood_size": {"target_deferred_orders": 0, "neighborhood_orders": 0, "vehicles": 0, "vehicle_ids": []},
            "raw_solver_status": "SKIPPED",
            "outcome": "SKIPPED_NO_DEFERRED_ORDERS",
            "improvement_accepted": False,
            "rejection_or_skip_reason": "No deferred orders in incumbent plan; all orders already served.",
            "incumbent_deferral_penalty": 0.0,
            "final_deferral_penalty": 0.0,
            "incumbent_served_count": incumbent_served,
            "final_served_count": incumbent_served,
            "runtime_seconds": round(time.perf_counter() - t_start, 4),
        }

    # 5. Select Bounded Neighborhood
    sorted_deferred = sorted(deferred_orders, key=lambda o: _order_priority_key(o, config), reverse=True)
    target_deferred = sorted_deferred[:3]

    candidate_vids: list[str] = []
    for d_ord in target_deferred:
        u = outlets.get(d_ord.outlet_id)
        depot = u.depot if u else d_ord.depot
        for v in fleet:
            if not v.is_available or v.exclusion_reason is not None:
                continue
            if v.depot != depot or v.remaining_trips <= 0:
                continue
            if d_ord.requires_refrigeration and not v.is_refrigerated:
                continue
            dock = u.dock_type if u else d_ord.dock_type
            parking = u.parking_constraint if u else d_ord.parking_constraint
            if parking == ParkingConstraint.VAN_ONLY and v.type != VehicleType.VAN:
                continue
            prior_fuel = (v.weekly_fuel_used_l or 0.0) + (v.external_reservations_l or 0.0)
            if prior_fuel >= v.weekly_fuel_quota_l:
                continue
            if v.vehicle_id not in candidate_vids:
                candidate_vids.append(v.vehicle_id)

    target_districts = {o.district for o in target_deferred}
    target_brands = {o.brand for o in target_deferred}
    for tr in incumbent_plan_state.get("trip_schedules", []):
        if tr.district in target_districts or tr.brand in target_brands:
            if tr.vehicle_id not in candidate_vids:
                parent_v = next((v for v in fleet if v.vehicle_id == tr.vehicle_id), None)
                if parent_v and parent_v.is_available and parent_v.exclusion_reason is None:
                    candidate_vids.append(tr.vehicle_id)

    candidate_vids = candidate_vids[:4]

    if not candidate_vids:
        return incumbent_plan_state, {
            "executed": False,
            "neighborhood_size": {"target_deferred_orders": len(target_deferred), "neighborhood_orders": 0, "vehicles": 0, "vehicle_ids": []},
            "raw_solver_status": "SKIPPED",
            "outcome": "SKIPPED_NO_COMPATIBLE_VEHICLES",
            "improvement_accepted": False,
            "rejection_or_skip_reason": "No compatible available vehicles found in fleet for target deferred orders.",
            "incumbent_deferral_penalty": round(incumbent_penalty, 2),
            "final_deferral_penalty": round(incumbent_penalty, 2),
            "incumbent_served_count": incumbent_served,
            "final_served_count": incumbent_served,
            "runtime_seconds": round(time.perf_counter() - t_start, 4),
        }

    neigh_vehicles = [v for v in fleet if v.vehicle_id in candidate_vids]
    neigh_incumbent_trips = [t for t in incumbent_plan_state.get("trip_schedules", []) if t.vehicle_id in candidate_vids]
    neigh_assigned_refs = {ref for t in neigh_incumbent_trips for ref in t.assigned_order_refs}
    neigh_existing_orders = [o for o in orders if o.order_ref in neigh_assigned_refs]

    seen_refs = set()
    neighborhood_orders: list[Order] = []
    for o in neigh_existing_orders + target_deferred:
        if o.order_ref not in seen_refs:
            seen_refs.add(o.order_ref)
            neighborhood_orders.append(o)

    num_orders = len(neighborhood_orders)
    num_vehicles = len(neigh_vehicles)

    stage_info: dict[str, Any] = {
        "executed": True,
        "neighborhood_size": {
            "target_deferred_orders": len(target_deferred),
            "neighborhood_orders": num_orders,
            "vehicles": num_vehicles,
            "vehicle_ids": candidate_vids,
        },
        "raw_solver_status": "NOT_RUN",
        "outcome": "UNKNOWN",
        "improvement_accepted": False,
        "rejection_or_skip_reason": None,
        "incumbent_deferral_penalty": round(incumbent_penalty, 2),
        "final_deferral_penalty": round(incumbent_penalty, 2),
        "incumbent_served_count": incumbent_served,
        "final_served_count": incumbent_served,
        "runtime_seconds": 0.0,
    }

    try:
        model = cp_model.CpModel()

        vehicle_trip_slots: list[tuple[int, int]] = []
        for vi, v in enumerate(neigh_vehicles):
            max_t = min(v.remaining_trips, 2)
            for ti in range(1, max_t + 1):
                vehicle_trip_slots.append((vi, ti))

        x: dict[tuple[int, int, int], cp_model.IntVar] = {}
        for oi, o in enumerate(neighborhood_orders):
            u = outlets.get(o.outlet_id)
            dock = u.dock_type if u else o.dock_type
            parking = u.parking_constraint if u else o.parking_constraint
            for vi, ti in vehicle_trip_slots:
                v = neigh_vehicles[vi]
                if o.requires_refrigeration and not v.is_refrigerated:
                    continue
                if parking == ParkingConstraint.VAN_ONLY and v.type != VehicleType.VAN:
                    continue
                if v.depot != (u.depot if u else o.depot):
                    continue
                if (o.district, v.depot) not in travel_data:
                    continue
                x[(oi, vi, ti)] = model.NewBoolVar(f"x_{oi}_{vi}_{ti}")

        # Whole-order assignment: each order assigned at most once
        for oi in range(num_orders):
            assigned_slots = [x[(oi, vi, ti)] for vi, ti in vehicle_trip_slots if (oi, vi, ti) in x]
            if assigned_slots:
                model.Add(sum(assigned_slots) <= 1)

        # Trip active indicators
        trip_active: dict[tuple[int, int], cp_model.IntVar] = {}
        for vi, ti in vehicle_trip_slots:
            trip_active[(vi, ti)] = model.NewBoolVar(f"active_{vi}_{ti}")
            orders_in_slot = [x[(oi, vi, ti)] for oi in range(num_orders) if (oi, vi, ti) in x]
            if orders_in_slot:
                model.Add(sum(orders_in_slot) >= trip_active[(vi, ti)])
                for var in orders_in_slot:
                    model.Add(var <= trip_active[(vi, ti)])
            else:
                model.Add(trip_active[(vi, ti)] == 0)

        for vi, v in enumerate(neigh_vehicles):
            if (vi, 2) in trip_active and (vi, 1) in trip_active:
                model.Add(trip_active[(vi, 2)] <= trip_active[(vi, 1)])

        # Capacity constraints
        for vi, ti in vehicle_trip_slots:
            v = neigh_vehicles[vi]
            orders_in_slot = [
                (oi, x[(oi, vi, ti)]) for oi in range(num_orders) if (oi, vi, ti) in x
            ]
            if orders_in_slot:
                model.Add(
                    sum(int(round(neighborhood_orders[oi].order_weight_kg * 1000)) * var for oi, var in orders_in_slot)
                    <= int(round(v.weight_cap_kg * 1000))
                )
                model.Add(
                    sum(int(round(neighborhood_orders[oi].order_volume_m3 * 10000)) * var for oi, var in orders_in_slot)
                    <= int(round(v.volume_cap_m3 * 10000))
                )

        # Single Brand per trip: Fresh, Style, Tech modeled separately
        brand_var: dict[tuple[int, int, Brand], cp_model.IntVar] = {}
        for vi, ti in vehicle_trip_slots:
            for b in (Brand.FRESH, Brand.STYLE, Brand.TECH):
                brand_var[(vi, ti, b)] = model.NewBoolVar(f"brand_{vi}_{ti}_{b.value}")
            model.Add(sum(brand_var[(vi, ti, b)] for b in (Brand.FRESH, Brand.STYLE, Brand.TECH)) == trip_active[(vi, ti)])
            for oi in range(num_orders):
                if (oi, vi, ti) in x:
                    o_brand = neighborhood_orders[oi].brand
                    model.Add(x[(oi, vi, ti)] <= brand_var[(vi, ti, o_brand)])

        # Single District per trip
        unique_districts = sorted({o.district for o in neighborhood_orders})
        dist_var: dict[tuple[int, int, str], cp_model.IntVar] = {}
        for vi, ti in vehicle_trip_slots:
            for d in unique_districts:
                dist_var[(vi, ti, d)] = model.NewBoolVar(f"dist_{vi}_{ti}_{d}")
            model.Add(sum(dist_var[(vi, ti, d)] for d in unique_districts) <= 1)
            for oi in range(num_orders):
                if (oi, vi, ti) in x:
                    o_dist = neighborhood_orders[oi].district
                    model.Add(x[(oi, vi, ti)] <= dist_var[(vi, ti, o_dist)])

        # Visited Outlets, Non-overlapping Intervals, and Delivery Windows
        unique_outlets = sorted({o.outlet_id for o in neighborhood_orders})
        visited_outlet: dict[tuple[int, int, str], cp_model.IntVar] = {}
        start_time_outlet: dict[tuple[int, int, str], cp_model.IntVar] = {}
        end_time_outlet: dict[tuple[int, int, str], cp_model.IntVar] = {}
        depot_return_var: dict[tuple[int, int], cp_model.IntVar] = {}
        dep_time_var: dict[tuple[int, int], cp_model.IntVar] = {}

        for vi, ti in vehicle_trip_slots:
            v = neigh_vehicles[vi]
            dep_time_var[(vi, ti)] = model.NewIntVar(0, 1440, f"dep_time_{vi}_{ti}")
            depot_return_var[(vi, ti)] = model.NewIntVar(0, 1440, f"depot_return_{vi}_{ti}")
            model.Add(depot_return_var[(vi, ti)] <= 1440).OnlyEnforceIf(trip_active[(vi, ti)])

            v_avail_min = 0
            if v.earliest_available_time:
                dt_avail = parse_iso_or_time_str(v.earliest_available_time, context.planning_date, context.timezone)
                if dt_avail:
                    v_avail_min = dt_avail.hour * 60 + dt_avail.minute

            if ti == 1:
                model.Add(dep_time_var[(vi, 1)] >= max(v_avail_min, 240)).OnlyEnforceIf(brand_var[(vi, 1, Brand.FRESH)])
                model.Add(dep_time_var[(vi, 1)] >= max(v_avail_min, 390)).OnlyEnforceIf(brand_var[(vi, 1, Brand.STYLE)])
                model.Add(dep_time_var[(vi, 1)] >= max(v_avail_min, 390)).OnlyEnforceIf(brand_var[(vi, 1, Brand.TECH)])
            else:
                turnaround = int(round(context.depot_turnaround_duration_min))
                model.Add(dep_time_var[(vi, 2)] >= depot_return_var[(vi, 1)] + turnaround).OnlyEnforceIf(trip_active[(vi, 2)])
                model.Add(dep_time_var[(vi, 2)] >= max(v_avail_min, 240)).OnlyEnforceIf(brand_var[(vi, 2, Brand.FRESH)])
                model.Add(dep_time_var[(vi, 2)] >= max(v_avail_min, 390)).OnlyEnforceIf(brand_var[(vi, 2, Brand.STYLE)])
                model.Add(dep_time_var[(vi, 2)] >= max(v_avail_min, 390)).OnlyEnforceIf(brand_var[(vi, 2, Brand.TECH)])

            intervals_for_slot = []

            for u_id in unique_outlets:
                u_orders = [oi for oi, o in enumerate(neighborhood_orders) if o.outlet_id == u_id and (oi, vi, ti) in x]
                if not u_orders:
                    continue
                vis = model.NewBoolVar(f"vis_{vi}_{ti}_{u_id}")
                visited_outlet[(vi, ti, u_id)] = vis
                model.Add(sum(x[(oi, vi, ti)] for oi in u_orders) >= vis)
                for oi in u_orders:
                    model.Add(x[(oi, vi, ti)] <= vis)

                u_obj = outlets.get(u_id)
                dock = u_obj.dock_type if u_obj else neighborhood_orders[u_orders[0]].dock_type

                dur_by_brand = {}
                for b in [Brand.FRESH, Brand.STYLE, Brand.TECH]:
                    if (b, dock) in allowances:
                        dur_by_brand[b] = int(round(allowances[(b, dock)]))

                if not dur_by_brand:
                    raise ValueError(
                        f"Missing service allowance for dock type {dock.value!r} at outlet {u_id!r}. "
                        f"Ensure service_allowance.csv covers all (brand, dock_type) combinations used."
                    )

                o_dist = neighborhood_orders[u_orders[0]].district
                travel = travel_data.get((o_dist, v.depot))
                tt_inter = int(round(travel.inter_stop_freeflow_min)) if travel else 0
                tt_outbound = int(round(travel.depot_to_district_freeflow_min)) if travel else 0

                min_dur = min(dur_by_brand.values()) + tt_inter
                max_dur = max(dur_by_brand.values()) + tt_inter

                dur_var = model.NewIntVar(min_dur, max_dur, f"dur_{vi}_{ti}_{u_id}")
                for b in [Brand.FRESH, Brand.STYLE, Brand.TECH]:
                    if b in dur_by_brand:
                        model.Add(dur_var == dur_by_brand[b] + tt_inter).OnlyEnforceIf(brand_var[(vi, ti, b)])
                    else:
                        model.Add(brand_var[(vi, ti, b)] == 0).OnlyEnforceIf(vis)

                start_u = model.NewIntVar(0, 1440, f"start_{vi}_{ti}_{u_id}")
                end_u = model.NewIntVar(0, 1440, f"end_{vi}_{ti}_{u_id}")
                start_time_outlet[(vi, ti, u_id)] = start_u
                end_time_outlet[(vi, ti, u_id)] = end_u

                iv = model.NewOptionalIntervalVar(start_u, dur_var, end_u, vis, f"iv_{vi}_{ti}_{u_id}")
                intervals_for_slot.append(iv)

                model.Add(start_u >= dep_time_var[(vi, ti)] + tt_outbound).OnlyEnforceIf(vis)

                w_open_min = 0
                w_close_min = 1440
                w_open_str = u_obj.window_open_time if u_obj and u_obj.window_open_time else neighborhood_orders[u_orders[0]].window_open_time
                w_close_str = u_obj.window_close_time if u_obj and u_obj.window_close_time else neighborhood_orders[u_orders[0]].window_close_time
                if w_open_str:
                    dt_o = parse_iso_or_time_str(w_open_str, context.planning_date, context.timezone)
                    if dt_o:
                        w_open_min = dt_o.hour * 60 + dt_o.minute
                if w_close_str:
                    dt_c = parse_iso_or_time_str(w_close_str, context.planning_date, context.timezone)
                    if dt_c:
                        w_close_min = dt_c.hour * 60 + dt_c.minute

                svc_end_u = model.NewIntVar(0, 1440, f"svc_end_{vi}_{ti}_{u_id}")
                for b in [Brand.FRESH, Brand.STYLE, Brand.TECH]:
                    if b in dur_by_brand:
                        model.Add(svc_end_u == start_u + dur_by_brand[b]).OnlyEnforceIf(brand_var[(vi, ti, b)])

                model.Add(start_u >= w_open_min).OnlyEnforceIf(vis)

                if context.window_policy == WindowPolicy.SERVICE_END_BEFORE_CLOSE:
                    model.Add(svc_end_u <= w_close_min).OnlyEnforceIf(vis)
                    model.Add(svc_end_u <= 480).OnlyEnforceIf([vis, brand_var[(vi, ti, Brand.FRESH)]])
                else:
                    model.Add(start_u <= w_close_min).OnlyEnforceIf(vis)
                    model.Add(start_u <= 480).OnlyEnforceIf([vis, brand_var[(vi, ti, Brand.FRESH)]])

                model.Add(depot_return_var[(vi, ti)] >= svc_end_u + tt_outbound).OnlyEnforceIf(vis)

            if intervals_for_slot:
                model.AddNoOverlap(intervals_for_slot)

        # Exact distance & fuel constraints per vehicle
        # Distance = outbound + (visits - 1)*inter_stop + return = 2*depot_to_district - inter_stop + sum(visits)*inter_stop
        all_fuel_terms = []
        for vi, v in enumerate(neigh_vehicles):
            prior_fuel = (v.weekly_fuel_used_l if v.weekly_fuel_used_l is not None else 0.0) + (
                v.external_reservations_l if v.external_reservations_l is not None else 0.0
            )
            avail_fuel = max(0.0, v.weekly_fuel_quota_l - prior_fuel)
            km_per_l = v.km_per_l
            if km_per_l is None or km_per_l <= 0:
                raise ValueError(f"Vehicle {v.vehicle_id} has invalid or missing km_per_l: {km_per_l}")

            v_fuel_terms = []
            for ti in range(1, min(v.remaining_trips, 2) + 1):
                for d in unique_districts:
                    travel = travel_data.get((d, v.depot))
                    if travel:
                        base_dist = 2.0 * travel.depot_to_district_km - travel.inter_stop_km
                        base_fuel = base_dist / km_per_l
                        scaled_term = int(round(base_fuel * 1000)) * dist_var[(vi, ti, d)]
                        v_fuel_terms.append(scaled_term)
                        all_fuel_terms.append(scaled_term)

                for u_id in unique_outlets:
                    if (vi, ti, u_id) in visited_outlet:
                        u_obj = outlets.get(u_id)
                        o_dist = u_obj.district if u_obj else unique_districts[0]
                        travel = travel_data.get((o_dist, v.depot))
                        inter_km = travel.inter_stop_km if travel else 0.0
                        inter_fuel = inter_km / km_per_l
                        scaled_inter = int(round(inter_fuel * 1000)) * visited_outlet[(vi, ti, u_id)]
                        v_fuel_terms.append(scaled_inter)
                        all_fuel_terms.append(scaled_inter)

            if v_fuel_terms:
                model.Add(sum(v_fuel_terms) <= int(round(avail_fuel * 1000)))

        # Multi-objective Lexicographic Search
        # Phase 1: Minimize deferral penalty (Maximize priority of served orders)
        served_vars: list[cp_model.IntVar] = []
        pen_terms = []
        for oi in range(num_orders):
            assigned_slots = [x[(oi, vi, ti)] for vi, ti in vehicle_trip_slots if (oi, vi, ti) in x]
            served_oi = model.NewBoolVar(f"served_{oi}")
            served_vars.append(served_oi)
            if assigned_slots:
                model.Add(served_oi == sum(assigned_slots))
                pen = int(round(_order_priority_key(neighborhood_orders[oi], config) * 100))
                pen_terms.append(pen * served_oi)
            else:
                model.Add(served_oi == 0)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_s
        solver.parameters.num_workers = 4

        # Step 1: Maximize Deferral Penalty Saved
        model.Maximize(sum(pen_terms))
        status = solver.Solve(model)
        status_name = solver.StatusName(status)
        stage_info["raw_solver_status"] = status_name

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            stage_info["outcome"] = "NO_FEASIBLE_IMPROVEMENT" if status == cp_model.INFEASIBLE else "TIMEOUT_OR_NO_SOLUTION"
            stage_info["rejection_or_skip_reason"] = f"CP-SAT solver returned {status_name} without an improving candidate."
            stage_info["runtime_seconds"] = round(time.perf_counter() - t_start, 4)
            return incumbent_plan_state, stage_info

        # Step 2: Maximize Served Order Count
        best_pen_val = int(round(solver.Value(sum(pen_terms))))
        model.Add(sum(pen_terms) >= best_pen_val)
        model.Maximize(sum(served_vars))
        status2 = solver.Solve(model)
        if status2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            status_name = solver.StatusName(status2)
            stage_info["raw_solver_status"] = status_name
            best_served_val = int(round(solver.Value(sum(served_vars))))
            model.Add(sum(served_vars) >= best_served_val)

            # Step 3: Minimize Fuel Consumed
            if all_fuel_terms:
                model.Minimize(sum(all_fuel_terms))
                status3 = solver.Solve(model)
                if status3 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                    status_name = solver.StatusName(status3)
                    stage_info["raw_solver_status"] = status_name

        # Candidate solution found -> reconstruct and evaluate schedules
        new_vehicle_timelines: list[VehicleScheduleTimeline] = []
        new_trip_schedules: list[EvaluatedTripSchedule] = []

        for vi, v in enumerate(neigh_vehicles):
            v_trips: list[EvaluatedTripSchedule] = []
            for ti in range(1, min(v.remaining_trips, 2) + 1):
                if solver.Value(trip_active[(vi, ti)]) != 1:
                    continue
                slot_orders = [
                    neighborhood_orders[oi] for oi in range(num_orders)
                    if (oi, vi, ti) in x and solver.Value(x[(oi, vi, ti)]) == 1
                ]
                if not slot_orders:
                    continue

                brand = Brand.STYLE
                for b in (Brand.FRESH, Brand.STYLE, Brand.TECH):
                    if solver.Value(brand_var[(vi, ti, b)]) == 1:
                        brand = b
                        break

                district = next(d for d in unique_districts if solver.Value(dist_var[(vi, ti, d)]) == 1)

                visited_outlets_with_time = []
                for u_id in unique_outlets:
                    if (vi, ti, u_id) in visited_outlet and solver.Value(visited_outlet[(vi, ti, u_id)]) == 1:
                        t_st = solver.Value(start_time_outlet[(vi, ti, u_id)])
                        visited_outlets_with_time.append((u_id, t_st))
                visited_outlets_with_time.sort(key=lambda item: item[1])
                stop_seq = [item[0] for item in visited_outlets_with_time]

                dep_min = int(round(solver.Value(dep_time_var[(vi, ti)])))
                dep_iso = f"{context.planning_date}T{dep_min // 60:02d}:{dep_min % 60:02d}:00"

                sched = evaluate_trip_schedule(
                    vehicle=v,
                    trip_number=ti,
                    orders=slot_orders,
                    brand=brand,
                    district=district,
                    depot=v.depot,
                    departure_time_iso=dep_iso,
                    travel_data=travel_data,
                    outlets=outlets,
                    allowances=allowances,
                    context=context,
                    stop_sequence=stop_seq,
                )
                v_trips.append(sched)

            tl = evaluate_vehicle_timeline(v, v_trips, context)
            new_vehicle_timelines.append(tl)
            new_trip_schedules.extend(v_trips)

        # Merge with fixed outside vehicles
        merged_timelines = [
            tl for tl in incumbent_plan_state.get("timelines", []) if tl.vehicle_id not in candidate_vids
        ] + new_vehicle_timelines

        # Independent Operational Validation with full authoritative inputs
        candidate_val_res = validate_operational_plan(
            orders=orders,
            timelines=merged_timelines,
            context=context,
            fleet=fleet,
            travel_data=travel_data,
            outlets=outlets,
            allowances=allowances,
        )
        if not candidate_val_res.valid:
            stage_info["outcome"] = "REJECTED_INVALID"
            stage_info["rejection_or_skip_reason"] = (
                f"CP-SAT candidate failed independent operational validation: "
                f"{[v.rule for v in candidate_val_res.violations]}"
            )
            stage_info["runtime_seconds"] = round(time.perf_counter() - t_start, 4)
            return incumbent_plan_state, stage_info

        # Check objective improvement
        candidate_assigned_refs = {
            ref for tl in merged_timelines for tr in tl.trips for ref in tr.assigned_order_refs
        }
        candidate_penalty = sum(
            _order_priority_key(o, config) for o in orders if o.order_ref not in candidate_assigned_refs
        )
        candidate_served = len(candidate_assigned_refs)
        candidate_fuel = sum(tr.fuel_consumed_l for tl in merged_timelines for tr in tl.trips)
        incumbent_fuel = sum(tr.fuel_consumed_l for tr in incumbent_plan_state.get("trip_schedules", []))

        # Consistent documented objective tuple: (penalty, -served_count, fuel)
        cand_obj = (round(candidate_penalty, 4), -candidate_served, round(candidate_fuel, 4))
        inc_obj = (round(incumbent_penalty, 4), -incumbent_served, round(incumbent_fuel, 4))

        if cand_obj >= inc_obj:
            stage_info["outcome"] = "REJECTED_NO_IMPROVEMENT"
            stage_info["rejection_or_skip_reason"] = (
                f"CP-SAT candidate objective {cand_obj} did not strictly improve incumbent {inc_obj}."
            )
            stage_info["runtime_seconds"] = round(time.perf_counter() - t_start, 4)
            return incumbent_plan_state, stage_info

        # Candidate accepted!
        all_merged_trips = [
            tr for tr in incumbent_plan_state.get("trip_schedules", []) if tr.vehicle_id not in candidate_vids
        ] + new_trip_schedules

        improved_state = {
            "trip_schedules": all_merged_trips,
            "timelines": merged_timelines,
            "validation_result": candidate_val_res,
            "assigned_orders": candidate_assigned_refs,
        }

        stage_info["outcome"] = "ACCEPTED"
        stage_info["improvement_accepted"] = True
        stage_info["final_deferral_penalty"] = round(candidate_penalty, 2)
        stage_info["final_served_count"] = candidate_served
        stage_info["runtime_seconds"] = round(time.perf_counter() - t_start, 4)

        return improved_state, stage_info

    except Exception as ex:
        stage_info["outcome"] = "ERROR"
        stage_info["rejection_or_skip_reason"] = f"Unexpected exception during CP-SAT stage: {str(ex)}"
        stage_info["runtime_seconds"] = round(time.perf_counter() - t_start, 4)
        return incumbent_plan_state, stage_info

