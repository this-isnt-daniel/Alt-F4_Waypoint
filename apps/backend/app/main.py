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
    yield

app = FastAPI(
    title="Waypoint Driver API",
    version="1.0.0",
    description="Driver backend: frozen route-snapshot provider + append-only event ledger + offline sync/conflict API",
    lifespan=lifespan,
)

@app.exception_handler(IntegrityError)
async def sqlalchemy_integrity_handler(request: Request, exc: IntegrityError):
    # This translates DB unique/foreign-key violations to 409 Conflict
    return JSONResponse(
        status_code=409,
        content={"detail": "Resource conflict or duplicate operation"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.endpoints import platform_auth

app.include_router(platform_auth.router, prefix="/api/v1/auth", tags=["Platform Auth"])
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Waypoint Driver API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/demo/orders", response_model=OrderResponse)
def demo_create_order(request: CreateOrderRequest, db: Session = Depends(get_db)):
    # 1. Create the Order
    new_order = Order(
        order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        outlet_id=request.outlet_id,
        created_by="system", # Hardcoded for demo until Auth is integrated
        brand=request.brand,
        temp_req=request.temp_req,
        order_date=request.order_date,
        status="draft",
        submitted_at=datetime.now(timezone.utc)
    )
    
    db.add(new_order)
    
    # 2. Create the OrderLines
    created_lines = []
    for item in request.items:
        line = OrderLine(
            line_item_id=f"LI-{uuid.uuid4().hex[:8].upper()}",
            order_id=new_order.order_id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(line)
        created_lines.append(line)
        
    # 3. Save to Database
    db.commit()
    db.refresh(new_order)
        
    new_order.items = created_lines
    return new_order