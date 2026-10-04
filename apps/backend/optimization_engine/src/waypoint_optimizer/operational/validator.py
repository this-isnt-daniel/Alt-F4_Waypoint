"""
Waypoint Optimizer — Operational Hard-Constraint Validator (Hackathon H1)
==========================================================================
Recomputes and independently verifies all operational constraints across an entire
daily dispatch plan:
  - Requires authoritative fleet, outlets, travel, and allowance reference data.
  - Reconstructs compatibility, vehicle capacities, schedules, chronology, and fuel.
  - Validates line items independently: line_item_id existence, unit equality, no duplicates,
    no unauthorized splits, no over-allocation, and exact demand conservation.
  - Validates live fleet state (weekly_fuel_used_l and external_reservations_l) strictly.
  - Validates and recomputes all timestamps (departure, stop arrival, service start,
    service departure, depot return, vehicle next-available) against authoritative travel & allowances.
  - Rejects invalid or timezone-naive timestamps and timestamps contradicting vehicle availability.
  - Preserves quantity totals separated by unit.
  - Never trusts cached violation lists or compliance booleans.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo

from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, OrderAllocationStatus,
    Outlet, ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleStatus, VehicleType, classify_order_allocation,
)
from waypoint_optimizer.operational.models import (
    DEFAULT_FRESH_DEPARTURE_TIME, DEFAULT_STYLE_TECH_DEPARTURE_TIME,
    DEFAULT_TIMEZONE, FRESH_DEADLINE_TIME,
    EvaluatedTripSchedule, OperationalContext, OperationalMissingData,
    OperationalViolation, VehicleScheduleTimeline, WindowPolicy,
)
from waypoint_optimizer.operational.schedule_evaluator import (
    parse_iso_or_time_str,
)


def parse_timezone_aware_iso(val: Optional[str]) -> tuple[Optional[datetime], Optional[str]]:
    """
    Parses a string and verifies it is a valid, timezone-aware ISO-8601 timestamp.
    Returns (datetime, None) on success, or (None, error_reason) on failure.
    """
    if not val or not isinstance(val, str) or not val.strip():
        return None, "Empty or non-string timestamp"
    val = val.strip()
    try:
        dt = datetime.fromisoformat(val)
    except Exception as e:
        return None, f"Malformed ISO-8601 timestamp {val!r}: {e}"
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return None, f"Timestamp {val!r} is timezone-naive; timezone-aware ISO-8601 required."
    return dt, None


@dataclass(frozen=True)
class OperationalValidationResult:
    """
    Independent operational validation result.
    """
    valid: bool
    violations: list[OperationalViolation] = field(default_factory=list)
    missing_data: list[OperationalMissingData] = field(default_factory=list)
    order_counts: dict[str, int] = field(default_factory=dict)
    quantity_totals: dict[str, float] = field(default_factory=dict)
    quantity_totals_by_unit: dict[str, dict[str, float]] = field(default_factory=dict)
    vehicle_timelines: dict[str, VehicleScheduleTimeline] = field(default_factory=dict)

    @property
    def is_dispatch_ready(self) -> bool:
        """An operational plan must never be labelled ready for dispatch if invalid."""
        return self.valid and len(self.violations) == 0 and len(self.missing_data) == 0


def validate_operational_plan(
    orders: Sequence[Order],
    timelines: Sequence[VehicleScheduleTimeline] | dict[str, Any],
    context: OperationalContext,
    fleet: Optional[Sequence[Vehicle]] = None,
    reference_data: Optional[Any] = None,
    travel_data: Optional[dict[tuple[str, str], DistrictTravel]] = None,
    outlets: Optional[dict[str, Outlet]] = None,
    allowances: Optional[dict[tuple[Brand, DockType], float]] = None,
    deferred_orders: Optional[list[dict[str, Any]]] = None,
    config: Optional[Any] = None,
) -> OperationalValidationResult:
    """
    Independently validate a complete daily dispatch plan against authoritative inputs.

    Never trusts cached violation lists or pre-computed compliance booleans.
    Reconstructs compatibility, capacities, schedules, chronology, and cumulative fuel.
    Verifies explicit demand conservation and rejects unknown references, duplicates,
    unauthorized splits, missing demand, and manipulated metrics.
    """
    violations: list[OperationalViolation] = []
    missing_data: list[OperationalMissingData] = []

    # ── 1. Resolve Authoritative Reference Lookups ───────────────────────────
    orders_by_ref: dict[str, Order] = {o.order_ref: o for o in orders}

    fleet_by_id: dict[str, Vehicle] = {}
    if fleet:
        fleet_by_id = {v.vehicle_id: v for v in fleet}
    elif reference_data and hasattr(reference_data, "vehicles") and reference_data.vehicles:
        fleet_by_id = {v.vehicle_id: v for v in reference_data.vehicles}

    outlets_by_id: dict[str, Outlet] = {}
    if outlets:
        outlets_by_id = outlets
    elif reference_data and hasattr(reference_data, "outlets") and reference_data.outlets:
        outlets_by_id = reference_data.outlets

    travel_by_pair: dict[tuple[str, str], DistrictTravel] = {}
    if travel_data:
        travel_by_pair = travel_data
    elif reference_data and hasattr(reference_data, "travel") and reference_data.travel:
        if isinstance(reference_data.travel, dict):
            travel_by_pair = reference_data.travel
        else:
            travel_by_pair = {(t.district, t.depot): t for t in reference_data.travel}

    allowances_by_pair: dict[tuple[Brand, DockType], float] = {}
    if allowances:
        allowances_by_pair = allowances
    elif reference_data and hasattr(reference_data, "allowances") and reference_data.allowances:
        if isinstance(reference_data.allowances, dict):
            allowances_by_pair = reference_data.allowances
        else:
            allowances_by_pair = {
                (a.brand, a.dock_type): a.service_allowance_min for a in reference_data.allowances
            }

    # Strict check: Authoritative references must exist
    if not fleet_by_id:
        missing_data.append(OperationalMissingData(
            field="fleet",
            entity_id="all",
            detail="Authoritative fleet reference data is missing or empty. Validator requires authoritative fleet."
        ))
    if not outlets_by_id:
        missing_data.append(OperationalMissingData(
            field="outlets",
            entity_id="all",
            detail="Authoritative outlets reference data is missing or empty. Validator requires authoritative outlets."
        ))
    if not travel_by_pair:
        missing_data.append(OperationalMissingData(
            field="travel_data",
            entity_id="all",
            detail="Authoritative district travel reference data is missing or empty. Validator requires authoritative travel data."
        ))
    if not allowances_by_pair:
        missing_data.append(OperationalMissingData(
            field="allowances",
            entity_id="all",
            detail="Authoritative service allowances reference data is missing or empty. Validator requires authoritative service allowances."
        ))

    # ── 2. Normalize Trips and Deferred Records ──────────────────────────────
    plan_trips: list[Any] = []
    timelines_by_vehicle: dict[str, VehicleScheduleTimeline] = {}
    def_records: list[dict[str, Any]] = []

    if isinstance(timelines, dict):
        plan_trips = timelines.get("trips", [])
        def_records = deferred_orders or timelines.get("deferred_orders", [])
        # Check nonfinite reported metrics
        metrics = timelines.get("metrics", {})
        for m_name in ("total_distance_km", "total_fuel_litres", "total_weight_kg", "total_volume_m3"):
            m_val = metrics.get(m_name)
            if m_val is not None and (not math.isfinite(float(m_val)) or float(m_val) < 0):
                violations.append(OperationalViolation("NONFINITE_METRIC", f"Reported metric {m_name} is nonfinite: {m_val}."))
    else:
        for tl in timelines:
            timelines_by_vehicle[tl.vehicle_id] = tl
            plan_trips.extend(tl.trips)
        def_records = deferred_orders or []

    # ── 3. Demand Conservation and Separation by Quantity Unit ────────────────
    requested_by_unit: dict[str, float] = {}
    assigned_by_unit: dict[str, float] = {}
    deferred_by_unit: dict[str, float] = {}

    auth_line_items_by_order: dict[str, dict[str, LineItem]] = {}
    for o in orders:
        if o.line_items:
            auth_line_items_by_order[o.order_ref] = {li.line_item_id: li for li in o.line_items}
            for li in o.line_items:
                u = li.quantity_unit or "units"
                requested_by_unit[u] = requested_by_unit.get(u, 0.0) + li.quantity
        else:
            auth_line_items_by_order[o.order_ref] = {}
            requested_by_unit["units"] = requested_by_unit.get("units", 0.0) + float(o.order_units)

    assigned_qty_by_line_item: dict[tuple[str, str], float] = {}
    assigned_qty_by_order: dict[str, float] = {}
    assigned_by_order_item: dict[str, dict[str, float]] = {}
    order_trip_occurrences: dict[str, set[str]] = {}

    for trip in plan_trips:
        t_id = getattr(trip, "trip_id", None) or (trip.get("trip_id") if isinstance(trip, dict) else "TRIP_UNKNOWN")
        stops = getattr(trip, "stops", None) if hasattr(trip, "stops") else (trip.get("stops") or trip.get("driver_itinerary", []))
        for s_idx, stop in enumerate(stops, start=1):
            raw_items = getattr(stop, "line_items_delivered", None) if hasattr(stop, "line_items_delivered") else (stop.get("line_items_delivered") if isinstance(stop, dict) else None)
            if raw_items is not None:
                items = raw_items
            else:
                stop_refs = getattr(stop, "order_refs", None) if hasattr(stop, "order_refs") else (stop.get("order_refs") if isinstance(stop, dict) else None)
                if stop_refs:
                    items = [
                        {"order_ref": oref, "line_item_id": f"{oref}-ALL", "quantity": float(orders_by_ref[oref].order_units) if oref in orders_by_ref else 0.0, "quantity_unit": "units"}
                        for oref in stop_refs
                    ]
                else:
                    items = []
            seen_items_in_stop: set[tuple[str, str]] = set()

            for item_dict in items:
                oref = item_dict.get("order_ref") if isinstance(item_dict, dict) else getattr(item_dict, "order_ref", None)
                if not oref:
                    violations.append(OperationalViolation("MISSING_ORDER_REF", f"Delivered item in trip {t_id} stop {s_idx} missing order_ref."))
                    continue
                if oref not in orders_by_ref:
                    violations.append(OperationalViolation(
                        "UNKNOWN_ORDER_REF",
                        f"Assigned order {oref!r} in trip {t_id} does not exist in authoritative orders.",
                        order_ref=oref,
                    ))
                    continue

                parent_o = orders_by_ref[oref]
                item_id = item_dict.get("line_item_id") if isinstance(item_dict, dict) else getattr(item_dict, "line_item_id", None)
                qty_raw = item_dict.get("quantity", 0.0) if isinstance(item_dict, dict) else getattr(item_dict, "quantity", 0.0)
                unit = item_dict.get("quantity_unit", "units") if isinstance(item_dict, dict) else getattr(item_dict, "quantity_unit", "units")

                # Validate line_item_id against authoritative line items
                auth_order_lis = auth_line_items_by_order.get(oref, {})
                if auth_order_lis:
                    if not item_id:
                        violations.append(OperationalViolation(
                            "MISSING_LINE_ITEM_ID",
                            f"Order {oref!r} has line items, but delivered item in trip {t_id} stop {s_idx} is missing line_item_id.",
                            order_ref=oref,
                        ))
                        continue
                    if item_id not in auth_order_lis:
                        violations.append(OperationalViolation(
                            "UNKNOWN_LINE_ITEM",
                            f"Delivered line item {item_id!r} in trip {t_id} stop {s_idx} does not exist on authoritative order {oref!r}.",
                            order_ref=oref,
                        ))
                        continue
                    auth_li = auth_order_lis[item_id]
                    if unit != auth_li.quantity_unit:
                        violations.append(OperationalViolation(
                            "QUANTITY_UNIT_MISMATCH",
                            f"Delivered line item {item_id!r} unit {unit!r} does not match authoritative unit {auth_li.quantity_unit!r}.",
                            order_ref=oref,
                        ))
                else:
                    if item_id is None:
                        item_id = f"{oref}-ALL"

                li_key = (oref, item_id)
                if li_key in seen_items_in_stop:
                    violations.append(OperationalViolation(
                        "DUPLICATE_LINE_ITEM",
                        f"Duplicate line item {item_id!r} of order {oref!r} delivered multiple times in trip {t_id} stop {s_idx}.",
                        order_ref=oref,
                    ))
                seen_items_in_stop.add(li_key)

                try:
                    qty = float(qty_raw)
                except (ValueError, TypeError):
                    violations.append(OperationalViolation(
                        "NONFINITE_QUANTITY",
                        f"Line item quantity {qty_raw!r} for order {oref!r} cannot be parsed.",
                        order_ref=oref,
                    ))
                    continue

                if not math.isfinite(qty) or qty < 0:
                    violations.append(OperationalViolation(
                        "NONFINITE_OR_NEGATIVE_QUANTITY",
                        f"Line item quantity {qty} for order {oref!r} must be finite and non-negative.",
                        order_ref=oref,
                    ))
                    continue

                assigned_by_unit[unit] = assigned_by_unit.get(unit, 0.0) + qty
                assigned_qty_by_order[oref] = assigned_qty_by_order.get(oref, 0.0) + qty
                assigned_qty_by_line_item[(oref, item_id)] = (
                    assigned_qty_by_line_item.get((oref, item_id), 0.0) + qty
                )
                assigned_by_order_item.setdefault(oref, {})[item_id] = (
                    assigned_by_order_item.setdefault(oref, {}).get(item_id, 0.0) + qty
                )
                order_trip_occurrences.setdefault(oref, set()).add(t_id)

    # Check unauthorized order splitting
    for oref, trip_ids in order_trip_occurrences.items():
        parent_o = orders_by_ref.get(oref)
        if parent_o and not parent_o.line_items and len(trip_ids) > 1:
            violations.append(OperationalViolation(
                "UNAUTHORIZED_ORDER_SPLIT",
                f"Whole order {oref!r} assigned across multiple trips {sorted(trip_ids)} without line-item splitting.",
                order_ref=oref,
            ))

    # Process Deferred Orders and Line Items
    deferred_qty_by_line_item: dict[tuple[str, str], float] = {}
    deferred_by_order: dict[str, float] = {}
    deferred_seen: set[str] = set()
    has_explicit_deferred = bool(def_records or isinstance(timelines, dict) or deferred_orders is not None)

    if has_explicit_deferred:
        for d in def_records:
            oref = d.get("order_ref")
            if not oref:
                continue
            if oref not in orders_by_ref:
                violations.append(OperationalViolation(
                    "UNKNOWN_DEFERRED_ORDER_REF",
                    f"Deferred order {oref!r} does not exist in authoritative orders.",
                    order_ref=oref,
                ))
                continue
            if oref in deferred_seen:
                violations.append(OperationalViolation(
                    "DUPLICATE_DEFERRED_ORDER",
                    f"Duplicate deferred record for order {oref!r}.",
                    order_ref=oref,
                ))
            deferred_seen.add(oref)

            parent_o = orders_by_ref[oref]
            auth_order_lis = auth_line_items_by_order.get(oref, {})

            def_lis = d.get("line_items")
            if def_lis and isinstance(def_lis, list):
                order_def_sum = 0.0
                for d_li in def_lis:
                    d_li_id = d_li.get("line_item_id")
                    if auth_order_lis and d_li_id not in auth_order_lis:
                        violations.append(OperationalViolation(
                            "UNKNOWN_LINE_ITEM",
                            f"Deferred line item {d_li_id!r} does not exist on authoritative order {oref!r}.",
                            order_ref=oref,
                        ))
                        continue
                    d_qty_raw = d_li.get("deferred_quantity", d_li.get("quantity", 0.0))
                    d_unit = d_li.get("quantity_unit", "units")
                    try:
                        d_qty = float(d_qty_raw)
                    except (ValueError, TypeError):
                        violations.append(OperationalViolation(
                            "NONFINITE_DEFERRED_QUANTITY",
                            f"Deferred quantity {d_qty_raw!r} for line item {d_li_id!r} is invalid.",
                            order_ref=oref,
                        ))
                        continue
                    if not math.isfinite(d_qty) or d_qty < 0:
                        violations.append(OperationalViolation(
                            "NONFINITE_DEFERRED_QUANTITY",
                            f"Deferred quantity {d_qty} for line item {d_li_id!r} is invalid.",
                            order_ref=oref,
                        ))
                        continue
                    deferred_qty_by_line_item[(oref, d_li_id)] = d_qty
                    order_def_sum += d_qty
                    deferred_by_unit[d_unit] = deferred_by_unit.get(d_unit, 0.0) + d_qty
                deferred_by_order[oref] = order_def_sum
            else:
                d_qty_raw = d.get("deferred_quantity", d.get("deferred_units", parent_o.order_units))
                try:
                    d_qty = float(d_qty_raw)
                except (ValueError, TypeError):
                    violations.append(OperationalViolation(
                        "NONFINITE_DEFERRED_QUANTITY",
                        f"Deferred quantity {d_qty_raw!r} for order {oref!r} is invalid.",
                        order_ref=oref,
                    ))
                    continue
                if not math.isfinite(d_qty) or d_qty < 0:
                    violations.append(OperationalViolation(
                        "NONFINITE_DEFERRED_QUANTITY",
                        f"Deferred quantity {d_qty} for order {oref!r} is invalid.",
                        order_ref=oref,
                    ))
                    continue

                d_unit = d.get("quantity_unit", "units")
                deferred_by_order[oref] = d_qty
                deferred_by_unit[d_unit] = deferred_by_unit.get(d_unit, 0.0) + d_qty

                if auth_order_lis:
                    for li_id, li in auth_order_lis.items():
                        asg_li = assigned_qty_by_line_item.get((oref, li_id), 0.0)
                        deferred_qty_by_line_item[(oref, li_id)] = max(0.0, li.quantity - asg_li)
    else:
        for o in orders:
            auth_order_lis = auth_line_items_by_order.get(o.order_ref, {})
            if auth_order_lis:
                order_def_sum = 0.0
                for li_id, li in auth_order_lis.items():
                    asg = assigned_qty_by_line_item.get((o.order_ref, li_id), 0.0)
                    rem = max(0.0, li.quantity - asg)
                    deferred_qty_by_line_item[(o.order_ref, li_id)] = rem
                    order_def_sum += rem
                    u = li.quantity_unit or "units"
                    deferred_by_unit[u] = deferred_by_unit.get(u, 0.0) + rem
                deferred_by_order[o.order_ref] = order_def_sum
            else:
                req_qty = float(o.order_units)
                asg_qty = assigned_qty_by_order.get(o.order_ref, 0.0)
                rem = max(0.0, req_qty - asg_qty)
                deferred_by_order[o.order_ref] = rem
                deferred_by_unit["units"] = deferred_by_unit.get("units", 0.0) + rem

    # Verify Explicit Conservation and Classification
    fully_served_count = 0
    partially_served_count = 0
    fully_deferred_count = 0

    total_requested_units = sum(float(o.order_units) for o in orders)
    total_assigned_units = sum(assigned_qty_by_order.values())
    total_deferred_units = sum(deferred_by_order.values())

    for o in orders:
        oref = o.order_ref
        auth_order_lis = auth_line_items_by_order.get(oref, {})
        if auth_order_lis:
            for li_id, li in auth_order_lis.items():
                asg = assigned_qty_by_line_item.get((oref, li_id), 0.0)
                def_qty = deferred_qty_by_line_item.get((oref, li_id), 0.0)
                req = li.quantity

                if asg > req + 1e-4:
                    violations.append(OperationalViolation(
                        "LINE_ITEM_OVER_ALLOCATION",
                        f"Line item {li_id!r} of order {oref!r} assigned {asg:.2f}, exceeding requested {req:.2f}.",
                        order_ref=oref,
                    ))
                if abs((asg + def_qty) - req) > 1e-4:
                    violations.append(OperationalViolation(
                        "DEMAND_CONSERVATION_VIOLATION",
                        f"Line item {li_id!r} of order {oref!r} demand not conserved: assigned ({asg:.2f}) + deferred ({def_qty:.2f}) != requested ({req:.2f}).",
                        order_ref=oref,
                    ))
        else:
            assigned_qty = assigned_qty_by_order.get(oref, 0.0)
            deferred_qty = deferred_by_order.get(oref, 0.0)
            req_qty = float(o.order_units)

            if assigned_qty > req_qty + 1e-4:
                violations.append(OperationalViolation(
                    "OVER_ALLOCATION",
                    f"Order {oref!r} assigned {assigned_qty:.2f} units, exceeding requested {req_qty:.2f}.",
                    order_ref=oref,
                ))

            if has_explicit_deferred and assigned_qty == 0.0 and oref not in deferred_by_order:
                violations.append(OperationalViolation(
                    "MISSING_DEMAND_ACCOUNTING",
                    f"Order {oref!r} is unserved but missing from deferred orders list.",
                    order_ref=oref,
                ))

            if abs((assigned_qty + deferred_qty) - req_qty) > 1e-4:
                violations.append(OperationalViolation(
                    "DEMAND_CONSERVATION_VIOLATION",
                    f"Order {oref!r} demand not conserved: assigned ({assigned_qty:.2f}) + deferred ({deferred_qty:.2f}) != requested ({req_qty:.2f}).",
                    order_ref=oref,
                ))

        status = classify_order_allocation(o, assigned_by_order_item.get(oref, {}))
        if status == OrderAllocationStatus.FULLY_SERVED:
            fully_served_count += 1
        elif status == OrderAllocationStatus.PARTIALLY_SERVED:
            partially_served_count += 1
        else:
            fully_deferred_count += 1

    # ── 4. Reconstruct Vehicle Compatibility & Capacities ─────────────────────
    trips_by_vehicle: dict[str, list[Any]] = {}
    seen_trip_keys: set[tuple[str, int]] = set()

    for trip in plan_trips:
        vid = getattr(trip, "vehicle_id", None) or (trip.get("vehicle_id") if isinstance(trip, dict) else None)
        t_num = getattr(trip, "trip_number", None) or (trip.get("trip_number", 1) if isinstance(trip, dict) else 1)
        if (vid, t_num) in seen_trip_keys:
            violations.append(OperationalViolation(
                "DUPLICATE_TRIP_KEY",
                f"Duplicate trip assignment for vehicle {vid!r} trip {t_num}.",
                vehicle_id=vid,
                trip_number=t_num,
            ))
        seen_trip_keys.add((vid, t_num))
        trips_by_vehicle.setdefault(vid, []).append(trip)

    for vid, v_trips in trips_by_vehicle.items():
        if fleet_by_id and vid not in fleet_by_id:
            violations.append(OperationalViolation(
                "UNKNOWN_VEHICLE_REF",
                f"Plan assigns trips to vehicle {vid!r} which does not exist in authoritative fleet.",
                vehicle_id=vid,
            ))
            continue

        v = fleet_by_id.get(vid)
        if v:
            if v.status == VehicleStatus.IN_WORKSHOP and v_trips:
                violations.append(OperationalViolation(
                    "WORKSHOP_VEHICLE_ASSIGNED",
                    f"Vehicle {vid!r} is in workshop but assigned {len(v_trips)} trip(s).",
                    vehicle_id=vid,
                ))
            if not v.is_selected_for_planning and v_trips:
                violations.append(OperationalViolation(
                    "UNSELECTED_VEHICLE_ASSIGNED",
                    f"Vehicle {vid!r} was not selected for planning but assigned {len(v_trips)} trip(s).",
                    vehicle_id=vid,
                ))
            if len(v_trips) > v.remaining_trips:
                violations.append(OperationalViolation(
                    "EXCEEDED_REMAINING_TRIPS",
                    f"Vehicle {vid!r} assigned {len(v_trips)} trips, exceeding remaining {v.remaining_trips}.",
                    vehicle_id=vid,
                ))

            max_trips_allowed = config.max_trips_per_vehicle if config and hasattr(config, "max_trips_per_vehicle") else 2
            if len(v_trips) > max_trips_allowed:
                violations.append(OperationalViolation(
                    "EXCEEDED_MAX_TRIPS",
                    f"Vehicle {vid!r} assigned {len(v_trips)} trips, exceeding configured maximum allowable trips ({max_trips_allowed}).",
                    vehicle_id=vid,
                ))

            # Fleet state validation: Fuel state must not be missing or None
            if v.weekly_fuel_used_l is None:
                violations.append(OperationalViolation(
                    "MISSING_FLEET_FUEL_STATE",
                    f"Vehicle {vid!r} is missing required weekly_fuel_used_l.",
                    vehicle_id=vid,
                ))
                missing_data.append(OperationalMissingData(
                    field="weekly_fuel_used_l",
                    entity_id=vid,
                    detail=f"Vehicle {vid!r} is missing required weekly_fuel_used_l.",
                ))
            if v.external_reservations_l is None:
                violations.append(OperationalViolation(
                    "MISSING_FLEET_FUEL_STATE",
                    f"Vehicle {vid!r} is missing required external_reservations_l.",
                    vehicle_id=vid,
                ))
                missing_data.append(OperationalMissingData(
                    field="external_reservations_l",
                    entity_id=vid,
                    detail=f"Vehicle {vid!r} is missing required external_reservations_l.",
                ))
            if v.km_per_l is None or not math.isfinite(v.km_per_l) or v.km_per_l <= 0:
                violations.append(OperationalViolation(
                    "INVALID_VEHICLE_FUEL_EFFICIENCY",
                    f"Vehicle {vid!r} has invalid or non-positive km_per_l: {v.km_per_l}.",
                    vehicle_id=vid,
                ))

        for trip in v_trips:
            t_id = getattr(trip, "trip_id", None) or (trip.get("trip_id") if isinstance(trip, dict) else None)
            stops = getattr(trip, "stops", None) if hasattr(trip, "stops") else (trip.get("stops") or trip.get("driver_itinerary", []))
            t_orders: list[Order] = []
            for s in stops:
                raw_items = getattr(s, "line_items_delivered", None) if hasattr(s, "line_items_delivered") else (s.get("line_items_delivered") if isinstance(s, dict) else None)
                if raw_items:
                    for item in raw_items:
                        oref = item.get("order_ref") if isinstance(item, dict) else getattr(item, "order_ref", None)
                        if oref in orders_by_ref and orders_by_ref[oref] not in t_orders:
                            t_orders.append(orders_by_ref[oref])
                else:
                    s_refs = getattr(s, "order_refs", None) if hasattr(s, "order_refs") else (s.get("order_refs") if isinstance(s, dict) else None)
                    if s_refs:
                        for oref in s_refs:
                            if oref in orders_by_ref and orders_by_ref[oref] not in t_orders:
                                t_orders.append(orders_by_ref[oref])

            if not t_orders:
                continue

            first_brand = t_orders[0].brand
            first_district = t_orders[0].district

            # Check Brand and District Homogeneity (One brand and one district per trip)
            trip_brand_raw = getattr(trip, "brand", None) or (trip.get("brand") if isinstance(trip, dict) else None)
            trip_brand = Brand(trip_brand_raw) if isinstance(trip_brand_raw, str) else trip_brand_raw
            trip_district = getattr(trip, "district", None) or (trip.get("district") if isinstance(trip, dict) else None)

            for o in t_orders:
                if o.brand != first_brand or (trip_brand and o.brand != trip_brand):
                    violations.append(OperationalViolation(
                        "MIXED_BRAND_TRIP",
                        f"Trip {t_id} mixes brand {o.brand.value!r} with {first_brand.value!r}.",
                        vehicle_id=vid,
                    ))
                if o.district != first_district or (trip_district and o.district != trip_district):
                    violations.append(OperationalViolation(
                        "MIXED_DISTRICT_TRIP",
                        f"Trip {t_id} mixes district {o.district!r} with {first_district!r}.",
                        vehicle_id=vid,
                    ))

            if v:
                # Depot Matching
                for o in t_orders:
                    if o.depot != v.depot:
                        violations.append(OperationalViolation(
                            "DEPOT_MISMATCH",
                            f"Trip {t_id} order depot {o.depot!r} does not match vehicle depot {v.depot!r}.",
                            vehicle_id=vid,
                        ))
                    if o.temp_requirement == TempRequirement.CHILLED and v.temp != TempSpec.REEFER:
                        violations.append(OperationalViolation(
                            "REEFER_RESTRICTION",
                            f"Trip {t_id} chilled order assigned to non-reefer vehicle {v.vehicle_id!r}.",
                            vehicle_id=vid,
                        ))
                    if o.parking_constraint == ParkingConstraint.VAN_ONLY and v.type != VehicleType.VAN:
                        violations.append(OperationalViolation(
                            "VAN_ACCESS_RESTRICTION",
                            f"Trip {t_id} van_only order assigned to non-van vehicle {v.vehicle_id!r}.",
                            vehicle_id=vid,
                        ))

                # Reconstruct Payload Weights & Volumes
                tot_w = sum(o.order_weight_kg for o in t_orders)
                tot_vol = sum(o.order_volume_m3 for o in t_orders)

                if tot_w > v.weight_cap_kg + 1e-4:
                    violations.append(OperationalViolation(
                        "WEIGHT_OVERLOAD",
                        f"Trip {t_id} payload weight {tot_w:.1f} kg exceeds vehicle capacity {v.weight_cap_kg:.1f} kg.",
                        vehicle_id=vid,
                    ))
                if tot_vol > v.volume_cap_m3 + 1e-4:
                    violations.append(OperationalViolation(
                        "VOLUME_OVERLOAD",
                        f"Trip {t_id} payload volume {tot_vol:.2f} m3 exceeds vehicle capacity {v.volume_cap_m3:.2f} m3.",
                        vehicle_id=vid,
                    ))

    # ── 5. Reconstruct Chronology, Schedules, and Delivery Windows ───────────
    if travel_by_pair and outlets_by_id and allowances_by_pair and fleet_by_id:
        for vid, v_trips in trips_by_vehicle.items():
            v = fleet_by_id.get(vid)
            if not v:
                continue

            sorted_trips = sorted(v_trips, key=lambda t: getattr(t, "trip_number", None) or (t.get("trip_number", 1) if isinstance(t, dict) else 1))

            # Parse earliest availability
            v_avail_dt: Optional[datetime] = None
            if v.earliest_availability_iso:
                v_avail_dt, _ = parse_timezone_aware_iso(v.earliest_availability_iso)
                if v_avail_dt is None:
                    v_avail_dt = parse_iso_or_time_str(v.earliest_availability_iso, context.planning_date, context.timezone)
                if v_avail_dt is None:
                    violations.append(OperationalViolation(
                        "INVALID_VEHICLE_AVAILABILITY_TIMESTAMP",
                        f"Vehicle {vid!r} earliest_availability_iso {v.earliest_availability_iso!r} cannot be parsed.",
                        vehicle_id=vid,
                    ))
                else:
                    try:
                        p_parts = [int(p) for p in context.planning_date.split("-")]
                        plan_d = datetime(p_parts[0], p_parts[1], p_parts[2], 0, 0, 0, tzinfo=ZoneInfo(context.timezone)).date()
                        if v_avail_dt.date() > plan_d:
                            violations.append(OperationalViolation(
                                "VEHICLE_UNAVAILABLE_ON_PLANNING_DATE",
                                f"Vehicle {vid!r} is not available on planning date {context.planning_date} (available: {v.earliest_availability_iso}).",
                                vehicle_id=vid,
                            ))
                    except Exception:
                        pass

            prev_recomputed_next_avail: Optional[datetime] = None

            for trip_idx, trip in enumerate(sorted_trips):
                t_id = getattr(trip, "trip_id", None) or (trip.get("trip_id") if isinstance(trip, dict) else None)
                rep_dep_iso = getattr(trip, "departure_time_iso", None) or (trip.get("departure_time_iso") if isinstance(trip, dict) else None)
                dep_dt, dep_err = parse_timezone_aware_iso(rep_dep_iso)

                if dep_dt is None:
                    violations.append(OperationalViolation(
                        "TIMEZONE_NAIVE_OR_INVALID_TIMESTAMP",
                        f"Trip {t_id} departure timestamp {rep_dep_iso!r} is invalid or timezone-naive: {dep_err}.",
                        vehicle_id=vid,
                    ))
                    continue

                if v_avail_dt and dep_dt < v_avail_dt:
                    violations.append(OperationalViolation(
                        "DEPARTURE_BEFORE_VEHICLE_AVAILABILITY",
                        f"Trip {t_id} departure {dep_dt.isoformat()} is before vehicle availability {v_avail_dt.isoformat()}.",
                        vehicle_id=vid,
                    ))

                # Brand earliest release check for Trip 1
                t_brand_raw = getattr(trip, "brand", None) or (trip.get("brand") if isinstance(trip, dict) else None)
                t_brand = Brand(t_brand_raw) if isinstance(t_brand_raw, str) else t_brand_raw
                if trip_idx == 0:
                    brand_release_str = DEFAULT_FRESH_DEPARTURE_TIME if t_brand == Brand.FRESH else DEFAULT_STYLE_TECH_DEPARTURE_TIME
                    brand_release_dt = parse_iso_or_time_str(brand_release_str, context.planning_date, context.timezone)
                    if brand_release_dt and dep_dt < brand_release_dt:
                        violations.append(OperationalViolation(
                            "EARLY_DEPARTURE_VIOLATION",
                            f"Trip {t_id} departure {dep_dt.isoformat()} is before brand {t_brand.value!r} earliest departure {brand_release_dt.isoformat()}.",
                            vehicle_id=vid,
                        ))

                # Consecutive trip turnaround check
                if prev_recomputed_next_avail is not None:
                    if dep_dt < prev_recomputed_next_avail - timedelta(seconds=1):
                        violations.append(OperationalViolation(
                            "CHRONOLOGY_VIOLATION",
                            f"Trip {t_id} departure {dep_dt.isoformat()} is before vehicle next available time {prev_recomputed_next_avail.isoformat()}.",
                            vehicle_id=vid,
                        ))

                t_dist = getattr(trip, "district", None) or (trip.get("district") if isinstance(trip, dict) else None)
                depot = v.depot if v else (getattr(trip, "depot", None) or (trip.get("depot") if isinstance(trip, dict) else None))
                travel = travel_by_pair.get((t_dist, depot))
                if not travel:
                    missing_data.append(OperationalMissingData(
                        field="district_travel",
                        entity_id=f"{t_dist}::{depot}",
                        detail=f"Missing travel data for district {t_dist!r} and depot {depot!r}."
                    ))
                    continue

                curr_time = dep_dt
                stops = getattr(trip, "stops", None) if hasattr(trip, "stops") else (trip.get("stops") or trip.get("driver_itinerary", []))

                for s_idx, stop in enumerate(stops, start=1):
                    leg_travel = travel.depot_to_district_freeflow_min if s_idx == 1 else travel.inter_stop_freeflow_min
                    recomputed_arrival = curr_time + timedelta(minutes=leg_travel)

                    reported_arr_iso = getattr(stop, "arrival_time_iso", None) or (stop.get("arrival_time_iso") if isinstance(stop, dict) else None)
                    arr_dt, arr_err = parse_timezone_aware_iso(reported_arr_iso)
                    if arr_dt is None:
                        violations.append(OperationalViolation(
                            "TIMEZONE_NAIVE_OR_INVALID_TIMESTAMP",
                            f"Trip {t_id} stop {s_idx} arrival timestamp {reported_arr_iso!r} is invalid or timezone-naive: {arr_err}.",
                            vehicle_id=vid,
                        ))
                    elif abs((arr_dt - recomputed_arrival).total_seconds()) > 60:
                        violations.append(OperationalViolation(
                            "MANIPULATED_OR_INCORRECT_TIMESTAMPS",
                            f"Trip {t_id} stop {s_idx} reported arrival {reported_arr_iso!r} differs from recomputed {recomputed_arrival.isoformat()}.",
                            vehicle_id=vid,
                        ))

                    out_id = getattr(stop, "outlet_id", None) or (stop.get("outlet_id") if isinstance(stop, dict) else None)
                    outlet_obj = outlets_by_id.get(out_id)
                    if not outlet_obj:
                        missing_data.append(OperationalMissingData(
                            field="outlets",
                            entity_id=str(out_id),
                            detail=f"Outlet {out_id!r} referenced in trip {t_id} does not exist in authoritative outlets."
                        ))
                        continue

                    # Window evaluation & service times
                    allowance_min = allowances_by_pair.get((t_brand, outlet_obj.dock_type))
                    if allowance_min is None:
                        missing_data.append(OperationalMissingData(
                            field="service_allowances",
                            entity_id=f"{t_brand.value}::{outlet_obj.dock_type.value}",
                            detail=f"Missing service allowance for brand {t_brand.value!r} and dock {outlet_obj.dock_type.value!r}."
                        ))
                        allowance_min = 0.0

                    w_open_dt = parse_iso_or_time_str(outlet_obj.window_open_time, context.planning_date, context.timezone) if outlet_obj.window_open_time else None
                    w_close_dt = parse_iso_or_time_str(outlet_obj.window_close_time, context.planning_date, context.timezone) if outlet_obj.window_close_time else None

                    recomputed_svc_start = max(recomputed_arrival, w_open_dt) if w_open_dt else recomputed_arrival
                    reported_svc_start_iso = getattr(stop, "service_start_time_iso", None) or (stop.get("service_start_time_iso") if isinstance(stop, dict) else None)
                    svc_start_dt, svc_start_err = parse_timezone_aware_iso(reported_svc_start_iso)
                    if svc_start_dt is None:
                        violations.append(OperationalViolation(
                            "TIMEZONE_NAIVE_OR_INVALID_TIMESTAMP",
                            f"Trip {t_id} stop {s_idx} service start timestamp {reported_svc_start_iso!r} is invalid or timezone-naive: {svc_start_err}.",
                            vehicle_id=vid,
                        ))
                    elif abs((svc_start_dt - recomputed_svc_start).total_seconds()) > 60:
                        violations.append(OperationalViolation(
                            "MANIPULATED_OR_INCORRECT_TIMESTAMPS",
                            f"Trip {t_id} stop {s_idx} reported service start {reported_svc_start_iso!r} differs from recomputed {recomputed_svc_start.isoformat()}.",
                            vehicle_id=vid,
                        ))

                    recomputed_svc_end = recomputed_svc_start + timedelta(minutes=allowance_min)
                    reported_svc_end_iso = getattr(stop, "departure_time_iso", None) or (stop.get("departure_time_iso") if isinstance(stop, dict) else None)
                    svc_end_dt, svc_end_err = parse_timezone_aware_iso(reported_svc_end_iso)
                    if svc_end_dt is None:
                        violations.append(OperationalViolation(
                            "TIMEZONE_NAIVE_OR_INVALID_TIMESTAMP",
                            f"Trip {t_id} stop {s_idx} service departure timestamp {reported_svc_end_iso!r} is invalid or timezone-naive: {svc_end_err}.",
                            vehicle_id=vid,
                        ))
                    elif abs((svc_end_dt - recomputed_svc_end).total_seconds()) > 60:
                        violations.append(OperationalViolation(
                            "MANIPULATED_OR_INCORRECT_TIMESTAMPS",
                            f"Trip {t_id} stop {s_idx} reported departure {reported_svc_end_iso!r} differs from recomputed {recomputed_svc_end.isoformat()}.",
                            vehicle_id=vid,
                        ))

                    if w_close_dt is not None:
                        if context.window_policy == WindowPolicy.ARRIVAL_BEFORE_CLOSE and recomputed_arrival > w_close_dt:
                            violations.append(OperationalViolation(
                                "DELIVERY_WINDOW_VIOLATION",
                                f"Trip {t_id} stop {s_idx} arrival {recomputed_arrival.isoformat()} is after window close {w_close_dt.isoformat()}.",
                                outlet_id=out_id,
                                vehicle_id=vid,
                            ))
                        elif context.window_policy == WindowPolicy.SERVICE_START_BEFORE_CLOSE and recomputed_svc_start > w_close_dt:
                            violations.append(OperationalViolation(
                                "DELIVERY_WINDOW_VIOLATION",
                                f"Trip {t_id} stop {s_idx} service start {recomputed_svc_start.isoformat()} is after window close {w_close_dt.isoformat()}.",
                                outlet_id=out_id,
                                vehicle_id=vid,
                            ))
                        elif context.window_policy == WindowPolicy.SERVICE_END_BEFORE_CLOSE and recomputed_svc_end > w_close_dt:
                            violations.append(OperationalViolation(
                                "DELIVERY_WINDOW_VIOLATION",
                                f"Trip {t_id} stop {s_idx} service end {recomputed_svc_end.isoformat()} is after window close {w_close_dt.isoformat()}.",
                                outlet_id=out_id,
                                vehicle_id=vid,
                            ))

                    curr_time = recomputed_svc_end

                # Recomputed return to depot
                recomputed_return = curr_time + timedelta(minutes=travel.depot_to_district_freeflow_min)
                rep_ret_iso = getattr(trip, "depot_return_arrival_iso", None) or (trip.get("depot_return_arrival_iso") if isinstance(trip, dict) else None)
                if rep_ret_iso is not None:
                    ret_dt, ret_err = parse_timezone_aware_iso(rep_ret_iso)
                    if ret_dt is None:
                        violations.append(OperationalViolation(
                            "TIMEZONE_NAIVE_OR_INVALID_TIMESTAMP",
                            f"Trip {t_id} return arrival timestamp {rep_ret_iso!r} is invalid or timezone-naive: {ret_err}.",
                            vehicle_id=vid,
                        ))
                    elif abs((ret_dt - recomputed_return).total_seconds()) > 60:
                        violations.append(OperationalViolation(
                            "MANIPULATED_OR_INCORRECT_TIMESTAMPS",
                            f"Trip {t_id} reported depot return {rep_ret_iso!r} differs from recomputed {recomputed_return.isoformat()}.",
                            vehicle_id=vid,
                        ))

                # Recomputed vehicle next available
                recomputed_next_avail = recomputed_return + timedelta(minutes=context.depot_turnaround_duration_min)
                rep_next_iso = getattr(trip, "vehicle_next_available_iso", None) or (trip.get("vehicle_next_available_iso") if isinstance(trip, dict) else None)
                if rep_next_iso is not None:
                    next_dt, next_err = parse_timezone_aware_iso(rep_next_iso)
                    if next_dt is None:
                        violations.append(OperationalViolation(
                            "TIMEZONE_NAIVE_OR_INVALID_TIMESTAMP",
                            f"Trip {t_id} next available timestamp {rep_next_iso!r} is invalid or timezone-naive: {next_err}.",
                            vehicle_id=vid,
                        ))
                    elif abs((next_dt - recomputed_next_avail).total_seconds()) > 60:
                        violations.append(OperationalViolation(
                            "MANIPULATED_OR_INCORRECT_TIMESTAMPS",
                            f"Trip {t_id} reported vehicle next available {rep_next_iso!r} differs from recomputed {recomputed_next_avail.isoformat()}.",
                            vehicle_id=vid,
                        ))

                prev_recomputed_next_avail = recomputed_next_avail

    # ── 6. Reconstruct Cumulative Fuel Quotas ─────────────────────────────────
    if travel_by_pair and fleet_by_id:
        for vid, v_trips in trips_by_vehicle.items():
            v = fleet_by_id.get(vid)
            if not v or v.km_per_l is None or v.km_per_l <= 0:
                continue

            v_plan_fuel = 0.0
            for trip in v_trips:
                t_id = getattr(trip, "trip_id", None) or (trip.get("trip_id") if isinstance(trip, dict) else None)
                t_dist = getattr(trip, "district", None) or (trip.get("district") if isinstance(trip, dict) else None)
                depot = v.depot if v else (getattr(trip, "depot", None) or (trip.get("depot") if isinstance(trip, dict) else None))
                travel = travel_by_pair.get((t_dist, depot))
                if not travel:
                    continue

                stops = getattr(trip, "stops", None) if hasattr(trip, "stops") else (trip.get("stops") or trip.get("driver_itinerary", []))
                num_stops = len(stops)
                recomputed_distance = (2.0 * travel.depot_to_district_km) + (max(0, num_stops - 1) * travel.inter_stop_km)

                rep_dist = getattr(trip, "total_distance_km", None)
                if rep_dist is None and isinstance(trip, dict):
                    rep_dist = trip.get("total_distance_km")
                    if rep_dist is None:
                        rep_dist = trip.get("distance_km")
                    if rep_dist is None and "fuel" in trip and isinstance(trip["fuel"], dict):
                        rep_dist = trip["fuel"].get("distance_km")

                if rep_dist is not None:
                    if not math.isfinite(float(rep_dist)) or abs(float(rep_dist) - recomputed_distance) > 0.5:
                        violations.append(OperationalViolation(
                            "MANIPULATED_OR_INCORRECT_DISTANCE",
                            f"Trip {t_id} reported distance {rep_dist} km contradicts recomputed distance {recomputed_distance:.1f} km.",
                            vehicle_id=vid,
                        ))

                trip_fuel = recomputed_distance / v.km_per_l
                rep_fuel = getattr(trip, "fuel_consumed_l", None)
                if rep_fuel is None and isinstance(trip, dict):
                    rep_fuel = trip.get("fuel_consumed_l")
                    if rep_fuel is None:
                        rep_fuel = trip.get("fuel_used_l")
                    if rep_fuel is None and "fuel" in trip and isinstance(trip["fuel"], dict):
                        rep_fuel = trip["fuel"].get("fuel_consumed_l")

                if rep_fuel is not None:
                    if not math.isfinite(float(rep_fuel)) or abs(float(rep_fuel) - trip_fuel) > 0.2:
                        violations.append(OperationalViolation(
                            "MANIPULATED_OR_INCORRECT_FUEL",
                            f"Trip {t_id} reported fuel {rep_fuel} L contradicts recomputed fuel {trip_fuel:.2f} L.",
                            vehicle_id=vid,
                        ))
                v_plan_fuel += trip_fuel

            if v.weekly_fuel_used_l is not None and v.external_reservations_l is not None:
                prior_used = v.weekly_fuel_used_l
                reservations = v.external_reservations_l
                total_cumulative = prior_used + reservations + v_plan_fuel
                if v.weekly_fuel_quota_l and total_cumulative > v.weekly_fuel_quota_l + 1e-4:
                    violations.append(OperationalViolation(
                        "FUEL_QUOTA_EXCEEDED",
                        f"Vehicle {vid!r} cumulative fuel ({total_cumulative:.2f} L) exceeds weekly quota ({v.weekly_fuel_quota_l:.1f} L). "
                        f"Prior: {prior_used:.1f} L, External reservations: {reservations:.1f} L, Plan: {v_plan_fuel:.2f} L.",
                        vehicle_id=vid,
                    ))

    is_valid = (len(violations) == 0 and len(missing_data) == 0)

    # Compile Quantity Totals by Unit
    all_units = sorted(set(requested_by_unit.keys()) | set(assigned_by_unit.keys()) | set(deferred_by_unit.keys()))
    quantity_totals_by_unit: dict[str, dict[str, float]] = {}
    for u in all_units:
        quantity_totals_by_unit[u] = {
            "requested": round(requested_by_unit.get(u, 0.0), 2),
            "assigned": round(assigned_by_unit.get(u, 0.0), 2),
            "deferred": round(deferred_by_unit.get(u, 0.0), 2),
        }

    return OperationalValidationResult(
        valid=is_valid,
        violations=violations,
        missing_data=missing_data,
        order_counts={
            "total_orders": len(orders),
            "fully_served_orders": fully_served_count,
            "partially_served_orders": partially_served_count,
            "fully_deferred_orders": fully_deferred_count,
        },
        quantity_totals={
            "requested_units": round(total_requested_units, 2),
            "assigned_units": round(total_assigned_units, 2),
            "deferred_units": round(total_deferred_units, 2),
        },
        quantity_totals_by_unit=quantity_totals_by_unit,
        vehicle_timelines=timelines_by_vehicle,
    )
