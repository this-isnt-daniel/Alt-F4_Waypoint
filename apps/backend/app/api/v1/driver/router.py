"""Canonical Driver API (shared PostgreSQL schema), mounted at /api/v1/driver-platform.

Every route authenticates with the shared platform JWT and requires role=driver, except
conflict resolution, which is the Dispatcher's side of the conflict workflow.
Writes return 200 for applied / already_applied and 409 (same body) for a row_version conflict.
"""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import RoleChecker
from app.db.session import get_db
from app.models.user import User
from app.schemas import driver as s
from app.services import driver_service
from app.services.driver_service import DriverActionError

router = APIRouter()
driver_role = RoleChecker("driver")
dispatcher_role = RoleChecker("dispatcher")


def _run(db: Session, driver: User, kind: str, target_id: str, request, client_event_id: str, occurred_at=None):
    try:
        result = driver_service.run_event(
            db, driver, kind, target_id, request, client_event_id,
            occurred_at=occurred_at, device_id=getattr(request, "device_id", None),
        )
    except DriverActionError as err:
        raise HTTPException(status_code=err.status_code, detail=err.detail)
    if result.status == "conflict":
        return JSONResponse(status_code=409, content=result.model_dump(mode="json"))
    return result


# ── Trips ────────────────────────────────────────────────────────────────

@router.get("/trips/today", response_model=s.TodayTripsResponse)
def get_today_trips(
    on_date: Optional[date] = Query(None, alias="date", description="Defaults to today in Asia/Colombo"),
    db: Session = Depends(get_db),
    driver: User = Depends(driver_role),
):
    return driver_service.get_today_trips(db, driver, on_date)


