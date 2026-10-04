from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import date, datetime

class OrderItemInput(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, description="Quantity must be > 0")

class CreateOrderRequest(BaseModel):
    outlet_id: str
    brand: str
    temp_req: str
    order_date: date
    items: List[OrderItemInput] = Field(min_length=1, description="At least one item required")

class UpdateOrderRequest(BaseModel):
    items: List[OrderItemInput] = Field(min_length=1, description="At least one item required")

class DiscrepancyInput(BaseModel):
    product_id: str
    expected_qty: Optional[int] = None
    actual_qty: Optional[int] = None
    reported_qty: Optional[int] = None
    reason_code: Optional[str] = None # e.g. 'missing', 'damaged', 'wrong_item'
    note: Optional[str] = None

class ConfirmReceiptRequest(BaseModel):
    client_op_id: str
    pod_id: str
    items_ok: bool
    discrepancies: Optional[List[DiscrepancyInput]] = None

class ProductResponse(BaseModel):
    product_id: str
    name: str
    brand: str
    category: Optional[str] = None
    temp_req: str
    unit: str
    unit_wt_kg: Optional[float] = None
    unit_vol_m3: Optional[float] = None
    active: bool = True
    model_config = ConfigDict(from_attributes=True)

class OutletDetailResponse(BaseModel):
    outlet_id: str
    name: str
    brand: str
    district: Optional[str] = None
    depot_id: Optional[str] = None
    window_open: Optional[str] = None
    window_close: Optional[str] = None
    mall_window: Optional[str] = None
    dock_type: Optional[str] = None
    park_constraint: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DeferralResponse(BaseModel):
    deferral_id: str
    order_id: str
    outlet_id: str
    original_date: date
    new_date: date
    reason: Optional[str] = None
    created_at: datetime
    created_by: str
    trip_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class OrderETAResponse(BaseModel):
    order_id: str
    outlet_id: str
    status: str
    window_open: Optional[str] = None
    window_close: Optional[str] = None
    exp_arrival: Optional[str] = None
    actual_arrival: Optional[str] = None
    trip_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    delivery_otp: Optional[str] = None
    stop_seq: Optional[int] = None
    stop_status: Optional[str] = None
    defer_count: int = 0
    deferred_prev: bool = False
    model_config = ConfigDict(from_attributes=True)

