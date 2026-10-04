import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.urgency import UrgencyRequest
from app.models.order import Order
from app.models.outlet import Outlet
from app.schemas.urgency import (
    CreateUrgencyRequest,
    DispatcherUrgencyListItemResponse,
    UrgencyRequestStatus,
    UrgencyReason,
)


def create_order_urgency_request(
    db: Session,
    order_id: str,
    request: CreateUrgencyRequest,
    store_manager_outlet: str,
    user_id: str,
) -> UrgencyRequest:
    """
    Phase 3: Store Manager submits an urgency request for an existing order.
    Rules:
    - Order must exist and belong to the Store Manager's outlet.
    - Order status must be 'confirmed' or 'deferred'.
    - Statuses 'draft', 'planned', 'loaded', 'out_for_delivery', 'delivered' return 409.
    - Only one UrgencyRequest per order (UNIQUE constraint on order_id).
    - Idempotent on client_op_id retry.
    - Returns 409 if a request already exists for the order.
    - Status initialized to 'pending'.
    """
    # 1. Verify order exists
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    # 2. Verify outlet scope (foreign outlet blocked)
    if order.outlet_id != store_manager_outlet:
        raise HTTPException(
            status_code=403,
            detail="Store Manager can only request urgency for their own outlet",
        )

    # 3. Idempotency check via client_op_id
    if request.client_op_id:
        existing_by_op = (
            db.query(UrgencyRequest)
            .filter(UrgencyRequest.client_op_id == request.client_op_id)
            .first()
        )
        if existing_by_op:
            # Do NOT leak request owned by another outlet or user
            if existing_by_op.outlet_id != store_manager_outlet or existing_by_op.reported_by != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access or replay this operation",
                )
            # Different order_id -> 409 Conflict
            if existing_by_op.order_id != order_id:
                raise HTTPException(
                    status_code=409,
                    detail="client_op_id has already been used for a different order",
                )
            # Same client_op_id, same order_id, same Store Manager/outlet -> return existing request
            return existing_by_op

    # 4. Verify order eligibility: only 'confirmed' or 'deferred' permitted
    if order.status not in ("confirmed", "deferred"):
        raise HTTPException(
            status_code=409,
            detail=f"Urgency can only be requested for confirmed or deferred orders (current: {order.status})",
        )

    # 5. Check if an urgency request already exists for this order (different request blocked)
    existing_request = (
        db.query(UrgencyRequest).filter(UrgencyRequest.order_id == order_id).first()
    )
    if existing_request:
        raise HTTPException(
            status_code=409,
            detail="An urgency request already exists for this order",
        )

    # 6. Create new pending urgency request
    now = datetime.now(timezone.utc)
    reason_code_str = (
        request.reason_code.value
        if hasattr(request.reason_code, "value")
        else str(request.reason_code)
    )

    urgency = UrgencyRequest(
        urgency_request_id=f"URG-{uuid.uuid4().hex[:8].upper()}",
        order_id=order.order_id,
        outlet_id=order.outlet_id,
        reported_by=user_id,
        reason_code=reason_code_str,
        reason_text=request.reason_text,
        status="pending",
        reviewed_by=None,
        reviewed_at=None,
        decision_note=None,
        created_at=now,
        resolved_at=None,
        client_op_id=request.client_op_id,
    )
    db.add(urgency)
    try:
        db.commit()
        db.refresh(urgency)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An urgency request already exists for this order or duplicate operation",
        )

    return urgency


