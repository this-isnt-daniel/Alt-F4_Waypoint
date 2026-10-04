import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

class MessageDTO(BaseModel):
    id: str
    outlet_id: Optional[str] = None
    stop_id: Optional[str] = None
    sender_role: str # 'driver' | 'store' | 'dispatch'
    sender_id: str
    sender_name: str
    recipient_role: str # 'driver' | 'store' | 'dispatch'
    body: str
    quick_reply: bool = False
    created_at: str

class SendMessageRequest(BaseModel):
    outlet_id: Optional[str] = None
    stop_id: Optional[str] = None
    sender_role: str = "driver"
    sender_id: Optional[str] = "USR-DRIV"
    sender_name: Optional[str] = "Driver Demo"
    recipient_role: str = "store"
    body: str
    quick_reply: bool = False

class CallIntentRequest(BaseModel):
    outlet_id: Optional[str] = None
    stop_id: Optional[str] = None
    requested_by: str = "driver"

# In-memory chat message store
_chat_messages_db: List[MessageDTO] = [
  MessageDTO(
    id="MSG-001",
    outlet_id="OUT001",
    stop_id="STOP-001",
    sender_role="store",
    sender_id="USR-SM",
    sender_name="Colpetty Store Manager",
    recipient_role="driver",
    body="Morning Daniru. Use the rear bay—main street access is blocked.",
    created_at="06:05 AM"
  ),
  MessageDTO(
    id="MSG-002",
    outlet_id="OUT001",
    stop_id="STOP-001",
    sender_role="driver",
    sender_id="USR-DRIV",
    sender_name="Daniru (VEH014)",
    recipient_role="store",
    body="On my way. ETA 12 minutes.",
    created_at="06:06 AM"
  ),
  MessageDTO(
    id="MSG-003",
    outlet_id="OUT001",
    stop_id="STOP-001",
    sender_role="store",
    sender_id="USR-SM",
    sender_name="Colpetty Store Manager",
    recipient_role="driver",
    body="I'll meet you at bay B.",
    created_at="06:07 AM"
  )
]

@router.get("/messages", response_model=List[MessageDTO])
def get_chat_messages(
    outlet_id: Optional[str] = Query(None),
    stop_id: Optional[str] = Query(None),
    recipient_role: Optional[str] = Query(None)
):
    """Retrieve chat history filtered by outlet, stop, or role."""
    filtered = _chat_messages_db
    if outlet_id:
        filtered = [m for m in filtered if m.outlet_id == outlet_id or not m.outlet_id]
    if stop_id:
        filtered = [m for m in filtered if m.stop_id == stop_id or not m.stop_id]
    if recipient_role:
        filtered = [m for m in filtered if m.recipient_role == recipient_role or m.sender_role == recipient_role]
    return filtered

@router.post("/messages")
def send_chat_message(request: SendMessageRequest):
    """Send a new message between Driver, Store Manager, or Dispatcher."""
    if not request.body.trim():
        raise HTTPException(status_code=400, detail="Message body cannot be empty")
        
    now_str = datetime.now(timezone.utc).strftime("%I:%M %p")
    msg_id = f"MSG-{uuid.uuid4().hex[:6].upper()}"
    
    msg = MessageDTO(
        id=msg_id,
        outlet_id=request.outlet_id or "OUT001",
        stop_id=request.stop_id or "STOP-001",
        sender_role=request.sender_role,
        sender_id=request.sender_id or "user",
        sender_name=request.sender_name or (
            "Driver" if request.sender_role == "driver" else ("Store Manager" if request.sender_role == "store" else "Dispatcher")
        ),
        recipient_role=request.recipient_role,
        body=request.body,
        quick_reply=request.quick_reply,
        created_at=now_str
    )
    _chat_messages_db.append(msg)
    return {"status": "success", "message_id": msg_id, "message": msg}

@router.post("/call-intent")
def initiate_call_intent(request: CallIntentRequest):
    """Initiate a call or call request between Driver and Store Manager / Dispatcher."""
    call_id = f"CALL-{uuid.uuid4().hex[:6].upper()}"
    return {
        "status": "connected",
        "call_id": call_id,
        "channel": "audio_webrtc_mock",
        "requested_by": request.requested_by,
        "detail": "Direct audio call initiated successfully."
    }

@router.get("/drivers")
def get_assigned_drivers(outlet_id: Optional[str] = Query(None)):
    """List drivers assigned to orders for the store manager's outlet."""
    return [
        {
            "driver_id": "USR-DRIV",
            "name": "Daniru Perera",
            "phone": "+94770000004",
            "vehicle_id": "VEH014",
            "vehicle_type": "Reefer Van",
            "status": "In Transit",
            "eta": "12 mins",
            "current_stop": "En route to Outlet",
            "assigned_orders": ["ORD-30190", "ORD-30302"]
        },
        {
            "driver_id": "USR-DRIV-2",
            "name": "Kamal Silva",
            "phone": "+94771112233",
            "vehicle_id": "VEH009",
            "vehicle_type": "Reefer Truck",
            "status": "Arrived at Bay",
            "eta": "Arrived",
            "current_stop": "Bay B",
            "assigned_orders": ["ORD-30182"]
        }
    ]
