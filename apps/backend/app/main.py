import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        db.commit()
        db.refresh(new_order)
    except IntegrityError as e:
        db.rollback()
        # Catch DB constraint violations (like UniqueConstraint on outlet/date/temp)
        raise HTTPException(status_code=400, detail="Database integrity error (Possible duplicate order or missing foreign keys)")
        
    new_order.items = created_lines
    return new_order