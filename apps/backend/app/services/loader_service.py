import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.trip import Trip, TripStop
from app.models.order import Order, OrderLine
from app.models.load_check import LoadCheck, LoadCheckItem
from app.models.delivery import Discrepancy
from app.models.events import DeliveryEvent
from app.schemas.loader import SubmitLoadCheckRequest

def submit_load_check(db: Session, trip_id: str, request: SubmitLoadCheckRequest, loader_depot: str, user_id: str):
    # Idempotency
    existing = db.query(LoadCheck).filter_by(client_op_id=request.client_op_id).first()
    if existing:
        return existing
        
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    if trip.depot_id != loader_depot:
        raise HTTPException(status_code=403, detail="Not authorized for this depot")
        
    if trip.status != "planned":
        raise HTTPException(status_code=400, detail="Trip must be planned to load")
        
    now = datetime.now(timezone.utc)
    
    check = LoadCheck(
        check_id=str(uuid.uuid4()),
        trip_id=trip_id,
        checked_by=user_id,
        checked_at=now,
        status="completed",
        client_op_id=request.client_op_id
    )
    db.add(check)
    
    for item in request.items:
        line = db.query(OrderLine).join(Order).join(TripStop).filter(
            TripStop.trip_id == trip_id,
            OrderLine.product_id == item.product_id
        ).first()
        
        if not line:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found in trip")

        chk_item = LoadCheckItem(
            chk_item_id=str(uuid.uuid4()),
            check_id=check.check_id,
            line_item_id=line.line_item_id,
            exp_qty=item.expected_qty,
            loaded_qty=item.loaded_qty,
            status=item.status
        )
        db.add(chk_item)
        
        if item.loaded_qty != item.expected_qty:
            disc = Discrepancy(
                discrepancy_id=str(uuid.uuid4()),
                order_id=line.order_id,
                raised_by=user_id,
                source_stage="loading",
                chk_item_id=chk_item.chk_item_id,
                product_id=item.product_id,
                type="shortage" if item.loaded_qty < item.expected_qty else "overage",
                reported_qty=abs(item.expected_qty - item.loaded_qty),
                status="open",
                note=item.discrepancy_reason
            )
            db.add(disc)

    # Move trip to loaded
    trip.status = "loaded"
    
    # Update orders to loaded and add events
    stops = db.query(TripStop).filter(TripStop.trip_id == trip_id).all()
    for stop in stops:
        order = db.query(Order).filter(Order.order_id == stop.order_id).first()
        if order:
            order.status = "loaded"
            db.add(DeliveryEvent(
                event_id=str(uuid.uuid4()),
                order_id=order.order_id,
                event_type="order_loaded",
                occurred_at=now,
                actor_role="loader",
                actor_id=user_id
            ))
            
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflict during load check")
        
    db.refresh(check)
    return check
