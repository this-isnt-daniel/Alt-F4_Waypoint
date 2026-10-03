"""
Backend Adapter for the Waypoint Hybrid Optimization Engine
============================================================
Adheres to strict ownership boundaries:
  - Optimizer: allocation, scheduling, validation, CP-SAT improvement.
  - Backend: database, authentication, cutoff rules, persistence, approval, status changes.
  - Dispatcher: reviews, edits, and confirms/approves the draft plan.

Interacts with public optimizer APIs only:
  - generate_daily_draft_plan(...)
  - evaluate_edited_draft(...)
  - reallocate_broken_vehicle(...)
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.deferral import Deferral
from app.models.events import DeliveryEvent
from app.models.incident import VehicleIncident
from app.models.order import Order as DbOrder, OrderLine as DbOrderLine
from app.models.outlet import Outlet as DbOutlet
from app.models.plan import DraftPlan
from app.models.product import Product as DbProduct
from app.models.trip import Trip as DbTrip, TripStop as DbTripStop
from app.models.vehicle import Vehicle as DbVehicle
from app.services.manifest_service import add_stop_items, delete_stop_items

from waypoint_optimizer.domain import (
    Brand,
    DockType,
    LineItem,
    Order as OptimizerOrder,
    ParkingConstraint,
    TempRequirement,
    TempSpec,
    Vehicle as OptimizerVehicle,
    VehicleStatus,
    VehicleType,
)
from waypoint_optimizer.operational.models import OperationalContext
from waypoint_optimizer.operational.draft_editor import (
    DeferWholeOrderAction,
    MoveLineItemAction,
    MoveWholeOrderAction,
    ReinstateWholeOrderAction,
    SplitLineItemAction,
    evaluate_edited_draft,
)
from waypoint_optimizer.operational.breakdown_recovery import reallocate_broken_vehicle
from waypoint_optimizer.hackathon_planner import generate_daily_draft_plan
from waypoint_optimizer.adapters.csv_adapter import ReferenceData, load_reference_data


# ──────────────────────────────────────────────────────────────────────────────
# 1. Authoritative Reference CSV Resolver
# ──────────────────────────────────────────────────────────────────────────────

REQUIRED_REAL_CSVS = (
    "outlets.csv",
    "vehicles.csv",
    "district_travel.csv",
    "service_allowance.csv",
    "calendar.csv",
    "traffic_speed.csv",
    "road_conditions.csv",
)

_CACHED_REF_DATA: Optional[ReferenceData] = None


def resolve_real_data_dir() -> Path:
    """Locates the directory containing the 7 authoritative reference CSVs."""
    current_dir = Path(__file__).resolve().parent
    candidates = [
        current_dir.parent.parent / "data",                         # apps/backend/data
        current_dir.parent.parent / "optimization_engine" / "data", # apps/backend/optimization_engine/data
        Path("apps/backend/data").resolve(),
        Path("data").resolve(),
    ]

    for cand in candidates:
        if cand.is_dir():
            missing = [f for f in REQUIRED_REAL_CSVS if not (cand / f).is_file()]
            if not missing:
                return cand.resolve()

    raise FileNotFoundError(
        "Authoritative reference CSV directory not found. "
        f"Checked candidate locations: {[str(c) for c in candidates]}"
    )


def get_reference_data(force_reload: bool = False) -> ReferenceData:
    """Loads and caches reference data from real CSVs."""
    global _CACHED_REF_DATA
    if _CACHED_REF_DATA is None or force_reload:
        data_dir = resolve_real_data_dir()
        _CACHED_REF_DATA = load_reference_data(data_dir)
    return _CACHED_REF_DATA


# ──────────────────────────────────────────────────────────────────────────────
# 2. Database -> Optimizer Domain Converters
# ──────────────────────────────────────────────────────────────────────────────

def convert_db_order_to_optimizer(
    db_order: DbOrder,
    ref_data: ReferenceData,
    db: Session,
) -> OptimizerOrder:
    """Converts a confirmed backend DbOrder into an immutable optimizer Order."""
    # Check authoritative outlet in reference data
    authoritative_outlet = ref_data.outlets.get(db_order.outlet_id)

    if authoritative_outlet:
        brand = authoritative_outlet.brand
        district = authoritative_outlet.district
        depot = authoritative_outlet.depot
        dock_type = authoritative_outlet.dock_type
        parking_constraint = authoritative_outlet.parking_constraint
        mall_window = authoritative_outlet.mall_window
        window_open_time = db_order.window_open or authoritative_outlet.window_open_time
        window_close_time = db_order.window_close or authoritative_outlet.window_close_time
    else:
        # Fallback to database Outlet record
        db_outlet = db.query(DbOutlet).filter(DbOutlet.outlet_id == db_order.outlet_id).first()
        try:
            brand = Brand(db_order.brand.lower()) if db_order.brand else (
                Brand(db_outlet.brand.lower()) if db_outlet and db_outlet.brand else Brand.FRESH
            )
        except ValueError:
            brand = Brand.FRESH

        district = (db_outlet.district if db_outlet and db_outlet.district else "Colombo")
        depot = (db_outlet.depot_id if db_outlet and db_outlet.depot_id else "DEP1")

        try:
            dock_type = (
                DockType(db_outlet.dock_type.lower())
                if db_outlet and db_outlet.dock_type
                else DockType.NORMAL
            )
        except ValueError:
            dock_type = DockType.NORMAL

        try:
            parking_constraint = (
                ParkingConstraint(db_outlet.park_constraint.lower())
                if db_outlet and db_outlet.park_constraint
                else ParkingConstraint.NONE
            )
        except ValueError:
            parking_constraint = ParkingConstraint.NONE

        mall_window = db_outlet.mall_window if db_outlet else None
        window_open_time = db_order.window_open or (db_outlet.window_open if db_outlet else None)
        window_close_time = db_order.window_close or (db_outlet.window_close if db_outlet else None)

    # Temperature requirement
    try:
        temp_req = (
            TempRequirement(db_order.temp_req.lower())
            if db_order.temp_req
            else TempRequirement.AMBIENT
        )
    except ValueError:
        temp_req = TempRequirement.AMBIENT

    # Convert line items
    line_items: List[LineItem] = []
    total_line_weight = 0.0
    total_line_volume = 0.0
    total_line_units = 0

    if db_order.lines:
        for line in db_order.lines:
            product = db.query(DbProduct).filter(DbProduct.product_id == line.product_id).first()
            u_wt = float(product.unit_wt_kg) if product and product.unit_wt_kg else 1.0
            u_vol = float(product.unit_vol_m3) if product and product.unit_vol_m3 else 0.01
            u_unit = product.unit if product and product.unit else "units"
            desc = product.name if product and product.name else f"Item {line.product_id}"
            qty = float(line.quantity)

            line_items.append(
                LineItem(
                    line_item_id=str(line.line_item_id),
                    quantity=qty,
                    quantity_unit=u_unit,
                    unit_weight_kg=u_wt,
                    unit_volume_m3=u_vol,
                    description=desc,
                )
            )
            total_line_weight += qty * u_wt
            total_line_volume += qty * u_vol
            total_line_units += int(qty)

    order_units = db_order.order_units if db_order.order_units else (total_line_units or 1)
    order_weight_kg = (
        float(db_order.order_wt_kg)
        if db_order.order_wt_kg is not None
        else (total_line_weight if total_line_weight > 0 else 1.0)
    )
    order_volume_m3 = (
        float(db_order.order_vol_m3)
        if db_order.order_vol_m3 is not None
        else (total_line_volume if total_line_volume > 0 else 0.01)
    )

    if not line_items:
        line_items.append(
            LineItem(
                line_item_id=f"{db_order.order_id}-LI-1",
                quantity=float(order_units),
                quantity_unit="units",
                unit_weight_kg=round(order_weight_kg / max(1, order_units), 4),
                unit_volume_m3=round(order_volume_m3 / max(1, order_units), 6),
                description=f"Order {db_order.order_id} cargo",
            )
        )

    return OptimizerOrder(
        order_ref=str(db_order.order_id),
        outlet_id=str(db_order.outlet_id),
        brand=brand,
        district=district,
        depot=depot,
        dock_type=dock_type,
        parking_constraint=parking_constraint,
        mall_window=mall_window,
        window_open_time=window_open_time,
        window_close_time=window_close_time,
        temp_requirement=temp_req,
        order_units=int(order_units),
        order_weight_kg=float(order_weight_kg),
        order_volume_m3=float(order_volume_m3),
        deferred_yesterday=bool(db_order.deferred_prev),
        days_since_last_served=int(db_order.defer_count or 0),
        line_items=line_items,
    )


def convert_db_vehicle_to_optimizer(
    db_vehicle: DbVehicle,
    ref_data: ReferenceData,
) -> OptimizerVehicle:
    """Converts a database DbVehicle into an immutable optimizer Vehicle."""
    # Check if reference data has standard profile specs
    ref_match = next((v for v in ref_data.vehicles if v.vehicle_id == db_vehicle.vehicle_id), None)

    try:
        v_type = VehicleType(db_vehicle.type.lower()) if db_vehicle.type else (
            ref_match.type if ref_match else VehicleType.TRUCK
        )
    except ValueError:
        v_type = VehicleType.TRUCK

    try:
        v_temp = TempSpec(db_vehicle.temp.lower()) if db_vehicle.temp else (
            ref_match.temp if ref_match else TempSpec.AMBIENT
        )
    except ValueError:
        v_temp = TempSpec.AMBIENT

    # Status: available vs in_workshop
    status_str = (db_vehicle.status or "available").lower()
    if status_str in ("in_workshop", "maintenance", "disabled", "breakdown"):
        v_status = VehicleStatus.IN_WORKSHOP
    else:
        v_status = VehicleStatus.AVAILABLE

    weight_cap = float(db_vehicle.weight_cap_kg) if db_vehicle.weight_cap_kg else (
        ref_match.weight_cap_kg if ref_match else 2500.0
    )
    vol_cap = float(db_vehicle.vol_cap_m3) if db_vehicle.vol_cap_m3 else (
        ref_match.volume_cap_m3 if ref_match else 12.0
    )
    depot = db_vehicle.depot_id or (ref_match.depot if ref_match else "DEP1")
    fuel_type = db_vehicle.fuel_type or (ref_match.fuel_type if ref_match else "diesel")
    km_per_l = float(db_vehicle.km_per_l) if db_vehicle.km_per_l else (
        ref_match.km_per_l if ref_match else 4.5
    )
    weekly_quota = float(db_vehicle.fuel_quota_l) if db_vehicle.fuel_quota_l else (
        ref_match.weekly_fuel_quota_l if ref_match else 250.0
    )

    return OptimizerVehicle(
        vehicle_id=str(db_vehicle.vehicle_id),
        status=v_status,
        type=v_type,
        temp=v_temp,
        weight_cap_kg=weight_cap,
        volume_cap_m3=vol_cap,
        depot=depot,
        fuel_type=fuel_type,
        km_per_l=km_per_l,
        weekly_fuel_quota_l=weekly_quota,
        weekly_fuel_used_l=0.0,
        external_reservations_l=0.0,
        is_selected_for_planning=(v_status == VehicleStatus.AVAILABLE),
        remaining_trips=2,
    )


def _ensure_live_fleet_state(v: OptimizerVehicle) -> OptimizerVehicle:
    import dataclasses
    updates = {}
    if v.external_reservations_l is None:
        updates["external_reservations_l"] = 0.0
    if v.weekly_fuel_used_l is None:
        updates["weekly_fuel_used_l"] = 0.0
    if updates:
        return dataclasses.replace(v, **updates)
    return v


def _to_json_serializable_plan(plan_obj: Any) -> Any:
    """Recursively converts optimizer response dicts into pure JSON serializable dicts."""
    if isinstance(plan_obj, dict):
        clean = {}
        for k, v in plan_obj.items():
            if k == "validation_result":
                continue
            clean[k] = _to_json_serializable_plan(v)
        return clean
    elif hasattr(plan_obj, "__dataclass_fields__"):
        import dataclasses
        return dataclasses.asdict(plan_obj)
    elif isinstance(plan_obj, (list, tuple)):
        return [_to_json_serializable_plan(x) for x in plan_obj]
    elif hasattr(plan_obj, "value"):
        return plan_obj.value
    return plan_obj


# ──────────────────────────────────────────────────────────────────────────────
# 3. Core Optimization Operations
# ──────────────────────────────────────────────────────────────────────────────

def generate_daily_draft_plan_operation(
    db: Session,
    depot_id: Optional[str] = None,
    target_date: Optional[date] = None,
    brand: Optional[str] = None,
    enable_targeted_cpsat: bool = True,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    POST /dispatcher/plans/draft implementation.
    Reads confirmed orders, reads fleet state, loads real reference CSVs,
    runs hybrid optimizer, and persists returned draft plan in database.
    """
    effective_date = target_date or date.today()
    planning_date_str = effective_date.isoformat()
    ref_data = get_reference_data()

    # Query confirmed orders
    order_query = db.query(DbOrder).filter(DbOrder.status == "confirmed")
    if target_date:
        order_query = order_query.filter(DbOrder.order_date == target_date)
    if brand:
        order_query = order_query.filter(DbOrder.brand == brand)

    db_orders = order_query.all()
    if not db_orders:
        raise HTTPException(
            status_code=400,
            detail=f"No confirmed orders found for planning date {planning_date_str}"
        )

    # Convert orders to optimizer domain
    optimizer_orders = [convert_db_order_to_optimizer(o, ref_data, db) for o in db_orders]

    # Query vehicles from DB; fallback to reference fleet if DB is empty
    vehicle_query = db.query(DbVehicle)
    if depot_id:
        vehicle_query = vehicle_query.filter(DbVehicle.depot_id == depot_id)
    db_vehicles = vehicle_query.all()

    if db_vehicles:
        optimizer_fleet = [convert_db_vehicle_to_optimizer(v, ref_data) for v in db_vehicles]
    else:
        # Fallback to authoritative reference fleet
        if depot_id:
            optimizer_fleet = [v for v in ref_data.vehicles if v.depot == depot_id]
        else:
            optimizer_fleet = list(ref_data.vehicles)

    optimizer_fleet = [_ensure_live_fleet_state(v) for v in optimizer_fleet]

    # Setup operational context
    context = OperationalContext(
        planning_date=planning_date_str,
        timezone="Asia/Colombo",
    )

    # Execute optimizer public API (hybrid multi-start greedy + targeted CP-SAT)
    plan_dict = generate_daily_draft_plan(
        orders=optimizer_orders,
        fleet=optimizer_fleet,
        reference_data=ref_data,
        context=context,
        enable_targeted_cpsat=enable_targeted_cpsat,
    )

    plan_id = plan_dict.get("plan_id", f"PLAN-{planning_date_str}-{uuid.uuid4().hex[:6].upper()}")
    now = datetime.now(timezone.utc)

    # Persist draft plan in DB
    existing_plan = db.query(DraftPlan).filter(DraftPlan.plan_id == plan_id).first()
    if existing_plan:
        existing_plan.plan_data = plan_dict
        existing_plan.updated_at = now
        existing_plan.algorithm = plan_dict.get("algorithm")
    else:
        draft_record = DraftPlan(
            plan_id=plan_id,
            depot_id=depot_id,
            target_date=effective_date,
            status="draft",
            algorithm=plan_dict.get("algorithm"),
            plan_data=plan_dict,
            created_at=now,
            updated_at=now,
            created_by=user_id,
        )
        db.add(draft_record)

    db.commit()
    return plan_dict


