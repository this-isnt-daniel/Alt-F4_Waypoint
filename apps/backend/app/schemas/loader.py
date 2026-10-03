from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


LOAD_ITEM_STATUSES = {
    "pending",
    "verified",
    "short",
    "over",
    "damaged",
    "missing",
    "substituted",
}

DISCREPANCY_STATUSES = {"short", "over", "damaged", "missing", "substituted"}


class LoaderQueueTrip(BaseModel):
    trip_id: str
    vehicle_id: str
    vehicle_plate: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_temp: Optional[str] = None
    trip_date: date
    trip_no: int
    status: str
    stop_count: int
    total_items: int
    verified_items: int
    discrepancy_count: int
    route_label: Optional[str] = None
    read_only: bool = False


class LoadItem(BaseModel):
    line_item_id: str
    stop_item_id: Optional[str] = None
    order_id: str
    product_id: str
    product_name: Optional[str] = None
    unit: Optional[str] = None
    assigned_qty: int
    loaded_qty: Optional[int] = None
    status: str = "pending"
    discrepancy_reason: Optional[str] = None
    note: Optional[str] = None


class LoadStop(BaseModel):
    stop_id: str
    order_id: str
    outlet_id: str
    outlet_name: Optional[str] = None
    stop_seq: int
    pack_seq: Optional[int] = None
    eta: Optional[str] = None
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    temp_req: str
    status: str
    items: List[LoadItem] = Field(default_factory=list)
    complete: bool = False


class LoaderWorkbench(BaseModel):
    trip_id: str
    depot_id: str
    vehicle_id: str
    vehicle_plate: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_temp: Optional[str] = None
    trip_date: date
    trip_no: int
    status: str
    read_only: bool
    check_id: Optional[str] = None
    check_status: Optional[str] = None
    checked_by: Optional[str] = None
    checked_at: Optional[datetime] = None
    stop_count: int
    total_items: int
    verified_items: int
    discrepancy_count: int
    stops: List[LoadStop] = Field(default_factory=list)


class SaveLoadItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_op_id: Optional[str] = None
    loaded_qty: int = Field(..., ge=0)
    status: str
    discrepancy_reason: Optional[str] = None
    note: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in LOAD_ITEM_STATUSES:
            raise ValueError(f"status must be one of {sorted(LOAD_ITEM_STATUSES)}")
        return value


class LoadCheckItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # line_item_id is the canonical identity. product_id alone is unsafe because
    # the same product can appear in multiple orders on the same trip.
    line_item_id: str
    loaded_qty: int = Field(..., ge=0)
    status: str
    discrepancy_reason: Optional[str] = None
    note: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in LOAD_ITEM_STATUSES:
            raise ValueError(f"status must be one of {sorted(LOAD_ITEM_STATUSES)}")
        return value


class SubmitLoadCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_op_id: str
    items: List[LoadCheckItemInput]


class VehicleUnavailableRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_op_id: str
    reason: str = Field(..., min_length=3)
    note: Optional[str] = None


class LoaderDeferralResponse(BaseModel):
    deferral_id: str
    order_id: str
    outlet_id: str
    outlet_name: Optional[str] = None
    original_date: date
    new_date: Optional[date] = None
    reason: Optional[str] = None
    created_at: Optional[datetime] = None
    trip_id: Optional[str] = None
    items: List[LoadItem] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class LoaderActionResponse(BaseModel):
    status: str
    trip_id: Optional[str] = None
    check_id: Optional[str] = None
    stop_id: Optional[str] = None
    line_item_id: Optional[str] = None
    message: Optional[str] = None
