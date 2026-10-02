from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.store_manager import CreateOrderRequest, ConfirmReceiptRequest
from app.schemas.shared import OrderResponse
from app.services import order_service

router = APIRouter()

# Enforce Store Manager Role for all routes
store_manager_role = RoleChecker("store_manager")

@router.post("/orders", response_model=OrderResponse, dependencies=[Depends(store_manager_role)])
def create_order(request: CreateOrderRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(f"DEBUG: username={current_user.username}, role={current_user.role}, outlet={current_user.outlet_id}")
    return order_service.create_or_update_draft_order(db, request, current_user.outlet_id, current_user.user_id)

@router.post("/orders/{order_id}/confirm", response_model=OrderResponse, dependencies=[Depends(store_manager_role)])
def confirm_order(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return order_service.confirm_order(db, order_id, current_user.outlet_id)

@router.get("/orders/{order_id}", response_model=OrderResponse, dependencies=[Depends(store_manager_role)])
def get_order(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.order import Order
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.outlet_id != current_user.outlet_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return order

@router.post("/orders/{order_id}/receipt", dependencies=[Depends(store_manager_role)])
def confirm_receipt(order_id: str, request: ConfirmReceiptRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    receipt = order_service.confirm_receipt(db, order_id, request, current_user.outlet_id, current_user.user_id)
    return {"status": "success", "confirm_id": receipt.confirm_id}
