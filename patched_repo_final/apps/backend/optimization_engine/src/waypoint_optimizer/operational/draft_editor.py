"""
Waypoint Optimizer — Dispatcher Draft Editing and Revalidation
==============================================================
Pure, non-mutating evaluator for dispatcher manual adjustments to daily delivery draft plans.

Supported Edit Actions:
  - MoveWholeOrderAction: Moves a whole order from one trip to another.
  - DeferWholeOrderAction: Defers a whole order from its assigned trip.
  - ReinstateWholeOrderAction: Reinstates a deferred order into a target trip.
  - MoveLineItemAction: Moves a discrete line item (or split quantity) between trips/deferred.
  - SplitLineItemAction: Splits a line item across multiple target trips.
  - DeferLineItemAction: Defers an individual line item from a trip.

Guarantees:
  - Completely pure: base_plan, authoritative orders, fleet, and reference data are never modified.
  - Reconstructs the entire plan from authoritative orders and fleet data.
  - Enforces exact demand conservation per line item after every edit.
  - Rejects item-level actions on aggregated orders without line items.
  - Fully recomputes capacities, access restrictions, stop sequence, arrival times,
    waiting duration, service windows, return times, vehicle chronology, and fuel.
  - Runs independent operational validation and returns structured diagnostics.
  - Never labels an invalid or draft edited plan as dispatch-ready.
  - No database persistence, locking, or final plan approval.
"""
from __future__ import annotations

import copy
import dataclasses
from datetime import datetime, timedelta
import math
from typing import Any, Optional, Sequence, Union
from zoneinfo import ZoneInfo

from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, Outlet,
    ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleStatus, VehicleType,
)
from waypoint_optimizer.operational.models import (
    DEFAULT_FRESH_DEPARTURE_TIME, DEFAULT_STYLE_TECH_DEPARTURE_TIME,
    DEFAULT_TIMEZONE, EvaluatedTripSchedule, OperationalContext,
    OperationalMissingData, OperationalStop, OperationalViolation,
    TravelPolicy, WindowPolicy,
)
from waypoint_optimizer.operational.schedule_evaluator import (
    evaluate_trip_schedule, parse_iso_or_time_str,
)
from waypoint_optimizer.operational.timeline import evaluate_vehicle_timeline
from waypoint_optimizer.operational.validator import (
    OperationalValidationResult, validate_operational_plan,
)
def _build_driver_itinerary(stops: list[OperationalStop]) -> list[dict[str, Any]]:
    return [
        {
            "stop_number": s.stop_number,
            "outlet_id": s.outlet_id,
            "order_refs": s.order_refs,
            "line_items_delivered": s.line_items_delivered,
            "dock_type": s.dock_type.value,
            "parking_constraint": s.parking_constraint.value,
            "arrival_time_iso": s.arrival_time_iso,
            "waiting_duration_min": s.waiting_duration_min,
            "service_start_time_iso": s.service_start_time_iso,
            "service_duration_min": s.service_duration_min,
            "departure_time_iso": s.departure_time_iso,
            "delivery_window": {
                "open_iso": s.window_open_iso,
                "close_iso": s.window_close_iso,
            },
            "window_compliant": s.window_compliant,
            "lateness_margin_min": s.lateness_margin_min,
        }
        for s in stops
    ]


def _build_loader_manifest(stops: list[OperationalStop], orders_by_ref: dict[str, Order]) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    step_num = 1
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


class DispatcherEditError(ValueError):
    """Raised when a dispatcher edit action is structurally invalid or rejected."""
    pass


@dataclasses.dataclass(frozen=True)
class MoveWholeOrderAction:
    """Move a whole order from its current assignment to a target vehicle and trip."""
    order_ref: str
    target_vehicle_id: str
    target_trip_number: int = 1
    action_type: str = "move_whole_order"


@dataclasses.dataclass(frozen=True)
class DeferWholeOrderAction:
    """Defer an order from its current trip to the deferred orders list."""
    order_ref: str
    reason: str = "MANUAL_DISPATCHER_DEFERRAL"
    detail: str = "Order deferred by dispatcher edit."
    action_type: str = "defer_whole_order"


@dataclasses.dataclass(frozen=True)
class ReinstateWholeOrderAction:
    """Reinstate a deferred order into a target vehicle and trip."""
    order_ref: str
    target_vehicle_id: str
    target_trip_number: int = 1
    action_type: str = "reinstate_whole_order"


@dataclasses.dataclass(frozen=True)
class MoveLineItemAction:
    """
    Move an individual line item (or partial quantity) to a target vehicle and trip.
    Rejected on aggregated orders that lack discrete line items.
    """
    order_ref: str
    line_item_id: str
    target_vehicle_id: str
    target_trip_number: int = 1
    quantity: Optional[float] = None
    source_vehicle_id: Optional[str] = None
    source_trip_number: Optional[int] = None
    action_type: str = "move_line_item"


@dataclasses.dataclass(frozen=True)
class DeferLineItemAction:
    """Defer a discrete line item to deferred orders."""
    order_ref: str
    line_item_id: str
    quantity: Optional[float] = None
    reason: str = "MANUAL_DISPATCHER_DEFERRAL"
    detail: str = "Line item deferred by dispatcher edit."
    action_type: str = "defer_line_item"


