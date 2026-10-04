import uuid
from datetime import datetime, timezone, timedelta, time
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional

from app.models.product import Product
from app.models.order import Order, OrderLine
from app.models.outlet import Outlet
from app.models.events import DeliveryEvent
from app.models.delivery import ReceiptConfirmation, Discrepancy, ProofOfDelivery
from app.models.deferral import Deferral
from app.models.trip import Trip, TripStop
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.urgency import UrgencyRequest
from app.schemas.store_manager import CreateOrderRequest, UpdateOrderRequest, ConfirmReceiptRequest


COLOMBO = ZoneInfo("Asia/Colombo")

def order_cutoff(order_date):
    return datetime.combine(order_date - timedelta(days=1), time(16), tzinfo=COLOMBO)

def get_or_create_product(db: Session, product_id: str, brand: str, temp_req: str) -> Product:
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        product = Product(
            product_id=product_id,
            name=product_id,
            brand=brand,
            category="Catalogue",
            temp_req=temp_req,
            unit="unit",
            unit_wt_kg=1.0,
            unit_vol_m3=0.002,
            active=True
        )
        db.add(product)
        db.flush()
    return product

def validate_product(product, brand, temp_req):
    if not product or not product.active:
        raise HTTPException(status_code=400, detail="Product is missing or inactive")
    if product.brand != brand:
        raise HTTPException(status_code=400, detail="Product does not belong to the outlet brand")
    if product.temp_req == "chilled" and temp_req != "chilled":
        raise HTTPException(status_code=400, detail="Chilled products require a chilled order")


