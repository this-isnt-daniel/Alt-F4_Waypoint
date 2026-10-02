"""
Waypoint Optimizer — Hackathon Daily Draft Planner
==================================================
Produces operationally feasible daily delivery draft plans for the Waypoint Web Application.

Hybrid Operational Workflow:
  1. Validate all inputs against authoritative reference data.
  2. Run a multi-start greedy portfolio (5 orderings) to build the best
     feasible greedy baseline plan.
  3. Run operational targeted CP-SAT improvement on the top-priority deferred
     orders and a bounded vehicle neighborhood (up to 3 deferred orders,
     up to 4 vehicles).
  4. Independently validate the CP-SAT candidate using the full operational
     validator (capacity, volume, refrigeration, depot, access, windows,
     chronology, fuel, line-item demand).
  5. Accept the CP-SAT candidate only when it is valid AND strictly improves
     the lexicographic objective (deferral penalty, served count, fuel).
  6. If CP-SAT is infeasible, invalid, does not improve, times out, or raises
     any exception, return the original greedy plan unchanged.
  7. Label the final output 'hybrid_greedy_targeted_cpsat' when accepted,
     'multistart_greedy_operational' otherwise.

Guarantees:
  - Atomic whole-order allocations (splits permitted only via explicit manual edits).
  - Enforces vehicle selection/availability, weight, volume, refrigeration, access,
    depot containment, trip limits, and single brand/district per trip.
  - Active chronological feasibility guidance: Stop arrivals, waiting times, delivery
    windows, depot turnaround, and cumulative weekly fuel quota actively guide placement.
  - Generates Driver chronological itinerary and Loader reverse LIFO manifest.
  - Fully independent operational validation after every candidate plan.
  - Non-mutating: never writes to databases or modifies input objects.
"""
from __future__ import annotations

import copy
import time
from typing import Any, Optional

from waypoint_optimizer.adapters.csv_adapter import ReferenceData
from waypoint_optimizer.input_validation import (
    InputErrorDetail, InputValidationError, validate_operational_inputs,
)
from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, OrderAllocationStatus,
    Outlet, ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleStatus, VehicleType, classify_order_allocation,
)
from waypoint_optimizer.objective import defer_penalty
from waypoint_optimizer.operational.models import (
    DEFAULT_FRESH_DEPARTURE_TIME, DEFAULT_STYLE_TECH_DEPARTURE_TIME,
    DEFAULT_TIMEZONE, ESTIMATED_DEPOT_TURNAROUND_MIN, EvaluatedTripSchedule,
    OperationalContext, OperationalMissingData, OperationalStop,
    OperationalViolation, TravelPolicy, VehicleScheduleTimeline, WindowPolicy,
)
from waypoint_optimizer.operational.schedule_evaluator import (
    evaluate_trip_schedule, parse_iso_or_time_str,
)
from waypoint_optimizer.operational.timeline import evaluate_vehicle_timeline
from waypoint_optimizer.operational.validator import (
    OperationalValidationResult, validate_operational_plan,
)
from waypoint_optimizer.operational.draft_editor import _build_driver_itinerary


def _order_priority_key(order: Order, config: Optional[OptimizerConfig] = None) -> float:
    """Computes priority weighting for greedy candidate sorting."""
    weight = 0.0
    if order.deferred_yesterday:
        weight += 1000.0
    weight += order.days_since_last_served * 100.0
    if config:
        weight += defer_penalty(order, config)
    else:
        weight += float(order.order_units)
    return weight


def _get_candidate_orderings(orders: list[Order], config: Optional[OptimizerConfig] = None) -> list[list[Order]]:
    """Generates portfolio ordering heuristics for operational greedy search."""
    orderings: list[list[Order]] = []

    # 1. Highest priority score first
    orderings.append(sorted(orders, key=lambda o: _order_priority_key(o, config), reverse=True))

    # 2. Earliest window close first (urgency ascending)
    def window_close_key(o: Order) -> str:
        return o.window_close_time or "23:59"
    orderings.append(sorted(orders, key=lambda o: (window_close_key(o), -_order_priority_key(o, config))))

    # 3. Density / Payload descending (weight & volume)
    orderings.append(sorted(orders, key=lambda o: (o.order_weight_kg + o.order_volume_m3 * 100.0, _order_priority_key(o, config)), reverse=True))

    # 4. District and Outlet clustering (group by district, then priority)
    orderings.append(sorted(orders, key=lambda o: (o.district, -_order_priority_key(o, config))))

    # 5. Units descending
    orderings.append(sorted(orders, key=lambda o: (o.order_units, -_order_priority_key(o, config)), reverse=True))

    return orderings


