from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.trip import Trip
from app.schemas.shared import TripResponse
from app.schemas.loader import SubmitLoadCheckRequest
from app.services import loader_service

router = APIRouter()
loader_role = RoleChecker("loader")

@router.get("/trips", response_model=List[TripResponse], dependencies=[Depends(loader_role)])
def get_trips(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Trip).filter(Trip.depot_id == current_user.depot_id, Trip.status == "planned").all()

@router.get("/trips/{trip_id}", response_model=TripResponse, dependencies=[Depends(loader_role)])
def get_trip(trip_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.depot_id != current_user.depot_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return trip

@router.post("/trips/{trip_id}/load", dependencies=[Depends(loader_role)])
def submit_load(trip_id: str, request: SubmitLoadCheckRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check = loader_service.submit_load_check(db, trip_id, request, current_user.depot_id, current_user.user_id)
    return {"status": "success", "check_id": check.check_id}
