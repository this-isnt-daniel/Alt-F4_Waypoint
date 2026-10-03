from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import date, datetime

class OrderLineResponse(BaseModel):
    line_item_id: str
    product_id: str
    quantity: int
    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    order_id: str
    outlet_id: str
    brand: str
    temp_req: str
    order_date: date
    status: str
    
    # Delivery window derived at creation
    window_open: Optional[str] = None
    window_close: Optional[str] = None
    
    # Calculated values at confirmation
    order_units: Optional[int] = None
    order_wt_kg: Optional[float] = None
    order_vol_m3: Optional[float] = None
    
    # Timestamps
    submitted_at: Optional[datetime] = None
    cutoff_at: Optional[datetime] = None
    
    # Assignments (Shared views)
    trip_id: Optional[str]
    stop_seq: Optional[int]
    defer_count: int
    
    items: List[OrderLineResponse] = []
    model_config = ConfigDict(from_attributes=True)

class TimelineEventResponse(BaseModel):
    event_id: str
    order_id: Optional[str] = None
    trip_id: Optional[str] = None
    event_type: str
    occurred_at: datetime
    details: Optional[dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)

class TripStopItemResponse(BaseModel):
    item_id: str
    product_id: str
    quantity: int
    loaded_qty: Optional[int] = None
    delivered_qty: Optional[int] = None
    returned_qty: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class TripStopResponse(BaseModel):
    stop_id: str
    order_id: str
    outlet_id: str
    sequence: int
    status: str
    expected_arrival: Optional[str] = None
    items: List[TripStopItemResponse] = []
    model_config = ConfigDict(from_attributes=True)

class TripResponse(BaseModel):
    trip_id: str
    depot_id: str
    vehicle_id: Optional[str] = None
    status: str
    trip_date: date
    brand: Optional[str] = None
    temp_type: Optional[str] = None
    stops: List[TripStopResponse] = []
    model_config = ConfigDict(from_attributes=True)

class VehicleResponse(BaseModel):
    vehicle_id: str
    depot_id: str
    type: str
    temp: str
    weight_cap_kg: float
    vol_cap_m3: float
    fuel_type: Optional[str] = None
    km_per_l: Optional[float] = None
    fuel_quota_l: Optional[int] = None
    plate: Optional[str] = None
    status: str
    last_lat: Optional[float] = None
    last_lng: Optional[float] = None
    last_seen_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class OutletResponse(BaseModel):
    outlet_id: str
    name: str
    brand: str
    district: Optional[str] = None
    depot_id: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    window_open: Optional[str] = None
    window_close: Optional[str] = None
    mall_window: Optional[str] = None
    dock_type: Optional[str] = None
    park_constraint: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