def get_order_urgency_request(
    db: Session,
    order_id: str,
    store_manager_outlet: str,
) -> UrgencyRequest:
    """
    Phase 3: Store Manager retrieves the urgency request for their order.
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    if order.outlet_id != store_manager_outlet:
        raise HTTPException(
            status_code=403,
            detail="Store Manager can only view urgency for their own outlet",
        )

    urgency = (
        db.query(UrgencyRequest).filter(UrgencyRequest.order_id == order_id).first()
    )
    if not urgency:
        raise HTTPException(
            status_code=404,
            detail="No urgency request found for this order",
        )

    return urgency


def list_dispatcher_urgency_requests(
    db: Session,
    depot_id: str,
    status_filter: Optional[str] = None,
) -> List[DispatcherUrgencyListItemResponse]:
    """
    Phase 4: Dispatcher lists urgency requests within their depot scope.
    """
    query = (
        db.query(UrgencyRequest, Order, Outlet)
        .join(Outlet, UrgencyRequest.outlet_id == Outlet.outlet_id)
        .join(Order, UrgencyRequest.order_id == Order.order_id)
        .filter(Outlet.depot_id == depot_id)
    )

    if status_filter:
        query = query.filter(UrgencyRequest.status == status_filter)

    query = query.order_by(UrgencyRequest.created_at.desc())
    rows = query.all()

    items = []
    for urg, order, outlet in rows:
        items.append(
            DispatcherUrgencyListItemResponse(
                urgency_request_id=urg.urgency_request_id,
                order_id=urg.order_id,
                outlet_id=urg.outlet_id,
                outlet_name=outlet.name if outlet else None,
                brand=order.brand if order else None,
                temp_req=order.temp_req if order else None,
                reported_by=urg.reported_by,
                reason_code=urg.reason_code,
                reason_text=urg.reason_text,
                status=urg.status,
                created_at=urg.created_at,
                reviewed_by=urg.reviewed_by,
                reviewed_at=urg.reviewed_at,
                decision_note=urg.decision_note,
                order_status=order.status if order else None,
                defer_count=order.defer_count if order else None,
                deferred_prev=order.deferred_prev if order else None,
                window_open=order.window_open if order else None,
                window_close=order.window_close if order else None,
                order_wt_kg=float(order.order_wt_kg) if order and order.order_wt_kg is not None else None,
                order_vol_m3=float(order.order_vol_m3) if order and order.order_vol_m3 is not None else None,
            )
        )
    return items


def approve_urgency_request(
    db: Session,
    urgency_request_id: str,
    dispatcher_depot: str,
    user_id: str,
    decision_note: Optional[str] = None,
) -> UrgencyRequest:
    """
    Phase 4: Dispatcher approves a pending urgency request.
    Rules:
    - Urgency request must exist and belong to an outlet in the dispatcher's depot.
    - Current request status must be 'pending' (or 'approved' for safe retry).
    - If already rejected -> 409 Conflict.
    - If already resolved -> 409 Conflict.
    - Associated order must still be in 'confirmed' or 'deferred' status.
    - Sets status='approved', reviewed_by=user_id, reviewed_at=now, decision_note (optional).
    """
    urg = (
        db.query(UrgencyRequest)
        .filter(UrgencyRequest.urgency_request_id == urgency_request_id)
        .first()
    )
    if not urg:
        raise HTTPException(
            status_code=404,
            detail=f"Urgency request {urgency_request_id} not found",
        )

    outlet = db.query(Outlet).filter(Outlet.outlet_id == urg.outlet_id).first()
    if not outlet or outlet.depot_id != dispatcher_depot:
        raise HTTPException(
            status_code=403,
            detail="Cannot approve urgency request for an outlet outside your depot",
        )

    # State transition checks
    if urg.status == "approved":
        return urg  # Safe retry
    if urg.status == "rejected":
        raise HTTPException(
            status_code=409,
            detail="Cannot approve an already rejected urgency request",
        )
    if urg.status == "resolved":
        raise HTTPException(
            status_code=409,
            detail="Cannot approve an already resolved urgency request",
        )
    if urg.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve urgency request in status '{urg.status}'",
        )

    # Verify order state
    order = db.query(Order).filter(Order.order_id == urg.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Associated order not found")
    if order.status not in ("confirmed", "deferred"):
        raise HTTPException(
            status_code=409,
            detail=f"Order status changed to '{order.status}'; urgency can only be approved for confirmed or deferred orders",
        )

    now = datetime.now(timezone.utc)
    urg.status = "approved"
    urg.reviewed_by = user_id
    urg.reviewed_at = now
    if decision_note is not None:
        urg.decision_note = decision_note

    db.commit()
    db.refresh(urg)
    return urg


def reject_urgency_request(
    db: Session,
    urgency_request_id: str,
    dispatcher_depot: str,
    user_id: str,
    decision_note: str,
) -> UrgencyRequest:
    """
    Phase 4: Dispatcher rejects a pending urgency request.
    Rules:
    - Urgency request must exist and belong to an outlet in the dispatcher's depot.
    - decision_note is strictly required and non-empty.
    - Current request status must be 'pending' (or 'rejected' for safe retry).
    - If already approved -> 409 Conflict.
    - If already resolved -> 409 Conflict.
    - Associated order must still be in 'confirmed' or 'deferred' status.
    - Sets status='rejected', reviewed_by=user_id, reviewed_at=now, decision_note.
    """
    if not decision_note or not decision_note.strip():
        raise HTTPException(
            status_code=422,
            detail="decision_note is mandatory when rejecting an urgency request",
        )

    urg = (
        db.query(UrgencyRequest)
        .filter(UrgencyRequest.urgency_request_id == urgency_request_id)
        .first()
    )
    if not urg:
        raise HTTPException(
            status_code=404,
            detail=f"Urgency request {urgency_request_id} not found",
        )

    outlet = db.query(Outlet).filter(Outlet.outlet_id == urg.outlet_id).first()
    if not outlet or outlet.depot_id != dispatcher_depot:
        raise HTTPException(
            status_code=403,
            detail="Cannot reject urgency request for an outlet outside your depot",
        )

    # State transition checks
    if urg.status == "rejected":
        return urg  # Safe retry
    if urg.status == "approved":
        raise HTTPException(
            status_code=409,
            detail="Cannot reject an already approved urgency request",
        )
    if urg.status == "resolved":
        raise HTTPException(
            status_code=409,
            detail="Cannot reject an already resolved urgency request",
        )
    if urg.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject urgency request in status '{urg.status}'",
        )

    # Verify order state
    order = db.query(Order).filter(Order.order_id == urg.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Associated order not found")
    if order.status not in ("confirmed", "deferred"):
        raise HTTPException(
            status_code=409,
            detail=f"Order status changed to '{order.status}'; urgency can only be reviewed for confirmed or deferred orders",
        )

    now = datetime.now(timezone.utc)
    urg.status = "rejected"
    urg.reviewed_by = user_id
    urg.reviewed_at = now
    urg.decision_note = decision_note

    db.commit()
    db.refresh(urg)
    return urg
