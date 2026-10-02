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
