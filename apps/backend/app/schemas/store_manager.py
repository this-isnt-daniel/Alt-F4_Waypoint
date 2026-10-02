from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class OrderItemInput(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, description="Quantity must be > 0")

class CreateOrderRequest(BaseModel):
    outlet_id: str
    brand: str
    temp_req: str
    order_date: date
    items: List[OrderItemInput] = Field(min_length=1, description="At least one item required")

class ConfirmReceiptRequest(BaseModel):
    client_op_id: str
    pod_id: str
    items_ok: bool
    discrepancies: Optional[List[dict]] = None
