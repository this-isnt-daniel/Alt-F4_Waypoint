from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.dispatcher import (
    DraftPlanCreateRequest,
    EditDraftPlanRequest,
    ApprovePlanRequest,
)
from app.adapters.optimizer_adapter import (
    generate_daily_draft_plan_operation,
    get_plan_by_id_operation,
    edit_draft_plan_operation,
    approve_draft_plan_operation,
)

dispatcher_role = RoleChecker("dispatcher")
router = APIRouter(dependencies=[Depends(dispatcher_role)])


@router.post("/generate")
@router.post("/draft")
def generate_daily_plan(
    request: Optional[DraftPlanCreateRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    POST /api/v1/plans/generate (and alias POST /api/v1/plans/draft)
    Generates a draft daily delivery plan using hybrid multi-start greedy
    and targeted CP-SAT solver (enable_targeted_cpsat=True).
    Persists ONLY as a draft record in database. Never automatically approves.
    Requires dispatcher role.
    """
    req = request or DraftPlanCreateRequest()
    depot_id = req.depot_id or current_user.depot_id
    user_id = current_user.user_id

    return generate_daily_draft_plan_operation(
        db=db,
        depot_id=depot_id,
        target_date=req.target_date,
        brand=req.brand,
        enable_targeted_cpsat=True,
        user_id=user_id,
    )


@router.get("/{plan_id}")
def get_plan_by_id(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GET /api/v1/plans/{plan_id}
    Retrieves the persisted draft plan by ID. Requires dispatcher role.
    """
    return get_plan_by_id_operation(db=db, plan_id=plan_id)


@router.post("/{plan_id}/edit")
def edit_plan(
    plan_id: str,
    request: EditDraftPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    POST /api/v1/plans/{plan_id}/edit
    Re-evaluates manual dispatcher adjustments using evaluate_edited_draft(...)
    and re-validates operational constraints. Requires dispatcher role.
    """
    return edit_draft_plan_operation(
        db=db,
        plan_id=plan_id,
        actions=request.actions,
        user_id=current_user.user_id,
    )


@router.post("/{plan_id}/approve")
def approve_plan(
    plan_id: str,
    request: Optional[ApprovePlanRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    POST /api/v1/plans/{plan_id}/approve
    Explicit dispatcher approval boundary. Converts draft plan into approved state,
    creating operational trips, stops, and updating order status to 'planned'.
    Requires dispatcher role.
    """
    client_op_id = request.client_op_id if request else None
    return approve_draft_plan_operation(
        db=db,
        plan_id=plan_id,
        user_id=current_user.user_id,
        client_op_id=client_op_id,
    )