def _diagnose_deferral_reason(
    order: Order,
    fleet: list[Vehicle],
    travel_data: dict[tuple[str, str], DistrictTravel],
    outlets: dict[str, Outlet],
    allowances: dict[tuple[Brand, DockType], float],
    context: OperationalContext,
) -> tuple[str, str]:
    """Determines structured typed deferral reason with quantitative evidence."""
    # Check depot travel
    if (order.district, order.depot) not in travel_data:
        return (
            "NO_COMPATIBLE_TRAVEL_DATA",
            f"No travel route between depot {order.depot!r} and district {order.district!r}.",
        )

    # Check vehicle compatibility
    compatible_vehicles = []
    for v in fleet:
        if not v.is_available or not v.is_selected_for_planning:
            continue
        if v.depot != order.depot:
            continue
        if order.temp_requirement == TempRequirement.CHILLED and v.temp != TempSpec.REEFER:
            continue
        if order.parking_constraint == ParkingConstraint.VAN_ONLY and v.type != VehicleType.VAN:
            continue
        compatible_vehicles.append(v)

    if not compatible_vehicles:
        if order.temp_requirement == TempRequirement.CHILLED:
            return (
                "REEFER_CAPACITY_EXHAUSTED",
                "Chilled order has no available refrigerated vehicles at its depot.",
            )
        if order.parking_constraint == ParkingConstraint.VAN_ONLY:
            return (
                "VAN_CAPACITY_EXHAUSTED",
                "van_only access requirement has no available vans at its depot.",
            )
        return (
            "NO_COMPATIBLE_VEHICLE",
            f"No available vehicles matching depot {order.depot!r}, temp {order.temp_requirement.value!r}, and access {order.parking_constraint.value!r}.",
        )

    # Check if order exceeds payload ratings of all compatible vehicles
    if all(order.order_weight_kg > v.weight_cap_kg for v in compatible_vehicles):
        return (
            "WEIGHT_CAPACITY",
            f"Order weight {order.order_weight_kg:.1f} kg exceeds all compatible vehicle payloads.",
        )
    if all(order.order_volume_m3 > v.volume_cap_m3 for v in compatible_vehicles):
        return (
            "VOLUME_CAPACITY",
            f"Order volume {order.order_volume_m3:.2f} m3 exceeds all compatible vehicle volume capacities.",
        )

    return (
        "NOT_SELECTED_BY_HEURISTIC",
        "Could not be placed within available vehicle trip slots without violating delivery windows or fuel quotas.",
    )


def _build_loader_manifest(stops: list[OperationalStop], orders_by_ref: dict[str, Order]) -> list[dict[str, Any]]:
    """
    Constructs warehouse loading sequence in reverse delivery order (LIFO).
    Stop N is loaded first, ..., Stop 1 is loaded last (near vehicle doors).
    """
    manifest: list[dict[str, Any]] = []
    step_num = 1

    # Reverse order of delivery: highest stop_number first
    reversed_stops = sorted(stops, key=lambda s: s.stop_number, reverse=True)

    for stop in reversed_stops:
        for item in stop.line_items_delivered:
            oref = item["order_ref"]
            parent_order = orders_by_ref.get(oref)
            temp_req = parent_order.temp_requirement.value if parent_order else "ambient"

            manifest.append({
                "loading_step": step_num,
                "delivering_stop_number": stop.stop_number,
                "order_ref": oref,
                "outlet_id": stop.outlet_id,
                "line_item_id": item.get("line_item_id", f"{oref}-ALL"),
                "description": item.get("description", "Standard Cargo"),
                "quantity": item.get("quantity", 0),
                "quantity_unit": item.get("quantity_unit", "units"),
                "weight_kg": round(float(item.get("quantity", 0)) * float(item.get("unit_weight_kg", 0.0)), 2),
                "volume_m3": round(float(item.get("quantity", 0)) * float(item.get("unit_volume_m3", 0.0)), 3),
                "temp_requirement": temp_req,
            })
            step_num += 1

    return manifest


def _determine_trip1_departure(v: Vehicle, brand: Brand, context: OperationalContext) -> str:
    default_release = (
        DEFAULT_FRESH_DEPARTURE_TIME if brand == Brand.FRESH else DEFAULT_STYLE_TECH_DEPARTURE_TIME
    )
    rel_dt = parse_iso_or_time_str(default_release, context.planning_date, context.timezone)
    if v.earliest_available_time:
        avail_dt = parse_iso_or_time_str(v.earliest_available_time, context.planning_date, context.timezone)
        if avail_dt and rel_dt and avail_dt > rel_dt:
            return avail_dt.isoformat()
    return rel_dt.isoformat() if rel_dt else default_release