def create_or_update_draft_order(db: Session, request: CreateOrderRequest, store_manager_outlet: str, user_id: str) -> Order:
    # 1. Verify scope
    if request.outlet_id != store_manager_outlet:
        raise HTTPException(status_code=403, detail="Store Manager can only create orders for their own outlet")
        
    outlet = db.query(Outlet).filter(Outlet.outlet_id == store_manager_outlet).first()
    if not outlet or request.brand != outlet.brand:
        raise HTTPException(status_code=400, detail="Order brand must match the outlet")
    if request.temp_req not in ("ambient", "chilled"):
        raise HTTPException(status_code=400, detail="Invalid temperature requirement")
    for item in request.items:
        prod = get_or_create_product(db, item.product_id, outlet.brand, request.temp_req)
        validate_product(prod, outlet.brand, request.temp_req)

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
        
    order.cutoff_at = order_cutoff(request.order_date)

    # Derive Delivery Window
    outlet = db.query(Outlet).filter(Outlet.outlet_id == request.outlet_id).first()
    if outlet and outlet.mall_window:
        order.window_open, order.window_close = outlet.mall_window.split("-", 1)
    elif outlet and outlet.window_open and outlet.window_close:
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
        product = get_or_create_product(db, item.product_id, request.brand, request.temp_req)
        line = OrderLine(
            line_item_id=str(uuid.uuid4()),
            order_id=order.order_id,
            product_id=product.product_id,
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
        
    for item in request.items:
        prod = get_or_create_product(db, item.product_id, order.brand, order.temp_req)
        validate_product(prod, order.brand, order.temp_req)

    # Replace lines
    db.query(OrderLine).filter(OrderLine.order_id == order_id).delete()
    
    for item in request.items:
        product = get_or_create_product(db, item.product_id, order.brand, order.temp_req)
        line = OrderLine(
            line_item_id=str(uuid.uuid4()),
            order_id=order.order_id,
            product_id=product.product_id,
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
        
    cutoff = order_cutoff(order.order_date)
    order.cutoff_at = cutoff

    # Calculate volume/weight and ensure items exist
    lines = db.query(OrderLine).filter(OrderLine.order_id == order_id).all()
    if not lines:
        raise HTTPException(status_code=400, detail="Order has no items")
        
    total_units = 0
    total_wt = 0.0
    total_vol = 0.0
    
    for line in lines:
        product = get_or_create_product(db, line.product_id, order.brand, order.temp_req)
        validate_product(product, order.brand, order.temp_req)
        total_units += line.quantity
        total_wt += float(product.unit_wt_kg or 0.0) * float(line.quantity)
        total_vol += float(product.unit_vol_m3 or 0.0) * float(line.quantity)
        
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
    # 1. Order existence check
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # 2. Outlet authorization check (foreign outlet blocked before idempotency check)
    if order.outlet_id != store_manager_outlet:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 3. Hardened idempotency check via client_op_id
    if request.client_op_id:
        existing_receipt = db.query(ReceiptConfirmation).filter_by(client_op_id=request.client_op_id).first()
        if existing_receipt:
            # Check ownership: do NOT leak receipt belonging to another outlet or user
            existing_receipt_order = db.query(Order).filter(Order.order_id == existing_receipt.order_id).first()
            if (
                existing_receipt.confirmed_by != user_id
                or not existing_receipt_order
                or existing_receipt_order.outlet_id != store_manager_outlet
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access or replay this operation",
                )
            
            # Different order_id -> 409 Conflict
            if existing_receipt.order_id != order_id:
                raise HTTPException(
                    status_code=409,
                    detail="client_op_id has already been used for a different order",
                )

            # Same client_op_id, same order_id, same Store Manager/outlet -> return existing receipt
            return existing_receipt
        
    if order.status not in ("out_for_delivery", "delivered"):
        raise HTTPException(status_code=409, detail="Order has not reached delivery")
    pod = db.get(ProofOfDelivery, request.pod_id)
    if not pod or pod.order_id != order_id:
        raise HTTPException(status_code=400, detail="Proof of delivery does not belong to this order")
    product_ids = {line.product_id for line in db.query(OrderLine).filter_by(order_id=order_id)}
    if any(d.product_id not in product_ids for d in (request.discrepancies or [])):
        raise HTTPException(status_code=400, detail="Discrepancy product does not belong to this order")
    if request.items_ok and request.discrepancies:
        raise HTTPException(status_code=400, detail="items_ok cannot be true with discrepancies")
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
            exp_q = disc.expected_qty
            act_q = disc.actual_qty
            rep_q = disc.reported_qty
            r_code = getattr(disc, "reason_code", None) or (disc.get("reason_code") if isinstance(disc, dict) else None)
            n_val = getattr(disc, "note", None) or (disc.get("note") if isinstance(disc, dict) else None)
            
            calc_reported = rep_q if rep_q is not None else ((exp_q - act_q) if exp_q is not None and act_q is not None else 0)
            
            # Map legacy/UI reason codes to canonical Discrepancy.type
            canonical_type = "other"
            if r_code in ("short", "short_quantity", "short_qty"):
                canonical_type = "short_qty"
            elif r_code in ("missing",):
                canonical_type = "missing"
            elif r_code in ("damaged",):
                canonical_type = "damaged"
            elif r_code in ("substituted", "wrong_item"):
                canonical_type = "wrong_item"
            
            # Preserve original reason in note if it's being mapped to 'other' or modified
            final_note = n_val or ""
            if r_code and r_code not in ("short_qty", "missing", "damaged", "wrong_item", "other"):
                prefix = f"Original receipt reason: {r_code}"
                final_note = f"{prefix}; {final_note}" if final_note else prefix

            d = Discrepancy(
                discrepancy_id=str(uuid.uuid4()),
                order_id=order_id,
                raised_by=user_id,
                source_stage="receipt",
                confirm_id=receipt.confirm_id,
                product_id=p_id or "UNKNOWN",
                type=canonical_type,
                reported_qty=calc_reported,
                status="open",
                note=final_note if final_note else None
            )
            db.add(d)
            
    order.status = "delivered"
    
    # Resolve approved urgency request on final delivery
    urgency = db.query(UrgencyRequest).filter(UrgencyRequest.order_id == order_id).first()
    if urgency and urgency.status == "approved":
        urgency.status = "resolved"
        urgency.resolved_at = now

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
    driver_phone = None
    delivery_otp = None
    vehicle_id = None
    stop_status = None
    
    if order.trip_id:
        trip = db.query(Trip).filter(Trip.trip_id == order.trip_id).first()
        if trip:
            vehicle_id = trip.vehicle_id
            
            # Fetch driver details: prefer trip's driver, fallback to vehicle's driver
            active_driver_id = trip.driver_id
            if not active_driver_id and vehicle_id:
                vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
                if vehicle:
                    active_driver_id = vehicle.driver_id
            
            if active_driver_id:
                driver = db.query(User).filter(User.user_id == active_driver_id).first()
                if driver:
                    driver_name = driver.name
                    driver_phone = driver.phone
                    
        stop = db.query(TripStop).filter(TripStop.order_id == order_id).first()
        if stop:
            stop_status = stop.status
            # Check for POD to get OTP
            from app.models.delivery import ProofOfDelivery
            pod = db.query(ProofOfDelivery).filter(ProofOfDelivery.order_id == order_id).first()
            if pod and pod.otp_code:
                # format OTP with space for UI e.g., "123 456"
                if len(pod.otp_code) == 6:
                    delivery_otp = f"{pod.otp_code[:3]} {pod.otp_code[3:]}"
                else:
                    delivery_otp = pod.otp_code
            if not order.exp_arrival and stop.eta:
                order.exp_arrival = stop.eta

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
        "driver_phone": driver_phone,
        "delivery_otp": delivery_otp,
        "stop_seq": order.stop_seq,
        "stop_status": stop_status,
        "defer_count": order.defer_count,
        "deferred_prev": order.deferred_prev,
    }

