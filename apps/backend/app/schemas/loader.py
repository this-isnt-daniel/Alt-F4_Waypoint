from pydantic import BaseModel
from typing import List, Optional

class LoadCheckItemInput(BaseModel):
    product_id: str
    expected_qty: int
    loaded_qty: int
    status: str
    discrepancy_reason: Optional[str] = None

class SubmitLoadCheckRequest(BaseModel):
    client_op_id: str
    items: List[LoadCheckItemInput]
