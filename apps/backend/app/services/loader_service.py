import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.delivery import Discrepancy
from app.models.events import DeliveryEvent
from app.models.load_check import LoadCheck, LoadCheckItem
from app.models.order import Order, OrderLine
from app.models.outlet import Outlet
from app.models.product import Product
from app.models.trip import Trip, TripStop, TripStopItem
from app.models.vehicle import Vehicle
from app.models.deferral import Deferral
from app.schemas.loader import (
    DISCREPANCY_STATUSES,
    LoaderDeferralResponse,
    LoaderQueueTrip,
    LoaderWorkbench,
    LoadItem,
    LoadStop,
    SaveLoadItemRequest,
    SubmitLoadCheckRequest,
    VehicleUnavailableRequest,
)


EDITABLE_TRIP_STATUSES = {"planned", "loading"}
READ_ONLY_TRIP_STATUSES = {"loaded", "out_for_delivery", "cancelled", "vehicle_unavailable"}
COMPLETED_ITEM_STATUSES = {"verified", "short", "over", "damaged", "missing", "substituted"}


def _now():
    return datetime.now(timezone.utc)


def _to_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def _get_trip_for_loader(db: Session, trip_id: str, loader_depot: str) -> Trip:
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.depot_id != loader_depot:
        raise HTTPException(status_code=403, detail="Not authorized for this depot")
    return trip


def _get_vehicle(db: Session, vehicle_id: str) -> Optional[Vehicle]:
    return db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()


def _line_rows_for_trip(db: Session, trip_id: str):
    """Return one row per trip line item.

    Some current planning code creates TripStop rows but does not always create
    TripStopItem rows. The fallback through OrderLine keeps the loader API usable
    with the existing dispatcher implementation while still identifying items by
    line_item_id.
    """
    rows = (
        db.query(TripStop, OrderLine, Product, Outlet, TripStopItem)
        .join(Order, Order.order_id == TripStop.order_id)
        .join(OrderLine, OrderLine.order_id == Order.order_id)
        .outerjoin(TripStopItem, TripStopItem.line_item_id == OrderLine.line_item_id)
        .outerjoin(Product, Product.product_id == OrderLine.product_id)
        .outerjoin(Outlet, Outlet.outlet_id == TripStop.outlet_id)
        .filter(TripStop.trip_id == trip_id)
        .order_by(TripStop.pack_seq.is_(None), TripStop.pack_seq, TripStop.stop_seq, OrderLine.line_item_id)
        .all()
    )
    return rows


def _line_index_for_trip(db: Session, trip_id: str):
    return {line.line_item_id: (stop, line, product, outlet, stop_item) for stop, line, product, outlet, stop_item in _line_rows_for_trip(db, trip_id)}


def _ensure_load_check(db: Session, trip: Trip, user_id: str, status: str = "in_progress") -> LoadCheck:
    existing = db.query(LoadCheck).filter(LoadCheck.trip_id == trip.trip_id).first()
    if existing:
        return existing

    check = LoadCheck(
        check_id=str(uuid.uuid4()),
        trip_id=trip.trip_id,
        checked_by=user_id,
        checked_at=_now(),
        status=status,
        client_op_id=f"draft:{trip.trip_id}",
    )
    db.add(check)
    db.flush()
    return check


def _get_load_item(db: Session, check_id: str, line_item_id: str) -> Optional[LoadCheckItem]:
    return (
        db.query(LoadCheckItem)
        .filter(LoadCheckItem.check_id == check_id, LoadCheckItem.line_item_id == line_item_id)
        .first()
    )


