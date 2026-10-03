import uuid
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.route import RouteChange
from app.models.trip import Trip

def create_route_change(
    db: Session,
    depot_id: str,
    user_id: str,
    trip_id: str,
    change_type: str,
    payload: dict,
    change_id: str = None
) -> RouteChange:
    # 1. Validate trip exists and belongs to depot
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.depot_id != depot_id:
        raise HTTPException(status_code=403, detail="Trip not in your depot scope")

    # 2. Check if trip is in a state where route change makes sense
    if trip.status not in ["planned", "departed", "in_progress"]:
        raise HTTPException(status_code=422, detail=f"Cannot change route for trip in status {trip.status}")

    # 3. Handle idempotency
    _change_id = change_id or str(uuid.uuid4())
    existing = db.query(RouteChange).filter(RouteChange.change_id == _change_id).first()
    if existing:
        return existing

    # 4. Enforce payload structure basic validation based on change_type if needed
    # The payload is stored as a JSON string
    payload_str = json.dumps(payload)

    # 5. Create RouteChange
    route_change = RouteChange(
        change_id=_change_id,
        trip_id=trip_id,
        change_type=change_type,
        payload=payload_str,
        issued_at=datetime.now(timezone.utc),
        issued_by=user_id,
        acknowledged=False
    )
    db.add(route_change)
    db.commit()
    db.refresh(route_change)
    return route_change

def get_route_changes(db: Session, depot_id: str, trip_id: str):
    # Ensure trip belongs to depot
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.depot_id != depot_id:
        raise HTTPException(status_code=403, detail="Trip not in your depot scope")
        
    return db.query(RouteChange).filter(RouteChange.trip_id == trip_id).order_by(RouteChange.issued_at.desc()).all()
