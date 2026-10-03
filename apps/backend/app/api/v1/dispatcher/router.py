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
from app.schemas.dispatcher import OptimizeRequest, ProposedPlanResponse, ConfirmPlanRequest, DeferOrderRequest
from app.services import planning_service

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
    # In a real app, we filter by orders relevant to current_user.depot_id.
    # We might need to join with Outlet to check depot_id.
    query = db.query(Order)
    if date:
        query = query.filter(Order.order_date == date)
    if status:
        query = query.filter(Order.status == status)
    if brand:
        query = query.filter(Order.brand == brand)
    return query.all()

@router.get("/vehicles", response_model=List[VehicleResponse], dependencies=[Depends(dispatcher_role)])
def get_vehicles(
    depot_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Vehicle)
    # Filter by explicitly passed depot_id, or default to current user's depot
    filter_depot = depot_id or current_user.depot_id
    if filter_depot:
        query = query.filter(Vehicle.depot_id == filter_depot)
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
    filter_depot = depot_id or current_user.depot_id
    if filter_depot:
        query = query.filter(Outlet.depot_id == filter_depot)
    if brand:
        query = query.filter(Outlet.brand == brand.lower())
    if district:
        query = query.filter(Outlet.district == district)
    return query.all()

@router.post("/planning/optimize", response_model=ProposedPlanResponse, dependencies=[Depends(dispatcher_role)])
def optimize_plan(request: OptimizeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return planning_service.create_optimization_run(db, request.depot_id, request.target_date, request.brand)

@router.get("/planning/runs/{run_id}", response_model=ProposedPlanResponse, dependencies=[Depends(dispatcher_role)])
def get_plan(run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return planning_service.get_optimization_run(run_id)

@router.post("/planning/runs/{run_id}/confirm", dependencies=[Depends(dispatcher_role)])
def confirm_plan(run_id: str, request: ConfirmPlanRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return planning_service.confirm_plan(db, run_id, request.client_op_id, current_user.depot_id, current_user.user_id)

@router.post("/orders/{order_id}/defer", dependencies=[Depends(dispatcher_role)])
def defer_order(order_id: str, request: DeferOrderRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if order_id != request.order_id:
        raise HTTPException(status_code=400, detail="Path ID and body ID mismatch")
    deferral = planning_service.defer_order(db, request, current_user.depot_id, current_user.user_id)
    return {"status": "success", "deferral_id": deferral.deferral_id}


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
    depot_id = request.depot_id or current_user.depot_id
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
    return get_plan_by_id_operation(db=db, plan_id=plan_id)


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
    )