def score_plan_objective(penalty: float, served_count: int, fuel_l: float) -> tuple[float, int, float]:
    """
    Consistent documented lexicographic comparison key:
    1. Minimize penalty
    2. Maximize served orders (-served_count)
    3. Minimize estimated fuel
    """
    return (round(penalty, 4), -served_count, round(fuel_l, 4))


def generate_daily_draft_plan(
    orders: list[Order],
    fleet: list[Vehicle],
    reference_data: ReferenceData,
    context: OperationalContext,
    config: Optional[OptimizerConfig] = None,
    enable_targeted_cpsat: bool = True,
    targeted_cpsat_time_limit_s: float = 5.0,
) -> dict[str, Any]:
    """
    Generates an operationally feasible daily delivery draft plan using the
    hybrid multi-start greedy + targeted CP-SAT operational engine.

    Workflow:
      1. Validates inputs against authoritative reference data.
      2. Runs portfolio greedy search (5 orderings) guided by chronological
         window and fuel feasibility; selects best feasible baseline.
      3. Runs targeted CP-SAT improvement stage on top-priority deferred
         orders (up to 3) and a bounded vehicle neighborhood (up to 4).
      4. Independently validates the CP-SAT candidate plan.
      5. Accepts CP-SAT result only when valid AND strictly improving.
      6. Falls back to greedy baseline on any CP-SAT failure.
      7. Builds driver itineraries and reverse LIFO loading manifests.
      8. Returns a non-mutating strict JSON-serializable draft plan.

    Args:
        orders: Confirmed backend orders (authoritative).
        fleet: Live fleet state including remaining trips and fuel.
        reference_data: Loaded from real CSV files (outlets, travel, allowances).
        context: Operational context (date, timezone, policy).
        config: Optional optimizer configuration.
        enable_targeted_cpsat: Enable the hybrid CP-SAT improvement stage.
            Defaults to True. Set False to run greedy-only.
        targeted_cpsat_time_limit_s: CP-SAT per-invocation time budget.
    """
    t_start = time.perf_counter()

    # 1. Strict Operational Input Validation at Python API Boundary
    validate_operational_inputs(
        orders=orders,
        fleet=fleet,
        reference_data=reference_data,
        context=context,
        config=config,
    )

    # 2. Prepare Reference Indexes
    travel_data = {(t.district, t.depot): t for t in reference_data.travel}
    outlets = reference_data.outlets
    allowances = {(a.brand, a.dock_type): a.service_allowance_min for a in reference_data.allowances}
    orders_by_ref = {o.order_ref: o for o in orders}

    # 3. Identify Priority-Boosted Orders
    priority_boosted_orders: list[dict[str, str]] = []
    for o in orders:
        reasons = []
        if o.deferred_yesterday:
            reasons.append("deferred_yesterday")
        if o.days_since_last_served >= 3:
            reasons.append(f"days_since_last_served={o.days_since_last_served}")
        if reasons:
            priority_boosted_orders.append({
                "order_ref": o.order_ref,
                "reason": ", ".join(reasons),
            })

    # 4. Filter Eligible Fleet
    # Only vehicles that are mechanically available, selected by dispatcher, and have remaining trips
    eligible_vehicles = [
        v for v in fleet
        if v.is_available and v.is_selected_for_planning and v.remaining_trips > 0
    ]

    if not eligible_vehicles or not orders:
        # Zero feasible fleet or orders
        runtime = time.perf_counter() - t_start
        return {
            "plan_id": f"PLAN-{context.planning_date}-V1",
            "status": "FEASIBLE" if not orders else "INVALID",
            "planning_date": context.planning_date,
            "engine_mode": "hackathon_operational",
            "algorithm": "multistart_greedy_operational",
            "runtime_seconds": round(runtime, 4),
            "order_counts": {
                "total_orders": len(orders),
                "fully_served_orders": 0,
                "partially_served_orders": 0,
                "fully_deferred_orders": len(orders),
            },
            "quantity_totals": {
                "requested_units": sum(o.order_units for o in orders),
                "assigned_units": 0,
                "deferred_units": sum(o.order_units for o in orders),
            },
            "priority_boosted_orders": priority_boosted_orders,
            "metrics": {
                "total_weight_kg": 0.0,
                "total_volume_m3": 0.0,
                "total_distance_km": 0.0,
                "total_fuel_litres": 0.0,
                "trips_created": 0,
                "vehicles_used": 0,
            },
            "trips": [],
            "deferred_orders": [
                {
                    "order_ref": o.order_ref,
                    "outlet_id": o.outlet_id,
                    "deferred_quantity": o.order_units,
                    "reason": "NO_COMPATIBLE_VEHICLE",
                    "evidence_detail": "No eligible fleet vehicles available for dispatch.",
                }
                for o in orders
            ],
            "validation": {
                "valid": len(orders) == 0,
                "errors": [{"rule": "NO_AVAILABLE_FLEET", "detail": "No vehicles selected or available."}] if orders else [],
            },
        }

    # 5. Multi-Start Greedy Portfolio Search
    candidate_orderings = _get_candidate_orderings(orders, config)
    best_plan_state: Optional[dict[str, Any]] = None
    best_plan_objective: Optional[tuple[float, int, float]] = None

    for ordering_idx, order_list in enumerate(candidate_orderings):
        # State: vehicle_id -> list of trips; trip = {"brand": Brand, "district": str, "orders": list[Order]}
        vehicle_trips: dict[str, list[dict[str, Any]]] = {v.vehicle_id: [] for v in eligible_vehicles}
        assigned_orders: set[str] = set()

        for candidate_order in order_list:
            placed = False
            best_placement: Optional[tuple[str, int, int]] = None  # (vehicle_id, trip_idx, stop_pos)
            best_placement_cost = float("inf")

            # Try eligible vehicles
            for v in eligible_vehicles:
                # Basic vehicle compatibility checks
                if v.depot != candidate_order.depot:
                    continue
                if candidate_order.temp_requirement == TempRequirement.CHILLED and v.temp != TempSpec.REEFER:
                    continue
                if candidate_order.parking_constraint == ParkingConstraint.VAN_ONLY and v.type != VehicleType.VAN:
                    continue

                trips = vehicle_trips[v.vehicle_id]

                # Option A: Try inserting into existing trips
                for t_idx, trip_dict in enumerate(trips):
                    # Check brand and district homogeneity
                    if trip_dict["brand"] != candidate_order.brand or trip_dict["district"] != candidate_order.district:
                        continue

                    # Check weight and volume ratings
                    tentative_orders = trip_dict["orders"] + [candidate_order]
                    if sum(o.order_weight_kg for o in tentative_orders) > v.weight_cap_kg:
                        continue
                    if sum(o.order_volume_m3 for o in tentative_orders) > v.volume_cap_m3:
                        continue

                    # Determine candidate stop sequences
                    # If outlet is already visited, test consolidation directly
                    outlet_ids = [o.outlet_id for o in trip_dict["orders"]]
                    if candidate_order.outlet_id in outlet_ids:
                        test_orders_seqs = [tentative_orders]
                    else:
                        # Test appending at end, or inserting at positions
                        test_orders_seqs = [tentative_orders]
                        if len(trip_dict["orders"]) > 1:
                            test_orders_seqs.append([candidate_order] + trip_dict["orders"])

                    for seq in test_orders_seqs:
                        # Construct tentative trip schedule
                        if t_idx == 0:
                            trip_dep_time = _determine_trip1_departure(v, trip_dict["brand"], context)
                        else:
                            t1_dict = trips[0]
                            t1_dep = _determine_trip1_departure(v, t1_dict["brand"], context)
                            t1_sched = evaluate_trip_schedule(
                                vehicle=v,
                                trip_number=1,
                                orders=t1_dict["orders"],
                                brand=t1_dict["brand"],
                                district=t1_dict["district"],
                                depot=v.depot,
                                departure_time_iso=t1_dep,
                                travel_data=travel_data,
                                outlets=outlets,
                                allowances=allowances,
                                context=context,
                            )
                            trip_dep_time = t1_sched.vehicle_next_available_iso
                        tentative_sched = evaluate_trip_schedule(
                            vehicle=v,
                            trip_number=t_idx + 1,
                            orders=seq,
                            brand=trip_dict["brand"],
                            district=trip_dict["district"],
                            depot=v.depot,
                            departure_time_iso=trip_dep_time,
                            travel_data=travel_data,
                            outlets=outlets,
                            allowances=allowances,
                            context=context,
                        )

                        if not tentative_sched.is_feasible:
                            continue

                        # Evaluate entire vehicle timeline with tentative trip
                        tentative_trip_scheds = []
                        for other_idx, other_t in enumerate(trips):
                            if other_idx == t_idx:
                                tentative_trip_scheds.append(tentative_sched)
                            else:
                                dep_t = (
                                    DEFAULT_FRESH_DEPARTURE_TIME if other_t["brand"] == Brand.FRESH
                                    else DEFAULT_STYLE_TECH_DEPARTURE_TIME
                                )
                                tentative_trip_scheds.append(evaluate_trip_schedule(
                                    vehicle=v,
                                    trip_number=other_idx + 1,
                                    orders=other_t["orders"],
                                    brand=other_t["brand"],
                                    district=other_t["district"],
                                    depot=v.depot,
                                    departure_time_iso=dep_t,
                                    travel_data=travel_data,
                                    outlets=outlets,
                                    allowances=allowances,
                                    context=context,
                                ))

                        timeline = evaluate_vehicle_timeline(v, tentative_trip_scheds, context)
                        if timeline.is_feasible:
                            cost = tentative_sched.total_distance_km
                            if cost < best_placement_cost:
                                best_placement_cost = cost
                                best_placement = (v.vehicle_id, t_idx, -1)  # -1 = existing trip
                            break

                # Option B: Try opening a new trip (if under vehicle remaining trips and <= 2)
                max_allowable_trips = min(2, v.remaining_trips)
                if best_placement is None and len(trips) < max_allowable_trips:
                    if candidate_order.order_weight_kg <= v.weight_cap_kg and candidate_order.order_volume_m3 <= v.volume_cap_m3:
                        new_trip_num = len(trips) + 1
                        # If vehicle already has Trip 1, Trip 2 departure must be scheduled after Trip 1
                        if len(trips) == 1:
                            # Evaluate existing Trip 1 to find when vehicle returns + turnaround
                            t1_dict = trips[0]
                            t1_dep = _determine_trip1_departure(v, t1_dict["brand"], context)
                            t1_sched = evaluate_trip_schedule(
                                vehicle=v,
                                trip_number=1,
                                orders=t1_dict["orders"],
                                brand=t1_dict["brand"],
                                district=t1_dict["district"],
                                depot=v.depot,
                                departure_time_iso=t1_dep,
                                travel_data=travel_data,
                                outlets=outlets,
                                allowances=allowances,
                                context=context,
                            )
                            tentative_t2_dep = t1_sched.vehicle_next_available_iso
                        else:
                            tentative_t2_dep = _determine_trip1_departure(v, candidate_order.brand, context)

                        tentative_sched = evaluate_trip_schedule(
                            vehicle=v,
                            trip_number=new_trip_num,
                            orders=[candidate_order],
                            brand=candidate_order.brand,
                            district=candidate_order.district,
                            depot=v.depot,
                            departure_time_iso=tentative_t2_dep,
                            travel_data=travel_data,
                            outlets=outlets,
                            allowances=allowances,
                            context=context,
                        )

                        if tentative_sched.is_feasible:
                            tentative_trip_scheds = []
                            if len(trips) == 1:
                                tentative_trip_scheds.append(t1_sched)
                            tentative_trip_scheds.append(tentative_sched)

                            timeline = evaluate_vehicle_timeline(v, tentative_trip_scheds, context)
                            if timeline.is_feasible:
                                # New trip penalty encourages packing existing trips first
                                cost = 1000.0 + tentative_sched.total_distance_km
                                if cost < best_placement_cost:
                                    best_placement_cost = cost
                                    best_placement = (v.vehicle_id, -1, -1)  # -1 = new trip

            # Apply best placement found
            if best_placement is not None:
                vid, t_idx, _ = best_placement
                if t_idx >= 0:
                    vehicle_trips[vid][t_idx]["orders"].append(candidate_order)
                else:
                    vehicle_trips[vid].append({
                        "brand": candidate_order.brand,
                        "district": candidate_order.district,
                        "orders": [candidate_order],
                    })
                assigned_orders.add(candidate_order.order_ref)

        # 6. Evaluate and Score Complete Plan for this Ordering
        all_trip_schedules: list[EvaluatedTripSchedule] = []
        all_vehicle_timelines: list[VehicleScheduleTimeline] = []

        vehicles_by_id = {v.vehicle_id: v for v in eligible_vehicles}
        for vid, tr_list in vehicle_trips.items():
            if not tr_list:
                continue
            v = vehicles_by_id[vid]
            v_trips_evaluated: list[EvaluatedTripSchedule] = []

            # First pass: schedule Trip 1
            t1_dep = _determine_trip1_departure(v, tr_list[0]["brand"], context)
            t1_sched = evaluate_trip_schedule(
                vehicle=v,
                trip_number=1,
                orders=tr_list[0]["orders"],
                brand=tr_list[0]["brand"],
                district=tr_list[0]["district"],
                depot=v.depot,
                departure_time_iso=t1_dep,
                travel_data=travel_data,
                outlets=outlets,
                allowances=allowances,
                context=context,
            )
            v_trips_evaluated.append(t1_sched)

            # Second pass: schedule Trip 2 if present
            if len(tr_list) > 1:
                t2_dep = t1_sched.vehicle_next_available_iso
                t2_sched = evaluate_trip_schedule(
                    vehicle=v,
                    trip_number=2,
                    orders=tr_list[1]["orders"],
                    brand=tr_list[1]["brand"],
                    district=tr_list[1]["district"],
                    depot=v.depot,
                    departure_time_iso=t2_dep,
                    travel_data=travel_data,
                    outlets=outlets,
                    allowances=allowances,
                    context=context,
                )
                v_trips_evaluated.append(t2_sched)

            timeline = evaluate_vehicle_timeline(v, v_trips_evaluated, context)
            all_vehicle_timelines.append(timeline)
            all_trip_schedules.extend(v_trips_evaluated)

        # Validate with independent operational validator
        val_result = validate_operational_plan(
            orders=orders,
            timelines=all_vehicle_timelines,
            context=context,
            fleet=fleet,
            travel_data=travel_data,
            outlets=outlets,
            allowances=allowances,
            config=config,
        )
        if val_result.valid:
            # Consistent documented objective tuple: (penalty, -served_count, fuel)
            deferred_penalty_sum = sum(
                _order_priority_key(o, config) for o in orders if o.order_ref not in assigned_orders
            )
            total_fuel = sum(t.fuel_consumed_l for t in all_trip_schedules)
            cand_objective = score_plan_objective(deferred_penalty_sum, len(assigned_orders), total_fuel)

            if best_plan_objective is None or cand_objective < best_plan_objective:
                best_plan_objective = cand_objective
                best_plan_state = {
                    "trip_schedules": all_trip_schedules,
                    "timelines": all_vehicle_timelines,
                    "validation_result": val_result,
                    "assigned_orders": assigned_orders,
                }

    # 7. Final Plan Extraction & Construction
    plan_id = f"PLAN-{context.planning_date}-V1"

    if best_plan_state is None:
        runtime_s = time.perf_counter() - t_start
        # Fallback if no feasible assignment could be formed
        return {
            "plan_id": plan_id,
            "status": "INVALID",
            "planning_date": context.planning_date,
            "engine_mode": "hackathon_operational",
            "algorithm": "multistart_greedy_operational",
            "targeted_cpsat_stage": {
                "executed": False,
                "neighborhood_size": {"target_deferred_orders": 0, "neighborhood_orders": 0, "vehicles": 0, "vehicle_ids": []},
                "raw_solver_status": "SKIPPED",
                "outcome": "SKIPPED_NO_GREEDY_SOLUTION",
                "improvement_accepted": False,
                "rejection_or_skip_reason": "No valid greedy plan could be formed.",
                "incumbent_deferral_penalty": 0.0,
                "final_deferral_penalty": 0.0,
                "incumbent_served_count": 0,
                "final_served_count": 0,
                "runtime_seconds": 0.0,
            },
            "runtime_seconds": round(runtime_s, 4),
            "order_counts": {
                "total_orders": len(orders),
                "fully_served_orders": 0,
                "partially_served_orders": 0,
                "fully_deferred_orders": len(orders),
            },
            "quantity_totals": {
                "requested_units": sum(o.order_units for o in orders),
                "assigned_units": 0,
                "deferred_units": sum(o.order_units for o in orders),
            },
            "priority_boosted_orders": priority_boosted_orders,
            "metrics": {
                "total_weight_kg": 0.0,
                "total_volume_m3": 0.0,
                "total_distance_km": 0.0,
                "total_fuel_litres": 0.0,
                "trips_created": 0,
                "vehicles_used": 0,
            },
            "trips": [],
            "deferred_orders": [
                {
                    "order_ref": o.order_ref,
                    "outlet_id": o.outlet_id,
                    "deferred_quantity": o.order_units,
                    "reason": "NOT_SELECTED_BY_HEURISTIC",
                    "evidence_detail": "No valid operational placement found under strict delivery windows.",
                    **({"line_items": [
                        {
                            "line_item_id": li.line_item_id,
                            "description": li.description,
                            "deferred_quantity": li.quantity,
                            "quantity_unit": li.quantity_unit,
                        }
                        for li in o.line_items
                    ]} if o.line_items else {}),
                }
                for o in orders
            ],
            "validation": {
                "valid": False,
                "errors": [{"rule": "SEARCH_EXHAUSTED", "detail": "Portfolio greedy search produced no valid plan."}],
            },
        }

    # Operational Targeted CP-SAT Improvement Stage
    current_plan_state = best_plan_state
    algorithm = "multistart_greedy_operational"
    targeted_cpsat_stage_info: dict[str, Any] = {
        "executed": False,
        "neighborhood_size": {"target_deferred_orders": 0, "neighborhood_orders": 0, "vehicles": 0, "vehicle_ids": []},
        "raw_solver_status": "NOT_RUN",
        "outcome": "SKIPPED_DISABLED",
        "improvement_accepted": False,
        "rejection_or_skip_reason": "Targeted CP-SAT improvement disabled by configuration.",
        "incumbent_deferral_penalty": round(sum(
            _order_priority_key(o, config) for o in orders if o.order_ref not in best_plan_state["assigned_orders"]
        ), 2),
        "final_deferral_penalty": round(sum(
            _order_priority_key(o, config) for o in orders if o.order_ref not in best_plan_state["assigned_orders"]
        ), 2),
        "incumbent_served_count": len(best_plan_state["assigned_orders"]),
        "final_served_count": len(best_plan_state["assigned_orders"]),
        "runtime_seconds": 0.0,
    }

    if enable_targeted_cpsat:
        try:
            from waypoint_optimizer.targeted_cpsat import operational_targeted_cpsat_improve
            improved_state, cpsat_stage_info = operational_targeted_cpsat_improve(
                incumbent_plan_state=best_plan_state,
                orders=orders,
                fleet=fleet,
                travel_data=travel_data,
                outlets=outlets,
                allowances=allowances,
                context=context,
                time_limit_s=targeted_cpsat_time_limit_s,
                config=config,
            )
            current_plan_state = improved_state
            targeted_cpsat_stage_info = cpsat_stage_info
            if cpsat_stage_info.get("improvement_accepted"):
                algorithm = "hybrid_greedy_targeted_cpsat"
        except Exception as _cpsat_exc:  # noqa: BLE001
            # Belt-and-suspenders: operational_targeted_cpsat_improve catches its
            # own exceptions, but if something escapes (e.g. import error, env issue),
            # we preserve the greedy baseline rather than crashing the planner.
            targeted_cpsat_stage_info.update({
                "executed": False,
                "outcome": "ERROR_FALLBACK_TO_GREEDY",
                "rejection_or_skip_reason": (
                    f"CP-SAT stage raised an unexpected exception; "
                    f"greedy baseline preserved. Error: {_cpsat_exc!r}"
                ),
            })

    total_runtime_s = time.perf_counter() - t_start

    return _build_plan_dict_from_schedules(
        plan_id=plan_id,
        plan_state=current_plan_state,
        orders=orders,
        fleet=fleet,
        travel_data=travel_data,
        outlets=outlets,
        allowances=allowances,
        context=context,
        priority_boosted_orders=priority_boosted_orders,
        runtime_s=total_runtime_s,
        algorithm=algorithm,
        targeted_cpsat_stage_info=targeted_cpsat_stage_info,
    )


