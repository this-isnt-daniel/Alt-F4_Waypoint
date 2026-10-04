from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.store_manager import (
    CreateOrderRequest,
    UpdateOrderRequest,
    ConfirmReceiptRequest,
    ProductResponse,
    OutletDetailResponse,
    DeferralResponse,
    OrderETAResponse
)
from app.schemas.shared import OrderResponse
from app.schemas.urgency import CreateUrgencyRequest, UrgencyRequestResponse
from app.services import order_service, urgency_service

router = APIRouter()

# Enforce Store Manager Role for all routes
store_manager_role = RoleChecker("store_manager")


@router.post("/orders", response_model=OrderResponse, dependencies=[Depends(store_manager_role)])
def create_order(
    request: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new draft order or replace items for existing draft order for current store manager's outlet."""
    return order_service.create_or_update_draft_order(db, request, current_user.outlet_id, current_user.user_id)


@router.get("/orders", response_model=List[OrderResponse], dependencies=[Depends(store_manager_role)])
def list_orders(
    status: Optional[str] = Query(None, description="Filter by order status (draft, confirmed, planned, loaded, out_for_delivery, delivered, deferred)"),
    order_date: Optional[str] = Query(None, description="Filter by order date (YYYY-MM-DD)"),
    brand: Optional[str] = Query(None, description="Filter by brand (fresh, style, tech)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all orders belonging to current store manager's outlet."""
    return order_service.get_store_manager_orders(
        db,
        outlet_id=current_user.outlet_id,
        status_filter=status,
        order_date_filter=order_date,
        brand_filter=brand
    )


@router.get("/orders/{order_id}", response_model=OrderResponse, dependencies=[Depends(store_manager_role)])
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single order details for store manager's outlet."""
    return order_service.get_store_manager_order(db, order_id, current_user.outlet_id)


@router.put("/orders/{order_id}", response_model=OrderResponse, dependencies=[Depends(store_manager_role)])
def update_draft_order(
    order_id: str,
    request: UpdateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update item quantities for a draft order before confirmation."""
    return order_service.update_draft_order(db, order_id, request, current_user.outlet_id)


@router.delete("/orders/{order_id}", dependencies=[Depends(store_manager_role)])
def cancel_draft_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel/delete a draft order before confirmation."""
    return order_service.cancel_draft_order(db, order_id, current_user.outlet_id)


@router.post("/orders/{order_id}/confirm", response_model=OrderResponse, dependencies=[Depends(store_manager_role)])
def confirm_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm draft order, calculating totals and moving status to confirmed."""
    return order_service.confirm_order(db, order_id, current_user.outlet_id, user_id=current_user.user_id)


@router.post("/orders/{order_id}/receipt", dependencies=[Depends(store_manager_role)])
def confirm_receipt(
    order_id: str,
    request: ConfirmReceiptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm physical receipt of delivered order and record proof of delivery/discrepancies."""
    receipt = order_service.confirm_receipt(db, order_id, request, current_user.outlet_id, current_user.user_id)
    return {"status": "success", "confirm_id": receipt.confirm_id}


@router.get("/products", response_model=List[ProductResponse], dependencies=[Depends(store_manager_role)])
def list_products(
    brand: Optional[str] = Query(None, description="Filter products by brand"),
    temp_req: Optional[str] = Query(None, description="Filter products by temperature requirement"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active catalog products available for ordering."""
    return order_service.get_store_manager_products(db, brand_filter=brand, temp_req_filter=temp_req)


@router.get("/outlet", response_model=OutletDetailResponse, dependencies=[Depends(store_manager_role)])
def get_outlet_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current store manager's outlet information."""
    return order_service.get_store_manager_outlet(db, current_user.outlet_id)


@router.get("/deferrals", response_model=List[DeferralResponse], dependencies=[Depends(store_manager_role)])
def list_deferrals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List deferred orders and deferral notices for store manager's outlet."""
    return order_service.get_store_manager_deferrals(db, current_user.outlet_id)


@router.get("/orders/{order_id}/eta", response_model=OrderETAResponse, dependencies=[Depends(store_manager_role)])
def get_order_eta(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get live tracking and estimated arrival time (ETA) for an order."""
    return order_service.get_order_eta(db, order_id, current_user.outlet_id)


@router.post("/orders/{order_id}/urgency-request", response_model=UrgencyRequestResponse, status_code=201, dependencies=[Depends(store_manager_role)])
def request_order_urgency(
    order_id: str,
    request: CreateUrgencyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit business urgency request for an existing confirmed or deferred order."""
    return urgency_service.create_order_urgency_request(
        db=db,
        order_id=order_id,
        request=request,
        store_manager_outlet=current_user.outlet_id,
        user_id=current_user.user_id,
    )


@router.get("/orders/{order_id}/urgency-request", response_model=UrgencyRequestResponse, dependencies=[Depends(store_manager_role)])
def get_order_urgency(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current urgency request for an order."""
    return urgency_service.get_order_urgency_request(
        db=db,
        order_id=order_id,
        store_manager_outlet=current_user.outlet_id,
    )


