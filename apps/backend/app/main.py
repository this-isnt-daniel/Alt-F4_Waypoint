import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.schemas.order import CreateOrderRequest, OrderResponse
from app.db.session import get_db
from app.models.order import Order, OrderLine

from app.api.v1.router import api_router
from app.config import CORS_ORIGINS
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from app.db.base import Base
    from app.db.session import engine
    import app.models  # noqa
    Base.metadata.create_all(bind=engine)
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
        content={"detail": "Resource conflict or duplicate operation", "error": str(exc.orig)}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.endpoints import platform_auth
from app.api.v1.store_manager.router import router as sm_router
from app.api.v1.dispatcher.router import router as disp_router
from app.api.v1.loader.router import router as loader_router
from app.api.v1.driver.router import router as pd_router
from app.api.v1.orders.router import router as orders_router
from app.api.v1.plans.router import router as plans_router
from app.api.v1.vehicles.router import router as vehicles_router

app.include_router(platform_auth.router, prefix="/api/v1/auth", tags=["Platform Auth"])
app.include_router(sm_router, prefix="/api/v1/store-manager", tags=["Store Manager"])
app.include_router(disp_router, prefix="/api/v1/dispatcher", tags=["Dispatcher"])
app.include_router(disp_router, prefix="/dispatcher", tags=["Dispatcher Direct"])
app.include_router(plans_router, prefix="/api/v1/plans", tags=["Plans"])
app.include_router(vehicles_router, prefix="/api/v1/vehicles", tags=["Vehicles"])
app.include_router(loader_router, prefix="/api/v1/loader", tags=["Loader"])
app.include_router(pd_router, prefix="/api/v1/driver-platform", tags=["Platform Driver"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["Shared Orders"])

app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Waypoint Platform API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/demo/orders")
def demo_create_order(order: CreateOrderRequest, db: Session = Depends(get_db)):
    db_order = Order(
        order_id=str(uuid.uuid4()),
        outlet_id=order.outlet_id,
        brand=order.brand.value if hasattr(order.brand, "value") else str(order.brand),
        temp_req=order.temp_req.value if hasattr(order.temp_req, "value") else str(order.temp_req),
        order_date=order.order_date,
        created_by="system",
        status="draft",
        order_units=sum(item.quantity for item in order.items),
    )
    db.add(db_order)
    db.commit()
    return order