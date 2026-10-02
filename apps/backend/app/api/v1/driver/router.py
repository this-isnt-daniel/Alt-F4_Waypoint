from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.trip import Trip
from app.schemas.shared import TripResponse
from app.schemas.driver import ProofOfDeliveryRequest, SyncDriverEventsRequest, DepartTripRequest
from app.services import delivery_service

router = APIRouter()
driver_role = RoleChecker("driver")

@router.get("/trips/today", response_model=List[TripResponse], dependencies=[Depends(driver_role)])
def get_today_trips(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # In a real app we'd filter by user's assigned vehicle trips.
    return db.query(Trip).all()

@router.get("/trips/{trip_id}", response_model=TripResponse, dependencies=[Depends(driver_role)])
def get_trip(trip_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.post("/trips/{trip_id}/depart", dependencies=[Depends(driver_role)])
def depart_trip(trip_id: str, request: DepartTripRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    delivery_service.depart_trip(db, trip_id, request, current_user.user_id)
    return {"status": "success"}

@router.post("/stops/{stop_id}/pod", dependencies=[Depends(driver_role)])
def submit_pod(stop_id: str, request: ProofOfDeliveryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pod = delivery_service.submit_pod(db, stop_id, request, current_user.user_id)
    return {"status": "success", "pod_id": pod.pod_id}

@router.post("/events/sync", dependencies=[Depends(driver_role)])
def sync_events(request: SyncDriverEventsRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = delivery_service.sync_events(db, request, current_user.user_id)
    return {"status": "success", "results": results}
