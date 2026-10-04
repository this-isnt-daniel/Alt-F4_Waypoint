from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.enums import Brand, TempReq, OrderStatus

class OrderLineRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)

class CreateOrderRequest(BaseModel):
    outlet_id: str = Field(..., min_length=1)
    brand: Brand
    temp_req: TempReq
    order_date: date
    items: List[OrderLineRequest] = Field(..., min_length=1)

class OrderLineResponse(BaseModel):
    line_item_id: str
    product_id: str
    quantity: int
    
    model_config = {
        "from_attributes": True
    }

class OrderResponse(BaseModel):
    order_id: str
    outlet_id: str
    created_by: str
    brand: Brand
    temp_req: TempReq
    order_date: date
    submitted_at: Optional[datetime] = None
    cutoff_at: Optional[datetime] = None
    status: OrderStatus
    
    order_units: Optional[int] = None
    order_wt_kg: Optional[float] = None
    order_vol_m3: Optional[float] = None
    window_open: Optional[str] = None
    window_close: Optional[str] = None
    
    trip_id: Optional[str] = None
    stop_seq: Optional[int] = None
    exp_arrival: Optional[str] = None
    actual_arrival: Optional[str] = None
    
    deferred_prev: bool
    defer_count: int

    items: List[OrderLineResponse] = []
    
    model_config = {
        "from_attributes": True
    }
