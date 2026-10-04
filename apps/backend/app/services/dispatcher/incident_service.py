import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.incident import VehicleIncident
from app.models.vehicle import Vehicle
from app.models.trip import Trip

def create_incident(
    db: Session,
    depot_id: str,
    user_id: str,
    incident_id: str,
    vehicle_id: str,
    type: str,
    detail: str,
    trip_id: str = None
) -> VehicleIncident:
    # 1. Validate vehicle exists and belongs to depot
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.depot_id != depot_id:
        raise HTTPException(status_code=403, detail="Vehicle not in your depot scope")

    # 2. Validate trip if supplied
    if trip_id:
        trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        if trip.depot_id != depot_id:
            raise HTTPException(status_code=403, detail="Trip not in your depot scope")
        if trip.vehicle_id != vehicle_id:
            raise HTTPException(status_code=422, detail="Trip does not belong to the specified vehicle")

    # 3. Check for idempotency (if client provides incident_id)
    existing = db.query(VehicleIncident).filter(VehicleIncident.incident_id == incident_id).first()
    if existing:
        return existing

    # 4. Create incident
    incident = VehicleIncident(
        incident_id=incident_id,
        vehicle_id=vehicle_id,
        trip_id=trip_id,
        type=type,
        detail=detail,
        reported_by=user_id,
        reported_at=datetime.now(timezone.utc)
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident

def get_incidents(
    db: Session,
    depot_id: str,
    vehicle_id: str = None,
    trip_id: str = None,
    type: str = None,
    unresolved_only: bool = False
):
    query = db.query(VehicleIncident).join(Vehicle, VehicleIncident.vehicle_id == Vehicle.vehicle_id)
    query = query.filter(Vehicle.depot_id == depot_id)

    if vehicle_id:
        query = query.filter(VehicleIncident.vehicle_id == vehicle_id)
    if trip_id:
        query = query.filter(VehicleIncident.trip_id == trip_id)
    if type:
        query = query.filter(VehicleIncident.type == type)
    if unresolved_only:
        query = query.filter(VehicleIncident.resolved_at == None)

    return query.all()

def get_incident(db: Session, depot_id: str, incident_id: str):
    query = db.query(VehicleIncident).join(Vehicle, VehicleIncident.vehicle_id == Vehicle.vehicle_id)
    query = query.filter(VehicleIncident.incident_id == incident_id, Vehicle.depot_id == depot_id)
    incident = query.first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found or out of scope")
    return incident

def resolve_incident(db: Session, depot_id: str, incident_id: str, resolution_note: str):
    incident = get_incident(db, depot_id, incident_id)
    
    if incident.resolved_at is not None:
        raise HTTPException(status_code=409, detail="Incident already resolved")
        
    incident.resolved_at = datetime.now(timezone.utc)
    # The schema doesn't have a resolution_note field directly on VehicleIncident.
    # It only has resolved_at. If we want to record the note, we might append it to `detail`
    # or just omit it if the schema doesn't support it.
    if resolution_note:
        incident.detail = f"{incident.detail} | Resolution: {resolution_note}"
        
    db.commit()
    db.refresh(incident)
    return incident
