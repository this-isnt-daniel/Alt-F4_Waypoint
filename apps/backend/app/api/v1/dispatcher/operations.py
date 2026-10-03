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
    driver_id: str
    trip_id: Optional[str]
    stop_id: Optional[str]
    kind: str
    occurred_at: Optional[datetime]
    received_at: datetime
    applied_at: Optional[datetime]
    status: str
    row_version_before: Optional[int]
    row_version_after: Optional[int]
    error: Optional[str]
    payload: Optional[str]
    
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
    query = query.filter(Trip.status.in_(["planned", "loaded", "out_for_delivery"]))
    
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
        
    query = query.order_by(DriverEvent.received_at.desc()).limit(limit)
    return query.all()


class AssignDriverRequest(BaseModel):
    driver_id: str


class AssignDriverResponse(BaseModel):
    trip_id: str
    driver_id: str
    trip_no: int
    trip_date: date
    status: str


@router.post("/trips/{trip_id}/assign-driver", response_model=AssignDriverResponse)
def assign_driver(
    trip_id: str,
    request: AssignDriverRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign (or reassign) the driver who owns this trip in the Driver app.
    Allowed until the trip departs; the driver must belong to the trip's depot.
    """
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).with_for_update().first()
    if not trip or trip.depot_id != current_user.depot_id:
        raise HTTPException(status_code=404, detail="Trip not found in your depot")
    if trip.status not in ("planned", "loaded"):
        raise HTTPException(status_code=400, detail=f"Cannot reassign a trip that is '{trip.status}'")

    driver = db.query(User).filter(User.user_id == request.driver_id, User.role == "driver").first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if driver.depot_id and driver.depot_id != trip.depot_id:
        raise HTTPException(status_code=400, detail="Driver belongs to a different depot")

    clash = db.query(Trip).filter(
        Trip.driver_id == driver.user_id,
        Trip.trip_date == trip.trip_date,
        Trip.trip_no == trip.trip_no,
        Trip.trip_id != trip.trip_id,
    ).first()
    if clash:
        raise HTTPException(
            status_code=409,
            detail=f"Driver already has trip {trip.trip_no} on {trip.trip_date} ({clash.trip_id})",
        )

    trip.driver_id = driver.user_id
    db.commit()
    return AssignDriverResponse(
        trip_id=trip.trip_id, driver_id=driver.user_id, trip_no=trip.trip_no,
        trip_date=trip.trip_date, status=trip.status,
    )
