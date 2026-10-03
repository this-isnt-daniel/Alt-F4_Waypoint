from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.trip import Trip, TripStop
from app.models.events import DriverEvent, DeliveryEvent
from app.schemas.shared import TripResponse, TripStopResponse
from pydantic import BaseModel, ConfigDict

# Local schemas for this phase to avoid modifying shared files unnecessarily
class VehicleOperationalResponse(BaseModel):
    vehicle_id: str
    depot_id: str
    type: str
    temp: str
    status: str
    last_lat: Optional[float] = None
    last_lng: Optional[float] = None
    last_seen_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class DriverEventResponse(BaseModel):
    event_id: str
    client_event_id: str
    trip_id: str
    stop_id: Optional[str]
    type: str
    occurred_at: datetime
    received_at: datetime
    sync_status: str
    payload: str
    
    model_config = ConfigDict(from_attributes=True)

dispatcher_role = RoleChecker("dispatcher")
router = APIRouter(dependencies=[Depends(dispatcher_role)])

@router.get("/vehicles", response_model=List[VehicleOperationalResponse])
def get_fleet_visibility(
    depot_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fleet Visibility: Get all vehicles, their current status, and last known location.
    """
    query = db.query(Vehicle)
    if depot_id:
        query = query.filter(Vehicle.depot_id == depot_id)
    else:
        # Default to dispatcher's depot
        if current_user.depot_id:
            query = query.filter(Vehicle.depot_id == current_user.depot_id)
            
    if status:
        query = query.filter(Vehicle.status == status)
        
    return query.all()

@router.get("/trips/active", response_model=List[TripResponse])
def get_active_trips(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Active Trip Views: Get all trips currently in progress or planned for today.
    """
    query = db.query(Trip)
    if current_user.depot_id:
        query = query.filter(Trip.depot_id == current_user.depot_id)
        
    if target_date:
        query = query.filter(Trip.trip_date == target_date)
    else:
        query = query.filter(Trip.trip_date == date.today())
        
    # We want active or planned trips
    query = query.filter(Trip.status.in_(["planned", "departed", "in_progress"]))
    
    return query.all()

@router.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip_details(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed view of a specific trip including all stops.
    """
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    stops = db.query(TripStop).filter(TripStop.trip_id == trip_id).order_by(TripStop.stop_seq).all()
    
    from app.models.trip import TripStopItem
    for stop in stops:
        items = db.query(TripStopItem).filter(TripStopItem.stop_id == stop.stop_id).all()
        setattr(stop, 'items', items)
        
    setattr(trip, 'stops', stops)
    return trip

@router.get("/timeline", response_model=List[DriverEventResponse])
def get_shared_timeline(
    trip_id: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Shared timeline aggregation: Get recent driver/delivery events for operational monitoring.
    """
    query = db.query(DriverEvent)
    
    if trip_id:
        query = query.filter(DriverEvent.trip_id == trip_id)
    elif vehicle_id:
        query = query.join(Trip, DriverEvent.trip_id == Trip.trip_id).filter(Trip.vehicle_id == vehicle_id)
        
    query = query.order_by(DriverEvent.occurred_at.desc()).limit(limit)
    return query.all()