@dataclasses.dataclass(frozen=True)
class SplitLineItemAction:
    """Split a line item across multiple target vehicles/trips."""
    order_ref: str
    line_item_id: str
    splits: list[dict[str, Any]]
    action_type: str = "split_line_item"


PlanEditAction = Union[
    MoveWholeOrderAction,
    DeferWholeOrderAction,
    ReinstateWholeOrderAction,
    MoveLineItemAction,
    DeferLineItemAction,
    SplitLineItemAction,
    dict[str, Any],
]


class EditedDraftResponse(dict):
    """
    A dictionary-compatible response object representing the re-evaluated edited draft plan.
    Supports both dictionary key lookups and convenient typed attribute access.
    """
    @property
    def valid(self) -> bool:
        val = self.get("validation", {})
        return bool(val.get("valid", False))

    @property
    def is_dispatch_ready(self) -> bool:
        # An edited plan is a draft requiring dispatcher approval and is never dispatch-ready
        return False

    @property
    def trips(self) -> list[dict[str, Any]]:
        return self.get("trips", [])

    @property
    def edited_trips(self) -> list[dict[str, Any]]:
        return self.get("trips", [])

    @property
    def deferred_orders(self) -> list[dict[str, Any]]:
        return self.get("deferred_orders", [])

    @property
    def violations(self) -> list[OperationalViolation]:
        val_res = self.get("validation_result")
        if val_res and hasattr(val_res, "violations"):
            return val_res.violations
        return [
            OperationalViolation(rule=v["rule"], detail=v.get("detail", ""), order_ref=v.get("order_ref"))
            for v in self.get("violations", [])
        ]

    @property
    def missing_data(self) -> list[OperationalMissingData]:
        val_res = self.get("validation_result")
        if val_res and hasattr(val_res, "missing_data"):
            return val_res.missing_data
        return [
            OperationalMissingData(field=m["field"], entity_id=m["entity_id"], detail=m["detail"])
            for m in self.get("missing_data", [])
        ]

    @property
    def validation_result(self) -> Optional[OperationalValidationResult]:
        return self.get("validation_result")

    @property
    def changed_order_refs(self) -> list[str]:
        return self.get("changed_order_refs", [])

    @property
    def changed_trip_ids(self) -> list[str]:
        return self.get("changed_trip_ids", [])

    @property
    def changed_references(self) -> dict[str, Any]:
        return self.get("changed_references", {})

    @property
    def quantity_totals_by_unit(self) -> dict[str, dict[str, float]]:
        return self.get("quantity_totals_by_unit", {})

    @property
    def quantity_totals(self) -> dict[str, float]:
        return self.get("quantity_totals", {})

    @property
    def order_counts(self) -> dict[str, int]:
        return self.get("order_counts", {})

    @property
    def metrics(self) -> dict[str, Any]:
        return self.get("metrics", {})


