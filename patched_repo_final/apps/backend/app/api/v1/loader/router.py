from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import RoleChecker, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.loader import (
    LoadItem,
    LoaderActionResponse,
    LoaderDeferralResponse,
    LoaderQueueTrip,
    LoaderWorkbench,
    SaveLoadItemRequest,
    SubmitLoadCheckRequest,
    VehicleUnavailableRequest,
)
from app.services import loader_service


router = APIRouter()
loader_role = RoleChecker("loader")


def _loader_depot(current_user: User) -> str:
    if not current_user.depot_id:
        raise HTTPException(status_code=400, detail="Loader user is not assigned to a depot")
    return current_user.depot_id


@router.get("/queue", response_model=List[LoaderQueueTrip], dependencies=[Depends(loader_role)])
def get_queue(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return loader_service.get_loader_queue(db, _loader_depot(current_user))


@router.get("/trips", response_model=List[LoaderQueueTrip], dependencies=[Depends(loader_role)])
def get_trips(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Backward-compatible alias for the first loader screen.
    return loader_service.get_loader_queue(db, _loader_depot(current_user))


@router.get("/trips/{trip_id}/workbench", response_model=LoaderWorkbench, dependencies=[Depends(loader_role)])
def get_trip_workbench(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return loader_service.get_workbench(db, trip_id, _loader_depot(current_user))


@router.get("/trips/{trip_id}", response_model=LoaderWorkbench, dependencies=[Depends(loader_role)])
def get_trip(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Backward-compatible detail route with the richer loader workbench payload.
    return loader_service.get_workbench(db, trip_id, _loader_depot(current_user))


@router.post("/trips/{trip_id}/start", response_model=LoaderActionResponse, dependencies=[Depends(loader_role)])
def start_loading(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check = loader_service.start_loading(db, trip_id, _loader_depot(current_user), current_user.user_id)
    return LoaderActionResponse(status="success", trip_id=trip_id, check_id=check.check_id)


@router.patch(
    "/trips/{trip_id}/items/{line_item_id}",
    response_model=LoadItem,
    dependencies=[Depends(loader_role)],
)
def save_load_item(
    trip_id: str,
    line_item_id: str,
    request: SaveLoadItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return loader_service.save_load_item(
        db,
        trip_id,
        line_item_id,
        request,
        _loader_depot(current_user),
        current_user.user_id,
    )


@router.post(
    "/trips/{trip_id}/complete-stop/{stop_id}",
    response_model=LoaderActionResponse,
    dependencies=[Depends(loader_role)],
)
def complete_stop(
    trip_id: str,
    stop_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stop = loader_service.complete_stop(db, trip_id, stop_id, _loader_depot(current_user), current_user.user_id)
    return LoaderActionResponse(status="success", trip_id=trip_id, stop_id=stop.stop_id)


@router.post("/trips/{trip_id}/load", response_model=LoaderActionResponse, dependencies=[Depends(loader_role)])
def submit_load(
    trip_id: str,
    request: SubmitLoadCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check = loader_service.submit_load_check(
        db,
        trip_id,
        request,
        _loader_depot(current_user),
        current_user.user_id,
    )
    return LoaderActionResponse(status="success", trip_id=trip_id, check_id=check.check_id)


@router.post(
    "/trips/{trip_id}/vehicle-unavailable",
    response_model=LoaderActionResponse,
    dependencies=[Depends(loader_role)],
)
def mark_vehicle_unavailable(
    trip_id: str,
    request: VehicleUnavailableRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trip = loader_service.mark_vehicle_unavailable(
        db,
        trip_id,
        request,
        _loader_depot(current_user),
        current_user.user_id,
    )
    return LoaderActionResponse(
        status="success",
        trip_id=trip.trip_id,
        message="Vehicle marked unavailable and orders returned for dispatcher review",
    )


@router.get("/deferrals", response_model=List[LoaderDeferralResponse], dependencies=[Depends(loader_role)])
def get_deferrals(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return loader_service.get_deferrals(db, _loader_depot(current_user))
