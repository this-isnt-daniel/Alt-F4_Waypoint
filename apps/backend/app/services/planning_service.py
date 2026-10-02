import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.order import Order
from app.models.trip import Trip, TripStop
from app.models.events import DeliveryEvent
from app.models.deferral import Deferral
from app.models.outlet import Outlet
from app.schemas.dispatcher import ProposedPlanResponse, DeferOrderRequest

# Fake in-memory storage for optimization runs
# In reality, this would be a cache like Redis or a dedicated DB table
_mock_planning_runs = {}

def create_optimization_run(db: Session, depot_id: str, target_date: str, brand: str = None) -> ProposedPlanResponse:
    # Here CP-SAT would run. We mock it for the boundary design.
    run_id = f"RUN-{uuid.uuid4().hex[:6].upper()}"
    plan = ProposedPlanResponse(
        run_id=run_id,
        depot_id=depot_id,
        target_date=target_date,
        trips=[],
        deferred_orders=[]
    )
    _mock_planning_runs[run_id] = plan
    return plan

def get_optimization_run(run_id: str) -> ProposedPlanResponse:
    plan = _mock_planning_runs.get(run_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Planning run not found")
    return plan

def confirm_plan(db: Session, run_id: str, client_op_id: str, dispatcher_depot: str, user_id: str):
    plan = get_optimization_run(run_id)
    if plan.depot_id != dispatcher_depot:
        raise HTTPException(status_code=403, detail="Cannot confirm plan for a different depot")
        
    now = datetime.now(timezone.utc)
    # 1. Create Trips and TripStops
    for proposed_trip in plan.trips:
        trip_id = f"TRIP-{uuid.uuid4().hex[:8].upper()}"
        new_trip = Trip(
            trip_id=trip_id,
            depot_id=dispatcher_depot,
            vehicle_id=proposed_trip.vehicle_id,
            dispatcher_id=user_id,
            trip_date=plan.target_date,
            trip_no=1,
            status="planned"
        )
        db.add(new_trip)
        
        for stop in proposed_trip.stops:
            order = db.query(Order).filter(Order.order_id == stop.order_id).first()
            if not order:
                raise HTTPException(status_code=400, detail=f"Order {stop.order_id} not found")
            
            if order.status != "confirmed":
                raise HTTPException(status_code=400, detail=f"Order {stop.order_id} is not in confirmed state")
                
            # Assign canonical TripStop
            trip_stop = TripStop(
                stop_id=f"STOP-{uuid.uuid4().hex[:6].upper()}",
                trip_id=trip_id,
                order_id=order.order_id,
                outlet_id=order.outlet_id,
                stop_seq=stop.sequence,
                status="upcoming",
                eta=stop.expected_arrival,
                temp_req=order.temp_req
            )
            db.add(trip_stop)
            
            # Denormalize onto Order
            order.trip_id = trip_id
            order.stop_seq = stop.sequence
            order.status = "planned"
            
            # Event
            db.add(DeliveryEvent(
                event_id=str(uuid.uuid4()),
                order_id=order.order_id,
                event_type="order_planned",
                occurred_at=now,
                actor_role="dispatcher",
                actor_id=user_id
            ))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflict during plan confirmation (Orders already assigned or duplicate op)")
    
    return {"status": "applied"}


def defer_order(db: Session, request: DeferOrderRequest, dispatcher_depot: str, user_id: str):
    # Idempotency check
    existing = db.query(Deferral).filter_by(client_op_id=request.client_op_id).first()
    if existing:
        return existing
        
    order = db.query(Order).filter(Order.order_id == request.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.outlet_id != request.outlet_id:
        raise HTTPException(status_code=400, detail="Outlet mismatch")

    outlet = db.query(Outlet).filter(Outlet.outlet_id == order.outlet_id).first()
    if outlet and outlet.depot_id and outlet.depot_id != dispatcher_depot:
        raise HTTPException(status_code=403, detail="Cannot defer an order for a different depot")

    if order.status in {"loaded", "out_for_delivery", "delivered", "cancelled"}:
        raise HTTPException(status_code=400, detail=f"Order {order.order_id} cannot be deferred from {order.status}")

    now = datetime.now(timezone.utc)
    # Deferrals can happen from confirmed state usually, or from a loader failure path.
    order.defer_count += 1
    order.deferred_prev = True
    order.status = "deferred"
    
    deferral = Deferral(
        deferral_id=str(uuid.uuid4()),
        order_id=request.order_id,
        outlet_id=request.outlet_id,
        original_date=request.original_date,
        new_date=request.new_date or request.original_date,
        reason=request.reason,
        created_at=now,
        created_by=user_id,
        trip_id=order.trip_id,
        client_op_id=request.client_op_id
    )
    db.add(deferral)
    
    db.add(DeliveryEvent(
        event_id=str(uuid.uuid4()),
        order_id=request.order_id,
        event_type="order_deferred",
        occurred_at=now,
        actor_role="dispatcher",
        actor_id=user_id
    ))
    
    try:
        db.commit()
        db.refresh(deferral)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflict or duplicate")
        
    return deferral