def get_plan_by_id_operation(db: Session, plan_id: str) -> Dict[str, Any]:
    """GET /dispatcher/plans/{plan_id} implementation."""
    draft_record = db.query(DraftPlan).filter(DraftPlan.plan_id == plan_id).first()
    if not draft_record:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    return draft_record.plan_data


def edit_draft_plan_operation(
    db: Session,
    plan_id: str,
    actions: List[Dict[str, Any]],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    POST /dispatcher/plans/{plan_id}/edit implementation.
    Applies manual dispatcher actions and re-evaluates draft using evaluate_edited_draft.
    """
    draft_record = db.query(DraftPlan).filter(DraftPlan.plan_id == plan_id).first()
    if not draft_record:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    base_plan = draft_record.plan_data
    ref_data = get_reference_data()

    # Load authoritative orders and fleet for the plan
    order_query = db.query(DbOrder).filter(DbOrder.order_date == draft_record.target_date)
    db_orders = order_query.all()
    optimizer_orders = [convert_db_order_to_optimizer(o, ref_data, db) for o in db_orders]

    vehicle_query = db.query(DbVehicle)
    if draft_record.depot_id:
        vehicle_query = vehicle_query.filter(DbVehicle.depot_id == draft_record.depot_id)
    db_vehicles = vehicle_query.all()
    if db_vehicles:
        optimizer_fleet = [convert_db_vehicle_to_optimizer(v, ref_data) for v in db_vehicles]
    else:
        optimizer_fleet = list(ref_data.vehicles)

    optimizer_fleet = [_ensure_live_fleet_state(v) for v in optimizer_fleet]

    context = OperationalContext(
        planning_date=draft_record.target_date.isoformat(),
        timezone="Asia/Colombo",
    )

    # Convert dict actions to typed actions
    typed_actions = []
    for act in actions:
        action_type = act.get("action_type") or act.get("type")
        if action_type == "move_whole_order":
            typed_actions.append(
                MoveWholeOrderAction(
                    order_ref=act["order_ref"],
                    target_vehicle_id=act["target_vehicle_id"],
                    target_trip_number=act.get("target_trip_number", 1),
                )
            )
        elif action_type == "defer_whole_order":
            typed_actions.append(
                DeferWholeOrderAction(
                    order_ref=act["order_ref"],
                    reason=act.get("reason", "MANUAL_DISPATCHER_DEFERRAL"),
                    detail=act.get("detail", "Order deferred by dispatcher edit."),
                )
            )
        elif action_type == "reinstate_whole_order":
            typed_actions.append(
                ReinstateWholeOrderAction(
                    order_ref=act["order_ref"],
                    target_vehicle_id=act["target_vehicle_id"],
                    target_trip_number=act.get("target_trip_number", 1),
                )
            )
        elif action_type == "move_line_item":
            typed_actions.append(
                MoveLineItemAction(
                    order_ref=act["order_ref"],
                    line_item_id=act["line_item_id"],
                    target_vehicle_id=act["target_vehicle_id"],
                    target_trip_number=act.get("target_trip_number", 1),
                    quantity=act.get("quantity"),
                )
            )
        elif action_type == "split_line_item":
            typed_actions.append(
                SplitLineItemAction(
                    order_ref=act["order_ref"],
                    line_item_id=act["line_item_id"],
                    splits=act.get("splits", []),
                )
            )
        else:
            typed_actions.append(act)

    # Execute optimizer public API
    edited_response = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=typed_actions,
        authoritative_orders=optimizer_orders,
        authoritative_fleet=optimizer_fleet,
        reference_data=ref_data,
        operational_context=context,
    )

    edited_plan_dict = _to_json_serializable_plan(dict(edited_response))
    now = datetime.now(timezone.utc)
    draft_record.plan_data = edited_plan_dict
    draft_record.updated_at = now
    db.commit()

    return edited_plan_dict


def approve_draft_plan_operation(
    db: Session,
    plan_id: str,
    user_id: str,
    client_op_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    POST /dispatcher/plans/{plan_id}/approve implementation.
    Converts draft plan into backend trip/stop/deferred-order records.
    """
    draft_record = db.query(DraftPlan).filter(DraftPlan.plan_id == plan_id).first()
    if not draft_record:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    plan_data = draft_record.plan_data
    val = plan_data.get("validation", {})
    if not val.get("valid", False):
        raise HTTPException(
            status_code=400,
            detail="Cannot approve invalid draft plan. Resolve validation errors before approval."
        )

    now = datetime.now(timezone.utc)
    trips_created: List[str] = []
    depot_id = draft_record.depot_id or "DEP1"

    # Persist Trips and TripStops
    for proposed_trip in plan_data.get("trips", []):
        db_trip_id = proposed_trip.get("trip_id") or f"TRIP-{uuid.uuid4().hex[:8].upper()}"
        vehicle_id = proposed_trip["vehicle_id"]
        trip_no = proposed_trip.get("trip_number", 1)

        # Upsert Trip
        existing_trip = db.query(DbTrip).filter(
            DbTrip.vehicle_id == vehicle_id,
            DbTrip.trip_date == draft_record.target_date,
            DbTrip.trip_no == trip_no,
        ).first()

        if existing_trip:
            trip_obj = existing_trip
            trip_obj.status = "planned"
            trip_obj.dispatcher_id = user_id
        else:
            trip_obj = DbTrip(
                trip_id=db_trip_id,
                depot_id=depot_id,
                vehicle_id=vehicle_id,
                dispatcher_id=user_id,
                trip_date=draft_record.target_date,
                trip_no=trip_no,
                status="planned",
            )
            db.add(trip_obj)

        trips_created.append(trip_obj.trip_id)

        stops = proposed_trip.get("driver_itinerary") or proposed_trip.get("stops", [])
        for stop in stops:
            stop_num = stop.get("stop_number", 1)
            stop_outlet_id = stop.get("outlet_id", "")
            eta_time = stop.get("arrival_time_iso") or stop.get("arrival_time")

            for o_ref in stop.get("order_refs", []):
                db_order = db.query(DbOrder).filter(DbOrder.order_id == o_ref).first()
                if not db_order:
                    continue

                # Clean up existing stop for this order if any
                existing_stop = db.query(DbTripStop).filter(DbTripStop.order_id == db_order.order_id).first()
                if existing_stop:
                    delete_stop_items(db, existing_stop.stop_id)
                    db.delete(existing_stop)
                    db.flush()

                db_stop_id = f"STOP-{uuid.uuid4().hex[:8].upper()}"
                new_stop = DbTripStop(
                    stop_id=db_stop_id,
                    trip_id=trip_obj.trip_id,
                    outlet_id=stop_outlet_id or db_order.outlet_id,
                    order_id=db_order.order_id,
                    stop_seq=stop_num,
                    status="upcoming",
                    eta=eta_time,
                    temp_req=db_order.temp_req,
                )
                db.add(new_stop)

                # Link TripStopItems (all of the order's lines unless the optimizer listed specific ones)
                listed_lines = [
                    item.get("line_item_id")
                    for item in stop.get("line_items_delivered", [])
                    if item.get("order_ref") == o_ref and item.get("line_item_id")
                ]
                add_stop_items(db, db_stop_id, db_order.order_id, listed_lines or None)

                # Update Order state
                db_order.trip_id = trip_obj.trip_id
                db_order.stop_seq = stop_num
                db_order.status = "planned"

                db.add(
                    DeliveryEvent(
                        event_id=str(uuid.uuid4()),
                        order_id=db_order.order_id,
                        event_type="order_planned",
                        occurred_at=now,
                        actor_role="dispatcher",
                        actor_id=user_id,
                    )
                )

    # Persist Deferred Orders
    for deferred in plan_data.get("deferred_orders", []):
        o_ref = deferred["order_ref"]
        db_order = db.query(DbOrder).filter(DbOrder.order_id == o_ref).first()
        if not db_order:
            continue

        db_order.status = "deferred"
        db_order.defer_count = (db_order.defer_count or 0) + 1
        db_order.deferred_prev = True

        deferral = Deferral(
            deferral_id=str(uuid.uuid4()),
            order_id=db_order.order_id,
            outlet_id=db_order.outlet_id,
            original_date=draft_record.target_date,
            new_date=draft_record.target_date,
            reason=deferred.get("reason", "OPTIMIZER_CAPACITY_CONSTRAINT"),
            created_at=now,
            created_by=user_id,
            client_op_id=client_op_id,
        )
        db.add(deferral)

        db.add(
            DeliveryEvent(
                event_id=str(uuid.uuid4()),
                order_id=db_order.order_id,
                event_type="order_deferred",
                occurred_at=now,
                actor_role="dispatcher",
                actor_id=user_id,
            )
        )

    # Mark DraftPlan as approved
    draft_record.status = "approved"
    draft_record.approved_by = user_id
    draft_record.approved_at = now
    draft_record.updated_at = now
    db.commit()

    return {
        "status": "approved",
        "plan_id": plan_id,
        "trips_created": len(trips_created),
        "trips": trips_created,
        "approved_at": now.isoformat(),
    }


def reallocate_broken_vehicle_operation(
    db: Session,
    vehicle_id: str,
    plan_id: Optional[str] = None,
    undelivered_quantities: Optional[List[Dict[str, Any]]] = None,
    current_time_iso: Optional[str] = None,
    pickup_location: str = "DEPOT",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    POST /dispatcher/breakdowns/{vehicle_id}/reallocate implementation.
    Calls reallocate_broken_vehicle optimizer API to reassign stops/orders to surviving vehicles.
    """
    now = datetime.now(timezone.utc)
    now_iso = current_time_iso or now.isoformat()

    # Find the active or approved plan
    if plan_id:
        draft_record = db.query(DraftPlan).filter(DraftPlan.plan_id == plan_id).first()
    else:
        draft_record = (
            db.query(DraftPlan)
            .order_by(DraftPlan.updated_at.desc())
            .first()
        )

    if not draft_record:
        raise HTTPException(status_code=404, detail="No active plan found for breakdown reallocation")

    active_plan = draft_record.plan_data
    ref_data = get_reference_data()

    # Gather undelivered items if not provided
    if not undelivered_quantities:
        undelivered = []
        for trip in active_plan.get("trips", []):
            if trip.get("vehicle_id") == vehicle_id:
                stops = trip.get("driver_itinerary") or trip.get("stops", [])
                for stop in stops:
                    for item in stop.get("line_items_delivered", []):
                        undelivered.append({
                            "order_ref": item["order_ref"],
                            "line_item_id": item.get("line_item_id", f"{item['order_ref']}-ALL"),
                            "description": item.get("description", "Cargo"),
                            "quantity": item.get("quantity", 0),
                            "quantity_unit": item.get("quantity_unit", "units"),
                            "weight_kg": item.get("weight_kg", 0.0),
                            "volume_m3": item.get("volume_m3", 0.0),
                            "temp_requirement": item.get("temp_requirement", "ambient"),
                        })
        undelivered_quantities = undelivered

    # Load available fleet (excluding broken vehicle)
    vehicle_query = db.query(DbVehicle)
    if draft_record.depot_id:
        vehicle_query = vehicle_query.filter(DbVehicle.depot_id == draft_record.depot_id)
    db_vehicles = vehicle_query.all()

    if db_vehicles:
        optimizer_fleet = [convert_db_vehicle_to_optimizer(v, ref_data) for v in db_vehicles]
    else:
        optimizer_fleet = list(ref_data.vehicles)

    optimizer_fleet = [_ensure_live_fleet_state(v) for v in optimizer_fleet]

    # Authoritative orders
    order_query = db.query(DbOrder).filter(DbOrder.order_date == draft_record.target_date)
    optimizer_orders = [convert_db_order_to_optimizer(o, ref_data, db) for o in order_query.all()]

    context = OperationalContext(
        planning_date=draft_record.target_date.isoformat(),
        timezone="Asia/Colombo",
    )

    # Execute optimizer breakdown recovery API
    recovery_draft = reallocate_broken_vehicle(
        active_plan=active_plan,
        broken_vehicle_id=vehicle_id,
        undelivered_quantities=undelivered_quantities,
        available_fleet=optimizer_fleet,
        reference_data=ref_data,
        operational_context=context,
        current_time_iso=now_iso,
        pickup_location=pickup_location,
        authoritative_orders=optimizer_orders,
    )

    recovery_dict = _to_json_serializable_plan(dict(recovery_draft))

    # Update broken vehicle status in database
    db_v = db.query(DbVehicle).filter(DbVehicle.vehicle_id == vehicle_id).first()
    if db_v:
        db_v.status = "in_workshop"

    # Record vehicle incident
    db.add(
        VehicleIncident(
            incident_id=f"INC-{uuid.uuid4().hex[:8].upper()}",
            vehicle_id=vehicle_id,
            type="breakdown",
            detail=f"Vehicle breakdown reported at {now_iso}. Undelivered orders reallocated.",
            reported_by=user_id or "system",
            reported_at=now,
        )
    )

    # Update stored plan with recovery results
    draft_record.plan_data = recovery_dict
    draft_record.updated_at = now
    db.commit()

    return recovery_dict
