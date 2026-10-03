"""Driver API schemas (canonical PostgreSQL backend).

Write commands come in two shapes:
  * `<Name>Command`  — the business payload. Used as-is for offline `/events/sync`
                        payloads (plus the target id, e.g. "stop_id").
  * `<Name>Request`  — Command + `client_event_id` envelope, used by the REST endpoints.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Common
# ═══════════════════════════════════════════════════════════════════════════

class Coords(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class EventEnvelope(BaseModel):
    """Idempotency key carried by every REST write. `client_op_id` is accepted as an alias."""
    client_event_id: str = Field(
        min_length=1,
        max_length=128,
        validation_alias=AliasChoices("client_event_id", "client_op_id"),
    )
    device_id: Optional[str] = Field(default=None, max_length=128)


# ═══════════════════════════════════════════════════════════════════════════
# Read models
# ═══════════════════════════════════════════════════════════════════════════

class ManifestItemDTO(BaseModel):
    item_id: Optional[str] = None  # None only before departure when planning created no trip_stop_item rows
    line_item_id: str
    product_id: str
    product_name: Optional[str] = None
    sku: Optional[str] = None
    unit: Optional[str] = None
    handling_note: Optional[str] = None
    qty_assigned: float
    qty_loaded: Optional[float] = None
    qty_expected: float  # what the driver should have on the van: loaded → load check → assigned
    qty_delivered: Optional[float] = None
    qty_returned: Optional[float] = None


class PodDTO(BaseModel):
    pod_id: str
    order_id: str
    otp_code: str
    otp_verified: bool
    photo_url: Optional[str] = None
    signature_url: Optional[str] = None
    notes: Optional[str] = None
    delivered_at: datetime


class StopDTO(BaseModel):
    stop_id: str
    order_id: str
    outlet_id: str
    outlet_name: Optional[str] = None
    district: Optional[str] = None
    seq: int
    pack_seq: Optional[int] = None
    eta: Optional[str] = None
    status: str
    row_version: int
    coords: Optional[Coords] = None
    window_open: Optional[str] = None
    window_close: Optional[str] = None
    mall_window: Optional[str] = None
    dock_type: Optional[str] = None
    park_constraint: Optional[str] = None
    temp_req: Optional[str] = None
    forced_reefer: bool = False
    wt_kg: Optional[float] = None
    vol_m3: Optional[float] = None
    order_units: Optional[int] = None
    arrived_at: Optional[datetime] = None
    actual_arrival: Optional[str] = None
    completed_at: Optional[datetime] = None
    skip_reason: Optional[str] = None
    pod: Optional[PodDTO] = None
    items: List[ManifestItemDTO] = []


class ReturnItemDTO(BaseModel):
    item_id: str
    line_item_id: str
    product_id: str
    qty: float


class ReturnDTO(BaseModel):
    return_id: str
    trip_id: str
    stop_id: str
    items: List[ReturnItemDTO]
    reason: Optional[str] = None
    return_crate: Optional[str] = None
    status: str
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    officer_name: Optional[str] = None
    condition: Optional[str] = None


class TripSummaryDTO(BaseModel):
    trip_id: str
    trip_no: int
    trip_date: date
    status: str
    locked: bool  # trip_no 2 while trip_no 1 of the same driver/date is not completed
    vehicle_id: str
    vehicle_plate: Optional[str] = None
    depot_id: str
    brand: Optional[str] = None
    district: Optional[str] = None
    plan_depart: Optional[str] = None
    plan_return: Optional[str] = None
    dist_km: Optional[float] = None
    actual_depart: Optional[datetime] = None
    actual_return: Optional[datetime] = None
    stop_count: int
    finished_stop_count: int
    manifest_units: int


class TripDetailResponse(TripSummaryDTO):
    stops: List[StopDTO]
    returns: List[ReturnDTO]


class TodayTripsResponse(BaseModel):
    date: date
    driver_id: str
    driver_name: str
    trips: List[TripSummaryDTO]


# ═══════════════════════════════════════════════════════════════════════════
# Write commands
# ═══════════════════════════════════════════════════════════════════════════

class LoadConfirmationGroup(BaseModel):
    stop_id: str
    state: Literal["matches", "flagged"]
    note: Optional[str] = None


class DepartCommand(BaseModel):
    departed_at: Optional[datetime] = None
    load_confirmation: List[LoadConfirmationGroup] = []


class CompleteTripCommand(BaseModel):
    returned_at: Optional[datetime] = None
    actual_dist_km: Optional[float] = Field(default=None, ge=0)
    actual_fuel_l: Optional[float] = Field(default=None, ge=0)


class ArriveCommand(BaseModel):
    base_row_version: int
    arrived_at: Optional[datetime] = None
    gps: Optional[Coords] = None


class ChecklistLine(BaseModel):
    item_id: str
    qty_delivered: float = Field(ge=0)
    qty_returned: float = Field(default=0, ge=0)
    reason: Optional[str] = None


class ChecklistCommand(BaseModel):
    base_row_version: int
    lines: List[ChecklistLine] = Field(min_length=1)


class PhotoIntentRequest(BaseModel):
    content_type: Literal["image/jpeg", "image/png", "image/webp"] = "image/jpeg"


class PhotoIntentResponse(BaseModel):
    object_key: str
    upload_url: str
    expires_at: datetime


class PhotoCompleteCommand(BaseModel):
    object_key: str
    captured_at: Optional[datetime] = None


class PodCommand(BaseModel):
    order_id: str
    delivered_at: Optional[datetime] = None
    signature_url: Optional[str] = None
    notes: Optional[str] = None


class OutcomeCommand(BaseModel):
    base_row_version: int
    outcome: Literal["delivered", "partial", "failed"]
    reason: Optional[str] = None
    return_crate: Optional[str] = None
    finished_at: Optional[datetime] = None
    lines: Optional[List[ChecklistLine]] = None


class ReturnLine(BaseModel):
    item_id: str
    qty: float = Field(gt=0)


class ReturnCommand(BaseModel):
    base_row_version: int
    items: List[ReturnLine] = Field(min_length=1)
    reason: str = Field(min_length=1)
    return_crate: Optional[str] = None


class DepotConfirmCommand(BaseModel):
    officer_name: str = Field(min_length=1)
    condition: Optional[str] = None
    confirmed_at: Optional[datetime] = None


class AckChangeCommand(BaseModel):
    pass


class DepartRequest(DepartCommand, EventEnvelope): pass
class CompleteTripRequest(CompleteTripCommand, EventEnvelope): pass
class ArriveRequest(ArriveCommand, EventEnvelope): pass
class ChecklistRequest(ChecklistCommand, EventEnvelope): pass
class PhotoCompleteRequest(PhotoCompleteCommand, EventEnvelope): pass
class PodRequest(PodCommand, EventEnvelope): pass
class OutcomeRequest(OutcomeCommand, EventEnvelope): pass
class ReturnRequest(ReturnCommand, EventEnvelope): pass
class DepotConfirmRequest(DepotConfirmCommand, EventEnvelope): pass


class AckChangeRequest(AckChangeCommand):
    # Optional: defaults to "ack:<driver_id>:<change_id>" so blind retries are naturally idempotent.
    client_event_id: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices("client_event_id", "client_op_id"),
    )
    device_id: Optional[str] = None


class DriverActionResponse(BaseModel):
    """Result of any Driver write — REST or one event inside a sync batch."""
    status: str  # applied | already_applied | conflict | failed
    client_event_id: Optional[str] = None
    server_event_id: Optional[str] = None
    trip_id: Optional[str] = None
    stop_id: Optional[str] = None
    new_row_version: Optional[int] = None
    trip_status: Optional[str] = None
    stop_status: Optional[str] = None
    window_status: Optional[str] = None  # early | on_time | late_risk | missed
    flagged_count: Optional[int] = None
    return_id: Optional[str] = None
    return_status: Optional[str] = None
    unlocked_trip_id: Optional[str] = None
    change_id: Optional[str] = None
    pod: Optional[PodDTO] = None
    conflict_id: Optional[str] = None
    reason: Optional[str] = None
    system_record: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Offline sync
# ═══════════════════════════════════════════════════════════════════════════

class SyncEvent(BaseModel):
    client_event_id: str = Field(min_length=1, max_length=128)
    kind: str
    occurred_at: Optional[datetime] = None
    payload: Dict[str, Any] = {}


class SyncRequest(BaseModel):
    device_id: Optional[str] = Field(default=None, max_length=128)
    events: List[SyncEvent] = Field(max_length=200)


class SyncResponse(BaseModel):
    results: List[DriverActionResponse]
    server_time: datetime


# ═══════════════════════════════════════════════════════════════════════════
# Route changes / conflicts
# ═══════════════════════════════════════════════════════════════════════════

class RouteChangeDTO(BaseModel):
    change_id: str
    trip_id: str
    change_type: str
    payload: Dict[str, Any]
    issued_at: datetime
    acknowledged: bool
    ack_at: Optional[datetime] = None


class ChangesResponse(BaseModel):
    changes: List[RouteChangeDTO]
    next_cursor: datetime


class ConflictDTO(BaseModel):
    conflict_id: str
    stop_id: Optional[str] = None
    trip_id: Optional[str] = None
    driver_event_id: Optional[str] = None
    kind: Optional[str] = None
    driver_record: Optional[Dict[str, Any]] = None
    system_record: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    forwarded_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    resolution_note: Optional[str] = None


class ForwardConflictRequest(BaseModel):
    note: Optional[str] = None


class ResolveConflictRequest(BaseModel):
    resolution: Literal["accept_driver", "keep_server", "dismiss"]
    note: Optional[str] = None


class ResolveConflictResponse(BaseModel):
    conflict: ConflictDTO
    applied: Optional[DriverActionResponse] = None
