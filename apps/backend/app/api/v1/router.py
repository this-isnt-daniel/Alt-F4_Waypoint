"""V1 API Router assembling all driver modules."""

from fastapi import APIRouter, Depends
import sqlite3

from app.api.v1.endpoints import auth, trips, departure, stops, returns, sync, changes, conflicts, chat
from app.models.schemas import DriverProfile
from app.middleware.auth_middleware import get_current_driver
from app.database import get_db

api_router = APIRouter()

# Module A: Driver Auth
api_router.include_router(auth.router, prefix="/driver/auth", tags=["Driver Auth"])

# Explicitly mount /driver/me for convenience per spec: GET /api/driver/me
@api_router.get("/driver/me", response_model=DriverProfile, tags=["Driver Auth"])
def get_driver_me(payload: dict = Depends(get_current_driver), db: sqlite3.Connection = Depends(get_db)):
    return auth.me(payload=payload, db=db)

# Module B: Trips & Route Snapshot
api_router.include_router(trips.router, prefix="/driver/trips", tags=["Driver Trips"])

# Module C: Departure & Load Confirmation
api_router.include_router(departure.router, prefix="/driver/trips", tags=["Driver Departure"])

# Module D: Stop Lifecycle Events
api_router.include_router(stops.router, prefix="/driver/stops", tags=["Driver Stops"])

# Module D (cont.): Depot Returns Confirmation
api_router.include_router(returns.router, prefix="/driver/returns", tags=["Driver Returns"])

# Module E: Offline Sync Engine
api_router.include_router(sync.router, prefix="/driver/sync", tags=["Driver Sync"])

# Module F: Dispatcher Deltas (GET /api/driver/changes, POST /api/driver/changes/{id}/ack)
api_router.include_router(changes.router, prefix="/driver", tags=["Driver Changes"])

# Conflicts: In-review conflict forward API
api_router.include_router(conflicts.router, prefix="/driver/conflicts", tags=["Driver Conflicts"])

# Module G: Chat & Call Intent (GET/POST /api/driver/stops/{id}/messages, POST /api/driver/stops/{id}/call-intent)
api_router.include_router(chat.router, prefix="/driver", tags=["Driver Chat & Call"])