def _build_plan_dict_from_schedules(
    plan_id: str,
    plan_state: dict[str, Any],
    orders: list[Order],
    fleet: list[Vehicle],
    travel_data: dict[tuple[str, str], DistrictTravel],
    outlets: dict[str, Outlet],
    allowances: dict[tuple[Brand, DockType], float],
    context: OperationalContext,
    priority_boosted_orders: list[str],
    runtime_s: float,
    algorithm: str,
    targeted_cpsat_stage_info: dict[str, Any] | str,
) -> dict[str, Any]:
    """Serializes plan schedules and timelines into strict JSON dictionary."""
    orders_by_ref = {o.order_ref: o for o in orders}
    output_trips: list[dict[str, Any]] = []
    vehicles_used_set: set[str] = set()

    for trip_sched in plan_state["trip_schedules"]:
        vehicles_used_set.add(trip_sched.vehicle_id)
        parent_v = next(v for v in fleet if v.vehicle_id == trip_sched.vehicle_id)

        # Build Driver Itinerary
        driver_itinerary = _build_driver_itinerary(trip_sched.stops)

        # Build Loader Reverse Manifest (LIFO)
        loader_manifest = _build_loader_manifest(trip_sched.stops, orders_by_ref)

        output_trips.append({
            "trip_id": f"{plan_id}-TRIP-{trip_sched.vehicle_id}-{trip_sched.trip_number}",
            "vehicle_id": trip_sched.vehicle_id,
            "trip_number": trip_sched.trip_number,
            "brand": trip_sched.brand.value,
            "district": trip_sched.district,
            "depot": trip_sched.depot,
            "departure_time_iso": trip_sched.departure_time_iso,
            "depot_return_arrival_iso": trip_sched.depot_return_arrival_iso,
            "vehicle_next_available_iso": trip_sched.vehicle_next_available_iso,
            "load_utilization": {
                "weight_kg": trip_sched.total_weight_kg,
                "weight_cap_kg": trip_sched.weight_cap_kg,
                "volume_m3": trip_sched.total_volume_m3,
                "volume_cap_m3": trip_sched.volume_cap_m3,
            },
            "fuel": {
                "distance_km": trip_sched.total_distance_km,
                "fuel_consumed_l": trip_sched.fuel_consumed_l,
                "weekly_quota_l": trip_sched.weekly_quota_l,
                "prior_used_l": parent_v.weekly_fuel_used_l or 0.0,
                "external_reservations_l": parent_v.external_reservations_l or 0.0,
                "cumulative_fuel_used_l": trip_sched.cumulative_fuel_used_l,
                "fuel_compliant": trip_sched.fuel_compliant,
            },
            "driver_itinerary": driver_itinerary,
            "loader_manifest": loader_manifest,
        })

    # Build Deferred Orders List
    deferred_orders_list: list[dict[str, Any]] = []
    assigned_refs = plan_state["assigned_orders"]
    for o in orders:
        if o.order_ref not in assigned_refs:
            reason_code, detail = _diagnose_deferral_reason(
                o, fleet, travel_data, outlets, allowances, context
            )
            deferred_item: dict[str, Any] = {
                "order_ref": o.order_ref,
                "outlet_id": o.outlet_id,
                "deferred_quantity": o.order_units,
                "deferred_weight_kg": o.order_weight_kg,
                "deferred_volume_m3": o.order_volume_m3,
                "reason": reason_code,
                "evidence_detail": detail,
            }
            if o.line_items:
                deferred_item["line_items"] = [
                    {
                        "line_item_id": li.line_item_id,
                        "description": li.description,
                        "deferred_quantity": li.quantity,
                        "quantity_unit": li.quantity_unit,
                    }
                    for li in o.line_items
                ]
            deferred_orders_list.append(deferred_item)

    # Summary Metrics
    total_weight = sum(t["load_utilization"]["weight_kg"] for t in output_trips)
    total_volume = sum(t["load_utilization"]["volume_m3"] for t in output_trips)
    total_distance = sum(t["fuel"]["distance_km"] for t in output_trips)
    total_fuel = sum(t["fuel"]["fuel_consumed_l"] for t in output_trips)

    val_res = plan_state["validation_result"]

    return {
        "plan_id": plan_id,
        "status": "FEASIBLE" if val_res.valid else "INVALID",
        "planning_date": context.planning_date,
        "engine_mode": "hackathon_operational",
        "algorithm": algorithm,
        "targeted_cpsat_stage": targeted_cpsat_stage_info,
        "runtime_seconds": round(runtime_s, 4),
        "order_counts": val_res.order_counts,
        "quantity_totals": val_res.quantity_totals,
        "quantity_totals_by_unit": getattr(val_res, "quantity_totals_by_unit", {}),
        "priority_boosted_orders": priority_boosted_orders,
        "travel_policy_assumptions": {
            "policy": context.travel_policy.value,
            "window_policy": context.window_policy.value,
            "depot_turnaround_duration_min": context.depot_turnaround_duration_min,
            "notice": (
                "Travel times and distances are estimated using static district averages from district_travel.csv. "
                "Depot return distance mirrors outbound distance. Cross-district travel is unsupported."
            ),
        },
        "metrics": {
            "total_weight_kg": round(total_weight, 2),
            "total_volume_m3": round(total_volume, 3),
            "total_distance_km": round(total_distance, 2),
            "total_fuel_litres": round(total_fuel, 2),
            "trips_created": len(output_trips),
            "vehicles_used": len(vehicles_used_set),
        },
        "trips": output_trips,
        "deferred_orders": deferred_orders_list,
        "validation": {
            "valid": val_res.valid,
            "status": "DRAFT — REQUIRES DISPATCHER APPROVAL" if val_res.valid else "INVALID",
            "is_dispatch_ready": False,  # Draft plan: requires Dispatcher review and approval
            "quantity_totals_by_unit": getattr(val_res, "quantity_totals_by_unit", {}),
            "errors": [
                {
                    "rule": v.rule,
                    "detail": v.detail,
                    "order_ref": v.order_ref,
                    "outlet_id": v.outlet_id,
                    "vehicle_id": v.vehicle_id,
                }
                for v in val_res.violations
            ],
            "missing_data": [
                {
                    "field": m.field,
                    "entity_id": m.entity_id,
                    "detail": m.detail,
                }
                for m in val_res.missing_data
            ],
        },
    }


# Re-export dispatcher draft editing interfaces
from waypoint_optimizer.operational.draft_editor import (
    DispatcherEditError,
    EditedDraftResponse,
    MoveWholeOrderAction,
    DeferWholeOrderAction,
    ReinstateWholeOrderAction,
    MoveLineItemAction,
    DeferLineItemAction,
    SplitLineItemAction,
    evaluate_edited_draft,
)
from waypoint_optimizer.operational.breakdown_recovery import (
    BreakdownRecoveryError,
    RecoveryDraftResponse,
    UndeliveredQuantity,
    reallocate_broken_vehicle,
)

