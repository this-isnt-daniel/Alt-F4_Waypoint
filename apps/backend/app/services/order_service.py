import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional

from app.models.product import Product
from app.models.order import Order, OrderLine
from app.models.outlet import Outlet
from app.models.events import DeliveryEvent
from app.models.delivery import ReceiptConfirmation, Discrepancy
from app.models.deferral import Deferral
from app.models.trip import Trip, TripStop
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.store_manager import CreateOrderRequest, UpdateOrderRequest, ConfirmReceiptRequest


def create_or_update_draft_order(db: Session, request: CreateOrderRequest, store_manager_outlet: str, user_id: str) -> Order:
    # 1. Verify scope
    if request.outlet_id != store_manager_outlet:
        raise HTTPException(status_code=403, detail="Store Manager can only create orders for their own outlet")
        
    # 2. Check draft rule: Does a matching order exist?
    existing_order = db.query(Order).filter(
        Order.outlet_id == request.outlet_id,
        Order.order_date == request.order_date,
        Order.temp_req == request.temp_req
    ).first()
    
    if existing_order:
        if existing_order.status != "draft":
            raise HTTPException(status_code=409, detail="A non-draft order already exists for this outlet, date, and temp requirement.")
        order = existing_order
        # Delete old lines to replace them
        db.query(OrderLine).filter(OrderLine.order_id == order.order_id).delete()
    else:
        # Create new draft
        order = Order(
            order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            outlet_id=request.outlet_id,
            created_by=user_id,
            brand=request.brand,
            temp_req=request.temp_req,
            order_date=request.order_date,
            status="draft",
            defer_count=0,
            deferred_prev=False
        )
        db.add(order)
        
    # Derive Delivery Window
    outlet = db.query(Outlet).filter(Outlet.outlet_id == request.outlet_id).first()
    if outlet and outlet.window_open and outlet.window_close:
        order.window_open = outlet.window_open
        order.window_close = outlet.window_close
    elif request.brand.lower() == "fresh":
        order.window_open = "03:30"
        order.window_close = "08:00"
    else:
        order.window_open = "08:00"
        order.window_close = "18:00"
        
    # Add items
    for item in request.items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
        
        line = OrderLine(
            line_item_id=str(uuid.uuid4()),
            order_id=order.order_id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(line)
        
    db.commit()
    db.refresh(order)
    return order


def update_draft_order(db: Session, order_id: str, request: UpdateOrderRequest, store_manager_outlet: str) -> Order:
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.outlet_id != store_manager_outlet:
        raise HTTPException(status_code=403, detail="Not authorized to edit this order")
        
    if order.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft orders can be updated")
        
    # Replace lines
    db.query(OrderLine).filter(OrderLine.order_id == order_id).delete()
    
    for item in request.items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            
        line = OrderLine(
            line_item_id=str(uuid.uuid4()),
            order_id=order.order_id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(line)
        
    db.commit()
    db.refresh(order)
    return order


def cancel_draft_order(db: Session, order_id: str, store_manager_outlet: str):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.outlet_id != store_manager_outlet:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this order")
        
    if order.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft orders can be cancelled")
        
    db.delete(order)
    db.commit()
    return {"message": "Order cancelled successfully"}


def confirm_order(db: Session, order_id: str, store_manager_outlet: str, user_id: Optional[str] = None) -> Order:
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.outlet_id != store_manager_outlet:
        raise HTTPException(status_code=403, detail="Not authorized to confirm this order")
        
    if order.status != "draft":
        raise HTTPException(status_code=400, detail=f"Order cannot be confirmed from status: {order.status}")
        
    # Calculate volume/weight and ensure items exist
    lines = db.query(OrderLine).filter(OrderLine.order_id == order_id).all()
    if not lines:
        raise HTTPException(status_code=400, detail="Order has no items")
        
    total_units = 0
    total_wt = 0.0
    total_vol = 0.0
    
    for line in lines:
        product = db.query(Product).filter(Product.product_id == line.product_id).first()
        if not product:
            continue
        total_units += line.quantity
        total_wt += float(product.unit_wt_kg or 0.0) * line.quantity
        total_vol += float(product.unit_vol_m3 or 0.0) * line.quantity
        
    order.order_units = total_units
    order.order_wt_kg = total_wt
    order.order_vol_m3 = total_vol
    
    order.status = "confirmed"
    now = datetime.now(timezone.utc)
    order.submitted_at = now
    
    # Event
    event = DeliveryEvent(
        event_id=str(uuid.uuid4()),
        order_id=order_id,
        event_type="order_confirmed",
        occurred_at=now,
        actor_role="store_manager",
        actor_id=user_id or store_manager_outlet
    )
    db.add(event)
    
    db.commit()
    db.refresh(order)
    return order


def confirm_receipt(db: Session, order_id: str, request: ConfirmReceiptRequest, store_manager_outlet: str, user_id: str):
    # Idempotency check
    existing_receipt = db.query(ReceiptConfirmation).filter_by(client_op_id=request.client_op_id).first()
    if existing_receipt:
        return existing_receipt
        
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.outlet_id != store_manager_outlet:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    now = datetime.now(timezone.utc)
    receipt = ReceiptConfirmation(
        confirm_id=str(uuid.uuid4()),
        order_id=order_id,
        pod_id=request.pod_id,
        confirmed_by=user_id,
        confirmed_at=now,
        items_ok=request.items_ok,
        client_op_id=request.client_op_id
    )
    db.add(receipt)
    
    has_discrepancy = False
    if request.discrepancies:
        for disc in request.discrepancies:
            has_discrepancy = True
            p_id = getattr(disc, "product_id", None) or (disc.get("product_id") if isinstance(disc, dict) else None)
            exp_q = getattr(disc, "expected_qty", None) or (disc.get("expected_qty") if isinstance(disc, dict) else None)
            act_q = getattr(disc, "actual_qty", None) or (disc.get("actual_qty") if isinstance(disc, dict) else None)
            rep_q = getattr(disc, "reported_qty", None) or (disc.get("reported_qty") if isinstance(disc, dict) else None)
            r_code = getattr(disc, "reason_code", None) or (disc.get("reason_code") if isinstance(disc, dict) else None)
            n_val = getattr(disc, "note", None) or (disc.get("note") if isinstance(disc, dict) else None)
            
            calc_reported = rep_q if rep_q is not None else ((exp_q - act_q) if exp_q is not None and act_q is not None else 0)
            
            d = Discrepancy(
                discrepancy_id=str(uuid.uuid4()),
                order_id=order_id,
                raised_by=user_id,
                source_stage="receipt",
                confirm_id=receipt.confirm_id,
                product_id=p_id or "UNKNOWN",
                type=r_code or "receipt_discrepancy",
                reported_qty=calc_reported,
                status="open",
                note=n_val
            )
            db.add(d)
            
    order.status = "delivered"
    
    event = DeliveryEvent(
        event_id=str(uuid.uuid4()),
        order_id=order_id,
        event_type="order_delivered",
        occurred_at=now,
        actor_role="store_manager",
        actor_id=user_id
    )
    db.add(event)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate operation detected")
        
    db.refresh(receipt)
    return receipt


def get_store_manager_orders(
    db: Session,
    outlet_id: str,
    status_filter: Optional[str] = None,
    order_date_filter: Optional[str] = None,
    brand_filter: Optional[str] = None
) -> List[Order]:
    query = db.query(Order).filter(Order.outlet_id == outlet_id)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    if order_date_filter:
        query = query.filter(Order.order_date == order_date_filter)
    if brand_filter:
        query = query.filter(Order.brand == brand_filter)
        
    return query.order_by(Order.order_date.desc()).all()


def get_store_manager_order(db: Session, order_id: str, outlet_id: str) -> Order:
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.outlet_id != outlet_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")
    return order


def get_store_manager_products(
    db: Session,
    brand_filter: Optional[str] = None,
    temp_req_filter: Optional[str] = None
) -> List[Product]:
    query = db.query(Product).filter(Product.active == True)
    if brand_filter:
        query = query.filter(Product.brand == brand_filter)
    if temp_req_filter:
        query = query.filter(Product.temp_req == temp_req_filter)
    return query.all()


def get_store_manager_outlet(db: Session, outlet_id: str) -> Outlet:
    outlet = db.query(Outlet).filter(Outlet.outlet_id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    return outlet


def get_store_manager_deferrals(db: Session, outlet_id: str) -> List[Deferral]:
    return db.query(Deferral).filter(Deferral.outlet_id == outlet_id).order_by(Deferral.created_at.desc()).all()


def get_order_eta(db: Session, order_id: str, outlet_id: str) -> dict:
    order = get_store_manager_order(db, order_id, outlet_id)
    
    driver_name = None
    vehicle_id = None
    stop_status = None
    
    if order.trip_id:
        trip = db.query(Trip).filter(Trip.trip_id == order.trip_id).first()
        if trip:
            vehicle_id = trip.vehicle_id
            if trip.driver_id:
                driver = db.query(User).filter(User.user_id == trip.driver_id).first()
                if driver:
                    driver_name = driver.name
                    
        stop = db.query(TripStop).filter(TripStop.order_id == order_id).first()
        if stop:
            stop_status = stop.status
            if not order.exp_arrival and stop.expected_arrival:
                order.exp_arrival = stop.expected_arrival

    return {
        "order_id": order.order_id,
        "outlet_id": order.outlet_id,
        "status": order.status,
        "window_open": order.window_open,
        "window_close": order.window_close,
        "exp_arrival": order.exp_arrival,
        "actual_arrival": order.actual_arrival,
        "trip_id": order.trip_id,
        "vehicle_id": vehicle_id,
        "driver_name": driver_name,
        "stop_seq": order.stop_seq,
        "stop_status": stop_status,
        "defer_count": order.defer_count,
        "deferred_prev": order.deferred_prev,
    }

