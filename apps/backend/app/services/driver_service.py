"""Driver workflow on the canonical PostgreSQL schema.

Every Driver write goes through `run_event()`:

    authenticate (router) → idempotency (client_event_id) → handler
        handler: ownership check → row_version check → state-transition check → apply
    → ledger row in driver_events (applied | conflict | failed) → commit

The same handlers serve the REST endpoints and the offline `/events/sync` batch, so an
action has identical rules whether it arrives live or is replayed from the device.
"""

import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import MINIO_BUCKET, MINIO_ENDPOINT
from app.models.delivery import ProofOfDelivery
from app.models.events import Conflict, DeliveryEvent, DriverEvent
from app.models.load_check import LoadCheck, LoadCheckItem
from app.models.order import Order, OrderLine
from app.models.outlet import Outlet
from app.models.product import Product
from app.models.returns import ReturnCustody
from app.models.route import RouteChange
from app.models.trip import Trip, TripStop, TripStopItem
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas import driver as s
from app.services.manifest_service import add_stop_items

LOCAL_TZ = ZoneInfo("Asia/Colombo")

# Loader writes 'loading' / 'loading_complete' / 'loaded' onto trip_stop.status (F11 in
# schema_design.md). Until that is normalised they all mean "not yet arrived".
PRE_ARRIVAL_STOP_STATUSES = {"upcoming", "loading", "loading_complete", "loaded"}
FINISHED_STOP_STATUSES = {"delivered", "skipped"}
RESEQUENCE_CHANGE_TYPES = {"route.resequenced", "resequence"}


# ── Errors ───────────────────────────────────────────────────────────────

