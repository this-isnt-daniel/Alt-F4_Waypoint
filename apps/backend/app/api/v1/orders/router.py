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
    current_user: Optional[User] = Depends(get_current_user),
):
    events = db.query(DeliveryEvent).filter(DeliveryEvent.order_id == order_id).order_by(DeliveryEvent.occurred_at).all()
    if not events:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
    return events


@router.post("/urgent/insert")
def insert_urgent_order(
    request: UrgentOrderInsertRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    POST /api/v1/orders/urgent/insert
    Dynamically inserts an urgent order into the system and evaluates its
    insertion into the active delivery plan.
    """
    effective_date = request.order_date or date.today()
    order_id = request.order_id or f"ORD-URGENT-{uuid.uuid4().hex[:6].upper()}"
    if current_user:
        user_id = current_user.user_id
    else:
        existing_user = db.query(User).first()
        user_id = existing_user.user_id if existing_user else "system"

    # 1. Compute totals from items if present
    total_units = request.order_units or 0
    total_wt = request.order_wt_kg or 0.0
    total_vol = request.order_vol_m3 or 0.0

    order_lines = []
    if request.items:
        for idx, item in enumerate(request.items, start=1):
            total_units += item.quantity
            prod = db.query(Product).filter(Product.product_id == item.product_id).first()
            u_wt = float(prod.unit_wt_kg) if prod and prod.unit_wt_kg else 1.0
            u_vol = float(prod.unit_vol_m3) if prod and prod.unit_vol_m3 else 0.01
            total_wt += item.quantity * u_wt
            total_vol += item.quantity * u_vol

            order_lines.append(
                OrderLine(
                    line_item_id=f"{order_id}-L{idx}",
                    order_id=order_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                )
            )

    if total_units == 0:
        total_units = 10
        total_wt = total_wt or 50.0
        total_vol = total_vol or 0.2

    now = datetime.now(timezone.utc)
    # 2. Persist confirmed urgent order in DB
    db_order = Order(
        order_id=order_id,
        outlet_id=request.outlet_id,
        created_by=user_id,
        brand=request.brand or "fresh",
        temp_req=request.temp_req or "ambient",
        order_date=effective_date,
        submitted_at=now,
        status="confirmed",
        order_units=total_units,
        order_wt_kg=total_wt,
        order_vol_m3=total_vol,
        window_open=request.window_open,
        window_close=request.window_close,
        deferred_prev=False,
        defer_count=0,
    )
    db.add(db_order)
    for line in order_lines:
        db.add(line)
    db.commit()

    # 3. Update or re-evaluate draft plan
    updated_plan: Optional[Dict[str, Any]] = None
    target_plan_id = request.plan_id
    if not target_plan_id:
        latest_plan = (
            db.query(DraftPlan)
            .filter(DraftPlan.target_date == effective_date, DraftPlan.status == "draft")
            .order_by(DraftPlan.updated_at.desc())
            .first()
        )
        if latest_plan:
            target_plan_id = latest_plan.plan_id

    if target_plan_id:
        if request.target_vehicle_id:
            # Re-evaluate with explicit reinstate action
            action = {
                "action_type": "reinstate_whole_order",
                "order_ref": order_id,
                "target_vehicle_id": request.target_vehicle_id,
                "target_trip_number": request.target_trip_number or 1,
            }
            try:
                updated_plan = edit_draft_plan_operation(
                    db=db,
                    plan_id=target_plan_id,
                    actions=[action],
                    user_id=user_id,
                )
            except Exception:
                # Fallback to full re-optimization if manual slot infeasible
                updated_plan = generate_daily_draft_plan_operation(
                    db=db,
                    target_date=effective_date,
                    brand=request.brand,
                    enable_targeted_cpsat=True,
                    user_id=user_id,
                )
        else:
            # Run targeted re-optimization incorporating new confirmed urgent order
            updated_plan = generate_daily_draft_plan_operation(
                db=db,
                target_date=effective_date,
                brand=request.brand,
                enable_targeted_cpsat=True,
                user_id=user_id,
            )

    return {
        "status": "inserted",
        "order_id": order_id,
        "is_urgent": True,
        "order_date": effective_date.isoformat(),
        "outlet_id": request.outlet_id,
        "plan": updated_plan,
    }
