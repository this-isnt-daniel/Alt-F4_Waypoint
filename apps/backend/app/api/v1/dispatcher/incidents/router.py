from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.services.dispatcher.incident_service import (
    create_incident, get_incidents, get_incident, resolve_incident
)

router = APIRouter(tags=["Dispatcher Incidents"])
dispatcher_role = RoleChecker("dispatcher")

# Schemas
class IncidentCreateRequest(BaseModel):
    incident_id: Optional[str] = None
    vehicle_id: str
    trip_id: Optional[str] = None
    type: str # breakdown, pre_trip_failure, reefer_failure, other
    detail: str

class IncidentResolveRequest(BaseModel):
    resolution_note: Optional[str] = None

class IncidentResponse(BaseModel):
    incident_id: str
    vehicle_id: str
    trip_id: Optional[str]
    type: str
    detail: str
    reported_by: str
    reported_at: datetime
    resolved_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

@router.post("", response_model=IncidentResponse, dependencies=[Depends(dispatcher_role)])
def create_new_incident(
    request: IncidentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incident_id = request.incident_id or str(uuid.uuid4())
    incident = create_incident(
        db=db,
        depot_id=current_user.depot_id,
        user_id=current_user.user_id,
        incident_id=incident_id,
        vehicle_id=request.vehicle_id,
        type=request.type,
        detail=request.detail,
        trip_id=request.trip_id
    )
    return incident

@router.get("", response_model=List[IncidentResponse], dependencies=[Depends(dispatcher_role)])
def list_incidents(
    vehicle_id: Optional[str] = Query(None),
    trip_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    unresolved_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_incidents(
        db=db,
        depot_id=current_user.depot_id,
        vehicle_id=vehicle_id,
        trip_id=trip_id,
        type=type,
        unresolved_only=unresolved_only
    )

@router.get("/{incident_id}", response_model=IncidentResponse, dependencies=[Depends(dispatcher_role)])
def retrieve_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_incident(db, current_user.depot_id, incident_id)

@router.post("/{incident_id}/resolve", response_model=IncidentResponse, dependencies=[Depends(dispatcher_role)])
def mark_incident_resolved(
    incident_id: str,
    request: IncidentResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return resolve_incident(
        db=db, 
        depot_id=current_user.depot_id, 
        incident_id=incident_id, 
        resolution_note=request.resolution_note
    )