def _validate_item_state(expected_qty: int, loaded_qty: int, status: str, reason: Optional[str], final: bool = False):
    if final and status == "pending":
        raise HTTPException(status_code=400, detail="Final load check cannot contain pending items")
    if status == "verified" and loaded_qty != expected_qty:
        raise HTTPException(status_code=400, detail="Verified items must match assigned quantity")
    if status == "short" and loaded_qty >= expected_qty:
        raise HTTPException(status_code=400, detail="Short items must have loaded quantity below assigned quantity")
    if status == "missing" and loaded_qty != 0:
        raise HTTPException(status_code=400, detail="Missing items must have loaded quantity 0")
    if status == "over" and loaded_qty <= expected_qty:
        raise HTTPException(status_code=400, detail="Over items must have loaded quantity above assigned quantity")
    if status in DISCREPANCY_STATUSES and not reason:
        raise HTTPException(status_code=400, detail="Discrepancy reason is required for mismatch items")
    if status not in DISCREPANCY_STATUSES and reason:
        raise HTTPException(status_code=400, detail="Discrepancy reason is only allowed for mismatch items")
    if status == "pending" and loaded_qty != expected_qty:
        raise HTTPException(status_code=400, detail="Quantity mismatch must be reported as a discrepancy")


def _ensure_trip_manifest_current(db: Session, trip_id: str):
    """Detect dispatcher changes made after the loader opened a stale screen."""
    rows = (
        db.query(TripStop, Order)
        .join(Order, Order.order_id == TripStop.order_id)
        .filter(TripStop.trip_id == trip_id)
        .all()
    )
    for stop, order in rows:
        if order.status in {"deferred", "cancelled"}:
            raise HTTPException(status_code=409, detail=f"Order {order.order_id} is {order.status}")
        if order.trip_id != trip_id:
            raise HTTPException(status_code=409, detail=f"Order {order.order_id} is no longer assigned to this trip")


def _ensure_trip_has_loadable_manifest(db: Session, trip_id: str):
    stops = db.query(TripStop).filter(TripStop.trip_id == trip_id).all()
    if not stops:
        raise HTTPException(status_code=400, detail="Trip has no stops to load")

    empty_stops = []
    for stop in stops:
        item_count = (
            db.query(OrderLine)
            .filter(OrderLine.order_id == stop.order_id)
            .count()
        )
        if item_count == 0:
            empty_stops.append(stop.stop_id)
    if empty_stops:
        raise HTTPException(status_code=400, detail=f"Stops have no load items: {empty_stops}")


def _ensure_vehicle_temperature_compatible(db: Session, trip: Trip):
    vehicle = _get_vehicle(db, trip.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=400, detail="Trip vehicle is missing")
    if vehicle.temp == "reefer":
        return

    rows = _line_rows_for_trip(db, trip.trip_id)
    cold_items = sorted({line.product_id for _, line, product, _, _ in rows if product and product.temp_req == "reefer"})
    if cold_items:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle {vehicle.vehicle_id} is not temperature-compatible with items: {cold_items}",
        )


def _upsert_load_item(
    db: Session,
    check: LoadCheck,
    line: OrderLine,
    loaded_qty: int,
    status: str,
    note: Optional[str],
) -> LoadCheckItem:
    item = _get_load_item(db, check.check_id, line.line_item_id)
    if not item:
        item = LoadCheckItem(
            chk_item_id=str(uuid.uuid4()),
            check_id=check.check_id,
            line_item_id=line.line_item_id,
            exp_qty=line.quantity,
            loaded_qty=loaded_qty,
            status=status,
            note=note,
        )
        db.add(item)
    else:
        item.loaded_qty = loaded_qty
        item.status = status
        item.note = note
    db.flush()
    return item


def _sync_discrepancy(
    db: Session,
    *,
    check_item: LoadCheckItem,
    line: OrderLine,
    user_id: str,
    status: str,
    reason: Optional[str],
):
    existing = db.query(Discrepancy).filter(Discrepancy.chk_item_id == check_item.chk_item_id).first()
    if status not in DISCREPANCY_STATUSES:
        if existing:
            existing.status = "resolved"
            existing.note = reason or existing.note
        return None

    qty_delta = abs(check_item.exp_qty - check_item.loaded_qty)
    if status == "damaged" and qty_delta == 0:
        qty_delta = check_item.exp_qty
    if status == "substituted" and qty_delta == 0:
        qty_delta = check_item.loaded_qty

    if existing:
        existing.type = status
        existing.reported_qty = qty_delta
        existing.status = "open"
        existing.note = reason
        return existing

    discrepancy = Discrepancy(
        discrepancy_id=str(uuid.uuid4()),
        order_id=line.order_id,
        raised_by=user_id,
        source_stage="loading",
        chk_item_id=check_item.chk_item_id,
        product_id=line.product_id,
        type=status,
        reported_qty=qty_delta,
        status="open",
        note=reason,
    )
    db.add(discrepancy)
    return discrepancy


