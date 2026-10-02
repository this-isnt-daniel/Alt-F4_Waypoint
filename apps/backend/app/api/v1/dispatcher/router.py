from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.order import Order
from app.schemas.shared import OrderResponse
from app.schemas.dispatcher import OptimizeRequest, ProposedPlanResponse, ConfirmPlanRequest, DeferOrderRequest
from app.services import planning_service

router = APIRouter()
dispatcher_role = RoleChecker("dispatcher")

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
