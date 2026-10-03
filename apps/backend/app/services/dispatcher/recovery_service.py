import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
import json

from app.models.incident import VehicleIncident
from app.models.trip import Trip, TripStop, TripStopItem
from app.models.order import Order as DbOrder, OrderLine as DbOrderLine
from app.models.vehicle import Vehicle as DbVehicle
from app.models.plan import DraftPlan
from app.models.route import RouteChange
from app.services.manifest_service import add_stop_items

# Canonical trip statuses (docs/schema_design.md) plus legacy driver-back names.
ACTIVE_TRIP_STATUSES = ["planned", "loaded", "out_for_delivery", "in_progress", "departed"]
FINISHED_STOP_STATUSES = ["delivered", "skipped", "failed", "returned", "completed"]

from app.adapters.optimizer_adapter import (
    get_reference_data,
    convert_db_vehicle_to_optimizer,
    _ensure_live_fleet_state,
    convert_db_order_to_optimizer,
    _to_json_serializable_plan,
)
from waypoint_optimizer.operational.breakdown_recovery import reallocate_broken_vehicle
from waypoint_optimizer.operational.models import OperationalContext

def build_recovery_proposal(db: Session, depot_id: str, user_id: str, incident_id: str):
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # 1. Fetch incident
    incident = db.query(VehicleIncident).filter(
        VehicleIncident.incident_id == incident_id,
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    vehicle = db.query(DbVehicle).filter(DbVehicle.vehicle_id == incident.vehicle_id).first()
    if not vehicle or vehicle.depot_id != depot_id:
        raise HTTPException(status_code=403, detail="Incident vehicle not in your depot scope")

    # 2. Identify affected trip
    # Find active trip for this vehicle
    trip = db.query(Trip).filter(
        Trip.vehicle_id == incident.vehicle_id,
        Trip.status.in_(["planned", "departed", "in_progress"])
    ).first()
    
    if not trip:
        raise HTTPException(status_code=422, detail="No active trip found for this broken vehicle")

    # 3. Identify affected stops and build undelivered quantities
    stops = db.query(TripStop).filter(TripStop.trip_id == trip.trip_id).order_by(TripStop.stop_seq).all()
    
    undelivered_quantities = []
    has_remaining = False
    
    for stop in stops:
        if stop.status in FINISHED_STOP_STATUSES:
            continue # Already done
        
        has_remaining = True
        # For remaining stops, get their items to recover
        db_order = db.query(DbOrder).filter(DbOrder.order_id == stop.order_id).first()
        if not db_order:
            continue
            
        items = db.query(DbOrderLine).filter(DbOrderLine.order_id == stop.order_id).all()
        for item in items:
            undelivered_quantities.append({
                "order_ref": stop.order_id,
                "line_item_id": item.line_item_id,
                "description": item.product_id,
                "quantity": item.quantity,
                "quantity_unit": "units",
                "weight_kg": float(stop.wt_kg or 0.0),
                "volume_m3": float(stop.vol_m3 or 0.0),
                "temp_requirement": stop.temp_req,
            })

    if not has_remaining:
        raise HTTPException(status_code=422, detail="No remaining stops to recover")

    # 4. Get active plan
    draft_record = db.query(DraftPlan).filter(
        DraftPlan.target_date == trip.trip_date,
        DraftPlan.status == "approved"
    ).order_by(DraftPlan.updated_at.desc()).first()
    
    if not draft_record:
        # Fallback to the latest draft if no approved plan
        draft_record = db.query(DraftPlan).filter(
            DraftPlan.target_date == trip.trip_date
        ).order_by(DraftPlan.updated_at.desc()).first()
        
    if not draft_record:
        raise HTTPException(status_code=404, detail="No base plan found for the trip date")

    # 5. Build Optimizer Input
    ref_data = get_reference_data()
    
    # Available fleet (excluding broken vehicle)
    vehicle_query = db.query(DbVehicle).filter(DbVehicle.depot_id == depot_id)
    db_vehicles = vehicle_query.all()
    
    if db_vehicles:
        optimizer_fleet = [convert_db_vehicle_to_optimizer(v, ref_data) for v in db_vehicles if v.vehicle_id != incident.vehicle_id]
    else:
        optimizer_fleet = [v for v in ref_data.vehicles if v.id != incident.vehicle_id]
        
    optimizer_fleet = [_ensure_live_fleet_state(v) for v in optimizer_fleet]

    # Authoritative orders for the date
    order_query = db.query(DbOrder).filter(DbOrder.order_date == trip.trip_date)
    optimizer_orders = [convert_db_order_to_optimizer(o, ref_data, db) for o in order_query.all()]

    context = OperationalContext(
        planning_date=trip.trip_date.isoformat(),
        timezone="Asia/Colombo",
    )
    
    # 6. Execute existing recovery optimizer (Proposal generation)
    try:
        recovery_draft = reallocate_broken_vehicle(
            active_plan=draft_record.plan_data,
            broken_vehicle_id=incident.vehicle_id,
            undelivered_quantities=undelivered_quantities,
            available_fleet=optimizer_fleet,
            reference_data=ref_data,
            operational_context=context,
            current_time_iso=now_iso,
            pickup_location="DEPOT",
            authoritative_orders=optimizer_orders,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimizer failure: {str(e)}")

    recovery_dict = _to_json_serializable_plan(dict(recovery_draft))
    
    # 7. Persist Proposal as a DraftPlan (so Dispatcher can review it)
    proposal_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
    proposal = DraftPlan(
        plan_id=proposal_id,
        depot_id=depot_id,
        target_date=trip.trip_date,
        status="proposal",
        algorithm="recovery",
        plan_data=recovery_dict,
        created_at=now,
        updated_at=now,
        created_by=user_id,
    )
    # Save a reference to the incident in the plan_data for context during approval
    recovery_dict["_recovery_context"] = {
        "incident_id": incident.incident_id,
        "broken_trip_id": trip.trip_id,
        "broken_vehicle_id": incident.vehicle_id
    }
    proposal.plan_data = recovery_dict
    
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    
    return proposal


def approve_recovery_proposal(db: Session, depot_id: str, user_id: str, proposal_id: str):
    proposal = db.query(DraftPlan).filter(
        DraftPlan.plan_id == proposal_id,
        DraftPlan.status == "proposal"
    ).first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Recovery proposal not found or already processed")
        
    if proposal.depot_id != depot_id:
        raise HTTPException(status_code=403, detail="Proposal not in your depot scope")
        
    context = proposal.plan_data.get("_recovery_context", {})
    broken_vehicle_id = context.get("broken_vehicle_id")
    broken_trip_id = context.get("broken_trip_id")
    
    # Validation: Ensure the vehicle is still assigned to the broken trip
    broken_trip = db.query(Trip).filter(Trip.trip_id == broken_trip_id).first()
    if not broken_trip or broken_trip.status not in ACTIVE_TRIP_STATUSES:
        print(f"DEBUG: broken_trip={broken_trip}, status={broken_trip.status if broken_trip else 'None'}")
        raise HTTPException(status_code=409, detail=f"Broken trip is no longer active (stale proposal): status={broken_trip.status if broken_trip else 'None'}")
        
    # Transactional Application
    now = datetime.now(timezone.utc)
    
    # 1. Update old trip (mark as failed or completed depending on if it had any delivered)
    # Actually, we shouldn't change the trip status blindly, but typically a broken vehicle's trip ends.
    # Let's cancel the remaining stops on the broken trip
    broken_stops = db.query(TripStop).filter(TripStop.trip_id == broken_trip_id).all()
    remaining_orders = []
    for s in broken_stops:
        if s.status not in FINISHED_STOP_STATUSES:
            s.status = "failed" # Mark original stop as failed due to breakdown
            remaining_orders.append(s.order_id)
            
    broken_trip.status = "failed"
    
    # 2. Extract reassigned trips from the optimizer result and create them/update them
    plan_trips = proposal.plan_data.get("trips", [])
    
    route_changes = []
    
    for ptrip in plan_trips:
        vid = ptrip.get("vehicle_id")
        if vid == broken_vehicle_id:
            continue # Skip the broken vehicle's shell trip if any
            
        # Is this an existing trip we're modifying, or a new trip?
        # The optimizer usually returns the full day's trips.
        # We need to find the active trip for this vehicle on this date.
        v_trip = db.query(Trip).filter(
            Trip.vehicle_id == vid,
            Trip.trip_date == proposal.target_date,
            Trip.status.in_(ACTIVE_TRIP_STATUSES)
        ).first()
        
        if not v_trip:
            # Create a new trip for this vehicle if none active
            new_trip_id = f"T-{uuid.uuid4().hex[:6].upper()}"
            v_trip = Trip(
                trip_id=new_trip_id,
                depot_id=depot_id,
                vehicle_id=vid,
                dispatcher_id=user_id,
                trip_date=proposal.target_date,
                trip_no=1,
                status="planned"
            )
            db.add(v_trip)
            db.flush()
            
        # Now update stops for this vehicle based on proposal
        new_stops_data = ptrip.get("driver_itinerary") or ptrip.get("stops", [])
        
        # Determine if we need to issue a RouteChange (if the trip was already in progress/departed)
        needs_route_change = v_trip.status in ACTIVE_TRIP_STATUSES
        
        seq = 1
        new_stop_ids = []
        for stop_data in new_stops_data:
            order_ref = stop_data.get("order_ref") or stop_data.get("id")
            if not order_ref:
                continue
                
            existing_stop = db.query(TripStop).filter(TripStop.order_id == order_ref).first()
            if existing_stop:
                existing_stop.trip_id = v_trip.trip_id
                existing_stop.stop_seq = seq
                existing_stop.status = "upcoming"
                # Invalidate offline driver edits made against the old assignment
                existing_stop.row_version = (existing_stop.row_version or 1) + 1
                new_stop_ids.append(existing_stop.stop_id)
            else:
                # Should not happen typically if we are recovering, but handle just in case
                stop_id = f"TS-{uuid.uuid4().hex[:6].upper()}"
                db_order = db.query(DbOrder).filter(DbOrder.order_id == order_ref).first()
                if db_order:
                    new_ts = TripStop(
                        stop_id=stop_id,
                        trip_id=v_trip.trip_id,
                        outlet_id=db_order.outlet_id,
                        order_id=order_ref,
                        stop_seq=seq,
                        temp_req=db_order.temp_req,
                        status="upcoming"
                    )
                    db.add(new_ts)
                    add_stop_items(db, stop_id, order_ref)
                    new_stop_ids.append(stop_id)
            seq += 1
            
        if needs_route_change:
            # Issue RouteChange to the driver of v_trip
            rc_id = f"RC-{uuid.uuid4().hex[:8].upper()}"
            rc = RouteChange(
                change_id=rc_id,
                trip_id=v_trip.trip_id,
                change_type="route.resequenced",
                payload=json.dumps({"new_sequence": new_stop_ids, "reason": "recovery_reallocation"}),
                issued_at=now,
                issued_by=user_id,
                acknowledged=False
            )
            db.add(rc)
            route_changes.append(rc)
            
    # Mark the broken vehicle as in_workshop
    db_v = db.query(DbVehicle).filter(DbVehicle.vehicle_id == broken_vehicle_id).first()
    if db_v:
        db_v.status = "in_workshop"

    proposal.status = "approved"
    proposal.approved_by = user_id
    proposal.approved_at = now
    
    db.commit()
    return proposal


def reject_recovery_proposal(db: Session, depot_id: str, user_id: str, proposal_id: str, reason: str):
    proposal = db.query(DraftPlan).filter(
        DraftPlan.plan_id == proposal_id,
        DraftPlan.status == "proposal"
    ).first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Recovery proposal not found or already processed")
        
    if proposal.depot_id != depot_id:
        raise HTTPException(status_code=403, detail="Proposal not in your depot scope")
        
    proposal.status = "rejected"
    if reason:
        from sqlalchemy.orm.attributes import flag_modified
        context = proposal.plan_data.get("_recovery_context", {})
        context["rejection_reason"] = reason
        proposal.plan_data["_recovery_context"] = context
        flag_modified(proposal, "plan_data")
        
    db.commit()
    return proposal

def get_recovery_proposal(db: Session, depot_id: str, proposal_id: str):
    proposal = db.query(DraftPlan).filter(
        DraftPlan.plan_id == proposal_id,
    ).first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Recovery proposal not found")
        
    if proposal.depot_id != depot_id:
        raise HTTPException(status_code=403, detail="Proposal not in your depot scope")
        
    return proposal