def _add_order_event(
    db: Session,
    *,
    order_id: str,
    event_type: str,
    actor_id: str,
    note: Optional[str] = None,
    client_op_id: Optional[str] = None,
):
    if client_op_id:
        existing = db.query(DeliveryEvent).filter(DeliveryEvent.client_op_id == client_op_id).first()
        if existing:
            return existing

    event = DeliveryEvent(
        event_id=str(uuid.uuid4()),
        order_id=order_id,
        event_type=event_type,
        occurred_at=_now(),
        actor_role="loader",
        actor_id=actor_id,
        note=note,
        client_op_id=client_op_id,
    )
    db.add(event)
    return event


def _load_state_maps(db: Session, trip_id: str):
    check = db.query(LoadCheck).filter(LoadCheck.trip_id == trip_id).first()
    item_by_line = {}
    discrepancies_by_chk = {}
    if check:
        items = db.query(LoadCheckItem).filter(LoadCheckItem.check_id == check.check_id).all()
        item_by_line = {item.line_item_id: item for item in items}
        if items:
            chk_ids = [item.chk_item_id for item in items]
            discrepancies = db.query(Discrepancy).filter(Discrepancy.chk_item_id.in_(chk_ids)).all()
            discrepancies_by_chk = {disc.chk_item_id: disc for disc in discrepancies}
    return check, item_by_line, discrepancies_by_chk


def _build_workbench(db: Session, trip: Trip) -> LoaderWorkbench:
    vehicle = _get_vehicle(db, trip.vehicle_id)
    check, item_by_line, discrepancies_by_chk = _load_state_maps(db, trip.trip_id)
    rows = _line_rows_for_trip(db, trip.trip_id)

    stops_by_id = {}
    total_items = 0
    verified_items = 0
    discrepancy_count = 0

    for stop, line, product, outlet, stop_item in rows:
        if stop.stop_id not in stops_by_id:
            stops_by_id[stop.stop_id] = LoadStop(
                stop_id=stop.stop_id,
                order_id=stop.order_id,
                outlet_id=stop.outlet_id,
                outlet_name=outlet.name if outlet else None,
                stop_seq=stop.stop_seq,
                pack_seq=stop.pack_seq,
                eta=stop.eta,
                weight_kg=_to_float(stop.wt_kg),
                volume_m3=_to_float(stop.vol_m3),
                temp_req=stop.temp_req,
                status=stop.status,
                items=[],
                complete=stop.status in {"loaded", "loading_complete"},
            )

        saved = item_by_line.get(line.line_item_id)
        discrepancy = discrepancies_by_chk.get(saved.chk_item_id) if saved else None
        status = saved.status if saved else "pending"
        loaded_qty = saved.loaded_qty if saved else None
        if status in COMPLETED_ITEM_STATUSES:
            verified_items += 1
        if status in DISCREPANCY_STATUSES and (not discrepancy or discrepancy.status == "open"):
            discrepancy_count += 1
        total_items += 1

        stops_by_id[stop.stop_id].items.append(
            LoadItem(
                line_item_id=line.line_item_id,
                stop_item_id=stop_item.stop_item_id if stop_item else None,
                order_id=line.order_id,
                product_id=line.product_id,
                product_name=product.name if product else None,
                unit=product.unit if product else None,
                assigned_qty=line.quantity,
                loaded_qty=loaded_qty,
                status=status,
                discrepancy_reason=discrepancy.note if discrepancy else None,
                note=saved.note if saved else None,
            )
        )

    stops = list(stops_by_id.values())
    read_only = trip.status in READ_ONLY_TRIP_STATUSES
    return LoaderWorkbench(
        trip_id=trip.trip_id,
        depot_id=trip.depot_id,
        vehicle_id=trip.vehicle_id,
        vehicle_plate=vehicle.plate if vehicle else None,
        vehicle_type=vehicle.type if vehicle else None,
        vehicle_temp=vehicle.temp if vehicle else None,
        trip_date=trip.trip_date,
        trip_no=trip.trip_no,
        status=trip.status,
        read_only=read_only,
        check_id=check.check_id if check else None,
        check_status=check.status if check else None,
        checked_by=check.checked_by if check else None,
        checked_at=check.checked_at if check else None,
        stop_count=len(stops),
        total_items=total_items,
        verified_items=verified_items,
        discrepancy_count=discrepancy_count,
        stops=stops,
    )


