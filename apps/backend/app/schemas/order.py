from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import Brand, TempRequirement, OrderStatus

class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)

class CreateOrderRequest(BaseModel):
    outlet_id: str = Field(..., min_length=1)
    brand: Brand
    order_type: TempRequirement
    order_date: date
    items: List[OrderItemRequest] = Field(..., min_length=1)

class OrderResponse(BaseModel):
    order_id: str
    outlet_id: str
    brand: Brand
    order_type: TempRequirement
    order_date: date
    status: OrderStatus
    order_weight_kg: Optional[float] = None
    order_volume_m3: Optional[float] = None
    window_open_time: Optional[str] = None
    window_close_time: Optional[str] = None
    vehicle_id: Optional[str] = None
    trip_id: Optional[str] = None
    expected_arrival: Optional[str] = None
    actual_arrival: Optional[str] = None
    deferral_reason: Optional[str] = None
    stop_sequence: Optional[int] = None
    
    model_config = {
        "from_attributes": True
    }
