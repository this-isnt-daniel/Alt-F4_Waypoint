"""
Pydantic v2 schemas — ALL request/response models for the driver API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════
# Common
# ═══════════════════════════════════════════════════════════════════════════

class Coords(BaseModel):
    lat: float
    lng: float


class ErrorResponse(BaseModel):
    detail: str


# ═══════════════════════════════════════════════════════════════════════════
# Module A — Auth
# ═══════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    driver_id: str
    pin: str
    device_id: str = "default-device"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    driver_id: str
    driver_name: str


class RefreshRequest(BaseModel):
    refresh_token: str


class DriverProfile(BaseModel):
    driver_id: str
    name: str
    home_depot: str
    phone_masked: Optional[str] = None
    active: bool = True


# ═══════════════════════════════════════════════════════════════════════════
# Module B — Trips
# ═══════════════════════════════════════════════════════════════════════════

class TripSummary(BaseModel):
    trip_id: str
    trip_no: int
    brand: str
    district: str
    depot: str
    vehicle_id: str
    status: str
    stop_count: int
    manifest_units: int
    deliverable_units: int
    return_units: int
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    depart_time: Optional[str] = None
    eta_return: Optional[str] = None
    capability: Optional[str] = None
    distance_km: Optional[float] = None
    drive_time: Optional[str] = None


class TodayTripsResponse(BaseModel):
    date: str
    driver_id: str
    driver_name: str
    vehicle_id: str
    trips: list[TripSummary]


class StopDTO(BaseModel):
    stop_id: str
    seq: int
    outlet_id: str
    name: str
    address: Optional[str] = None
    coords: Optional[Coords] = None
    window_open: Optional[str] = None
    window_close: Optional[str] = None
    mall_window: Optional[str] = None
    dock_type: Optional[str] = None
    parking_constraint: Optional[str] = None
    temp_requirement: Optional[str] = None
    order_units: int = 0
    deliverable_units: int = 0
    return_units: int = 0
    return_crate: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone_masked: Optional[str] = None
    service_allowance_min: Optional[int] = None
    special_instructions: Optional[str] = None
    status: str = "upcoming"
    row_version: int = 1


class ManifestLineDTO(BaseModel):
    stop_id: str
    outlet_id: str
    item: str
    manifest_qty: int
    deliverable_qty: int
    return_qty: int = 0
    reason: Optional[str] = None
    return_crate: Optional[str] = None
    loader_id: Optional[str] = None
    loader_note: Optional[str] = None
    pre_flagged: bool = False


class RouteLegDTO(BaseModel):
    from_point: str
    to_outlet: Optional[str] = None
    to_stop_id: Optional[str] = None
    distance_km: Optional[float] = None
    planned_travel_duration_min: Optional[int] = None


class TripManifestResponse(BaseModel):
    trip: TripSummary
    stops: list[StopDTO]
    manifest_lines: list[ManifestLineDTO]
    legs: list[RouteLegDTO]


class TripBriefingResponse(BaseModel):
    trip: TripSummary
    stops: list[StopDTO]
    legs: list[RouteLegDTO]
    flagged_stops: list[str] = []
    total_distance_km: Optional[float] = None
    estimated_duration: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Module C — Departure / Load Confirmation
# ═══════════════════════════════════════════════════════════════════════════

class LoadConfirmationGroup(BaseModel):
    stop_id: str
    outlet_id: str
    state: str  # "matches" | "flagged"
    van_units: int
    deliverable_units: Optional[int] = None
    return_units: Optional[int] = None
    reason: Optional[str] = None
    return_crate: Optional[str] = None
    note: Optional[str] = None


class LoadConfirmation(BaseModel):
    groups: list[LoadConfirmationGroup]


class DepartRequest(BaseModel):
    client_event_id: str
    departed_at: str
    load_confirmation: LoadConfirmation


class DepartResponse(BaseModel):
    status: str
    trip_id: str
    trip_status: str
    server_event_id: Optional[str] = None
    flagged_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════
# Module D — Stop lifecycle
# ═══════════════════════════════════════════════════════════════════════════

class ArriveRequest(BaseModel):
    client_event_id: str
    arrived_at: str
    gps: Optional[Coords] = None
    base_row_version: int = 1


class ArriveResponse(BaseModel):
    status: str
    server_event_id: Optional[str] = None
    new_row_version: Optional[int] = None
    window_status: Optional[str] = None  # early | on_time | late_risk | missed


class ChecklistLine(BaseModel):
    line_id: str
    state: str  # "delivered" | "flagged"
    reason: Optional[str] = None
    quantity_flagged: Optional[int] = None
    return_crate: Optional[str] = None


class ChecklistRequest(BaseModel):
    client_event_id: str
    base_row_version: int
    lines: list[ChecklistLine]


class ChecklistResponse(BaseModel):
    status: str
    server_event_id: Optional[str] = None
    new_row_version: Optional[int] = None


class PhotoIntentResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_at: str


class PhotoCompleteRequest(BaseModel):
    client_event_id: str
    object_key: str
    captured_at: str
    base_row_version: int


class PhotoCompleteResponse(BaseModel):
    status: str
    server_event_id: Optional[str] = None
    evidence_id: Optional[str] = None


class PinRequest(BaseModel):
    client_event_id: str
    pin_state: str = "submitted"
    submitted_at: Optional[str] = None
    attempts: int = 1
    base_row_version: int = 1


class PinResponse(BaseModel):
    status: str
    server_event_id: Optional[str] = None
    pin_state: str  # "submitted" | "verified" | "pending_verification"
    verified_at: Optional[str] = None


class OutcomeRequest(BaseModel):
    client_event_id: str
    outcome: str  # "delivered" | "partial" | "failed"
    delivered_units: Optional[int] = None
    return_units: Optional[int] = None
    reason: Optional[str] = None
    return_crate: Optional[str] = None
    finished_at: Optional[str] = None
    base_row_version: int = 1


class OutcomeResponse(BaseModel):
    status: str
    server_event_id: Optional[str] = None
    new_row_version: Optional[int] = None
    return_id: Optional[str] = None


class ReturnItem(BaseModel):
    name: str
    quantity: int


class ReturnRequest(BaseModel):
    client_event_id: str
    items: list[ReturnItem]
    return_crate: Optional[str] = None
    destination_depot: Optional[str] = None
    handover_location: Optional[str] = None


class ReturnResponse(BaseModel):
    status: str
    return_id: Optional[str] = None
    server_event_id: Optional[str] = None


class DepotConfirmRequest(BaseModel):
    client_event_id: str
    confirmed_at: str
    officer_name: Optional[str] = None
    officer_pin_state: Optional[str] = None
    condition: Optional[str] = None


class DepotConfirmResponse(BaseModel):
    status: str
    return_id: str
    server_event_id: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Module E — Sync
# ═══════════════════════════════════════════════════════════════════════════

class SyncEventPayload(BaseModel):
    """A single event in a sync batch."""
    client_event_id: str
    kind: str
    occurred_at: Optional[str] = None
    payload: Optional[dict] = None


class SyncRequest(BaseModel):
    driver_id: str
    device_id: str
    last_sync_cursor: Optional[str] = None
    events: list[SyncEventPayload]


class SyncEventResult(BaseModel):
    client_event_id: str
    status: str  # applied | conflict | already_applied | failed
    server_event_id: Optional[str] = None
    new_row_version: Optional[int] = None
    conflict_id: Optional[str] = None
    reason: Optional[str] = None
    system_record: Optional[dict] = None
    error: Optional[str] = None


class SyncResponse(BaseModel):
    results: list[SyncEventResult]
    new_cursor: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Module F — Changes (dispatcher → driver)
# ═══════════════════════════════════════════════════════════════════════════

class ChangeDTO(BaseModel):
    change_id: str
    type: str
    issued_at: str
    trip_id: Optional[str] = None
    payload: Optional[dict] = None
    acknowledged: bool = False


class ChangesResponse(BaseModel):
    changes: list[ChangeDTO]
    next_cursor: Optional[str] = None


class AckChangeRequest(BaseModel):
    pass  # empty body is fine


class AckChangeResponse(BaseModel):
    status: str
    change_id: str


# ═══════════════════════════════════════════════════════════════════════════
# Module G — Chat / Call
# ═══════════════════════════════════════════════════════════════════════════

class MessageDTO(BaseModel):
    id: Optional[str] = None
    stop_id: str
    sender_role: str
    sender_id: str
    body: str
    quick_reply: bool = False
    created_at: Optional[str] = None


class SendMessageRequest(BaseModel):
    client_event_id: str
    body: str
    quick_reply: bool = False


class SendMessageResponse(BaseModel):
    status: str
    message_id: Optional[str] = None


class CallIntentRequest(BaseModel):
    stop_id: str
    requested_by: str = "driver"


class CallIntentResponse(BaseModel):
    masked_dial_number: str
    expires_at: str


# ═══════════════════════════════════════════════════════════════════════════
# Conflicts
# ═══════════════════════════════════════════════════════════════════════════

class ConflictDTO(BaseModel):
    id: str
    stop_id: Optional[str] = None
    driver_record: Optional[dict] = None
    system_record: Optional[dict] = None
    status: str
    created_at: Optional[str] = None
    forwarded_at: Optional[str] = None
    resolved_at: Optional[str] = None


class ForwardConflictRequest(BaseModel):
    note: Optional[str] = None


class ForwardConflictResponse(BaseModel):
    status: str
    conflict_id: str
    forwarded_at: str


# ═══════════════════════════════════════════════════════════════════════════
# Road Geometry
# ═══════════════════════════════════════════════════════════════════════════

class RoadGeometryRow(BaseModel):
    from_id: str
    to_id: str
    coords: list[list[float]]  # [[lat, lng], ...]
    coord_version: int = 1
    distance_meters: Optional[float] = None
    duration_seconds: Optional[float] = None


class RoadGeometryQueryRequest(BaseModel):
    edges: list[list[str]]  # e.g. [["DEPOT:KANDY_HUB", "OUT042"], ...]
    coord_version: int = 1


class RoadGeometryQueryResponse(BaseModel):
    rows: list[RoadGeometryRow]

