from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict
import json

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.services.dispatcher.route_change_service import (
    create_route_change, get_route_changes
)

router = APIRouter(tags=["Dispatcher Route Changes"])
dispatcher_role = RoleChecker("dispatcher")

class RouteChangeCreateRequest(BaseModel):
    change_id: Optional[str] = None
    change_type: str # route.resequenced, stop.added, stop.cancelled
    payload: Dict[str, Any]

class RouteChangeResponse(BaseModel):
    change_id: str
    trip_id: str
    change_type: str
    payload: Dict[str, Any]
    issued_at: datetime
    issued_by: str
    acknowledged: bool
    ack_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: Any) -> "RouteChangeResponse":
        # Need to parse payload string to dict
        dict_obj = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        if isinstance(dict_obj.get("payload"), str):
            try:
                dict_obj["payload"] = json.loads(dict_obj["payload"])
            except json.JSONDecodeError:
                dict_obj["payload"] = {}
        return cls(**dict_obj)

@router.post("/trips/{trip_id}/route-changes", response_model=RouteChangeResponse, dependencies=[Depends(dispatcher_role)])
def issue_route_change(
    trip_id: str,
    request: RouteChangeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rc = create_route_change(
        db=db,
        depot_id=current_user.depot_id,
        user_id=current_user.user_id,
        trip_id=trip_id,
        change_type=request.change_type,
        payload=request.payload,
        change_id=request.change_id
    )
    return RouteChangeResponse.from_orm(rc)

@router.get("/trips/{trip_id}/route-changes", response_model=List[RouteChangeResponse], dependencies=[Depends(dispatcher_role)])
def list_route_changes(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    changes = get_route_changes(db, current_user.depot_id, trip_id)
    return [RouteChangeResponse.from_orm(c) for c in changes]
