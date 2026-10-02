from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DepartTripRequest(BaseModel):
    client_op_id: str
    departed_at: datetime

class ProofOfDeliveryRequest(BaseModel):
    client_op_id: str
    order_id: str
    delivered_at: datetime
    otp_code: Optional[str] = None
    otp_verified: bool = False
    signature_url: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    recorded_offline: bool = False
    synced_at: Optional[datetime] = None

class DriverEventInput(BaseModel):
    client_event_id: str
    kind: str
    occurred_at: datetime
    payload: Dict[str, Any]

class SyncDriverEventsRequest(BaseModel):
    client_op_id: str
    events: List[DriverEventInput]
