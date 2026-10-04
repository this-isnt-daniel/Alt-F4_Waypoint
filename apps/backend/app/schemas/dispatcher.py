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

class DraftPlanCreateRequest(BaseModel):
    depot_id: Optional[str] = None
    target_date: Optional[date] = None
    brand: Optional[str] = None
    enable_targeted_cpsat: bool = True

class EditDraftPlanRequest(BaseModel):
    actions: List[dict]

class ApprovePlanRequest(BaseModel):
    client_op_id: Optional[str] = None

class BreakdownReallocateRequest(BaseModel):
    plan_id: Optional[str] = None
    undelivered_quantities: Optional[List[dict]] = None
    current_time_iso: Optional[str] = None
    pickup_location: Optional[str] = "DEPOT"
