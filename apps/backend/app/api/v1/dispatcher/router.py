from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.order import Order
from app.schemas.shared import OrderResponse, VehicleResponse, OutletResponse
from app.models.vehicle import Vehicle
from app.models.outlet import Outlet
from app.schemas.urgency import (
    DispatcherUrgencyListItemResponse,
    UrgencyRequestResponse,
    ApproveUrgencyRequest,
    RejectUrgencyRequest,
)
from app.services import urgency_service

dispatcher_role = RoleChecker("dispatcher")
router = APIRouter(dependencies=[Depends(dispatcher_role)])

from app.api.v1.dispatcher.operations import router as operations_router
router.include_router(operations_router)

from app.api.v1.dispatcher.incidents.router import router as incidents_router
router.include_router(incidents_router, prefix="/incidents")

from app.api.v1.dispatcher.route_changes.router import router as route_changes_router
router.include_router(route_changes_router)

from app.api.v1.dispatcher.recovery.router import router as recovery_router
router.include_router(recovery_router, prefix="/recovery")

@router.get("/orders", response_model=List[OrderResponse], dependencies=[Depends(dispatcher_role)])
def get_orders(
    date: Optional[date] = None,
    status: Optional[str] = None,
    brand: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Order).join(Outlet, Order.outlet_id == Outlet.outlet_id).filter(Outlet.depot_id == current_user.depot_id)
    if date:
        query = query.filter(Order.order_date == date)
    if status:
        query = query.filter(Order.status == status)
    if brand:
        query = query.filter(Order.brand == brand)
    return query.all()

@router.get("/outlets", response_model=List[OutletResponse], dependencies=[Depends(dispatcher_role)])
def get_outlets(
    depot_id: Optional[str] = None,
    brand: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Outlet)
    filter_depot = current_user.depot_id
    if filter_depot:
        query = query.filter(Outlet.depot_id == filter_depot)
    if brand:
        query = query.filter(Outlet.brand == brand.lower())
    if district:
        query = query.filter(Outlet.district == district)
    return query.all()



# ── Waypoint Optimizer Endpoints (Step 5) ───────────────────────────────────

from app.schemas.dispatcher import (
    DraftPlanCreateRequest,
    EditDraftPlanRequest,
    ApprovePlanRequest,
    BreakdownReallocateRequest,
)
from app.adapters.optimizer_adapter import (
    generate_daily_draft_plan_operation,
    get_plan_by_id_operation,
    edit_draft_plan_operation,
    approve_draft_plan_operation,
    reallocate_broken_vehicle_operation,
)


@router.post("/plans/draft", dependencies=[Depends(dispatcher_role)])
def create_draft_plan(
    request: DraftPlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    POST /dispatcher/plans/draft
    Reads confirmed orders, vehicle availability, and reference data.
    Runs hybrid multi-start greedy + targeted CP-SAT optimizer.
    Persists returned draft plan in database.
    """
    depot_id = current_user.depot_id
    return generate_daily_draft_plan_operation(
        db=db,
        depot_id=depot_id,
        target_date=request.target_date,
        brand=request.brand,
        enable_targeted_cpsat=request.enable_targeted_cpsat,
        user_id=current_user.user_id,
    )


@router.get("/plans/{plan_id}", dependencies=[Depends(dispatcher_role)])
def get_plan_by_id(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GET /dispatcher/plans/{plan_id}
    Retrieves the persisted draft plan.
    """
    return get_plan_by_id_operation(db=db, plan_id=plan_id, depot_id=current_user.depot_id)


@router.post("/plans/{plan_id}/edit", dependencies=[Depends(dispatcher_role)])
def edit_draft_plan(
    plan_id: str,
    request: EditDraftPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    POST /dispatcher/plans/{plan_id}/edit
    Re-evaluates and validates dispatcher edits using evaluate_edited_draft.
    """
    return edit_draft_plan_operation(
        db=db,
        plan_id=plan_id,
        actions=request.actions,
        user_id=current_user.user_id,
        depot_id=current_user.depot_id,
    )


@router.post("/plans/{plan_id}/approve", dependencies=[Depends(dispatcher_role)])
def approve_plan(
    plan_id: str,
    request: Optional[ApprovePlanRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    POST /dispatcher/plans/{plan_id}/approve
    Dispatcher reviews and confirms the draft.
    Persists trips, stops, and updates order states to 'planned'.
    """
    client_op_id = request.client_op_id if request else None
    return approve_draft_plan_operation(
        db=db,
        plan_id=plan_id,
        user_id=current_user.user_id,
        client_op_id=client_op_id,
        depot_id=current_user.depot_id,
    )


@router.post("/breakdowns/{vehicle_id}/reallocate", dependencies=[Depends(dispatcher_role)])
def reallocate_broken_vehicle_route(
    vehicle_id: str,
    request: Optional[BreakdownReallocateRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    POST /dispatcher/breakdowns/{vehicle_id}/reallocate
    Uses reallocate_broken_vehicle to reallocate undelivered orders to surviving fleet.
    """
    plan_id = request.plan_id if request else None
    undelivered = request.undelivered_quantities if request else None
    current_time_iso = request.current_time_iso if request else None
    pickup_loc = request.pickup_location if request and request.pickup_location else "DEPOT"

    return reallocate_broken_vehicle_operation(
        db=db,
        vehicle_id=vehicle_id,
        plan_id=plan_id,
        undelivered_quantities=undelivered,
        current_time_iso=current_time_iso,
        pickup_location=pickup_loc,
        user_id=current_user.user_id,
        depot_id=current_user.depot_id,
    )


@router.get("/urgency-requests", response_model=List[DispatcherUrgencyListItemResponse], dependencies=[Depends(dispatcher_role)])
def list_urgency_requests(
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected, resolved)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List urgency requests for outlets in dispatcher's depot."""
    return urgency_service.list_dispatcher_urgency_requests(
        db=db,
        depot_id=current_user.depot_id,
        status_filter=status,
    )


@router.post("/urgency-requests/{urgency_request_id}/approve", response_model=UrgencyRequestResponse, dependencies=[Depends(dispatcher_role)])
def approve_urgency(
    urgency_request_id: str,
    request: Optional[ApproveUrgencyRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a pending urgency request within dispatcher's depot."""
    note = request.decision_note if request else None
    return urgency_service.approve_urgency_request(
        db=db,
        urgency_request_id=urgency_request_id,
        dispatcher_depot=current_user.depot_id,
        user_id=current_user.user_id,
        decision_note=note,
    )


@router.post("/urgency-requests/{urgency_request_id}/reject", response_model=UrgencyRequestResponse, dependencies=[Depends(dispatcher_role)])
def reject_urgency(
    urgency_request_id: str,
    request: RejectUrgencyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a pending urgency request within dispatcher's depot with a mandatory note."""
    return urgency_service.reject_urgency_request(
        db=db,
        urgency_request_id=urgency_request_id,
        dispatcher_depot=current_user.depot_id,
        user_id=current_user.user_id,
        decision_note=request.decision_note,
    )

