from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.dispatcher import BreakdownReallocateRequest
from app.adapters.optimizer_adapter import reallocate_broken_vehicle_operation

router = APIRouter()


@router.post("/{vehicle_id}/breakdown")
def report_vehicle_breakdown(
    vehicle_id: str,
    request: Optional[BreakdownReallocateRequest] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    POST /api/v1/vehicles/{vehicle_id}/breakdown
    Triggers dynamic in-flight breakdown recovery using reallocate_broken_vehicle.
    Freezes completed trips, preserves already delivered quantities, and reassigns
    undelivered orders to surviving fleet.
    """
    user_id = current_user.user_id if current_user else "system"
    plan_id = request.plan_id if request else None
    undelivered = request.undelivered_quantities if request else None
    current_time_iso = request.current_time_iso if request else None
    pickup_loc = request.pickup_location if request and request.pickup_location else "DEPOT"

    return reallocate_broken_vehicle_operation(
        db=db,
        vehicle_id=vehicle_id,
        plan_id=plan_id,
        undelivered_quantities=undelivered,
        current_time_iso=current_time_iso,
        pickup_location=pickup_loc,
        user_id=user_id,
    )