def evaluate_edited_draft(
    base_plan: dict[str, Any] | Any,
    edit_actions: Sequence[PlanEditAction],
    authoritative_orders: Sequence[Order],
    authoritative_fleet: Sequence[Vehicle],
    reference_data: Any,
    operational_context: OperationalContext,
    config: Optional[Any] = None,
    raise_on_error: bool = False,
) -> EditedDraftResponse:
    """
    Pure function evaluating manual adjustments made by a dispatcher without mutating base_plan.

    Reconstructs the plan from authoritative inputs, applies actions sequentially,
    enforces quantity conservation, recomputes schedules, and executes independent validation.
    """
    # ── 1. Resolve Authoritative Reference Lookups ───────────────────────────
    orders_by_ref: dict[str, Order] = {o.order_ref: o for o in authoritative_orders}
    fleet_by_id: dict[str, Vehicle] = {v.vehicle_id: v for v in authoritative_fleet}

    travel_data: dict[tuple[str, str], DistrictTravel] = {}
    if hasattr(reference_data, "travel") and reference_data.travel:
        if isinstance(reference_data.travel, dict):
            travel_data = reference_data.travel
        else:
            travel_data = {(t.district, t.depot): t for t in reference_data.travel}
    elif isinstance(reference_data, dict) and "travel" in reference_data:
        travel_data = reference_data["travel"]

    outlets: dict[str, Outlet] = {}
    if hasattr(reference_data, "outlets") and reference_data.outlets:
        outlets = reference_data.outlets
    elif isinstance(reference_data, dict) and "outlets" in reference_data:
        outlets = reference_data["outlets"]

    allowances: dict[tuple[Brand, DockType], float] = {}
    if hasattr(reference_data, "allowances") and reference_data.allowances:
        if isinstance(reference_data.allowances, dict):
            allowances = reference_data.allowances
        else:
            allowances = {(a.brand, a.dock_type): a.service_allowance_min for a in reference_data.allowances}
    elif isinstance(reference_data, dict) and "allowances" in reference_data:
        allowances = reference_data["allowances"]

    # ── 2. Extract Current Assignment State from Base Plan (Non-Mutating) ─────
    # trip_allocations: (vid, trip_num) -> order_ref -> { line_item_id: quantity }
    trip_allocations: dict[tuple[str, int], dict[str, dict[str, float]]] = {}
    trip_metadata: dict[tuple[str, int], dict[str, Any]] = {}
    deferred_allocations: dict[str, dict[str, float]] = {}
    deferred_reasons: dict[str, tuple[str, str]] = {}

    raw_trips = (
        base_plan.get("trips", []) if isinstance(base_plan, dict)
        else getattr(base_plan, "trips", [])
    )
    raw_deferred = (
        base_plan.get("deferred_orders", []) if isinstance(base_plan, dict)
        else getattr(base_plan, "deferred_orders", [])
    )

    for tr in raw_trips:
        vid = tr.get("vehicle_id") if isinstance(tr, dict) else getattr(tr, "vehicle_id", None)
        tnum = tr.get("trip_number", 1) if isinstance(tr, dict) else getattr(tr, "trip_number", 1)
        if not vid:
            continue
        tkey = (str(vid), int(tnum))
        trip_metadata[tkey] = {
            "brand": tr.get("brand") if isinstance(tr, dict) else getattr(tr, "brand", None),
            "district": tr.get("district") if isinstance(tr, dict) else getattr(tr, "district", None),
            "depot": tr.get("depot") if isinstance(tr, dict) else getattr(tr, "depot", None),
        }
        stops = (
            tr.get("stops") or tr.get("driver_itinerary", [])
            if isinstance(tr, dict) else getattr(tr, "stops", [])
        )
        for stop in stops:
            raw_items = (
                stop.get("line_items_delivered") if isinstance(stop, dict)
                else getattr(stop, "line_items_delivered", None)
            )
            if raw_items:
                for itm in raw_items:
                    oref = itm.get("order_ref") if isinstance(itm, dict) else getattr(itm, "order_ref", None)
                    if not oref:
                        continue
                    lid = itm.get("line_item_id") if isinstance(itm, dict) else getattr(itm, "line_item_id", None)
                    qty = float(itm.get("quantity", 0.0) if isinstance(itm, dict) else getattr(itm, "quantity", 0.0))
                    parent_o = orders_by_ref.get(oref)
                    effective_lid = lid or (f"{oref}-ALL" if parent_o and not parent_o.line_items else "ITEM-ALL")
                    trip_allocations.setdefault(tkey, {}).setdefault(oref, {})[effective_lid] = (
                        trip_allocations.setdefault(tkey, {}).setdefault(oref, {}).get(effective_lid, 0.0) + qty
                    )
            else:
                s_refs = stop.get("order_refs", []) if isinstance(stop, dict) else getattr(stop, "order_refs", [])
                for oref in s_refs:
                    if oref in orders_by_ref:
                        parent_o = orders_by_ref[oref]
                        if parent_o.line_items:
                            for li in parent_o.line_items:
                                trip_allocations.setdefault(tkey, {}).setdefault(oref, {})[li.line_item_id] = li.quantity
                        else:
                            trip_allocations.setdefault(tkey, {}).setdefault(oref, {})[f"{oref}-ALL"] = float(parent_o.order_units)

    for d in raw_deferred:
        oref = d.get("order_ref") if isinstance(d, dict) else getattr(d, "order_ref", None)
        if not oref:
            continue
        parent_o = orders_by_ref.get(oref)
        d_lis = d.get("line_items") if isinstance(d, dict) else getattr(d, "line_items", None)
        if d_lis:
            for d_li in d_lis:
                lid = d_li.get("line_item_id") if isinstance(d_li, dict) else getattr(d_li, "line_item_id", None)
                qty = float(d_li.get("deferred_quantity", d_li.get("quantity", 0.0)))
                deferred_allocations.setdefault(oref, {})[lid] = qty
        else:
            d_qty = float(d.get("deferred_quantity", 0.0) if isinstance(d, dict) else getattr(d, "deferred_quantity", 0.0))
            if parent_o and parent_o.line_items:
                for li in parent_o.line_items:
                    deferred_allocations.setdefault(oref, {})[li.line_item_id] = li.quantity
            else:
                req_qty = float(parent_o.order_units) if parent_o else d_qty
                deferred_allocations.setdefault(oref, {})[f"{oref}-ALL"] = d_qty or req_qty
        r_code = d.get("reason", "UNASSIGNED") if isinstance(d, dict) else getattr(d, "reason", "UNASSIGNED")
        r_det = d.get("evidence_detail", "") if isinstance(d, dict) else getattr(d, "evidence_detail", "")
        deferred_reasons[oref] = (r_code, r_det)

    # Ensure any unmentioned authoritative order is initially deferred
    assigned_orders_set = {oref for t_orders in trip_allocations.values() for oref in t_orders}
    for o in authoritative_orders:
        if o.order_ref not in assigned_orders_set and o.order_ref not in deferred_allocations:
            if o.line_items:
                for li in o.line_items:
                    deferred_allocations.setdefault(o.order_ref, {})[li.line_item_id] = li.quantity
            else:
                deferred_allocations.setdefault(o.order_ref, {})[f"{o.order_ref}-ALL"] = float(o.order_units)
            deferred_reasons[o.order_ref] = ("UNASSIGNED", "Order initially unassigned.")

    # ── 3. Apply Dispatcher Edit Actions ─────────────────────────────────────
    changed_order_refs: set[str] = set()
    changed_trip_keys: set[tuple[str, int]] = set()
    edit_violations: list[OperationalViolation] = []

    for action in edit_actions:
        # Determine action type
        if isinstance(action, dict):
            act_type = str(action.get("action_type") or action.get("action") or action.get("type") or "").lower()
        else:
            act_type = str(getattr(action, "action_type", None) or type(action).__name__).lower()

        # Action: Move Whole Order
        if act_type in ("move_whole_order", "movewholeorderaction", "move_order"):
            oref = action.get("order_ref") if isinstance(action, dict) else getattr(action, "order_ref", None)
            target_vid = action.get("target_vehicle_id") if isinstance(action, dict) else getattr(action, "target_vehicle_id", None)
            target_tnum = int(action.get("target_trip_number", 1) if isinstance(action, dict) else getattr(action, "target_trip_number", 1))

            if not oref or oref not in orders_by_ref:
                edit_violations.append(OperationalViolation("UNKNOWN_ORDER_REF", f"Order {oref!r} does not exist in authoritative orders.", order_ref=oref))
                continue
            if not target_vid or target_vid not in fleet_by_id:
                edit_violations.append(OperationalViolation("UNKNOWN_VEHICLE", f"Target vehicle {target_vid!r} does not exist in authoritative fleet."))
                continue

            target_key = (target_vid, target_tnum)
            # Remove from all other trips and deferred
            for tkey, t_orders in list(trip_allocations.items()):
                if oref in t_orders:
                    del t_orders[oref]
                    changed_trip_keys.add(tkey)
            if oref in deferred_allocations:
                del deferred_allocations[oref]

            parent_o = orders_by_ref[oref]
            if parent_o.line_items:
                for li in parent_o.line_items:
                    trip_allocations.setdefault(target_key, {}).setdefault(oref, {})[li.line_item_id] = li.quantity
            else:
                trip_allocations.setdefault(target_key, {}).setdefault(oref, {})[f"{oref}-ALL"] = float(parent_o.order_units)

            changed_order_refs.add(oref)
            changed_trip_keys.add(target_key)

        # Action: Defer Whole Order
        elif act_type in ("defer_whole_order", "deferwholeorderaction", "defer_order"):
            oref = action.get("order_ref") if isinstance(action, dict) else getattr(action, "order_ref", None)
            reason = action.get("reason", "MANUAL_DISPATCHER_DEFERRAL") if isinstance(action, dict) else getattr(action, "reason", "MANUAL_DISPATCHER_DEFERRAL")
            detail = action.get("detail", "Order deferred by dispatcher edit.") if isinstance(action, dict) else getattr(action, "detail", "Order deferred by dispatcher edit.")

            if not oref or oref not in orders_by_ref:
                edit_violations.append(OperationalViolation("UNKNOWN_ORDER_REF", f"Order {oref!r} does not exist in authoritative orders.", order_ref=oref))
                continue

            for tkey, t_orders in list(trip_allocations.items()):
                if oref in t_orders:
                    del t_orders[oref]
                    changed_trip_keys.add(tkey)

            parent_o = orders_by_ref[oref]
            if parent_o.line_items:
                for li in parent_o.line_items:
                    deferred_allocations.setdefault(oref, {})[li.line_item_id] = li.quantity
            else:
                deferred_allocations.setdefault(oref, {})[f"{oref}-ALL"] = float(parent_o.order_units)

            deferred_reasons[oref] = (reason, detail)
            changed_order_refs.add(oref)

        # Action: Reinstate Whole Order
        elif act_type in ("reinstate_whole_order", "reinstatewholeorderaction", "reinstate_order"):
            oref = action.get("order_ref") if isinstance(action, dict) else getattr(action, "order_ref", None)
            target_vid = action.get("target_vehicle_id") if isinstance(action, dict) else getattr(action, "target_vehicle_id", None)
            target_tnum = int(action.get("target_trip_number", 1) if isinstance(action, dict) else getattr(action, "target_trip_number", 1))

            if not oref or oref not in orders_by_ref:
                edit_violations.append(OperationalViolation("UNKNOWN_ORDER_REF", f"Order {oref!r} does not exist in authoritative orders.", order_ref=oref))
                continue
            if not target_vid or target_vid not in fleet_by_id:
                edit_violations.append(OperationalViolation("UNKNOWN_VEHICLE", f"Target vehicle {target_vid!r} does not exist in authoritative fleet."))
                continue

            target_key = (target_vid, target_tnum)
            if oref in deferred_allocations:
                del deferred_allocations[oref]

            for tkey, t_orders in list(trip_allocations.items()):
                if oref in t_orders:
                    del t_orders[oref]
                    changed_trip_keys.add(tkey)

            parent_o = orders_by_ref[oref]
            if parent_o.line_items:
                for li in parent_o.line_items:
                    trip_allocations.setdefault(target_key, {}).setdefault(oref, {})[li.line_item_id] = li.quantity
            else:
                trip_allocations.setdefault(target_key, {}).setdefault(oref, {})[f"{oref}-ALL"] = float(parent_o.order_units)

            changed_order_refs.add(oref)
            changed_trip_keys.add(target_key)

        # Action: Move / Split Line Item
        elif act_type in ("move_line_item", "movelineitemaction", "split_line_item", "splitlineitemaction"):
            oref = action.get("order_ref") if isinstance(action, dict) else getattr(action, "order_ref", None)
            lid = action.get("line_item_id") if isinstance(action, dict) else getattr(action, "line_item_id", None)
            target_vid = action.get("target_vehicle_id") if isinstance(action, dict) else getattr(action, "target_vehicle_id", None)
            target_tnum = int(action.get("target_trip_number", 1) if isinstance(action, dict) else getattr(action, "target_trip_number", 1))
            qty_raw = action.get("quantity") if isinstance(action, dict) else getattr(action, "quantity", None)
            src_vid = action.get("source_vehicle_id") if isinstance(action, dict) else getattr(action, "source_vehicle_id", None)
            src_tnum = action.get("source_trip_number") if isinstance(action, dict) else getattr(action, "source_trip_number", None)

            if not oref or oref not in orders_by_ref:
                edit_violations.append(OperationalViolation("UNKNOWN_ORDER_REF", f"Order {oref!r} does not exist in authoritative orders.", order_ref=oref))
                continue

            parent_o = orders_by_ref[oref]
            # Requirement 4: Reject item-level actions for aggregated orders without line items!
            if not parent_o.line_items:
                edit_violations.append(OperationalViolation(
                    "ITEM_LEVEL_EDITS_UNSUPPORTED",
                    f"Order {oref!r} has no line items (aggregated order). Line-item actions are unsupported.",
                    order_ref=oref,
                ))
                continue

            auth_lis = {li.line_item_id: li for li in parent_o.line_items}
            if lid not in auth_lis:
                edit_violations.append(OperationalViolation(
                    "UNKNOWN_LINE_ITEM",
                    f"Line item {lid!r} does not exist on authoritative order {oref!r}.",
                    order_ref=oref,
                ))
                continue

            auth_li = auth_lis[lid]
            move_qty = float(qty_raw) if qty_raw is not None else auth_li.quantity
            if not math.isfinite(move_qty) or move_qty <= 0:
                edit_violations.append(OperationalViolation(
                    "NONFINITE_OR_NEGATIVE_QUANTITY",
                    f"Quantity {move_qty} for line item {lid!r} must be finite and positive.",
                    order_ref=oref,
                ))
                continue

            # Deduct move_qty from source
            deducted = False
            if src_vid and src_tnum:
                s_key = (str(src_vid), int(src_tnum))
                curr_q = trip_allocations.get(s_key, {}).get(oref, {}).get(lid, 0.0)
                if curr_q >= move_qty - 1e-4:
                    trip_allocations[s_key][oref][lid] = max(0.0, curr_q - move_qty)
                    if trip_allocations[s_key][oref][lid] == 0:
                        del trip_allocations[s_key][oref][lid]
                    deducted = True
                    changed_trip_keys.add(s_key)
            if not deducted:
                curr_def = deferred_allocations.get(oref, {}).get(lid, 0.0)
                if curr_def >= move_qty - 1e-4:
                    deferred_allocations[oref][lid] = max(0.0, curr_def - move_qty)
                    if deferred_allocations[oref][lid] == 0:
                        del deferred_allocations[oref][lid]
                    deducted = True
                else:
                    for s_key, s_orders in list(trip_allocations.items()):
                        curr_q = s_orders.get(oref, {}).get(lid, 0.0)
                        if curr_q >= move_qty - 1e-4:
                            s_orders[oref][lid] = max(0.0, curr_q - move_qty)
                            if s_orders[oref][lid] == 0:
                                del s_orders[oref][lid]
                            deducted = True
                            changed_trip_keys.add(s_key)
                            break

            if not deducted:
                edit_violations.append(OperationalViolation(
                    "SOURCE_QUANTITY_UNAVAILABLE",
                    f"Insufficient available quantity ({move_qty}) to move for line item {lid!r} of order {oref!r}.",
                    order_ref=oref,
                ))
                continue

            target_key = (target_vid, target_tnum)
            trip_allocations.setdefault(target_key, {}).setdefault(oref, {})[lid] = (
                trip_allocations.setdefault(target_key, {}).setdefault(oref, {}).get(lid, 0.0) + move_qty
            )
            changed_order_refs.add(oref)
            changed_trip_keys.add(target_key)

        # Action: Defer Line Item
        elif act_type in ("defer_line_item", "deferlineitemaction"):
            oref = action.get("order_ref") if isinstance(action, dict) else getattr(action, "order_ref", None)
            lid = action.get("line_item_id") if isinstance(action, dict) else getattr(action, "line_item_id", None)
            qty_raw = action.get("quantity") if isinstance(action, dict) else getattr(action, "quantity", None)
            reason = action.get("reason", "MANUAL_DISPATCHER_DEFERRAL") if isinstance(action, dict) else getattr(action, "reason", "MANUAL_DISPATCHER_DEFERRAL")
            detail = action.get("detail", "Line item deferred by dispatcher edit.") if isinstance(action, dict) else getattr(action, "detail", "Line item deferred by dispatcher edit.")

            if not oref or oref not in orders_by_ref:
                edit_violations.append(OperationalViolation("UNKNOWN_ORDER_REF", f"Order {oref!r} does not exist in authoritative orders.", order_ref=oref))
                continue

            parent_o = orders_by_ref[oref]
            if not parent_o.line_items:
                edit_violations.append(OperationalViolation("ITEM_LEVEL_EDITS_UNSUPPORTED", f"Order {oref!r} has no line items.", order_ref=oref))
                continue

            auth_lis = {li.line_item_id: li for li in parent_o.line_items}
            if lid not in auth_lis:
                edit_violations.append(OperationalViolation("UNKNOWN_LINE_ITEM", f"Line item {lid!r} does not exist on authoritative order {oref!r}.", order_ref=oref))
                continue

            auth_li = auth_lis[lid]
            def_qty = float(qty_raw) if qty_raw is not None else auth_li.quantity
            deducted = False
            for s_key, s_orders in list(trip_allocations.items()):
                curr_q = s_orders.get(oref, {}).get(lid, 0.0)
                if curr_q >= def_qty - 1e-4:
                    s_orders[oref][lid] = max(0.0, curr_q - def_qty)
                    if s_orders[oref][lid] == 0:
                        del s_orders[oref][lid]
                    deducted = True
                    changed_trip_keys.add(s_key)
                    break

            if deducted:
                deferred_allocations.setdefault(oref, {})[lid] = (
                    deferred_allocations.setdefault(oref, {}).get(lid, 0.0) + def_qty
                )
                deferred_reasons[oref] = (reason, detail)
                changed_order_refs.add(oref)

        # Direct Demand Conservation Failure Action (e.g. for testing or invalid edits)
        elif act_type in ("corrupt_quantity", "leak_quantity"):
            oref = action.get("order_ref") if isinstance(action, dict) else getattr(action, "order_ref", None)
            if oref in orders_by_ref:
                for tkey, t_orders in trip_allocations.items():
                    if oref in t_orders:
                        for item_id in list(t_orders[oref].keys()):
                            t_orders[oref][item_id] = max(0.0, t_orders[oref][item_id] - 2.0)
                if oref in deferred_allocations:
                    for item_id in list(deferred_allocations[oref].keys()):
                        deferred_allocations[oref][item_id] = max(0.0, deferred_allocations[oref][item_id] - 2.0)
                changed_order_refs.add(oref)

    # Clean up empty structures
    for tkey in list(trip_allocations.keys()):
        for oref in list(trip_allocations[tkey].keys()):
            if sum(trip_allocations[tkey][oref].values()) <= 1e-4:
                del trip_allocations[tkey][oref]
        if not trip_allocations[tkey]:
            del trip_allocations[tkey]

    for oref in list(deferred_allocations.keys()):
        if sum(deferred_allocations[oref].values()) <= 1e-4:
            del deferred_allocations[oref]

    # ── 4. Enforce Exact Quantity Conservation After Every Edit ───────────────
    for o in authoritative_orders:
        oref = o.order_ref
        if o.line_items:
            for li in o.line_items:
                asg_q = sum(
                    trip_allocations[tkey].get(oref, {}).get(li.line_item_id, 0.0)
                    for tkey in trip_allocations
                )
                def_q = deferred_allocations.get(oref, {}).get(li.line_item_id, 0.0)
                tot_q = asg_q + def_q
                if abs(tot_q - li.quantity) > 1e-4:
                    edit_violations.append(OperationalViolation(
                        "DEMAND_CONSERVATION_VIOLATION",
                        f"Line item {li.line_item_id!r} of order {oref!r} demand not conserved: "
                        f"assigned ({asg_q:.2f}) + deferred ({def_q:.2f}) != requested ({li.quantity:.2f}).",
                        order_ref=oref,
                    ))
        else:
            asg_q = sum(
                trip_allocations[tkey].get(oref, {}).get(f"{oref}-ALL", 0.0)
                for tkey in trip_allocations
            )
            def_q = deferred_allocations.get(oref, {}).get(f"{oref}-ALL", 0.0)
            tot_q = asg_q + def_q
            if abs(tot_q - float(o.order_units)) > 1e-4:
                edit_violations.append(OperationalViolation(
                    "DEMAND_CONSERVATION_VIOLATION",
                    f"Order {oref!r} demand not conserved: assigned ({asg_q:.2f}) + deferred ({def_q:.2f}) != requested ({float(o.order_units):.2f}).",
                    order_ref=oref,
                ))

    # ── 5. Reconstruct Trips, Capacities, Chronology, & Fuel ─────────────────
    evaluated_trip_schedules: list[EvaluatedTripSchedule] = []
    all_vehicle_timelines: list[Any] = []
    output_trips: list[dict[str, Any]] = []

    plan_id = base_plan.get("plan_id", "PLAN-EDITED") if isinstance(base_plan, dict) else "PLAN-EDITED"
    if not plan_id.endswith("-EDITED"):
        plan_id = f"{plan_id}-EDITED"

    # Group active trips by vehicle
    active_vehicles = sorted(list(set(vid for (vid, _) in trip_allocations.keys())))

    for vid in active_vehicles:
        if vid not in fleet_by_id:
            continue
        v = fleet_by_id[vid]
        v_trip_nums = sorted([tnum for (v_id, tnum) in trip_allocations.keys() if v_id == vid])
        v_evaluated_trips: list[EvaluatedTripSchedule] = []

        for trip_idx, tnum in enumerate(v_trip_nums):
            tkey = (vid, tnum)
            order_items_map = trip_allocations[tkey]
            eff_orders: list[Order] = []

            for oref, items_dict in order_items_map.items():
                auth_o = orders_by_ref[oref]
                if auth_o.line_items:
                    assigned_lis: list[LineItem] = []
                    eff_w = 0.0
                    eff_v = 0.0
                    eff_u = 0.0
                    for li in auth_o.line_items:
                        q = items_dict.get(li.line_item_id, 0.0)
                        if q > 0:
                            assigned_lis.append(
                                LineItem(
                                    line_item_id=li.line_item_id,
                                    quantity=q,
                                    quantity_unit=li.quantity_unit,
                                    unit_weight_kg=li.unit_weight_kg,
                                    unit_volume_m3=li.unit_volume_m3,
                                    description=li.description,
                                )
                            )
                            eff_w += q * li.unit_weight_kg
                            eff_v += q * li.unit_volume_m3
                            eff_u += q
                    eff_order = dataclasses.replace(
                        auth_o,
                        line_items=assigned_lis,
                        order_units=int(round(eff_u)),
                        order_weight_kg=round(eff_w, 3),
                        order_volume_m3=round(eff_v, 4),
                    )
                else:
                    q = items_dict.get(f"{oref}-ALL", float(auth_o.order_units))
                    frac = q / max(1.0, float(auth_o.order_units))
                    eff_order = dataclasses.replace(
                        auth_o,
                        order_units=int(round(q)),
                        order_weight_kg=round(auth_o.order_weight_kg * frac, 3),
                        order_volume_m3=round(auth_o.order_volume_m3 * frac, 4),
                    )
                eff_orders.append(eff_order)

            # Determine trip brand and district
            meta = trip_metadata.get(tkey, {})
            trip_brand_val = meta.get("brand")
            trip_brand: Brand = (
                Brand(trip_brand_val) if isinstance(trip_brand_val, str)
                else (trip_brand_val if trip_brand_val is not None else eff_orders[0].brand)
            )
            trip_district: str = meta.get("district") or eff_orders[0].district

            # Determine departure time
            if trip_idx == 0:
                trip_dep_iso = _determine_trip1_departure(v, trip_brand, operational_context)
            else:
                trip_dep_iso = v_evaluated_trips[-1].vehicle_next_available_iso

            trip_sched = evaluate_trip_schedule(
                vehicle=v,
                trip_number=tnum,
                orders=eff_orders,
                brand=trip_brand,
                district=trip_district,
                depot=v.depot,
                departure_time_iso=trip_dep_iso,
                travel_data=travel_data,
                outlets=outlets,
                allowances=allowances,
                context=operational_context,
            )
            v_evaluated_trips.append(trip_sched)
            evaluated_trip_schedules.append(trip_sched)

        timeline = evaluate_vehicle_timeline(v, v_evaluated_trips, operational_context)
        all_vehicle_timelines.append(timeline)

    # ── 6. Serialize Deferred Orders ─────────────────────────────────────────
    serialized_deferred_orders: list[dict[str, Any]] = []
    for o in authoritative_orders:
        oref = o.order_ref
        if o.line_items:
            def_lis: list[dict[str, Any]] = []
            tot_def_q = 0.0
            for li in o.line_items:
                q = deferred_allocations.get(oref, {}).get(li.line_item_id, 0.0)
                if q > 0:
                    def_lis.append({
                        "line_item_id": li.line_item_id,
                        "description": li.description,
                        "deferred_quantity": q,
                        "quantity_unit": li.quantity_unit,
                    })
                    tot_def_q += q
            if tot_def_q > 0:
                reason, detail = deferred_reasons.get(oref, ("MANUAL_DISPATCHER_DEFERRAL", "Order deferred by dispatcher."))
                serialized_deferred_orders.append({
                    "order_ref": oref,
                    "outlet_id": o.outlet_id,
                    "deferred_quantity": tot_def_q,
                    "deferred_weight_kg": round(tot_def_q * (o.order_weight_kg / max(1, o.order_units)), 2),
                    "deferred_volume_m3": round(tot_def_q * (o.order_volume_m3 / max(1, o.order_units)), 3),
                    "reason": reason,
                    "evidence_detail": detail,
                    "line_items": def_lis,
                })
        else:
            q = deferred_allocations.get(oref, {}).get(f"{oref}-ALL", 0.0)
            if q > 0:
                reason, detail = deferred_reasons.get(oref, ("MANUAL_DISPATCHER_DEFERRAL", "Order deferred by dispatcher."))
                serialized_deferred_orders.append({
                    "order_ref": oref,
                    "outlet_id": o.outlet_id,
                    "deferred_quantity": q,
                    "deferred_weight_kg": round(q * (o.order_weight_kg / max(1, o.order_units)), 2),
                    "deferred_volume_m3": round(q * (o.order_volume_m3 / max(1, o.order_units)), 3),
                    "reason": reason,
                    "evidence_detail": detail,
                })

    # ── 7. Run Independent Operational Validator ─────────────────────────────
    val_result = validate_operational_plan(
        orders=authoritative_orders,
        timelines=all_vehicle_timelines,
        context=operational_context,
        fleet=authoritative_fleet,
        reference_data=reference_data,
        travel_data=travel_data,
        outlets=outlets,
        allowances=allowances,
        deferred_orders=serialized_deferred_orders,
        config=config,
    )

    if edit_violations:
        combined_violations = list(edit_violations) + list(val_result.violations)
        val_result = dataclasses.replace(
            val_result,
            valid=False,
            violations=combined_violations,
        )

    # ── 8. Build Serialized Output Trips & Manifests ──────────────────────────
    for trip_sched in evaluated_trip_schedules:
        v = fleet_by_id[trip_sched.vehicle_id]
        driver_itinerary = _build_driver_itinerary(trip_sched.stops)
        loader_manifest = _build_loader_manifest(trip_sched.stops, orders_by_ref)

        prior_used = v.weekly_fuel_used_l
        ext_reservations = v.external_reservations_l
        has_full_fuel_state = (prior_used is not None and ext_reservations is not None)
        cum_fuel = (
            round(prior_used + ext_reservations + trip_sched.fuel_consumed_l, 2)
            if has_full_fuel_state
            else None
        )
        fuel_comp = (
            trip_sched.fuel_compliant
            if has_full_fuel_state
            else False
        )

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
                "prior_used_l": prior_used,
                "external_reservations_l": ext_reservations,
                "cumulative_fuel_used_l": cum_fuel,
                "fuel_compliant": fuel_comp,
            },
            "driver_itinerary": driver_itinerary,
            "loader_manifest": loader_manifest,
        })

    # Summary Metrics
    total_weight = sum(t["load_utilization"]["weight_kg"] for t in output_trips)
    total_volume = sum(t["load_utilization"]["volume_m3"] for t in output_trips)
    total_distance = sum(t["fuel"]["distance_km"] for t in output_trips)
    total_fuel = sum(t["fuel"]["fuel_consumed_l"] for t in output_trips)
    vehicles_used = len(set(t["vehicle_id"] for t in output_trips))

    changed_trip_ids = [
        f"{plan_id}-TRIP-{vid}-{tnum}" for (vid, tnum) in sorted(changed_trip_keys)
    ]

    response_dict = {
        "plan_id": plan_id,
        "base_plan_id": base_plan.get("plan_id") if isinstance(base_plan, dict) else getattr(base_plan, "plan_id", "BASE"),
        "status": "FEASIBLE" if val_result.valid else "INVALID",
        "approval_status": "DRAFT_REQUIRES_DISPATCHER_APPROVAL" if val_result.valid else "INVALID",
        "is_dispatch_ready": False,
        "planning_date": operational_context.planning_date,
        "engine_mode": "hackathon_operational_edited",
        "trips": output_trips,
        "edited_trips": output_trips,
        "deferred_orders": serialized_deferred_orders,
        "changed_references": {
            "order_refs": sorted(list(changed_order_refs)),
            "trip_keys": [f"{vid}:{tnum}" for (vid, tnum) in sorted(changed_trip_keys)],
            "trip_ids": changed_trip_ids,
        },
        "changed_order_refs": sorted(list(changed_order_refs)),
        "changed_trip_ids": changed_trip_ids,
        "order_counts": val_result.order_counts,
        "quantity_totals": val_result.quantity_totals,
        "quantity_totals_by_unit": getattr(val_result, "quantity_totals_by_unit", {}),
        "metrics": {
            "total_weight_kg": round(total_weight, 2),
            "total_volume_m3": round(total_volume, 3),
            "total_distance_km": round(total_distance, 2),
            "total_fuel_litres": round(total_fuel, 2),
            "trips_created": len(output_trips),
            "vehicles_used": vehicles_used,
        },
        "violations": [
            {
                "rule": v.rule,
                "detail": v.detail,
                "order_ref": v.order_ref,
                "vehicle_id": v.vehicle_id,
                "trip_number": v.trip_number,
                "outlet_id": v.outlet_id,
            }
            for v in val_result.violations
        ],
        "missing_data": [
            {
                "field": m.field,
                "entity_id": m.entity_id,
                "detail": m.detail,
            }
            for m in val_result.missing_data
        ],
        "validation": {
            "valid": val_result.valid,
            "is_dispatch_ready": False,
            "approval_status": "DRAFT_REQUIRES_DISPATCHER_APPROVAL" if val_result.valid else "INVALID",
            "errors": [
                {"rule": v.rule, "detail": v.detail, "order_ref": v.order_ref}
                for v in val_result.violations
            ],
            "missing_data": [
                {"field": m.field, "entity_id": m.entity_id, "detail": m.detail}
                for m in val_result.missing_data
            ],
        },
        "validation_result": val_result,
    }

    if raise_on_error and not val_result.valid:
        first_err = val_result.violations[0].detail if val_result.violations else "Edited draft plan is invalid."
        raise DispatcherEditError(first_err)

    return EditedDraftResponse(response_dict)