def get_loader_queue(db: Session, loader_depot: str) -> list[LoaderQueueTrip]:
    trips = (
        db.query(Trip)
        .filter(
            Trip.depot_id == loader_depot,
            Trip.status.in_(["planned", "loading", "loaded", "out_for_delivery", "vehicle_unavailable"]),
        )
        .order_by(Trip.trip_date, Trip.trip_no, Trip.vehicle_id)
        .all()
    )
    queue = []
    for trip in trips:
        wb = _build_workbench(db, trip)
        queue.append(
            LoaderQueueTrip(
                trip_id=trip.trip_id,
                vehicle_id=trip.vehicle_id,
                vehicle_plate=wb.vehicle_plate,
                vehicle_type=wb.vehicle_type,
                vehicle_temp=wb.vehicle_temp,
                trip_date=trip.trip_date,
                trip_no=trip.trip_no,
                status=trip.status,
                stop_count=wb.stop_count,
                total_items=wb.total_items,
                verified_items=wb.verified_items,
                discrepancy_count=wb.discrepancy_count,
                route_label=f"{trip.vehicle_id} - Trip {trip.trip_no}",
                read_only=wb.read_only,
            )
        )
    return queue


def get_workbench(db: Session, trip_id: str, loader_depot: str) -> LoaderWorkbench:
    trip = _get_trip_for_loader(db, trip_id, loader_depot)
    return _build_workbench(db, trip)


def start_loading(db: Session, trip_id: str, loader_depot: str, user_id: str):
    trip = _get_trip_for_loader(db, trip_id, loader_depot)
    if trip.status in READ_ONLY_TRIP_STATUSES:
        raise HTTPException(status_code=400, detail=f"Trip is {trip.status} and cannot be edited")
    if trip.status not in EDITABLE_TRIP_STATUSES:
        raise HTTPException(status_code=400, detail=f"Trip cannot be loaded from status {trip.status}")
    _ensure_trip_has_loadable_manifest(db, trip_id)
    _ensure_trip_manifest_current(db, trip_id)
    _ensure_vehicle_temperature_compatible(db, trip)

    check = _ensure_load_check(db, trip, user_id)
    if trip.status == "planned":
        trip.status = "loading"
        for stop in db.query(TripStop).filter(TripStop.trip_id == trip_id).all():
            _add_order_event(db, order_id=stop.order_id, event_type="loading_started", actor_id=user_id)

    db.commit()
    db.refresh(check)
    return check