class DriverActionError(Exception):
    """A rejected Driver action (validation, ownership, invalid transition)."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class VersionConflict(Exception):
    """The driver acted on a stale trip_stop.row_version."""

    def __init__(self, stop: TripStop, base_row_version: int):
        super().__init__("row_version_mismatch")
        self.stop_id = stop.stop_id
        self.trip_id = stop.trip_id
        self.system_record = {
            "stop_id": stop.stop_id,
            "trip_id": stop.trip_id,
            "row_version": stop.row_version,
            "status": stop.status,
            "stop_seq": stop.stop_seq,
            "base_row_version": base_row_version,
        }


# ── Helpers ──────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def local_today() -> date:
    return datetime.now(LOCAL_TZ).date()


def _dec(value: Any) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _num(value: Any) -> Optional[float]:
    return None if value is None else float(value)


def _json_or_none(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return {"raw": raw}


@dataclass
class EventContext:
    driver: User
    event: DriverEvent
    occurred_at: datetime
    offline: bool


def _bump(stop: TripStop, ctx: EventContext) -> None:
    ctx.event.row_version_before = stop.row_version
    stop.row_version = (stop.row_version or 1) + 1
    ctx.event.row_version_after = stop.row_version


def _check_version(stop: TripStop, base_row_version: int) -> None:
    if stop.row_version != base_row_version:
        raise VersionConflict(stop, base_row_version)


# ── Ownership-checked loaders ────────────────────────────────────────────

def _owned_trip(db: Session, driver: User, trip_id: str, lock: bool = False) -> Trip:
    query = db.query(Trip).filter(Trip.trip_id == trip_id, Trip.driver_id == driver.user_id)
    if lock:
        query = query.with_for_update()
    trip = query.first()
    if not trip:
        raise DriverActionError(404, "Trip not found or not assigned to you")
    return trip


def _owned_stop(db: Session, driver: User, stop_id: str, lock: bool = False) -> Tuple[TripStop, Trip]:
    query = (
        db.query(TripStop, Trip)
        .join(Trip, Trip.trip_id == TripStop.trip_id)
        .filter(TripStop.stop_id == stop_id, Trip.driver_id == driver.user_id)
    )
    if lock:
        query = query.with_for_update()
    row = query.first()
    if not row:
        raise DriverActionError(404, "Stop not found or not assigned to you")
    return row


def _require_trip_out(trip: Trip) -> None:
    if trip.status != "out_for_delivery":
        raise DriverActionError(400, f"Trip is '{trip.status}', stop actions require 'out_for_delivery'")


def _earlier_open_trip(db: Session, trip: Trip) -> Optional[Trip]:
    """Trip-unlock rule: a later trip_no is locked while an earlier one is not completed."""
    if not trip.driver_id:
        return None
    return (
        db.query(Trip)
        .filter(
            Trip.driver_id == trip.driver_id,
            Trip.trip_date == trip.trip_date,
            Trip.trip_no < trip.trip_no,
            Trip.status != "completed",
        )
        .order_by(Trip.trip_no)
        .first()
    )


# ── Manifest ─────────────────────────────────────────────────────────────

def _loaded_qty_by_line(db: Session, trip_id: str) -> Dict[str, Decimal]:
    rows = (
        db.query(LoadCheckItem.line_item_id, LoadCheckItem.loaded_qty)
        .join(LoadCheck, LoadCheck.check_id == LoadCheckItem.check_id)
        .filter(LoadCheck.trip_id == trip_id)
    )
    return {line_id: _dec(qty) for line_id, qty in rows if qty is not None}


def _expected_qty(item: TripStopItem, loaded_by_line: Dict[str, Decimal]) -> Decimal:
    if item.qty_loaded is not None:
        return _dec(item.qty_loaded)
    if item.line_item_id in loaded_by_line:
        return loaded_by_line[item.line_item_id]
    return _dec(item.qty_assigned)


def _stop_items(db: Session, stop: TripStop) -> List[TripStopItem]:
    items = (
        db.query(TripStopItem)
        .filter(TripStopItem.stop_id == stop.stop_id)
        .order_by(TripStopItem.line_item_id)
        .all()
    )
    if not items:
        add_stop_items(db, stop.stop_id, stop.order_id)
        db.flush()
        items = (
            db.query(TripStopItem)
            .filter(TripStopItem.stop_id == stop.stop_id)
            .order_by(TripStopItem.line_item_id)
            .all()
        )
    return items


def _apply_lines(
    db: Session, stop: TripStop, lines: List[s.ChecklistLine], *, require_all: bool
) -> List[TripStopItem]:
    """Validate checklist/outcome lines against the stop manifest and write the quantities."""
    items = {item.item_id: item for item in _stop_items(db, stop)}
    seen = set()
    for line in lines:
        if line.item_id not in items:
            raise DriverActionError(400, f"Item {line.item_id} is not on stop {stop.stop_id}")
        if line.item_id in seen:
            raise DriverActionError(400, f"Item {line.item_id} listed more than once")
        seen.add(line.item_id)
    if require_all and seen != set(items):
        missing = sorted(set(items) - seen)
        raise DriverActionError(400, f"Checklist must cover every manifest item; missing {missing}")

    loaded = _loaded_qty_by_line(db, stop.trip_id)
    for line in lines:
        item = items[line.item_id]
        expected = _expected_qty(item, loaded)
        delivered, returned = _dec(line.qty_delivered), _dec(line.qty_returned)
        if delivered + returned != expected:
            raise DriverActionError(
                400,
                f"Item {item.item_id}: delivered ({delivered}) + returned ({returned}) must equal the "
                f"quantity on the van ({expected})",
            )
        item.qty_delivered = delivered
        item.qty_returned = returned
    return list(items.values())


def _pod_for_stop(db: Session, stop: TripStop) -> Optional[ProofOfDelivery]:
    return db.query(ProofOfDelivery).filter(ProofOfDelivery.order_id == stop.order_id).first()


def _get_or_create_pod(db: Session, stop: TripStop, ctx: EventContext) -> ProofOfDelivery:
    pod = _pod_for_stop(db, stop)
    if pod:
        if pod.stop_id != stop.stop_id:  # order moved to another stop by recovery
            pod.stop_id = stop.stop_id
        return pod
    pod = ProofOfDelivery(
        pod_id=f"POD-{uuid.uuid4().hex[:12].upper()}",
        order_id=stop.order_id,
        stop_id=stop.stop_id,
        delivered_by=ctx.driver.user_id,
        delivered_at=ctx.occurred_at,
        otp_code=f"{secrets.randbelow(10**6):06d}",
        otp_verified=False,
        recorded_offline=ctx.offline,
        synced_at=_now() if ctx.offline else None,
        client_op_id=ctx.event.client_event_id,
    )
    db.add(pod)
    db.flush()
    return pod


def _pod_dto(pod: Optional[ProofOfDelivery]) -> Optional[s.PodDTO]:
    if not pod:
        return None
    return s.PodDTO(
        pod_id=pod.pod_id,
        order_id=pod.order_id,
        otp_code=pod.otp_code,
        otp_verified=bool(pod.otp_verified),
        photo_url=pod.photo_url,
        signature_url=pod.signature_url,
        notes=pod.notes,
        delivered_at=pod.delivered_at,
    )


def _create_return(
    db: Session,
    stop: TripStop,
    ctx: EventContext,
    quantities: List[Tuple[TripStopItem, Decimal]],
    reason: Optional[str],
    return_crate: Optional[str],
) -> ReturnCustody:
    lines = db.query(OrderLine).filter(OrderLine.line_item_id.in_([i.line_item_id for i, _ in quantities]))
    product_by_line = {line.line_item_id: line.product_id for line in lines}
    record = ReturnCustody(
        return_id=f"RET-{uuid.uuid4().hex[:12].upper()}",
        trip_id=stop.trip_id,
        stop_id=stop.stop_id,
        driver_id=ctx.driver.user_id,
        items=json.dumps([
            {
                "item_id": item.item_id,
                "line_item_id": item.line_item_id,
                "product_id": product_by_line.get(item.line_item_id),
                "qty": float(qty),
            }
            for item, qty in quantities
        ]),
        reason=reason,
        return_crate=return_crate,
        status="pending",
        created_at=_now(),
        created_event_id=ctx.event.event_id,
    )
    db.add(record)
    return record


def _window_status(order: Optional[Order], arrived_at: datetime) -> Optional[str]:
    if not order or not order.window_open or not order.window_close:
        return None
    local = arrived_at.astimezone(LOCAL_TZ)
    try:
        open_t = time.fromisoformat(order.window_open)
        close_t = time.fromisoformat(order.window_close)
    except ValueError:
        return None
    now_t = local.time().replace(second=0, microsecond=0)
    if now_t < open_t:
        return "early"
    if now_t > close_t:
        return "missed"
    close_dt = datetime.combine(local.date(), close_t)
    if datetime.combine(local.date(), now_t) >= close_dt - timedelta(minutes=15):
        return "late_risk"
    return "on_time"


# ═══════════════════════════════════════════════════════════════════════════
# Handlers — (db, ctx, target_id, command) -> response fields
# ═══════════════════════════════════════════════════════════════════════════

def _handle_depart(db: Session, ctx: EventContext, trip_id: str, cmd: s.DepartCommand) -> dict:
    trip = _owned_trip(db, ctx.driver, trip_id, lock=True)
    ctx.event.trip_id = trip.trip_id
    if trip.status != "loaded":
        raise DriverActionError(400, f"Trip is '{trip.status}'; it must be 'loaded' before departure")
    blocking = _earlier_open_trip(db, trip)
    if blocking:
        raise DriverActionError(
            400, f"Trip {trip.trip_no} is locked until trip {blocking.trip_no} ({blocking.trip_id}) is completed"
        )

    stops = db.query(TripStop).filter(TripStop.trip_id == trip.trip_id).all()
    stop_ids = {stop.stop_id for stop in stops}
    for group in cmd.load_confirmation:
        if group.stop_id not in stop_ids:
            raise DriverActionError(400, f"Load confirmation references stop {group.stop_id} not on this trip")

    departed_at = _aware(cmd.departed_at) or ctx.occurred_at
    trip.status = "out_for_delivery"
    trip.actual_depart = departed_at
    for stop in stops:
        _stop_items(db, stop)  # freeze the manifest at departure
        if stop.status in PRE_ARRIVAL_STOP_STATUSES:
            stop.status = "upcoming"
        order = db.query(Order).filter(Order.order_id == stop.order_id).first()
        if order:
            order.status = "out_for_delivery"
            db.add(DeliveryEvent(
                event_id=str(uuid.uuid4()),
                order_id=order.order_id,
                event_type="order_out_for_delivery",
                occurred_at=departed_at,
                actor_role="driver",
                actor_id=ctx.driver.user_id,
                offline=ctx.offline,
                synced_at=_now() if ctx.offline else None,
            ))

    flagged = sum(1 for group in cmd.load_confirmation if group.state == "flagged")
    return {"trip_id": trip.trip_id, "trip_status": trip.status, "flagged_count": flagged}


def _handle_complete(db: Session, ctx: EventContext, trip_id: str, cmd: s.CompleteTripCommand) -> dict:
    trip = _owned_trip(db, ctx.driver, trip_id, lock=True)
    ctx.event.trip_id = trip.trip_id
    if trip.status != "out_for_delivery":
        raise DriverActionError(400, f"Trip is '{trip.status}'; only an 'out_for_delivery' trip can be completed")

    open_stops = [
        stop.stop_id
        for stop in db.query(TripStop).filter(TripStop.trip_id == trip.trip_id)
        if stop.status not in FINISHED_STOP_STATUSES
    ]
    if open_stops:
        raise DriverActionError(400, f"Stops without an outcome: {sorted(open_stops)}")
    pending_returns = [
        record.return_id
        for record in db.query(ReturnCustody).filter(
            ReturnCustody.trip_id == trip.trip_id, ReturnCustody.status != "confirmed"
        )
    ]
    if pending_returns:
        raise DriverActionError(400, f"Returns not yet confirmed at the depot: {sorted(pending_returns)}")

    trip.status = "completed"
    trip.actual_return = _aware(cmd.returned_at) or ctx.occurred_at
    if cmd.actual_dist_km is not None:
        trip.actual_dist_km = _dec(cmd.actual_dist_km)
    if cmd.actual_fuel_l is not None:
        trip.actual_fuel_l = _dec(cmd.actual_fuel_l)

    next_trip = (
        db.query(Trip)
        .filter(Trip.driver_id == trip.driver_id, Trip.trip_date == trip.trip_date, Trip.trip_no > trip.trip_no)
        .order_by(Trip.trip_no)
        .first()
    )
    return {
        "trip_id": trip.trip_id,
        "trip_status": trip.status,
        "unlocked_trip_id": next_trip.trip_id if next_trip else None,
    }


def _handle_arrive(db: Session, ctx: EventContext, stop_id: str, cmd: s.ArriveCommand) -> dict:
    stop, trip = _owned_stop(db, ctx.driver, stop_id, lock=True)
    ctx.event.trip_id, ctx.event.stop_id = trip.trip_id, stop.stop_id
    _require_trip_out(trip)
    _check_version(stop, cmd.base_row_version)
    if stop.status not in PRE_ARRIVAL_STOP_STATUSES:
        raise DriverActionError(400, f"Stop is '{stop.status}'; arrival can only be recorded once")

    arrived_at = _aware(cmd.arrived_at) or ctx.occurred_at
    stop.status = "arrived"
    stop.arrived_at = arrived_at
    if cmd.gps:
        stop.arrival_lat, stop.arrival_lng = _dec(cmd.gps.lat), _dec(cmd.gps.lng)
    order = db.query(Order).filter(Order.order_id == stop.order_id).first()
    if order:
        order.actual_arrival = arrived_at.astimezone(LOCAL_TZ).strftime("%H:%M")
    _bump(stop, ctx)
    return {
        "trip_id": trip.trip_id,
        "stop_id": stop.stop_id,
        "stop_status": stop.status,
        "new_row_version": stop.row_version,
        "window_status": _window_status(order, arrived_at),
    }


def _handle_checklist(db: Session, ctx: EventContext, stop_id: str, cmd: s.ChecklistCommand) -> dict:
    stop, trip = _owned_stop(db, ctx.driver, stop_id, lock=True)
    ctx.event.trip_id, ctx.event.stop_id = trip.trip_id, stop.stop_id
    _require_trip_out(trip)
    _check_version(stop, cmd.base_row_version)
    if stop.status != "arrived":
        raise DriverActionError(400, f"Stop is '{stop.status}'; the checklist needs a recorded arrival and no outcome yet")
    _apply_lines(db, stop, cmd.lines, require_all=True)
    _bump(stop, ctx)
    return {"trip_id": trip.trip_id, "stop_id": stop.stop_id, "stop_status": stop.status, "new_row_version": stop.row_version}


def _handle_photo_complete(db: Session, ctx: EventContext, stop_id: str, cmd: s.PhotoCompleteCommand) -> dict:
    stop, trip = _owned_stop(db, ctx.driver, stop_id, lock=True)
    ctx.event.trip_id, ctx.event.stop_id = trip.trip_id, stop.stop_id
    _require_trip_out(trip)
    if stop.status != "arrived":
        raise DriverActionError(400, f"Stop is '{stop.status}'; POD can only be captured after arrival and before the outcome")
    if not cmd.object_key.startswith(f"pod/{stop.stop_id}/"):
        raise DriverActionError(400, "object_key does not belong to this stop")
    pod = _get_or_create_pod(db, stop, ctx)
    pod.photo_url = cmd.object_key
    return {"trip_id": trip.trip_id, "stop_id": stop.stop_id, "stop_status": stop.status, "pod": _pod_dto(pod)}


def _handle_pod(db: Session, ctx: EventContext, stop_id: str, cmd: s.PodCommand) -> dict:
    stop, trip = _owned_stop(db, ctx.driver, stop_id, lock=True)
    ctx.event.trip_id, ctx.event.stop_id = trip.trip_id, stop.stop_id
    _require_trip_out(trip)
    if cmd.order_id != stop.order_id:
        raise DriverActionError(400, "order_id does not belong to this stop")
    if stop.status != "arrived":
        raise DriverActionError(400, f"Stop is '{stop.status}'; POD can only be captured after arrival and before the outcome")
    pod = _get_or_create_pod(db, stop, ctx)
    if cmd.delivered_at:
        pod.delivered_at = _aware(cmd.delivered_at)
    if cmd.signature_url is not None:
        pod.signature_url = cmd.signature_url
    if cmd.notes is not None:
        pod.notes = cmd.notes
    return {"trip_id": trip.trip_id, "stop_id": stop.stop_id, "stop_status": stop.status, "pod": _pod_dto(pod)}


def _handle_outcome(db: Session, ctx: EventContext, stop_id: str, cmd: s.OutcomeCommand) -> dict:
    stop, trip = _owned_stop(db, ctx.driver, stop_id, lock=True)
    ctx.event.trip_id, ctx.event.stop_id = trip.trip_id, stop.stop_id
    _require_trip_out(trip)
    _check_version(stop, cmd.base_row_version)

    if cmd.outcome in ("delivered", "partial"):
        if stop.status != "arrived":
            raise DriverActionError(400, f"Cannot record '{cmd.outcome}' from stop status '{stop.status}'; arrive first")
        if not _pod_for_stop(db, stop):
            raise DriverActionError(400, "Proof of delivery is required before a delivered/partial outcome")
    else:
        if stop.status not in PRE_ARRIVAL_STOP_STATUSES | {"arrived"}:
            raise DriverActionError(400, f"Cannot record 'failed' from stop status '{stop.status}'")
        if not cmd.reason:
            raise DriverActionError(400, "A reason is required for a failed delivery")

    loaded = _loaded_qty_by_line(db, stop.trip_id)
    if cmd.lines is not None:
        if cmd.outcome == "failed" and any(line.qty_delivered > 0 for line in cmd.lines):
            raise DriverActionError(400, "A failed delivery cannot deliver any quantity")
        items = _apply_lines(db, stop, cmd.lines, require_all=True)
    else:
        items = _stop_items(db, stop)
        checklist_done = all(item.qty_delivered is not None for item in items)
        for item in items:
            expected = _expected_qty(item, loaded)
            if cmd.outcome == "failed":
                item.qty_delivered, item.qty_returned = Decimal(0), expected
            elif not checklist_done:
                if cmd.outcome == "partial":
                    raise DriverActionError(400, "A partial delivery needs per-item lines or a submitted checklist")
                item.qty_delivered, item.qty_returned = expected, Decimal(0)

    returned = [(item, _dec(item.qty_returned)) for item in items if item.qty_returned and _dec(item.qty_returned) > 0]
    if cmd.outcome == "partial" and not returned:
        raise DriverActionError(400, "A partial delivery must return at least one unit")

    stop.status = "skipped" if cmd.outcome == "failed" else "delivered"
    stop.skip_reason = cmd.reason if cmd.outcome == "failed" else None
    stop.completed_at = _aware(cmd.finished_at) or ctx.occurred_at
    db.flush()

    return_record = None
    if returned:
        return_record = _create_return(db, stop, ctx, returned, cmd.reason, cmd.return_crate)
    _bump(stop, ctx)
    return {
        "trip_id": trip.trip_id,
        "stop_id": stop.stop_id,
        "stop_status": stop.status,
        "new_row_version": stop.row_version,
        "return_id": return_record.return_id if return_record else None,
        "return_status": return_record.status if return_record else None,
    }


def _handle_return(db: Session, ctx: EventContext, stop_id: str, cmd: s.ReturnCommand) -> dict:
    """Goods handed back after the outcome (e.g. outlet rejects units at the door)."""
    stop, trip = _owned_stop(db, ctx.driver, stop_id, lock=True)
    ctx.event.trip_id, ctx.event.stop_id = trip.trip_id, stop.stop_id
    _require_trip_out(trip)
    _check_version(stop, cmd.base_row_version)
    if stop.status != "delivered":
        raise DriverActionError(400, f"Stop is '{stop.status}'; returns are recorded against a delivered stop")

    items = {item.item_id: item for item in _stop_items(db, stop)}
    quantities = []
    for line in cmd.items:
        item = items.get(line.item_id)
        if not item:
            raise DriverActionError(400, f"Item {line.item_id} is not on stop {stop.stop_id}")
        qty = _dec(line.qty)
        delivered = _dec(item.qty_delivered or 0)
        if qty > delivered:
            raise DriverActionError(400, f"Item {item.item_id}: cannot return {qty}, only {delivered} delivered")
        item.qty_delivered = delivered - qty
        item.qty_returned = _dec(item.qty_returned or 0) + qty
        quantities.append((item, qty))

    db.flush()
    record = _create_return(db, stop, ctx, quantities, cmd.reason, cmd.return_crate)
    _bump(stop, ctx)
    return {
        "trip_id": trip.trip_id,
        "stop_id": stop.stop_id,
        "stop_status": stop.status,
        "new_row_version": stop.row_version,
        "return_id": record.return_id,
        "return_status": record.status,
    }


def _handle_depot_confirm(db: Session, ctx: EventContext, return_id: str, cmd: s.DepotConfirmCommand) -> dict:
    row = (
        db.query(ReturnCustody, Trip)
        .join(Trip, Trip.trip_id == ReturnCustody.trip_id)
        .filter(ReturnCustody.return_id == return_id, ReturnCustody.driver_id == ctx.driver.user_id)
        .with_for_update()
        .first()
    )
    if not row:
        raise DriverActionError(404, "Return not found or not in your custody")
    record, trip = row
    ctx.event.trip_id, ctx.event.stop_id = trip.trip_id, record.stop_id
    if record.status != "pending":
        raise DriverActionError(400, f"Return is already '{record.status}'")
    if trip.status != "out_for_delivery":
        raise DriverActionError(400, f"Trip is '{trip.status}'; returns are confirmed before the trip is completed")

    record.status = "confirmed"
    record.confirmed_at = _aware(cmd.confirmed_at) or ctx.occurred_at
    record.confirmed_event_id = ctx.event.event_id
    record.officer_name = cmd.officer_name
    record.condition = cmd.condition
    return {"trip_id": trip.trip_id, "stop_id": record.stop_id, "return_id": record.return_id, "return_status": record.status}


def _handle_ack_change(db: Session, ctx: EventContext, change_id: str, cmd: s.AckChangeCommand) -> dict:
    row = (
        db.query(RouteChange, Trip)
        .join(Trip, Trip.trip_id == RouteChange.trip_id)
        .filter(RouteChange.change_id == change_id, Trip.driver_id == ctx.driver.user_id)
        .with_for_update()
        .first()
    )
    if not row:
        raise DriverActionError(404, "Route change not found or not for your trips")
    change, trip = row
    ctx.event.trip_id = trip.trip_id
    if change.acknowledged:
        return {"status": "already_applied", "trip_id": trip.trip_id, "change_id": change.change_id}

    change.acknowledged = True
    change.ack_at = ctx.occurred_at
    payload = _json_or_none(change.payload) or {}
    if change.change_type in RESEQUENCE_CHANGE_TYPES and isinstance(payload.get("new_sequence"), list):
        stops = {stop.stop_id: stop for stop in db.query(TripStop).filter(TripStop.trip_id == trip.trip_id)}
        for seq, stop_id in enumerate(payload["new_sequence"], start=1):
            stop = stops.get(stop_id)
            if not stop or stop.status in FINISHED_STOP_STATUSES or stop.stop_seq == seq:
                continue
            stop.stop_seq = seq
            stop.row_version = (stop.row_version or 1) + 1
            order = db.query(Order).filter(Order.order_id == stop.order_id).first()
            if order:
                order.stop_seq = seq  # F9: keep the denormalised copy in step
    return {"trip_id": trip.trip_id, "change_id": change.change_id}


@dataclass(frozen=True)
class EventKind:
    command: Type[BaseModel]
    target: str  # payload key carrying the target id in /events/sync
    handler: Callable[[Session, EventContext, str, Any], dict]


EVENT_KINDS: Dict[str, EventKind] = {
    "trip.departed": EventKind(s.DepartCommand, "trip_id", _handle_depart),
    "trip.completed": EventKind(s.CompleteTripCommand, "trip_id", _handle_complete),
    "stop.arrived": EventKind(s.ArriveCommand, "stop_id", _handle_arrive),
    "checklist.submitted": EventKind(s.ChecklistCommand, "stop_id", _handle_checklist),
    "pod.photo.completed": EventKind(s.PhotoCompleteCommand, "stop_id", _handle_photo_complete),
    "pod.submitted": EventKind(s.PodCommand, "stop_id", _handle_pod),
    "stop.outcome.submitted": EventKind(s.OutcomeCommand, "stop_id", _handle_outcome),
    "return.created": EventKind(s.ReturnCommand, "stop_id", _handle_return),
    "depot_return.confirmed": EventKind(s.DepotConfirmCommand, "return_id", _handle_depot_confirm),
    "route_change.acknowledged": EventKind(s.AckChangeCommand, "change_id", _handle_ack_change),
}


# ═══════════════════════════════════════════════════════════════════════════
# Event runner
# ═══════════════════════════════════════════════════════════════════════════

def _replay_existing(db: Session, driver: User, existing: DriverEvent) -> Optional[s.DriverActionResponse]:
    if existing.status not in ("applied", "already_applied", "conflict"):
        return None  # 'failed' / 'pending' rows never block a retry (by anyone)
    if existing.driver_id != driver.user_id:
        raise DriverActionError(409, "client_event_id is already used")
    base = dict(
        client_event_id=existing.client_event_id,
        server_event_id=existing.event_id,
        trip_id=existing.trip_id,
        stop_id=existing.stop_id,
    )
    if existing.status in ("applied", "already_applied"):
        return s.DriverActionResponse(status="already_applied", new_row_version=existing.row_version_after, **base)
    if existing.status == "conflict":
        conflict = db.query(Conflict).filter(Conflict.driver_event_id == existing.event_id).first()
        return s.DriverActionResponse(
            status="conflict",
            conflict_id=conflict.conflict_id if conflict else None,
            reason="row_version_mismatch",
            system_record=_json_or_none(conflict.system_json) if conflict else None,
            **base,
        )


def run_event(
    db: Session,
    driver: User,
    kind: str,
    target_id: Optional[str],
    command: Any,
    client_event_id: str,
    *,
    occurred_at: Optional[datetime] = None,
    device_id: Optional[str] = None,
    offline: bool = False,
) -> s.DriverActionResponse:
    """Apply one Driver event exactly once. Commits. Raises DriverActionError on rejection
    (after recording a 'failed' ledger row); returns status 'conflict' on a stale row_version."""
    driver_id = driver.user_id
    received_at = _now()
    occurred = _aware(occurred_at) or received_at
    spec = EVENT_KINDS.get(kind)
    raw_payload = (
        command.model_dump(mode="json", exclude={"client_event_id", "device_id"})
        if isinstance(command, BaseModel)
        else command
    )
    ledger_payload = json.dumps({**(raw_payload or {}), **({spec.target: target_id} if spec else {})}, default=str)

    existing = db.query(DriverEvent).filter(DriverEvent.client_event_id == client_event_id).first()
    if existing:
        replay = _replay_existing(db, driver, existing)
        if replay:
            return replay
        db.delete(existing)  # retry of a failed event
        db.flush()

    def record_failure(status_code: int, detail: str) -> None:
        db.rollback()
        db.add(DriverEvent(
            event_id=str(uuid.uuid4()), driver_id=driver_id, device_id=device_id,
            client_event_id=client_event_id, kind=kind, payload=ledger_payload,
            occurred_at=occurred, received_at=received_at, status="failed", error=detail[:1000],
        ))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        raise DriverActionError(status_code, detail)

    if not spec:
        record_failure(422, f"Unknown event kind '{kind}'")
    if not target_id:
        record_failure(422, f"Missing '{spec.target}'")
    if not isinstance(command, spec.command):
        try:
            command = spec.command.model_validate(command or {})
        except ValidationError as exc:
            record_failure(422, f"Invalid payload: {exc.errors(include_url=False)}")

    event = DriverEvent(
        event_id=str(uuid.uuid4()), driver_id=driver_id, device_id=device_id,
        client_event_id=client_event_id, kind=kind, payload=ledger_payload,
        occurred_at=occurred, received_at=received_at, status="pending",
    )
    ctx = EventContext(driver=driver, event=event, occurred_at=occurred, offline=offline)
    try:
        db.add(event)
        db.flush()
        result = spec.handler(db, ctx, target_id, command)
        event.status = result.pop("status", "applied")
        event.applied_at = _now()
        db.commit()
    except VersionConflict as vc:
        db.rollback()
        conflict_event = DriverEvent(
            event_id=str(uuid.uuid4()), driver_id=driver_id, device_id=device_id,
            client_event_id=client_event_id, kind=kind, stop_id=vc.stop_id, trip_id=vc.trip_id,
            payload=ledger_payload, occurred_at=occurred, received_at=received_at, status="conflict",
            row_version_before=vc.system_record["base_row_version"], error="row_version_mismatch",
        )
        db.add(conflict_event)
        db.flush()
        conflict = Conflict(
            conflict_id=f"CONF-{uuid.uuid4().hex[:12].upper()}",
            stop_id=vc.stop_id,
            driver_event_id=conflict_event.event_id,
            driver_json=json.dumps({"client_event_id": client_event_id, "kind": kind, "payload": json.loads(ledger_payload)}),
            system_json=json.dumps(vc.system_record),
            status="in_review",
            created_at=received_at,
        )
        db.add(conflict)
        db.commit()
        return s.DriverActionResponse(
            status="conflict", client_event_id=client_event_id, server_event_id=conflict_event.event_id,
            trip_id=vc.trip_id, stop_id=vc.stop_id, conflict_id=conflict.conflict_id,
            reason="row_version_mismatch", system_record=vc.system_record,
        )
    except DriverActionError as err:
        record_failure(err.status_code, err.detail)
    except IntegrityError:
        # Concurrent request with the same client_event_id won the race.
        db.rollback()
        existing = db.query(DriverEvent).filter(DriverEvent.client_event_id == client_event_id).first()
        replay = _replay_existing(db, driver, existing) if existing else None
        if replay:
            return replay
        raise

    return s.DriverActionResponse(
        status=event.status, client_event_id=client_event_id, server_event_id=event.event_id, **result
    )


def sync_events(db: Session, driver: User, request: s.SyncRequest) -> s.SyncResponse:
    """Apply a batch in order. Each event commits independently, so a failure or conflict
    never undoes earlier events, and replaying the whole batch is safe."""
    results = []
    for ev in request.events:
        payload = dict(ev.payload or {})
        spec = EVENT_KINDS.get(ev.kind)
        target_id = payload.pop(spec.target, None) if spec else None
        try:
            result = run_event(
                db, driver, ev.kind, target_id, payload, ev.client_event_id,
                occurred_at=ev.occurred_at, device_id=request.device_id, offline=True,
            )
        except DriverActionError as err:
            result = s.DriverActionResponse(status="failed", client_event_id=ev.client_event_id, error=err.detail)
        results.append(result)
    return s.SyncResponse(results=results, server_time=_now())


# ═══════════════════════════════════════════════════════════════════════════
# Reads
# ═══════════════════════════════════════════════════════════════════════════

def _trip_summary(db: Session, trip: Trip) -> dict:
    stops = db.query(TripStop.status, Order.order_units).outerjoin(Order, Order.order_id == TripStop.order_id).filter(
        TripStop.trip_id == trip.trip_id
    ).all()
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == trip.vehicle_id).first()
    return dict(
        trip_id=trip.trip_id,
        trip_no=trip.trip_no,
        trip_date=trip.trip_date,
        status=trip.status,
        locked=trip.status in ("planned", "loaded") and _earlier_open_trip(db, trip) is not None,
        vehicle_id=trip.vehicle_id,
        vehicle_plate=vehicle.plate if vehicle else None,
        depot_id=trip.depot_id,
        brand=trip.brand,
        district=trip.district,
        plan_depart=trip.plan_depart,
        plan_return=trip.plan_return,
        dist_km=_num(trip.dist_km),
        actual_depart=trip.actual_depart,
        actual_return=trip.actual_return,
        stop_count=len(stops),
        finished_stop_count=sum(1 for status, _ in stops if status in FINISHED_STOP_STATUSES),
        manifest_units=sum(units or 0 for _, units in stops),
    )


def get_today_trips(db: Session, driver: User, on_date: Optional[date] = None) -> s.TodayTripsResponse:
    target = on_date or local_today()
    trips = (
        db.query(Trip)
        .filter(Trip.driver_id == driver.user_id, Trip.trip_date == target)
        .order_by(Trip.trip_no)
        .all()
    )
    return s.TodayTripsResponse(
        date=target,
        driver_id=driver.user_id,
        driver_name=driver.name,
        trips=[s.TripSummaryDTO(**_trip_summary(db, trip)) for trip in trips],
    )


def _manifest_items(db: Session, stop: TripStop, loaded: Dict[str, Decimal]) -> List[s.ManifestItemDTO]:
    rows = (
        db.query(TripStopItem, OrderLine, Product)
        .join(OrderLine, OrderLine.line_item_id == TripStopItem.line_item_id)
        .outerjoin(Product, Product.product_id == OrderLine.product_id)
        .filter(TripStopItem.stop_id == stop.stop_id)
        .order_by(TripStopItem.line_item_id)
        .all()
    )
    if rows:
        return [
            s.ManifestItemDTO(
                item_id=item.item_id, line_item_id=line.line_item_id, product_id=line.product_id,
                product_name=product.name if product else None, sku=item.sku, unit=item.unit,
                handling_note=item.handling_note, qty_assigned=float(item.qty_assigned),
                qty_loaded=_num(item.qty_loaded), qty_expected=float(_expected_qty(item, loaded)),
                qty_delivered=_num(item.qty_delivered), qty_returned=_num(item.qty_returned),
            )
            for item, line, product in rows
        ]
    # No trip_stop_item rows yet (materialised at departure): derive from the order lines.
    lines = (
        db.query(OrderLine, Product)
        .outerjoin(Product, Product.product_id == OrderLine.product_id)
        .filter(OrderLine.order_id == stop.order_id)
        .order_by(OrderLine.line_item_id)
        .all()
    )
    return [
        s.ManifestItemDTO(
            line_item_id=line.line_item_id, product_id=line.product_id,
            product_name=product.name if product else None, sku=line.product_id,
            unit=product.unit if product else None, qty_assigned=float(line.quantity),
            qty_expected=float(loaded.get(line.line_item_id, line.quantity)),
        )
        for line, product in lines
    ]


def _return_dto(record: ReturnCustody) -> s.ReturnDTO:
    return s.ReturnDTO(
        return_id=record.return_id, trip_id=record.trip_id, stop_id=record.stop_id,
        items=[s.ReturnItemDTO(**item) for item in json.loads(record.items or "[]")],
        reason=record.reason, return_crate=record.return_crate, status=record.status,
        created_at=record.created_at, confirmed_at=record.confirmed_at,
        officer_name=record.officer_name, condition=record.condition,
    )


def get_trip_detail(db: Session, driver: User, trip_id: str) -> s.TripDetailResponse:
    try:
        trip = _owned_trip(db, driver, trip_id)
    except DriverActionError as err:
        raise HTTPException(status_code=err.status_code, detail=err.detail)

    loaded = _loaded_qty_by_line(db, trip.trip_id)
    rows = (
        db.query(TripStop, Order, Outlet)
        .outerjoin(Order, Order.order_id == TripStop.order_id)
        .outerjoin(Outlet, Outlet.outlet_id == TripStop.outlet_id)
        .filter(TripStop.trip_id == trip.trip_id)
        .order_by(TripStop.stop_seq)
        .all()
    )
    stops = []
    for stop, order, outlet in rows:
        coords = None
        if outlet and outlet.lat is not None and outlet.lng is not None:
            coords = s.Coords(lat=float(outlet.lat), lng=float(outlet.lng))
        stops.append(s.StopDTO(
            stop_id=stop.stop_id, order_id=stop.order_id, outlet_id=stop.outlet_id,
            outlet_name=outlet.name if outlet else None, district=outlet.district if outlet else None,
            seq=stop.stop_seq, pack_seq=stop.pack_seq, eta=stop.eta, status=stop.status,
            row_version=stop.row_version, coords=coords,
            window_open=order.window_open if order else None,
            window_close=order.window_close if order else None,
            mall_window=outlet.mall_window if outlet else None,
            dock_type=outlet.dock_type if outlet else None,
            park_constraint=outlet.park_constraint if outlet else None,
            temp_req=stop.temp_req, forced_reefer=bool(stop.forced_reefer),
            wt_kg=_num(stop.wt_kg), vol_m3=_num(stop.vol_m3),
            order_units=order.order_units if order else None,
            arrived_at=stop.arrived_at, actual_arrival=order.actual_arrival if order else None,
            completed_at=stop.completed_at, skip_reason=stop.skip_reason,
            pod=_pod_dto(_pod_for_stop(db, stop)),
            items=_manifest_items(db, stop, loaded),
        ))
    returns = db.query(ReturnCustody).filter(ReturnCustody.trip_id == trip.trip_id).order_by(ReturnCustody.created_at).all()
    return s.TripDetailResponse(**_trip_summary(db, trip), stops=stops, returns=[_return_dto(r) for r in returns])


def photo_intent(db: Session, driver: User, stop_id: str, request: s.PhotoIntentRequest) -> s.PhotoIntentResponse:
    try:
        stop, trip = _owned_stop(db, driver, stop_id)
        _require_trip_out(trip)
    except DriverActionError as err:
        raise HTTPException(status_code=err.status_code, detail=err.detail)
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[request.content_type]
    object_key = f"pod/{stop.stop_id}/{uuid.uuid4().hex}.{ext}"
    # TODO(storage): replace with a presigned PUT once MinIO credentials are wired in.
    return s.PhotoIntentResponse(
        object_key=object_key,
        upload_url=f"{MINIO_ENDPOINT.rstrip('/')}/{MINIO_BUCKET}/{object_key}",
        expires_at=_now() + timedelta(minutes=15),
    )


def get_changes(db: Session, driver: User, since: Optional[datetime], pending_only: bool) -> s.ChangesResponse:
    server_now = _now()
    query = (
        db.query(RouteChange)
        .join(Trip, Trip.trip_id == RouteChange.trip_id)
        .filter(Trip.driver_id == driver.user_id)
    )
    if since:
        query = query.filter(RouteChange.issued_at > since)
    if pending_only:
        query = query.filter(RouteChange.acknowledged.isnot(True))
    changes = [
        s.RouteChangeDTO(
            change_id=change.change_id, trip_id=change.trip_id, change_type=change.change_type,
            payload=_json_or_none(change.payload) or {}, issued_at=change.issued_at,
            acknowledged=bool(change.acknowledged), ack_at=change.ack_at,
        )
        for change in query.order_by(RouteChange.issued_at)
    ]
    return s.ChangesResponse(changes=changes, next_cursor=server_now)


# ═══════════════════════════════════════════════════════════════════════════
# Conflicts
# ═══════════════════════════════════════════════════════════════════════════

def _conflict_dto(conflict: Conflict, event: Optional[DriverEvent]) -> s.ConflictDTO:
    return s.ConflictDTO(
        conflict_id=conflict.conflict_id, stop_id=conflict.stop_id,
        trip_id=event.trip_id if event else None, driver_event_id=conflict.driver_event_id,
        kind=event.kind if event else None,
        driver_record=_json_or_none(conflict.driver_json), system_record=_json_or_none(conflict.system_json),
        status=conflict.status, created_at=conflict.created_at, forwarded_at=conflict.forwarded_at,
        resolved_at=conflict.resolved_at, resolution=conflict.resolution, resolution_note=conflict.resolution_note,
    )


def list_conflicts(db: Session, driver: User) -> List[s.ConflictDTO]:
    rows = (
        db.query(Conflict, DriverEvent)
        .join(DriverEvent, DriverEvent.event_id == Conflict.driver_event_id)
        .filter(DriverEvent.driver_id == driver.user_id)
        .order_by(Conflict.created_at.desc())
        .all()
    )
    return [_conflict_dto(conflict, event) for conflict, event in rows]


def forward_conflict(db: Session, driver: User, conflict_id: str, note: Optional[str]) -> s.ConflictDTO:
    row = (
        db.query(Conflict, DriverEvent)
        .join(DriverEvent, DriverEvent.event_id == Conflict.driver_event_id)
        .filter(Conflict.conflict_id == conflict_id, DriverEvent.driver_id == driver.user_id)
        .with_for_update()
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Conflict not found")
    conflict, event = row
    if conflict.status != "in_review":
        raise HTTPException(status_code=400, detail=f"Cannot forward a conflict that is '{conflict.status}'")
    conflict.status = "forwarded"
    conflict.forwarded_at = _now()
    conflict.resolution_note = note
    db.commit()
    return _conflict_dto(conflict, event)


def resolve_conflict(
    db: Session, dispatcher: User, conflict_id: str, request: s.ResolveConflictRequest
) -> s.ResolveConflictResponse:
    row = (
        db.query(Conflict, DriverEvent, TripStop, Trip)
        .join(DriverEvent, DriverEvent.event_id == Conflict.driver_event_id)
        .join(TripStop, TripStop.stop_id == Conflict.stop_id)
        .join(Trip, Trip.trip_id == TripStop.trip_id)
        .filter(Conflict.conflict_id == conflict_id)
        .first()
    )
    if not row or row[3].depot_id != dispatcher.depot_id:
        raise HTTPException(status_code=404, detail="Conflict not found in your depot")
    conflict, event, stop, _trip = row
    if conflict.status not in ("in_review", "forwarded"):
        raise HTTPException(status_code=400, detail=f"Conflict is already '{conflict.status}'")

    applied = None
    if request.resolution == "accept_driver":
        driver = db.query(User).filter(User.user_id == event.driver_id).first()
        spec = EVENT_KINDS[event.kind]
        payload = json.loads(event.payload or "{}")
        target_id = payload.pop(spec.target, None)
        if "base_row_version" in payload:
            payload["base_row_version"] = stop.row_version
        try:
            applied = run_event(
                db, driver, event.kind, target_id, payload, f"{event.client_event_id}:resolved",
                occurred_at=event.occurred_at, device_id=event.device_id, offline=True,
            )
        except DriverActionError as err:
            raise HTTPException(status_code=409, detail=f"Driver change can no longer be applied: {err.detail}")
        if applied.status == "conflict":
            raise HTTPException(status_code=409, detail="Stop changed again while resolving; retry")
        conflict = db.query(Conflict).filter(Conflict.conflict_id == conflict_id).first()

    conflict.status = "dismissed" if request.resolution == "dismiss" else "resolved"
    conflict.resolution = request.resolution
    conflict.resolution_note = request.note or conflict.resolution_note
    conflict.resolved_at = _now()
    conflict.resolved_by = dispatcher.user_id
    conflict.resolved_by_role = dispatcher.role
    db.commit()
    event = db.query(DriverEvent).filter(DriverEvent.event_id == conflict.driver_event_id).first()
    return s.ResolveConflictResponse(conflict=_conflict_dto(conflict, event), applied=applied)