@router.get("/trips/{trip_id}", response_model=s.TripDetailResponse)
def get_trip(trip_id: str, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return driver_service.get_trip_detail(db, driver, trip_id)


@router.post("/trips/{trip_id}/depart", response_model=s.DriverActionResponse,
             responses={409: {"model": s.DriverActionResponse}})
def depart_trip(trip_id: str, request: s.DepartRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return _run(db, driver, "trip.departed", trip_id, request, request.client_event_id, request.departed_at)


@router.post("/trips/{trip_id}/complete", response_model=s.DriverActionResponse,
             responses={409: {"model": s.DriverActionResponse}})
def complete_trip(trip_id: str, request: s.CompleteTripRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return _run(db, driver, "trip.completed", trip_id, request, request.client_event_id, request.returned_at)


# ── Stop lifecycle ───────────────────────────────────────────────────────

@router.post("/stops/{stop_id}/arrive", response_model=s.DriverActionResponse,
             responses={409: {"model": s.DriverActionResponse}})
def arrive(stop_id: str, request: s.ArriveRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return _run(db, driver, "stop.arrived", stop_id, request, request.client_event_id, request.arrived_at)


@router.post("/stops/{stop_id}/checklist", response_model=s.DriverActionResponse,
             responses={409: {"model": s.DriverActionResponse}})
def submit_checklist(stop_id: str, request: s.ChecklistRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return _run(db, driver, "checklist.submitted", stop_id, request, request.client_event_id)


@router.post("/stops/{stop_id}/pod/photo-intent", response_model=s.PhotoIntentResponse)
def pod_photo_intent(
    stop_id: str,
    request: Optional[s.PhotoIntentRequest] = None,
    db: Session = Depends(get_db),
    driver: User = Depends(driver_role),
):
    return driver_service.photo_intent(db, driver, stop_id, request or s.PhotoIntentRequest())


@router.post("/stops/{stop_id}/pod/photo-complete", response_model=s.DriverActionResponse,
             responses={409: {"model": s.DriverActionResponse}})
def pod_photo_complete(stop_id: str, request: s.PhotoCompleteRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return _run(db, driver, "pod.photo.completed", stop_id, request, request.client_event_id, request.captured_at)


@router.post("/stops/{stop_id}/pod", response_model=s.DriverActionResponse,
             responses={409: {"model": s.DriverActionResponse}})
def submit_pod(stop_id: str, request: s.PodRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    """Opens (or updates) the stop's proof of delivery. The response carries the OTP the
    Store Manager enters to confirm receipt."""
    return _run(db, driver, "pod.submitted", stop_id, request, request.client_event_id, request.delivered_at)


@router.post("/stops/{stop_id}/outcome", response_model=s.DriverActionResponse,
             responses={409: {"model": s.DriverActionResponse}})
def submit_outcome(stop_id: str, request: s.OutcomeRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return _run(db, driver, "stop.outcome.submitted", stop_id, request, request.client_event_id, request.finished_at)


@router.post("/stops/{stop_id}/return", response_model=s.DriverActionResponse,
             responses={409: {"model": s.DriverActionResponse}})
def submit_return(stop_id: str, request: s.ReturnRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return _run(db, driver, "return.created", stop_id, request, request.client_event_id)


@router.post("/returns/{return_id}/depot-confirm", response_model=s.DriverActionResponse,
             responses={409: {"model": s.DriverActionResponse}})
def depot_confirm(return_id: str, request: s.DepotConfirmRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return _run(db, driver, "depot_return.confirmed", return_id, request, request.client_event_id, request.confirmed_at)


# ── Offline sync ─────────────────────────────────────────────────────────

@router.post("/events/sync", response_model=s.SyncResponse)
def sync_events(request: s.SyncRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return driver_service.sync_events(db, driver, request)


class LocationPingRequest(s.BaseModel):
    lat: float
    lng: float
    vehicle_id: str

@router.post("/location")
def update_location(request: LocationPingRequest, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    """Update driver's current location to track the vehicle they are driving."""
    from app.models.vehicle import Vehicle
    from datetime import datetime, timezone
    
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == request.vehicle_id).first()
    if vehicle:
        vehicle.last_lat = request.lat
        vehicle.last_lng = request.lng
        vehicle.last_seen_at = datetime.now(timezone.utc)
        db.commit()
    return {"status": "ok"}


# ── Dispatcher route changes ─────────────────────────────────────────────

@router.get("/changes", response_model=s.ChangesResponse)
def get_changes(
    since: Optional[datetime] = Query(None, description="Return changes issued after this cursor"),
    pending_only: bool = Query(False),
    db: Session = Depends(get_db),
    driver: User = Depends(driver_role),
):
    return driver_service.get_changes(db, driver, since, pending_only)


@router.post("/changes/{change_id}/ack", response_model=s.DriverActionResponse)
def ack_change(
    change_id: str,
    request: Optional[s.AckChangeRequest] = None,
    db: Session = Depends(get_db),
    driver: User = Depends(driver_role),
):
    request = request or s.AckChangeRequest()
    client_event_id = request.client_event_id or f"ack:{driver.user_id}:{change_id}"
    return _run(db, driver, "route_change.acknowledged", change_id, request, client_event_id)


# ── Conflicts ────────────────────────────────────────────────────────────

@router.get("/conflicts", response_model=List[s.ConflictDTO])
def list_conflicts(db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    return driver_service.list_conflicts(db, driver)


@router.post("/conflicts/{conflict_id}/forward", response_model=s.ConflictDTO)
def forward_conflict(
    conflict_id: str,
    request: Optional[s.ForwardConflictRequest] = None,
    db: Session = Depends(get_db),
    driver: User = Depends(driver_role),
):
    return driver_service.forward_conflict(db, driver, conflict_id, request.note if request else None)


@router.post("/conflicts/{conflict_id}/resolve", response_model=s.ResolveConflictResponse)
def resolve_conflict(
    conflict_id: str,
    request: s.ResolveConflictRequest,
    db: Session = Depends(get_db),
    dispatcher: User = Depends(dispatcher_role),
):
    """Dispatcher resolves a driver sync conflict for a trip in their depot."""
    return driver_service.resolve_conflict(db, dispatcher, conflict_id, request)

from app.api.v1.driver.road_geometry import router as rg_router
router.include_router(rg_router, prefix="/road-geometry", tags=["Road Geometry"])


@router.post("/stops/{stop_id}/pod/photo-upload")
async def upload_pod_photo(stop_id: str, photo: UploadFile = File(...), db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    """Persist POD evidence on the mounted evidence volume and attach it to the server POD."""
    from pathlib import Path
    from app.models.delivery import ProofOfDelivery
    stop, _trip = driver_service._owned_stop(db, driver, stop_id)
    pod = driver_service._pod_for_stop(db, stop)
    if not pod:
        raise HTTPException(status_code=409, detail="Submit POD before uploading evidence")
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    suffix = allowed.get(photo.content_type or "")
    if not suffix:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG and WebP images are accepted")
    root = Path("/app/data/evidence") / stop_id
    root.mkdir(parents=True, exist_ok=True)
    filename = f"{pod.pod_id}-{uuid.uuid4().hex}{suffix}"
    path = root / filename
    data = await photo.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Photo exceeds 10 MB limit")
    path.write_bytes(data)
    pod.photo_url = f"/api/v1/driver-platform/stops/{stop_id}/pod/photo/{filename}"
    db.commit()
    return {"photo_url": pod.photo_url, "bytes": len(data)}

@router.get("/stops/{stop_id}/pod/photo/{filename}")
def get_pod_photo(stop_id: str, filename: str, db: Session = Depends(get_db), driver: User = Depends(driver_role)):
    from pathlib import Path
    from fastapi.responses import FileResponse
    stop, _trip = driver_service._owned_stop(db, driver, stop_id)
    pod = driver_service._pod_for_stop(db, stop)
    if not pod or not pod.photo_url or Path(filename).name != filename or not pod.photo_url.endswith(filename):
        raise HTTPException(status_code=404, detail="Evidence not found")
    path = Path("/app/data/evidence") / stop_id / filename
    if not path.is_file(): raise HTTPException(status_code=404, detail="Evidence not found")
    return FileResponse(path)