def save_load_item(
    db: Session,
    trip_id: str,
    line_item_id: str,
    request: SaveLoadItemRequest,
    loader_depot: str,
    user_id: str,
) -> LoadItem:
    if request.client_op_id:
        existing_event = db.query(DeliveryEvent).filter(DeliveryEvent.client_op_id == request.client_op_id).first()
        if existing_event:
            return _find_load_item_response(db, trip_id, line_item_id, loader_depot)

    trip = _get_trip_for_loader(db, trip_id, loader_depot)
    if trip.status in READ_ONLY_TRIP_STATUSES:
        raise HTTPException(status_code=400, detail=f"Trip is {trip.status} and cannot be edited")
    if trip.status not in EDITABLE_TRIP_STATUSES:
        raise HTTPException(status_code=400, detail=f"Trip cannot be loaded from status {trip.status}")
    _ensure_trip_has_loadable_manifest(db, trip_id)
    _ensure_trip_manifest_current(db, trip_id)
    _ensure_vehicle_temperature_compatible(db, trip)

    line_index = _line_index_for_trip(db, trip_id)
    row = line_index.get(line_item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Line item not found in trip")
    stop, line, _, _, _ = row
    _validate_item_state(line.quantity, request.loaded_qty, request.status, request.discrepancy_reason)

    check = _ensure_load_check(db, trip, user_id)
    if trip.status == "planned":
        trip.status = "loading"

    check_item = _upsert_load_item(db, check, line, request.loaded_qty, request.status, request.note)
    _sync_discrepancy(
        db,
        check_item=check_item,
        line=line,
        user_id=user_id,
        status=request.status,
        reason=request.discrepancy_reason,
    )
    _add_order_event(
        db,
        order_id=line.order_id,
        event_type="load_item_checked",
        actor_id=user_id,
        note=f"{line.product_id}: {request.status}",
        client_op_id=request.client_op_id,
    )

    db.commit()
    return _find_load_item_response(db, trip_id, line_item_id, loader_depot)


def _find_load_item_response(db: Session, trip_id: str, line_item_id: str, loader_depot: str) -> LoadItem:
    wb = get_workbench(db, trip_id, loader_depot)
    for stop in wb.stops:
        for item in stop.items:
            if item.line_item_id == line_item_id:
                return item
    raise HTTPException(status_code=404, detail="Line item not found in trip")


def complete_stop(db: Session, trip_id: str, stop_id: str, loader_depot: str, user_id: str):
    trip = _get_trip_for_loader(db, trip_id, loader_depot)
    if trip.status in READ_ONLY_TRIP_STATUSES:
        raise HTTPException(status_code=400, detail=f"Trip is {trip.status} and cannot be edited")
    _ensure_trip_manifest_current(db, trip_id)

    wb = _build_workbench(db, trip)
    target = next((stop for stop in wb.stops if stop.stop_id == stop_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Stop not found in trip")

    pending = [item.line_item_id for item in target.items if item.status not in COMPLETED_ITEM_STATUSES]
    if pending:
        raise HTTPException(status_code=400, detail=f"Stop has unchecked items: {pending}")

    stop_model = db.query(TripStop).filter(TripStop.stop_id == stop_id, TripStop.trip_id == trip_id).first()
    stop_model.status = "loading_complete"
    _add_order_event(db, order_id=stop_model.order_id, event_type="stop_loading_completed", actor_id=user_id)
    db.commit()
    return stop_model


def submit_load_check(
    db: Session,
    trip_id: str,
    request: SubmitLoadCheckRequest,
    loader_depot: str,
    user_id: str,
) -> LoadCheck:
    existing = db.query(LoadCheck).filter(LoadCheck.client_op_id == request.client_op_id).first()
    if existing:
        return existing

    trip = _get_trip_for_loader(db, trip_id, loader_depot)
    if trip.status in READ_ONLY_TRIP_STATUSES:
        raise HTTPException(status_code=400, detail=f"Trip is {trip.status} and cannot be edited")
    if trip.status not in EDITABLE_TRIP_STATUSES:
        raise HTTPException(status_code=400, detail=f"Trip cannot be loaded from status {trip.status}")
    _ensure_trip_has_loadable_manifest(db, trip_id)
    _ensure_trip_manifest_current(db, trip_id)
    _ensure_vehicle_temperature_compatible(db, trip)

    line_index = _line_index_for_trip(db, trip_id)
    expected_line_ids = set(line_index.keys())
    submitted_line_ids = {item.line_item_id for item in request.items}
    missing = sorted(expected_line_ids - submitted_line_ids)
    extra = sorted(submitted_line_ids - expected_line_ids)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing load check items: {missing}")
    if extra:
        raise HTTPException(status_code=400, detail=f"Items do not belong to trip: {extra}")

    check = _ensure_load_check(db, trip, user_id)
    check.client_op_id = request.client_op_id
    check.checked_by = user_id
    check.checked_at = _now()
    check.status = "completed"

    for item in request.items:
        stop, line, _, _, _ = line_index[item.line_item_id]
        _validate_item_state(line.quantity, item.loaded_qty, item.status, item.discrepancy_reason, final=True)
        check_item = _upsert_load_item(db, check, line, item.loaded_qty, item.status, item.note)
        _sync_discrepancy(
            db,
            check_item=check_item,
            line=line,
            user_id=user_id,
            status=item.status,
            reason=item.discrepancy_reason,
        )
        _add_order_event(
            db,
            order_id=line.order_id,
            event_type="load_item_checked",
            actor_id=user_id,
            note=f"{line.product_id}: {item.status}",
        )

    trip.status = "loaded"
    stops = db.query(TripStop).filter(TripStop.trip_id == trip_id).all()
    for stop in stops:
        stop.status = "loaded"
        order = db.query(Order).filter(Order.order_id == stop.order_id).first()
        if order:
            order.status = "loaded"
            _add_order_event(db, order_id=order.order_id, event_type="order_loaded", actor_id=user_id)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflict during load check")

    db.refresh(check)
    return check


def mark_vehicle_unavailable(
    db: Session,
    trip_id: str,
    request: VehicleUnavailableRequest,
    loader_depot: str,
    user_id: str,
) -> Trip:
    if db.query(DeliveryEvent).filter(DeliveryEvent.client_op_id == request.client_op_id).first():
        return _get_trip_for_loader(db, trip_id, loader_depot)

    trip = _get_trip_for_loader(db, trip_id, loader_depot)
    if trip.status in {"loaded", "out_for_delivery"}:
        raise HTTPException(status_code=400, detail=f"Cannot mark vehicle unavailable after trip is {trip.status}")
    if trip.status in {"cancelled", "vehicle_unavailable"}:
        raise HTTPException(status_code=400, detail=f"Trip is already {trip.status}")

    vehicle = _get_vehicle(db, trip.vehicle_id)
    if vehicle:
        vehicle.status = "unavailable"

    trip.status = "vehicle_unavailable"
    stops = db.query(TripStop).filter(TripStop.trip_id == trip_id).all()
    for index, stop in enumerate(stops):
        order = db.query(Order).filter(Order.order_id == stop.order_id).first()
        if order and order.status in {"planned", "loading"}:
            # Return the order to dispatcher-owned planning state without deleting
            # the historical TripStop, so the incident remains auditable.
            order.status = "confirmed"
            order.trip_id = None
            order.stop_seq = None
        _add_order_event(
            db,
            order_id=stop.order_id,
            event_type="vehicle_unavailable",
            actor_id=user_id,
            note=f"{request.reason}. {request.note or ''}".strip(),
            client_op_id=request.client_op_id if index == 0 else None,
        )

    db.commit()
    db.refresh(trip)
    return trip


def get_deferrals(db: Session, loader_depot: str) -> list[LoaderDeferralResponse]:
    rows = (
        db.query(Deferral, Order, Outlet)
        .join(Order, Order.order_id == Deferral.order_id)
        .outerjoin(Outlet, Outlet.outlet_id == Order.outlet_id)
        .outerjoin(Trip, Trip.trip_id == Deferral.trip_id)
        .filter(or_(Outlet.depot_id == loader_depot, Trip.depot_id == loader_depot))
        .order_by(Deferral.original_date.desc(), Deferral.order_id)
        .all()
    )

    responses = []
    for deferral, order, outlet in rows:
        items = []
        for line in db.query(OrderLine).filter(OrderLine.order_id == order.order_id).all():
            product = db.query(Product).filter(Product.product_id == line.product_id).first()
            items.append(
                LoadItem(
                    line_item_id=line.line_item_id,
                    order_id=order.order_id,
                    product_id=line.product_id,
                    product_name=product.name if product else None,
                    unit=product.unit if product else None,
                    assigned_qty=line.quantity,
                    loaded_qty=None,
                    status="pending",
                )
            )

        responses.append(
            LoaderDeferralResponse(
                deferral_id=deferral.deferral_id,
                order_id=deferral.order_id,
                outlet_id=order.outlet_id,
                outlet_name=outlet.name if outlet else None,
                original_date=deferral.original_date,
                new_date=deferral.new_date,
                reason=deferral.reason,
                created_at=deferral.created_at,
                trip_id=deferral.trip_id,
                items=items,
            )
        )
    return responses
