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
from app.api.v1.plans.router import router as plans_router
from app.api.v1.router import api_router
from app.api.v1.store_manager.router import router as sm_router
from app.api.v1.vehicles.router import router as vehicles_router
from app.config import CORS_ORIGINS
from app.database import init_db
from app.db.session import get_db
from app.models.order import Order, OrderLine
from app.schemas.order import CreateOrderRequest, OrderResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from app.db.base import Base
    from app.db.session import engine
    import app.models  # noqa: F401

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
        content={"detail": "Resource conflict or duplicate operation", "error": str(exc.orig)},
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
app.include_router(plans_router, prefix="/api/v1/plans", tags=["Plans"])
app.include_router(vehicles_router, prefix="/api/v1/vehicles", tags=["Vehicles"])
app.include_router(loader_router, prefix="/api/v1/loader", tags=["Loader"])
app.include_router(pd_router, prefix="/api/v1/driver-platform", tags=["Platform Driver"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["Shared Orders"])

app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")


@app.post("/api/v1/demo/orders", response_model=OrderResponse)
def create_demo_order(request: CreateOrderRequest, db: Session = Depends(get_db)):
    """Small unauthenticated endpoint used by schema tests.

    The production store-manager route remains the real workflow endpoint. This
    demo route exercises request validation and the global IntegrityError-to-409
    handler without requiring a login in schema tests.
    """
    order_id = f"DEMO-{uuid.uuid4().hex[:8].upper()}"
    order = Order(
        order_id=order_id,
        outlet_id=request.outlet_id,
        created_by="demo",
        brand=request.brand,
        temp_req=request.temp_req,
        order_date=request.order_date,
        status="draft",
        order_units=sum(item.quantity for item in request.items),
        deferred_prev=False,
        defer_count=0,
    )
    db.add(order)
    for item in request.items:
        db.add(
            OrderLine(
                line_item_id=str(uuid.uuid4()),
                order_id=order_id,
                product_id=item.product_id,
                quantity=item.quantity,
            )
        )

    db.commit()
    db.refresh(order)
    lines = db.query(OrderLine).filter(OrderLine.order_id == order.order_id).all()
    return {
        "order_id": order.order_id,
        "outlet_id": order.outlet_id,
        "created_by": order.created_by,
        "brand": order.brand,
        "temp_req": order.temp_req,
        "order_date": order.order_date,
        "status": order.status,
        "order_units": order.order_units,
        "order_wt_kg": order.order_wt_kg,
        "order_vol_m3": order.order_vol_m3,
        "window_open": order.window_open,
        "window_close": order.window_close,
        "trip_id": order.trip_id,
        "stop_seq": order.stop_seq,
        "exp_arrival": order.exp_arrival,
        "actual_arrival": order.actual_arrival,
        "deferred_prev": order.deferred_prev,
        "defer_count": order.defer_count,
        "items": lines,
    }


@app.get("/")
def root():
    return {"message": "Waypoint Platform API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
