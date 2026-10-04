from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User

from app.services.dispatcher.recovery_service import (
    build_recovery_proposal,
    get_recovery_proposal,
    approve_recovery_proposal,
    reject_recovery_proposal
)

router = APIRouter(tags=["Dispatcher Recovery"])
dispatcher_role = RoleChecker("dispatcher")

class RecoveryProposalResponse(BaseModel):
    plan_id: str
    status: str
    plan_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RecoveryRejectRequest(BaseModel):
    reason: str

@router.post("/incidents/{incident_id}/proposal", response_model=RecoveryProposalResponse, dependencies=[Depends(dispatcher_role)])
def create_recovery_proposal_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a recovery proposal for a given vehicle incident.
    Does NOT mutate the active trip.
    """
    return build_recovery_proposal(db, current_user.depot_id, current_user.user_id, incident_id)

@router.get("/proposals/{proposal_id}", response_model=RecoveryProposalResponse, dependencies=[Depends(dispatcher_role)])
def get_recovery_proposal_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get an existing recovery proposal.
    """
    return get_recovery_proposal(db, current_user.depot_id, proposal_id)

@router.post("/proposals/{proposal_id}/approve", response_model=RecoveryProposalResponse, dependencies=[Depends(dispatcher_role)])
def approve_recovery_proposal_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve a recovery proposal.
    Mutates the active trips, updates vehicle status, and issues RouteChanges to drivers.
    """
    return approve_recovery_proposal(db, current_user.depot_id, current_user.user_id, proposal_id)

@router.post("/proposals/{proposal_id}/reject", response_model=RecoveryProposalResponse, dependencies=[Depends(dispatcher_role)])
def reject_recovery_proposal_endpoint(
    proposal_id: str,
    request: RecoveryRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject a recovery proposal.
    Does NOT mutate the active trips.
    """
    return reject_recovery_proposal(db, current_user.depot_id, current_user.user_id, proposal_id, request.reason)
