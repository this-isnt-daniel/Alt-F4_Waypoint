"""
Waypoint Optimizer — Vehicle Breakdown Recovery
================================================
Pure, non-mutating recovery evaluator for dynamic in-flight vehicle breakdowns.

Supported Workflow:
  1. Identifies the broken vehicle and extracts remaining undelivered quantities.
  2. Freezes all unaffected vehicle trips and completed deliveries.
  3. Validates undelivered demand at line-item level against authoritative orders.
  4. Explicitly validates current pickup location (DEPOT or supported roadside transfer).
  5. Identifies candidate available vehicles (selected, mechanically available, not broken,
     within remaining trip limits, compatible capacity, refrigeration, and delivery windows).
  6. Schedules replacement trips from current_time_iso using greedy allocator and
     targeted local assignment.
  7. Runs independent operational validation on the combined recovery plan.
  8. Emits a new draft response with frozen trips, replacement trips, delivered,
     reassigned, and deferred quantities.
  9. Never marks a recovery plan as dispatch-ready; requires dispatcher approval.
"""
from __future__ import annotations

import copy
import dataclasses
from datetime import datetime
import math
from typing import Any, Optional, Sequence, Union

from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, Outlet,
    ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleStatus, VehicleType,
)
from waypoint_optimizer.operational.models import (
    DEFAULT_FRESH_DEPARTURE_TIME, DEFAULT_STYLE_TECH_DEPARTURE_TIME,
    DEFAULT_TIMEZONE, EvaluatedTripSchedule, OperationalContext,
    OperationalMissingData, OperationalStop, OperationalViolation,
    TravelPolicy, VehicleScheduleTimeline, WindowPolicy,
)
from waypoint_optimizer.operational.schedule_evaluator import (
    evaluate_trip_schedule, parse_iso_or_time_str,
)
from waypoint_optimizer.operational.timeline import evaluate_vehicle_timeline
from waypoint_optimizer.operational.validator import (
    OperationalValidationResult, validate_operational_plan,
)
from waypoint_optimizer.operational.draft_editor import (
    _build_driver_itinerary, _build_loader_manifest,
)


class BreakdownRecoveryError(ValueError):
    """Raised when breakdown recovery inputs are invalid or inconsistent."""
    pass


@dataclasses.dataclass(frozen=True)
class UndeliveredQuantity:
    """Line-item demand remaining undelivered following vehicle breakdown."""
    order_ref: str
    line_item_id: str
    quantity: float
    quantity_unit: str


class RecoveryDraftResponse(dict):
    """
    Dictionary-compatible response object representing a breakdown recovery draft plan.
    Provides typed property accessors and never marks a draft as dispatch-ready.
    """
    @property
    def valid(self) -> bool:
        val = self.get("validation", {})
        return bool(val.get("valid", False))

    @property
    def is_dispatch_ready(self) -> bool:
        # A recovery plan is a draft requiring dispatcher approval and is never dispatch-ready
        return False

    @property
    def frozen_trips(self) -> list[dict[str, Any]]:
        return self.get("frozen_trips", [])

    @property
    def replacement_trips(self) -> list[dict[str, Any]]:
        return self.get("replacement_trips", [])

    @property
    def trips(self) -> list[dict[str, Any]]:
        return self.get("trips", [])

    @property
    def delivered_quantities(self) -> list[dict[str, Any]]:
        return self.get("delivered_quantities", [])

    @property
    def reassigned_quantities(self) -> list[dict[str, Any]]:
        return self.get("reassigned_quantities", [])

    @property
    def deferred_quantities(self) -> list[dict[str, Any]]:
        return self.get("deferred_quantities", [])

    @property
    def deferred_orders(self) -> list[dict[str, Any]]:
        return self.get("deferred_orders", [])

    @property
    def recovery_reasons(self) -> list[dict[str, Any]]:
        return self.get("recovery_reasons", [])

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


