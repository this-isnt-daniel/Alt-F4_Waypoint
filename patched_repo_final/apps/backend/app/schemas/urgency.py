from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict

from app.schemas.enums import UrgencyRequestStatus, UrgencyReason

__all__ = [
    "UrgencyRequestStatus",
    "UrgencyReason",
    "CreateUrgencyRequest",
    "UrgencyDecisionRequest",
    "ApproveUrgencyRequest",
    "RejectUrgencyRequest",
    "UrgencyRequestResponse",
    "DispatcherUrgencyListItemResponse",
]

class CreateUrgencyRequest(BaseModel):
    reason_code: UrgencyReason
    reason_text: str = Field(..., min_length=10, max_length=500)
    client_op_id: Optional[str] = None

class ApproveUrgencyRequest(BaseModel):
    decision_note: Optional[str] = Field(None, max_length=500)

class RejectUrgencyRequest(BaseModel):
    decision_note: str = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_rejection_note(self):
        if not self.decision_note or not self.decision_note.strip():
            raise ValueError("decision_note is mandatory when rejecting an urgency request")
        return self

class UrgencyDecisionRequest(BaseModel):
    status: Literal[UrgencyRequestStatus.approved, UrgencyRequestStatus.rejected]
    decision_note: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_rejection_note(self):
        if self.status == UrgencyRequestStatus.rejected:
            if not self.decision_note or not self.decision_note.strip():
                raise ValueError("decision_note is mandatory when rejecting an urgency request")
        return self

class UrgencyRequestResponse(BaseModel):
    urgency_request_id: str
    order_id: str
    outlet_id: str
    reported_by: str
    reason_code: UrgencyReason
    reason_text: str
    status: UrgencyRequestStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    decision_note: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    client_op_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DispatcherUrgencyListItemResponse(BaseModel):
    urgency_request_id: str
    order_id: str
    outlet_id: str
    outlet_name: Optional[str] = None
    brand: Optional[str] = None
    temp_req: Optional[str] = None
    reported_by: str
    reason_code: UrgencyReason
    reason_text: str
    status: UrgencyRequestStatus
    created_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    decision_note: Optional[str] = None
    order_status: Optional[str] = None
    defer_count: Optional[int] = None
    deferred_prev: Optional[bool] = None
    window_open: Optional[str] = None
    window_close: Optional[str] = None
    order_wt_kg: Optional[float] = None
    order_vol_m3: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
