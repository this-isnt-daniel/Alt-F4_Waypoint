import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.order import Order, OrderLine
from app.models.product import Product
from app.models.plan import DraftPlan
from app.models.events import DeliveryEvent
from app.schemas.shared import TimelineEventResponse
from app.adapters.optimizer_adapter import (
    generate_daily_draft_plan_operation,
    edit_draft_plan_operation,
)

router = APIRouter()


class UrgentOrderItem(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class UrgentOrderInsertRequest(BaseModel):
    order_id: Optional[str] = None
    outlet_id: str
    brand: Optional[str] = "fresh"
    temp_req: Optional[str] = "ambient"
    order_date: Optional[date] = None
    order_units: Optional[int] = None
    order_wt_kg: Optional[float] = None
    order_vol_m3: Optional[float] = None
    window_open: Optional[str] = None
    window_close: Optional[str] = None
    items: Optional[List[UrgentOrderItem]] = None
    plan_id: Optional[str] = None
    target_vehicle_id: Optional[str] = None
    target_trip_number: Optional[int] = 1


@router.get("/{order_id}/timeline", response_model=List[TimelineEventResponse])
def get_order_timeline(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.outlet import Outlet
    from app.models.trip import Trip, TripStop
    
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    outlet = db.query(Outlet).filter(Outlet.outlet_id == order.outlet_id).first()
    
    if current_user.role == "store_manager":
        if order.outlet_id != current_user.outlet_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
    elif current_user.role in ("dispatcher", "loader"):
        if outlet and outlet.depot_id != current_user.depot_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
    elif current_user.role == "driver":
        # Check if the order is assigned to a trip this driver owns
        trip_stop = db.query(TripStop).join(Trip).filter(
            TripStop.order_id == order_id,
            Trip.driver_id == current_user.user_id
        ).first()
        if not trip_stop:
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    events = db.query(DeliveryEvent).filter(DeliveryEvent.order_id == order_id).order_by(DeliveryEvent.occurred_at).all()
    return events