def reallocate_broken_vehicle(
    active_plan: dict[str, Any] | Any,
    broken_vehicle_id: str,
    undelivered_quantities: Sequence[dict[str, Any] | Any],
    available_fleet: Sequence[Vehicle],
    reference_data: Any,
    operational_context: OperationalContext,
    current_time_iso: str,
    config: Optional[Any] = None,
    pickup_location: Optional[str] = "DEPOT",
    authoritative_orders: Optional[Sequence[Order]] = None,
    raise_on_error: bool = False,
    **kwargs: Any,
) -> RecoveryDraftResponse:
    """
    Pure function executing dynamic vehicle-breakdown recovery without mutating inputs.

    Parameters:
      active_plan: The active execution plan dictionary.
      broken_vehicle_id: Vehicle ID of the disabled vehicle.
      undelivered_quantities: Sequence of line-item quantities remaining undelivered.
      available_fleet: Full fleet containing available replacement candidates.
      reference_data: Authoritative reference data (travel, outlets, allowances).
      operational_context: OperationalContext containing planning date, timezone, and policies.
      current_time_iso: Current time timestamp at which breakdown occurred.
      config: Optional optimizer config.
      pickup_location: Location where cargo is transferred ('DEPOT' or roadside outlet ID).
      authoritative_orders: Mandatory sequence of authoritative orders.
      raise_on_error: If True, raises BreakdownRecoveryError on structural invalidity.
    """
    # ── 0. Handle Flexible Positional / Keyword Argument Conventions ─────────
    if authoritative_orders is None and "authoritative_orders" in kwargs:
        authoritative_orders = kwargs["authoritative_orders"]
    if isinstance(pickup_location, (list, tuple, set)) and authoritative_orders is None:
        authoritative_orders = pickup_location
        pickup_location = "DEPOT"
    if isinstance(config, (list, tuple, set)) and authoritative_orders is None:
        authoritative_orders = config
        config = None

    # ── 1. Resolve Reference Lookups (Non-Mutating) ───────────────────────────
    fleet_by_id: dict[str, Vehicle] = {v.vehicle_id: v for v in available_fleet} if available_fleet else {}

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

    # ── 2. Validate current_time_iso ──────────────────────────────────────────
    recovery_violations: list[OperationalViolation] = []
    recovery_missing_data: list[OperationalMissingData] = []
    recovery_reasons: list[dict[str, Any]] = []

    curr_dt: Optional[datetime] = None
    if not current_time_iso or not isinstance(current_time_iso, str):
        msg = "Missing or invalid current_time_iso for breakdown recovery."
        if raise_on_error:
            raise BreakdownRecoveryError(msg)
        recovery_violations.append(OperationalViolation(rule="MISSING_CURRENT_TIME", detail=msg))
    else:
        curr_dt = parse_iso_or_time_str(current_time_iso, operational_context.planning_date, operational_context.timezone)
        if curr_dt is None:
            msg = f"Cannot parse current_time_iso {current_time_iso!r}."
            if raise_on_error:
                raise BreakdownRecoveryError(msg)
            recovery_violations.append(OperationalViolation(rule="INVALID_CURRENT_TIME", detail=msg))

    # ── 3. Extract and Partition Active Plan Trips ────────────────────────────
    plan_id = (
        active_plan.get("plan_id", "RECOVERY") if isinstance(active_plan, dict)
        else getattr(active_plan, "plan_id", "RECOVERY")
    )
    raw_trips = (
        active_plan.get("trips", []) if isinstance(active_plan, dict)
        else getattr(active_plan, "trips", [])
    )
    raw_deferred = (
        active_plan.get("deferred_orders", []) if isinstance(active_plan, dict)
        else getattr(active_plan, "deferred_orders", [])
    )

    unaffected_trips: list[dict[str, Any]] = []
    broken_trips: list[dict[str, Any]] = []

    for tr in raw_trips:
        vid = tr.get("vehicle_id") if isinstance(tr, dict) else getattr(tr, "vehicle_id", None)
        if vid == broken_vehicle_id:
            broken_trips.append(copy.deepcopy(tr) if isinstance(tr, dict) else copy.deepcopy(tr.__dict__))
        else:
            unaffected_trips.append(copy.deepcopy(tr) if isinstance(tr, dict) else copy.deepcopy(tr.__dict__))

    if not broken_trips:
        msg = f"Broken vehicle {broken_vehicle_id!r} has no trips in active_plan."
        recovery_reasons.append({
            "category": "FLEET_STATE",
            "code": "BROKEN_VEHICLE_NOT_IN_PLAN",
            "detail": msg,
            "vehicle_id": broken_vehicle_id,
        })

    # ── 4. Check Mandatory Authoritative Orders (Requirement 1) ───────────────
    if not authoritative_orders:
        missing_diag = OperationalMissingData(
            field="authoritative_orders",
            entity_id="all",
            detail="Backend-confirmed orders are required for breakdown recovery.",
        )
        if raise_on_error:
            raise BreakdownRecoveryError("Backend-confirmed orders are required for breakdown recovery.")
        val_result = OperationalValidationResult(
            valid=False,
            violations=recovery_violations,
            missing_data=[missing_diag],
        )
        return RecoveryDraftResponse({
            "plan_id": f"{plan_id}-RECOVERY-{broken_vehicle_id}",
            "base_plan_id": plan_id,
            "broken_vehicle_id": broken_vehicle_id,
            "current_time_iso": current_time_iso,
            "pickup_location": (pickup_location or "DEPOT").strip() if isinstance(pickup_location, str) else "DEPOT",
            "status": "INVALID",
            "approval_status": "INVALID",
            "is_dispatch_ready": False,
            "planning_date": operational_context.planning_date if operational_context else "",
            "engine_mode": "hackathon_operational_recovery",
            "frozen_trips": unaffected_trips,
            "replacement_trips": [],
            "trips": unaffected_trips,
            "delivered_quantities": [],
            "reassigned_quantities": [],
            "deferred_quantities": [
                {
                    "order_ref": item.get("order_ref") if isinstance(item, dict) else getattr(item, "order_ref", ""),
                    "line_item_id": item.get("line_item_id") if isinstance(item, dict) else getattr(item, "line_item_id", ""),
                    "quantity": float(item.get("quantity", 0.0) if isinstance(item, dict) else getattr(item, "quantity", 0.0)),
                    "quantity_unit": item.get("quantity_unit") if isinstance(item, dict) else getattr(item, "quantity_unit", "units"),
                    "reason": "MISSING_AUTHORITATIVE_ORDERS",
                    "detail": "Backend-confirmed orders are required for breakdown recovery.",
                }
                for item in undelivered_quantities
            ],
            "deferred_orders": raw_deferred,
            "recovery_reasons": [{
                "category": "MISSING_DATA",
                "code": "MISSING_AUTHORITATIVE_ORDERS",
                "detail": "Backend-confirmed orders are required for breakdown recovery.",
            }],
            "validation": {
                "valid": False,
                "is_dispatch_ready": False,
                "violations_count": len(recovery_violations),
                "missing_data_count": 1,
            },
            "validation_result": val_result,
            "violations": [
                {"rule": v.rule, "detail": v.detail, "order_ref": v.order_ref}
                for v in recovery_violations
            ],
            "missing_data": [
                {"field": missing_diag.field, "entity_id": missing_diag.entity_id, "detail": missing_diag.detail}
            ],
            "metrics": {
                "total_weight_kg": 0.0,
                "total_volume_m3": 0.0,
                "total_distance_km": 0.0,
                "total_fuel_litres": 0.0,
                "trips_created": len(unaffected_trips),
                "vehicles_used": len(set(t.get("vehicle_id") for t in unaffected_trips if t.get("vehicle_id"))),
            },
        })

    auth_orders_by_ref: dict[str, Order] = {o.order_ref: o for o in authoritative_orders}

    # ── 5. Extract Broken Vehicle Planned Allocations & Completed Deliveries ───
    planned_on_broken: dict[tuple[str, str], float] = {}
    completed_stops: list[dict[str, Any]] = []
    completed_order_refs: set[str] = set()

    for b_tr in broken_trips:
        stops = b_tr.get("driver_itinerary") or b_tr.get("stops", [])
        for s in stops:
            s_dep = s.get("departure_time_iso")
            s_dep_dt = parse_iso_or_time_str(s_dep, operational_context.planning_date, operational_context.timezone) if s_dep else None
            stop_is_completed = (s_dep_dt is not None and curr_dt is not None and s_dep_dt <= curr_dt)
            
            raw_items = s.get("line_items_delivered", [])
            for itm in raw_items:
                oref = itm.get("order_ref")
                lid = itm.get("line_item_id") or f"{oref}-ALL"
                q = float(itm.get("quantity", 0.0))
                planned_on_broken[(oref, lid)] = planned_on_broken.get((oref, lid), 0.0) + q

            if stop_is_completed:
                completed_stops.append(s)
                for r in s.get("order_refs", []):
                    completed_order_refs.add(r)

    # ── 6. Parse and Validate Undelivered Quantities Against Authoritative Orders ──
    # Requirement 5: Validate that every undelivered order_ref and line_item_id exists in authoritative_orders
    normalized_undelivered: list[dict[str, Any]] = []
    undelivered_by_key: dict[tuple[str, str], float] = {}

    for item in undelivered_quantities:
        oref = item.get("order_ref") if isinstance(item, dict) else getattr(item, "order_ref", None)
        lid = item.get("line_item_id") if isinstance(item, dict) else getattr(item, "line_item_id", None)
        qty = float(item.get("quantity", 0.0) if isinstance(item, dict) else getattr(item, "quantity", 0.0))
        unit = item.get("quantity_unit") if isinstance(item, dict) else getattr(item, "quantity_unit", None)

        if not oref:
            msg = "Undelivered item missing order_ref."
            if raise_on_error:
                raise BreakdownRecoveryError(msg)
            recovery_violations.append(OperationalViolation(rule="UNKNOWN_ORDER_REF", detail=msg))
            continue

        if oref not in auth_orders_by_ref:
            msg = f"Order {oref!r} does not exist in authoritative_orders."
            if raise_on_error:
                raise BreakdownRecoveryError(msg)
            recovery_violations.append(OperationalViolation(rule="UNKNOWN_ORDER_REF", detail=msg, order_ref=oref))
            continue

        auth_o = auth_orders_by_ref[oref]

        # Resolve and validate line item ID against authoritative order
        if auth_o.line_items:
            matching_auth_lis = [li for li in auth_o.line_items if li.line_item_id == lid]
            if not matching_auth_lis:
                msg = f"Line item {lid!r} does not exist in authoritative order {oref!r}."
                if raise_on_error:
                    raise BreakdownRecoveryError(msg)
                recovery_violations.append(OperationalViolation(rule="UNKNOWN_LINE_ITEM_ID", detail=msg, order_ref=oref))
                continue
            effective_lid = lid
            expected_unit = matching_auth_lis[0].quantity_unit
        else:
            # Aggregated order without discrete line items
            valid_agg_lids = {f"{oref}-ALL", oref}
            if lid and lid not in valid_agg_lids:
                msg = f"Line item {lid!r} is invalid for aggregated order {oref!r} (expected {f'{oref}-ALL'!r})."
                if raise_on_error:
                    raise BreakdownRecoveryError(msg)
                recovery_violations.append(OperationalViolation(rule="UNKNOWN_LINE_ITEM_ID", detail=msg, order_ref=oref))
                continue
            effective_lid = lid or f"{oref}-ALL"
            expected_unit = unit or "units"

        key = (oref, effective_lid)

        # Check order existence on broken vehicle route
        if key not in planned_on_broken:
            matching_lids = [k[1] for k in planned_on_broken if k[0] == oref]
            if not matching_lids:
                msg = f"Order {oref!r} was not assigned to broken vehicle {broken_vehicle_id!r}."
                if raise_on_error:
                    raise BreakdownRecoveryError(msg)
                recovery_violations.append(OperationalViolation(rule="UNKNOWN_ORDER_REF", detail=msg, order_ref=oref))
                continue
            else:
                msg = f"Line item {effective_lid!r} was not assigned to broken vehicle {broken_vehicle_id!r}."
                if raise_on_error:
                    raise BreakdownRecoveryError(msg)
                recovery_violations.append(OperationalViolation(rule="UNKNOWN_LINE_ITEM_ID", detail=msg, order_ref=oref))
                continue

        # Check quantity unit
        if unit and expected_unit and unit != expected_unit:
            msg = f"Quantity unit mismatch for {oref}:{effective_lid}: expected {expected_unit!r}, got {unit!r}."
            if raise_on_error:
                raise BreakdownRecoveryError(msg)
            recovery_violations.append(OperationalViolation(rule="QUANTITY_UNIT_MISMATCH", detail=msg, order_ref=oref))
            continue

        # Check negative or zero quantity
        if qty <= 0:
            msg = f"Non-positive undelivered quantity {qty} for {oref}:{effective_lid}."
            if raise_on_error:
                raise BreakdownRecoveryError(msg)
            recovery_violations.append(OperationalViolation(rule="NEGATIVE_OR_ZERO_QUANTITY", detail=msg, order_ref=oref))
            continue

        # Check quantity greater than planned quantity
        planned_q = planned_on_broken[key]
        if qty > planned_q:
            msg = (
                f"Undelivered quantity {qty} exceeds planned quantity {planned_q} "
                f"for {oref}:{effective_lid} on broken vehicle {broken_vehicle_id!r}."
            )
            if raise_on_error:
                raise BreakdownRecoveryError(msg)
            recovery_violations.append(OperationalViolation(rule="EXCESS_UNDELIVERED_QUANTITY", detail=msg, order_ref=oref))
            continue

        undelivered_by_key[key] = undelivered_by_key.get(key, 0.0) + qty
        normalized_undelivered.append({
            "order_ref": oref,
            "line_item_id": effective_lid,
            "quantity": qty,
            "quantity_unit": expected_unit,
        })

    # ── 7. Compute Already-Delivered Quantities & Truncated Broken Trip ────────
    delivered_quantities: list[dict[str, Any]] = []
    delivered_by_key: dict[tuple[str, str], float] = {}
    for key, planned_q in planned_on_broken.items():
        undeliv_q = undelivered_by_key.get(key, 0.0)
        deliv_q = planned_q - undeliv_q
        if deliv_q > 0:
            delivered_by_key[key] = deliv_q
            oref, lid = key
            auth_o = auth_orders_by_ref.get(oref)
            unit_str = "units"
            if auth_o and auth_o.line_items:
                m_lis = [li for li in auth_o.line_items if li.line_item_id == lid]
                if m_lis:
                    unit_str = m_lis[0].quantity_unit
            delivered_quantities.append({
                "order_ref": oref,
                "line_item_id": lid,
                "quantity": round(deliv_q, 3),
                "quantity_unit": unit_str,
            })

    # Create truncated historical trip for broken vehicle with ONLY delivered quantities
    frozen_trips = list(unaffected_trips)
    if delivered_quantities and broken_trips:
        first_broken = broken_trips[0]
        completed_stops_filtered: list[dict[str, Any]] = []
        for s in first_broken.get("driver_itinerary") or first_broken.get("stops", []):
            delivered_items_for_stop: list[dict[str, Any]] = []
            stop_order_refs: list[str] = []
            for itm in s.get("line_items_delivered", []):
                oref = itm.get("order_ref")
                lid = itm.get("line_item_id") or f"{oref}-ALL"
                deliv_q = delivered_by_key.get((oref, lid), 0.0)
                if deliv_q > 0:
                    delivered_item = copy.deepcopy(itm)
                    delivered_item["quantity"] = deliv_q
                    delivered_items_for_stop.append(delivered_item)
                    if oref not in stop_order_refs:
                        stop_order_refs.append(oref)
            if delivered_items_for_stop:
                completed_stop = copy.deepcopy(s)
                completed_stop["line_items_delivered"] = delivered_items_for_stop
                completed_stop["order_refs"] = stop_order_refs
                completed_stops_filtered.append(completed_stop)

        if completed_stops_filtered:
            truncated_trip = copy.deepcopy(first_broken)
            truncated_trip["trip_id"] = f"{first_broken.get('trip_id')}-COMPLETED"
            truncated_trip["driver_itinerary"] = completed_stops_filtered
            truncated_trip["stops"] = completed_stops_filtered
            frozen_trips.append(truncated_trip)

    # ── 8. Validate Pickup Location & Roadside Geometry ───────────────────────
    # Identify all authoritative depots from:
    # 1. Broken vehicle's authoritative depot
    # 2. Available fleet and reference fleet
    # 3. Reference travel data, outlets, and authoritative orders
    broken_v = fleet_by_id.get(broken_vehicle_id)
    broken_depot = broken_v.depot if broken_v else None
    if not broken_depot and broken_trips:
        broken_depot = broken_trips[0].get("depot")

    known_depots: set[str] = set()
    if broken_depot:
        known_depots.add(broken_depot.strip().upper())
    for v in available_fleet:
        if v.depot:
            known_depots.add(v.depot.strip().upper())
    if hasattr(reference_data, "vehicles") and reference_data.vehicles:
        for v in reference_data.vehicles:
            if v.depot:
                known_depots.add(v.depot.strip().upper())
    if hasattr(reference_data, "travel") and reference_data.travel:
        if isinstance(reference_data.travel, dict):
            for k in reference_data.travel.keys():
                if isinstance(k, tuple) and len(k) > 1 and k[1]:
                    known_depots.add(str(k[1]).strip().upper())
        elif isinstance(reference_data.travel, list):
            for t in reference_data.travel:
                if hasattr(t, "depot") and t.depot:
                    known_depots.add(t.depot.strip().upper())
    if travel_data:
        for k in travel_data.keys():
            if isinstance(k, tuple) and len(k) > 1 and k[1]:
                known_depots.add(str(k[1]).strip().upper())
    for o in outlets.values():
        if o.depot:
            known_depots.add(o.depot.strip().upper())
    for o in authoritative_orders:
        if o.depot:
            known_depots.add(o.depot.strip().upper())

    pickup_loc_normalized = (pickup_location or "DEPOT").strip()
    is_depot_pickup = (
        pickup_loc_normalized.upper() == "DEPOT"
        or (broken_depot is not None and pickup_loc_normalized.upper() == broken_depot.strip().upper())
        or (pickup_loc_normalized.upper() in known_depots)
    )

    roadside_transfer_unsupported = False
    if not is_depot_pickup:
        has_roadside_support = False
        if hasattr(reference_data, "roadside_travel") and reference_data.roadside_travel:
            has_roadside_support = True
        elif isinstance(reference_data, dict) and "roadside_travel" in reference_data:
            has_roadside_support = True

        if not has_roadside_support:
            roadside_transfer_unsupported = True
            geom_msg = (
                f"Roadside transfer from outlet/location {pickup_loc_normalized!r} is unsupported "
                f"by available district travel model (requires DEPOT transfer)."
            )
            recovery_violations.append(OperationalViolation(
                rule="UNSUPPORTED_TRANSFER_GEOMETRY",
                detail=geom_msg,
            ))
            recovery_reasons.append({
                "category": "GEOMETRY",
                "code": "UNSUPPORTED_TRANSFER_GEOMETRY",
                "detail": geom_msg,
                "pickup_location": pickup_loc_normalized,
            })

    # ── 9. Authoritative Attribute Validation & Order Reallocation Reconstruction ───
    # Requirements 2, 3, 4:
    # Remove EVERY invented fallback value. If any required order or outlet attribute is missing,
    # return structured missing-data diagnostics and do NOT attempt recovery.
    undelivered_orders_req: dict[str, list[dict[str, Any]]] = {}
    for itm in normalized_undelivered:
        undelivered_orders_req.setdefault(itm["order_ref"], []).append(itm)

    reallocation_orders: list[Order] = []

    for oref, items in undelivered_orders_req.items():
        auth_o = auth_orders_by_ref[oref]

        # 9a. Validate Outlet
        if not auth_o.outlet_id:
            recovery_missing_data.append(OperationalMissingData(
                field="outlet_id", entity_id=oref, detail=f"Order {oref!r} is missing outlet_id.",
            ))
            continue

        outlet_obj = outlets.get(auth_o.outlet_id)
        if outlet_obj is None:
            recovery_missing_data.append(OperationalMissingData(
                field="outlets", entity_id=auth_o.outlet_id,
                detail=f"Authoritative outlet {auth_o.outlet_id!r} referenced by order {oref!r} not found in reference data.",
            ))
            continue

        # 9b. Validate Brand (No Fallback)
        brand_val = auth_o.brand or outlet_obj.brand
        if brand_val is None:
            recovery_missing_data.append(OperationalMissingData(
                field="brand", entity_id=oref, detail=f"Order {oref!r} and outlet {auth_o.outlet_id!r} are missing brand.",
            ))

        # 9c. Validate District (No Fallback)
        district_val = auth_o.district or outlet_obj.district
        if not district_val or not str(district_val).strip():
            recovery_missing_data.append(OperationalMissingData(
                field="district", entity_id=oref, detail=f"Order {oref!r} and outlet {auth_o.outlet_id!r} are missing district.",
            ))

        # 9d. Validate Depot (No Fallback)
        depot_val = auth_o.depot or outlet_obj.depot
        if not depot_val or not str(depot_val).strip():
            recovery_missing_data.append(OperationalMissingData(
                field="depot", entity_id=oref, detail=f"Order {oref!r} and outlet {auth_o.outlet_id!r} are missing depot.",
            ))

        # 9e. Validate Dock Type (No Fallback)
        dock_type = auth_o.dock_type or outlet_obj.dock_type
        if dock_type is None:
            recovery_missing_data.append(OperationalMissingData(
                field="dock_type", entity_id=oref, detail=f"Order {oref!r} and outlet {auth_o.outlet_id!r} are missing dock_type.",
            ))

        # 9f. Validate Parking Constraint (No Fallback)
        parking = auth_o.parking_constraint or outlet_obj.parking_constraint
        if parking is None:
            recovery_missing_data.append(OperationalMissingData(
                field="parking_constraint", entity_id=oref, detail=f"Order {oref!r} and outlet {auth_o.outlet_id!r} are missing parking_constraint.",
            ))

        # 9g. Validate Delivery Windows (No Fallback)
        w_open = auth_o.window_open_time or outlet_obj.window_open_time
        w_close = auth_o.window_close_time or outlet_obj.window_close_time
        if not w_open or not w_close:
            recovery_missing_data.append(OperationalMissingData(
                field="delivery_windows", entity_id=oref, detail=f"Order {oref!r} and outlet {auth_o.outlet_id!r} are missing delivery windows.",
            ))

        # 9h. Validate Temperature Requirement (No Fallback)
        temp_req = auth_o.temp_requirement
        if temp_req is None:
            recovery_missing_data.append(OperationalMissingData(
                field="temp_requirement", entity_id=oref, detail=f"Order {oref!r} is missing temp_requirement.",
            ))

        # 9i. Validate Service Allowance (No Fallback)
        if brand_val is not None and dock_type is not None:
            if (brand_val, dock_type) not in allowances:
                recovery_missing_data.append(OperationalMissingData(
                    field="service_allowance", entity_id=f"{brand_val.value}:{dock_type.value}",
                    detail=f"Service allowance for brand {brand_val.value!r} and dock {dock_type.value!r} is missing from reference data.",
                ))

        # 9j. Validate District Travel (No Fallback)
        if district_val and depot_val:
            if (district_val, depot_val) not in travel_data:
                recovery_missing_data.append(OperationalMissingData(
                    field="district_travel", entity_id=f"{district_val}:{depot_val}",
                    detail=f"District travel for district {district_val!r} and depot {depot_val!r} is missing from reference data.",
                ))

        # 9k. Validate Line-Item Unit Weight and Volume (No Fallback)
        built_lis: list[LineItem] = []
        tot_q = 0.0
        tot_w = 0.0
        tot_v = 0.0

        for itm in items:
            q = itm["quantity"]
            lid = itm["line_item_id"]
            if auth_o.line_items:
                matching_auth_lis = [li for li in auth_o.line_items if li.line_item_id == lid]
                if not matching_auth_lis:
                    recovery_missing_data.append(OperationalMissingData(
                        field="line_item", entity_id=lid, detail=f"Line item {lid!r} missing in authoritative order {oref!r}.",
                    ))
                    continue
                auth_li = matching_auth_lis[0]
                unit_w = auth_li.unit_weight_kg
                unit_v = auth_li.unit_volume_m3
                desc = auth_li.description
            else:
                if auth_o.order_units and auth_o.order_units > 0:
                    unit_w = auth_o.order_weight_kg / auth_o.order_units
                    unit_v = auth_o.order_volume_m3 / auth_o.order_units
                else:
                    unit_w = auth_o.order_weight_kg
                    unit_v = auth_o.order_volume_m3
                desc = f"{oref} cargo"

            if unit_w is None or math.isnan(unit_w) or unit_w <= 0:
                recovery_missing_data.append(OperationalMissingData(
                    field="unit_weight", entity_id=lid, detail=f"Line item {lid!r} of order {oref!r} has missing or non-positive unit weight.",
                ))
            if unit_v is None or math.isnan(unit_v) or unit_v <= 0:
                recovery_missing_data.append(OperationalMissingData(
                    field="unit_volume", entity_id=lid, detail=f"Line item {lid!r} of order {oref!r} has missing or non-positive unit volume.",
                ))

            if unit_w is not None and unit_v is not None and unit_w > 0 and unit_v > 0:
                built_lis.append(LineItem(
                    line_item_id=lid,
                    quantity=q,
                    quantity_unit=itm["quantity_unit"],
                    unit_weight_kg=unit_w,
                    unit_volume_m3=unit_v,
                    description=desc,
                ))
                tot_q += q
                tot_w += q * unit_w
                tot_v += q * unit_v

        if not recovery_missing_data and not any(v.order_ref == oref for v in recovery_violations):
            realloc_order = Order(
                order_ref=oref,
                outlet_id=auth_o.outlet_id,
                brand=brand_val,
                district=district_val,
                depot=depot_val,
                dock_type=dock_type,
                parking_constraint=parking,
                mall_window=auth_o.mall_window,
                window_open_time=w_open,
                window_close_time=w_close,
                temp_requirement=temp_req,
                order_units=int(round(tot_q)),
                order_weight_kg=round(tot_w, 3),
                order_volume_m3=round(tot_v, 4),
                line_items=built_lis,
                deferred_yesterday=auth_o.deferred_yesterday,
                days_since_last_served=auth_o.days_since_last_served,
            )
            reallocation_orders.append(realloc_order)

    # ── 10. Short-Circuit If Any Required Attribute Is Missing (Requirement 3) ──
    # If any required order or outlet attribute is missing, return structured missing-data
    # diagnostics and do NOT attempt recovery.
    if recovery_missing_data or (recovery_violations and not reallocation_orders):
        val_result = OperationalValidationResult(
            valid=False,
            violations=recovery_violations,
            missing_data=recovery_missing_data,
        )
        if raise_on_error:
            err_msg = recovery_missing_data[0].detail if recovery_missing_data else recovery_violations[0].detail
            raise BreakdownRecoveryError(err_msg)
        return RecoveryDraftResponse({
            "plan_id": f"{plan_id}-RECOVERY-{broken_vehicle_id}",
            "base_plan_id": plan_id,
            "broken_vehicle_id": broken_vehicle_id,
            "current_time_iso": current_time_iso,
            "pickup_location": pickup_loc_normalized,
            "status": "INVALID",
            "approval_status": "INVALID",
            "is_dispatch_ready": False,
            "planning_date": operational_context.planning_date if operational_context else "",
            "engine_mode": "hackathon_operational_recovery",
            "frozen_trips": frozen_trips,
            "replacement_trips": [],
            "trips": frozen_trips,
            "delivered_quantities": delivered_quantities,
            "reassigned_quantities": [],
            "deferred_quantities": [
                {
                    "order_ref": item.get("order_ref"),
                    "line_item_id": item.get("line_item_id"),
                    "quantity": float(item.get("quantity", 0.0)),
                    "quantity_unit": item.get("quantity_unit", "units"),
                    "reason": "MISSING_REQUIRED_ATTRIBUTES",
                    "detail": "Recovery aborted due to missing authoritative order or reference attributes.",
                }
                for item in undelivered_quantities
            ],
            "deferred_orders": raw_deferred,
            "recovery_reasons": recovery_reasons if recovery_reasons else [{
                "category": "MISSING_DATA",
                "code": "MISSING_REQUIRED_ATTRIBUTES",
                "detail": "Recovery aborted due to missing authoritative attributes.",
            }],
            "validation": {
                "valid": False,
                "is_dispatch_ready": False,
                "violations_count": len(recovery_violations),
                "missing_data_count": len(recovery_missing_data),
            },
            "validation_result": val_result,
            "violations": [
                {"rule": v.rule, "detail": v.detail, "order_ref": v.order_ref}
                for v in recovery_violations
            ],
            "missing_data": [
                {"field": m.field, "entity_id": m.entity_id, "detail": m.detail}
                for m in recovery_missing_data
            ],
            "metrics": {
                "total_weight_kg": 0.0,
                "total_volume_m3": 0.0,
                "total_distance_km": 0.0,
                "total_fuel_litres": 0.0,
                "trips_created": len(frozen_trips),
                "vehicles_used": len(set(t.get("vehicle_id") for t in frozen_trips if t.get("vehicle_id"))),
            },
        })

    # ── 9. Filter Candidate Replacement Vehicles ──────────────────────────────
    # Requirement 7:
    # - mechanically available
    # - selected for planning
    # - not broken
    # - available at current_time_iso
    # - within remaining trip limits
    # - compatible with weight, volume, refrigeration, depot, access
    candidate_vehicles: list[Vehicle] = []
    v_frozen_counts: dict[str, int] = {}
    v_next_avail_dt: dict[str, datetime] = {}

    for f_tr in frozen_trips:
        v_id = f_tr.get("vehicle_id")
        if v_id:
            v_frozen_counts[v_id] = v_frozen_counts.get(v_id, 0) + 1
            ret_iso = f_tr.get("vehicle_next_available_iso") or f_tr.get("depot_return_arrival_iso")
            if ret_iso and curr_dt:
                ret_dt = parse_iso_or_time_str(ret_iso, operational_context.planning_date, operational_context.timezone)
                if ret_dt and (v_id not in v_next_avail_dt or ret_dt > v_next_avail_dt[v_id]):
                    v_next_avail_dt[v_id] = ret_dt

    for v in available_fleet:
        # Strictly exclude broken vehicle
        if v.vehicle_id == broken_vehicle_id:
            continue
        # Check mechanical status and selection
        if v.status != VehicleStatus.AVAILABLE:
            continue
        if not v.is_selected_for_planning:
            continue
        # Check fuel state known
        if v.weekly_fuel_used_l is None or v.external_reservations_l is None:
            recovery_missing_data.append(OperationalMissingData(
                field="weekly_fuel_used_l",
                entity_id=v.vehicle_id,
                detail=f"Candidate vehicle {v.vehicle_id!r} is missing live fuel state.",
            ))
            continue

        # Check remaining trip limit
        trips_already = v_frozen_counts.get(v.vehicle_id, 0)
        max_trips = min(v.remaining_trips, config.max_trips_per_vehicle if config and hasattr(config, "max_trips_per_vehicle") else 2)
        if trips_already >= max_trips:
            continue

        candidate_vehicles.append(v)

    # ── 10. Reallocate Remaining Quantities (Greedy Allocator) ─────────────────
    replacement_trips: list[dict[str, Any]] = []
    reassigned_quantities: list[dict[str, Any]] = []
    deferred_quantities: list[dict[str, Any]] = []
    all_evaluated_replacement_scheds: list[EvaluatedTripSchedule] = []

    # If roadside geometry is unsupported, all undelivered items cannot be transferred
    if roadside_transfer_unsupported:
        for o in reallocation_orders:
            for li in o.line_items:
                deferred_quantities.append({
                    "order_ref": o.order_ref,
                    "line_item_id": li.line_item_id,
                    "quantity": li.quantity,
                    "quantity_unit": li.quantity_unit,
                    "reason": "UNSUPPORTED_TRANSFER_GEOMETRY",
                    "detail": f"Roadside transfer from {pickup_loc_normalized!r} is unsupported.",
                })
    else:
        # Group orders by brand and district to preserve single-brand & single-district policy
        orders_by_brand_dist: dict[tuple[Brand, str], list[Order]] = {}
        for o in reallocation_orders:
            orders_by_brand_dist.setdefault((o.brand, o.district), []).append(o)

        assigned_order_refs: set[str] = set()
        used_candidate_ids: set[str] = set()

        for (grp_brand, grp_district), grp_orders in orders_by_brand_dist.items():
            placed_for_group = False

            # Try candidate vehicles
            for cand_v in candidate_vehicles:
                if cand_v.vehicle_id in used_candidate_ids:
                    continue

                # Check refrigeration compatibility
                cand_temp_ok = True
                for o in grp_orders:
                    if o.temp_requirement == TempRequirement.CHILLED and cand_v.temp != TempSpec.REEFER:
                        cand_temp_ok = False
                        break
                if not cand_temp_ok:
                    continue

                # Check access constraints
                cand_access_ok = True
                for o in grp_orders:
                    if o.parking_constraint == ParkingConstraint.VAN_ONLY and cand_v.type != VehicleType.VAN:
                        cand_access_ok = False
                        break
                if not cand_access_ok:
                    continue

                # Check physical capacity
                req_w = sum(o.order_weight_kg for o in grp_orders)
                req_v = sum(o.order_volume_m3 for o in grp_orders)
                if req_w > cand_v.weight_cap_kg or req_v > cand_v.volume_cap_m3:
                    continue

                # Determine earliest departure time for this vehicle
                trips_done = v_frozen_counts.get(cand_v.vehicle_id, 0)
                trip_num = trips_done + 1
                base_avail_dt = curr_dt
                if cand_v.vehicle_id in v_next_avail_dt and v_next_avail_dt[cand_v.vehicle_id] > base_avail_dt:
                    base_avail_dt = v_next_avail_dt[cand_v.vehicle_id]
                if cand_v.earliest_available_time:
                    cand_e_dt = parse_iso_or_time_str(cand_v.earliest_available_time, operational_context.planning_date, operational_context.timezone)
                    if cand_e_dt and cand_e_dt > base_avail_dt:
                        base_avail_dt = cand_e_dt

                dep_iso = base_avail_dt.isoformat() if base_avail_dt else current_time_iso

                # Evaluate trip schedule
                trip_sched = evaluate_trip_schedule(
                    vehicle=cand_v,
                    trip_number=trip_num,
                    orders=grp_orders,
                    brand=grp_brand,
                    district=grp_district,
                    depot=cand_v.depot,
                    departure_time_iso=dep_iso,
                    travel_data=travel_data,
                    outlets=outlets,
                    allowances=allowances,
                    context=operational_context,
                )

                # Check feasibility
                if trip_sched.is_feasible:
                    placed_for_group = True
                    used_candidate_ids.add(cand_v.vehicle_id)
                    all_evaluated_replacement_scheds.append(trip_sched)

                    # Build serialized replacement trip
                    itinerary = _build_driver_itinerary(trip_sched.stops)
                    loader_man = _build_loader_manifest(trip_sched.stops, {o.order_ref: o for o in grp_orders})

                    rep_trip_id = f"{plan_id}-RECOVERY-{cand_v.vehicle_id}-{trip_num}"
                    rep_trip_dict = {
                        "trip_id": rep_trip_id,
                        "vehicle_id": cand_v.vehicle_id,
                        "trip_number": trip_num,
                        "brand": grp_brand.value,
                        "district": grp_district,
                        "depot": cand_v.depot,
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
                            "prior_used_l": cand_v.weekly_fuel_used_l,
                            "external_reservations_l": cand_v.external_reservations_l,
                            "cumulative_fuel_used_l": trip_sched.cumulative_fuel_used_l,
                            "fuel_compliant": trip_sched.fuel_compliant,
                        },
                        "driver_itinerary": itinerary,
                        "loader_manifest": loader_man,
                        "is_replacement_trip": True,
                        "recovery_from_vehicle_id": broken_vehicle_id,
                    }
                    replacement_trips.append(rep_trip_dict)

                    for o in grp_orders:
                        assigned_order_refs.add(o.order_ref)
                        for li in o.line_items:
                            reassigned_quantities.append({
                                "order_ref": o.order_ref,
                                "line_item_id": li.line_item_id,
                                "quantity": li.quantity,
                                "quantity_unit": li.quantity_unit,
                                "target_vehicle_id": cand_v.vehicle_id,
                                "target_trip_number": trip_num,
                            })
                    break

            if not placed_for_group:
                # Could not place group on any candidate vehicle
                for o in grp_orders:
                    for li in o.line_items:
                        deferred_quantities.append({
                            "order_ref": o.order_ref,
                            "line_item_id": li.line_item_id,
                            "quantity": li.quantity,
                            "quantity_unit": li.quantity_unit,
                            "reason": "INSUFFICIENT_FLEET_CAPACITY_AT_BREAKDOWN",
                            "detail": f"No available replacement vehicle satisfied capacity/window constraints for {o.order_ref!r}.",
                        })

    # ── 11. Build Unified Deferred Orders List ────────────────────────────────
    # Combine original deferred orders with newly deferred recovery orders
    unified_deferred_orders: list[dict[str, Any]] = []
    # Copy raw_deferred
    for d in raw_deferred:
        unified_deferred_orders.append(copy.deepcopy(d) if isinstance(d, dict) else copy.deepcopy(d.__dict__))

    for def_q in deferred_quantities:
        oref = def_q["order_ref"]
        # Find if order already represented in unified_deferred_orders
        existing = next((d for d in unified_deferred_orders if d.get("order_ref") == oref), None)
        if existing:
            lis = existing.setdefault("line_items", [])
            lis.append({
                "line_item_id": def_q["line_item_id"],
                "quantity": def_q["quantity"],
                "quantity_unit": def_q["quantity_unit"],
            })
            existing["deferred_quantity"] = existing.get("deferred_quantity", 0.0) + def_q["quantity"]
        else:
            unified_deferred_orders.append({
                "order_ref": oref,
                "deferred_quantity": def_q["quantity"],
                "reason": def_q.get("reason", "BREAKDOWN_DEFERRAL"),
                "evidence_detail": def_q.get("detail", "Deferred during vehicle breakdown recovery."),
                "line_items": [
                    {
                        "line_item_id": def_q["line_item_id"],
                        "quantity": def_q["quantity"],
                        "quantity_unit": def_q["quantity_unit"],
                    }
                ],
            })

    # ── 12. Run Independent Operational Validator ─────────────────────────────
    # Reconstruct vehicle timelines across all vehicles
    all_combined_trips = list(frozen_trips) + list(replacement_trips)

    # Reconstruct full order objects for validator demand conservation
    orders_for_validator: list[Order] = list(authoritative_orders)

    val_result = validate_operational_plan(
        orders=orders_for_validator,
        timelines={"trips": all_combined_trips},
        context=operational_context,
        fleet=available_fleet,
        reference_data=reference_data,
        travel_data=travel_data,
        outlets=outlets,
        allowances=allowances,
        deferred_orders=unified_deferred_orders,
        config=config,
    )

    if recovery_violations:
        comb_violations = list(recovery_violations) + list(val_result.violations)
        val_result = dataclasses.replace(
            val_result,
            valid=False,
            violations=comb_violations,
        )
    if recovery_missing_data:
        comb_missing = list(recovery_missing_data) + list(val_result.missing_data)
        val_result = dataclasses.replace(
            val_result,
            valid=False,
            missing_data=comb_missing,
        )

    # ── 13. Summary Metrics & Response Assembly ───────────────────────────────
    total_w = sum(t.get("load_utilization", {}).get("weight_kg", 0.0) for t in all_combined_trips)
    total_v = sum(t.get("load_utilization", {}).get("volume_m3", 0.0) for t in all_combined_trips)
    total_dist = sum(t.get("fuel", {}).get("distance_km", 0.0) for t in all_combined_trips)
    total_f = sum(t.get("fuel", {}).get("fuel_consumed_l", 0.0) for t in all_combined_trips)
    active_vids = set(t.get("vehicle_id") for t in all_combined_trips if t.get("vehicle_id"))

    response_dict = {
        "plan_id": f"{plan_id}-RECOVERY-{broken_vehicle_id}",
        "base_plan_id": plan_id,
        "broken_vehicle_id": broken_vehicle_id,
        "current_time_iso": current_time_iso,
        "pickup_location": pickup_loc_normalized,
        "status": "FEASIBLE" if val_result.valid else "INVALID",
        "approval_status": "DRAFT_REQUIRES_DISPATCHER_APPROVAL" if val_result.valid else "INVALID",
        "is_dispatch_ready": False,
        "planning_date": operational_context.planning_date,
        "engine_mode": "hackathon_operational_recovery",
        "frozen_trips": frozen_trips,
        "replacement_trips": replacement_trips,
        "trips": all_combined_trips,
        "delivered_quantities": delivered_quantities,
        "reassigned_quantities": reassigned_quantities,
        "deferred_quantities": deferred_quantities,
        "deferred_orders": unified_deferred_orders,
        "recovery_reasons": recovery_reasons,
        "validation": {
            "valid": val_result.valid,
            "is_dispatch_ready": False,
            "violations_count": len(val_result.violations),
            "missing_data_count": len(val_result.missing_data),
        },
        "validation_result": val_result,
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
        "metrics": {
            "total_weight_kg": round(total_w, 2),
            "total_volume_m3": round(total_v, 3),
            "total_distance_km": round(total_dist, 2),
            "total_fuel_litres": round(total_f, 2),
            "trips_created": len(all_combined_trips),
            "vehicles_used": len(active_vids),
        },
    }

    if raise_on_error and not val_result.valid:
        first_err = val_result.violations[0].detail if val_result.violations else "Recovery plan is invalid."
        raise BreakdownRecoveryError(first_err)

    return RecoveryDraftResponse(response_dict)
