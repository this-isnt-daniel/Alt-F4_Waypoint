from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class OptimizeRequest(BaseModel):
    depot_id: str
    target_date: date
    brand: Optional[str] = None
    
class ProposedTripStop(BaseModel):
    order_id: str
    sequence: int
    expected_arrival: Optional[str] = None

class ProposedTrip(BaseModel):
    vehicle_id: str
    brand: str
    temp_type: str
    stops: List[ProposedTripStop]
    
class ProposedPlanResponse(BaseModel):
    run_id: str
    depot_id: str
    target_date: date
    trips: List[ProposedTrip]
    deferred_orders: List[str]

class ConfirmPlanRequest(BaseModel):
    client_op_id: str

class DeferOrderRequest(BaseModel):
    client_op_id: str
    order_id: str
    outlet_id: str
    original_date: date
    new_date: Optional[date]
    reason: str
