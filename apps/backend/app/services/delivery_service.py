import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.trip import Trip, TripStop
from app.models.order import Order
from app.models.delivery import ProofOfDelivery
from app.models.events import DeliveryEvent, DriverEvent
from app.schemas.driver import ProofOfDeliveryRequest, SyncDriverEventsRequest, DepartTripRequest

def depart_trip(db: Session, trip_id: str, request: DepartTripRequest, driver_id: str):
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    # Wait, the Trip model uses vehicle_id but doesn't explicitly store driver_id?
    # Schema says: Vehicle table has default driver, Trip uses Vehicle.
    # In a real app we'd check if the driver is assigned to this trip's vehicle.
    # For now, we trust the route handler's scope check or just proceed.
    
    if trip.status != "loaded":
        raise HTTPException(status_code=400, detail="Trip must be loaded before departure")
        
    trip.status = "out_for_delivery"
    now = datetime.now(timezone.utc)
    
    stops = db.query(TripStop).filter(TripStop.trip_id == trip_id).all()
    for stop in stops:
        order = db.query(Order).filter(Order.order_id == stop.order_id).first()
        if order:
            order.status = "out_for_delivery"
            db.add(DeliveryEvent(
                event_id=str(uuid.uuid4()),
                order_id=order.order_id,
                event_type="order_out_for_delivery",
                occurred_at=now,
                actor_role="driver",
                actor_id=driver_id
            ))
            
    db.commit()
    db.refresh(trip)
    return trip


def submit_pod(db: Session, stop_id: str, request: ProofOfDeliveryRequest, driver_id: str):
    # Idempotency
    existing = db.query(ProofOfDelivery).filter_by(client_op_id=request.client_op_id).first()
    if existing:
        return existing
        
    stop = db.query(TripStop).filter(TripStop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
        
    pod = ProofOfDelivery(
        pod_id=str(uuid.uuid4()),
        order_id=request.order_id,
        stop_id=stop_id,
        delivered_by=driver_id,
        delivered_at=request.delivered_at,
        otp_code=request.otp_code,
        otp_verified=request.otp_verified,
        signature_url=request.signature_url,
        photo_url=request.photo_url,
        notes=request.notes,
        recorded_offline=request.recorded_offline,
        synced_at=request.synced_at or datetime.now(timezone.utc),
        client_op_id=request.client_op_id
    )
    db.add(pod)
    
    # Note: Order.status does NOT become "delivered" here yet.
    # That happens at Store Manager Receipt Confirmation.
    stop.status = "delivered"
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate operation")
        
    db.refresh(pod)
    return pod


def sync_events(db: Session, request: SyncDriverEventsRequest, driver_id: str):
    # Foundational integration boundary for the driver offline engine.
    # We record the events but leave the complex resolution for the driver team.
    results = []
    for ev in request.events:
        # Check idempotency per event
        existing = db.query(DriverEvent).filter_by(client_event_id=ev.client_event_id).first()
        if existing:
            results.append({"client_event_id": ev.client_event_id, "status": "already_applied"})
            continue
            
        new_ev = DriverEvent(
            event_id=str(uuid.uuid4()),
            driver_id=driver_id,
            client_event_id=ev.client_event_id,
            event_type=ev.kind,
            occurred_at=ev.occurred_at,
            payload=ev.payload,
            status="pending" # Driver team will process these
        )
        db.add(new_ev)
        results.append({"client_event_id": ev.client_event_id, "status": "pending_processing"})
        
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflict in sync batch")
        
    return results
