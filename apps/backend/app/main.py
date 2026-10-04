import sys
from pathlib import Path

# Guarantee optimization_engine src is discoverable
_opt_src = str(Path(__file__).resolve().parent.parent / "optimization_engine" / "src")
if _opt_src not in sys.path:
    sys.path.insert(0, _opt_src)

import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.dispatcher.router import router as disp_router
from app.api.v1.driver.router import router as pd_router
from app.api.v1.endpoints import platform_auth
from app.api.v1.loader.router import router as loader_router
from app.api.v1.orders.router import router as orders_router
from app.api.v1.store_manager.router import router as sm_router
from app.api.v1.vehicles.router import router as vehicles_router
from app.config import CORS_ORIGINS
from app.db.session import get_db
from app.models.order import Order, OrderLine
from app.schemas.order import CreateOrderRequest, OrderResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import engine
    from sqlalchemy import text
    try:
        # Verify PostgreSQL connection availability
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        raise RuntimeError("PostgreSQL database is required but unavailable.") from e
    yield


app = FastAPI(
    title="Waypoint Driver API",
    version="1.0.0",
    description="Driver backend: frozen route-snapshot provider + append-only event ledger + offline sync/conflict API",
    lifespan=lifespan,
)


@app.exception_handler(IntegrityError)
async def sqlalchemy_integrity_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "Resource conflict or duplicate operation"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(platform_auth.router, prefix="/api/v1/auth", tags=["Platform Auth"])
app.include_router(sm_router, prefix="/api/v1/store-manager", tags=["Store Manager"])
app.include_router(disp_router, prefix="/api/v1/dispatcher", tags=["Dispatcher"])
app.include_router(disp_router, prefix="/dispatcher", tags=["Dispatcher Direct"])
app.include_router(vehicles_router, prefix="/api/v1/vehicles", tags=["Vehicles"])
app.include_router(pd_router, prefix="/api/v1/driver-platform", tags=["Platform Driver"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["Shared Orders"])
from app.api.v1.chat.router import router as chat_router
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat & Driver Communication"])





@app.get("/")
def root():
    return {"message": "Waypoint Platform API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
