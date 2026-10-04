import re

with open('app/adapters/optimizer_adapter.py', 'r') as f:
    content = f.read()

# Fix generate_daily_draft_plan_operation
content = content.replace('order_query = db.query(DbOrder).filter(DbOrder.status == "confirmed")', 'order_query = db.query(DbOrder).join(DbOutlet, DbOutlet.outlet_id == DbOrder.outlet_id).filter(DbOrder.status == "confirmed", DbOutlet.depot_id == depot_id)')

# Fix edit_draft_plan_operation
content = content.replace('order_query = db.query(DbOrder).filter(DbOrder.order_date == draft_record.target_date)', 'order_query = db.query(DbOrder).join(DbOutlet, DbOutlet.outlet_id == DbOrder.outlet_id).filter(DbOrder.order_date == draft_record.target_date, DbOutlet.depot_id == draft_record.depot_id)')

# Fix get_plan_by_id_operation
content = content.replace('def get_plan_by_id_operation(db: Session, plan_id: str) -> Dict[str, Any]:', 'def get_plan_by_id_operation(db: Session, plan_id: str, depot_id: str = None) -> Dict[str, Any]:')
content = content.replace('if not draft_record:\n        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")\n    return draft_record.plan_data', 'if not draft_record:\n        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")\n    if depot_id and draft_record.depot_id != depot_id:\n        raise HTTPException(status_code=403, detail="Plan not in your depot scope")\n    return draft_record.plan_data')

# Fix approve_draft_plan_operation
content = content.replace('def approve_draft_plan_operation(\n    db: Session,\n    plan_id: str,\n    user_id: str,\n    client_op_id: Optional[str] = None,\n) -> Dict[str, Any]:', 'def approve_draft_plan_operation(\n    db: Session,\n    plan_id: str,\n    user_id: str,\n    client_op_id: Optional[str] = None,\n    depot_id: Optional[str] = None,\n) -> Dict[str, Any]:')
content = content.replace('if not draft_record:\n        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")\n\n    plan_data = draft_record.plan_data', 'if not draft_record:\n        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")\n    if depot_id and draft_record.depot_id != depot_id:\n        raise HTTPException(status_code=403, detail="Plan not in your depot scope")\n\n    plan_data = draft_record.plan_data')

# Fix edit_draft_plan_operation authorization check
content = content.replace('def edit_draft_plan_operation(\n    db: Session,\n    plan_id: str,\n    actions: List[Dict[str, Any]],\n    user_id: Optional[str] = None,\n) -> Dict[str, Any]:', 'def edit_draft_plan_operation(\n    db: Session,\n    plan_id: str,\n    actions: List[Dict[str, Any]],\n    user_id: Optional[str] = None,\n    depot_id: Optional[str] = None,\n) -> Dict[str, Any]:')
content = content.replace('if not draft_record:\n        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")\n\n    base_plan', 'if not draft_record:\n        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")\n    if depot_id and draft_record.depot_id != depot_id:\n        raise HTTPException(status_code=403, detail="Plan not in your depot scope")\n\n    base_plan')

# Fix reallocate_broken_vehicle_operation authorization check
content = content.replace('def reallocate_broken_vehicle_operation(\n    db: Session,\n    vehicle_id: str,\n    plan_id: Optional[str] = None,\n    undelivered_quantities: Optional[List[Dict[str, Any]]] = None,\n    current_time_iso: Optional[str] = None,\n    pickup_location: str = "DEPOT",\n    user_id: Optional[str] = None,\n) -> Dict[str, Any]:', 'def reallocate_broken_vehicle_operation(\n    db: Session,\n    vehicle_id: str,\n    plan_id: Optional[str] = None,\n    undelivered_quantities: Optional[List[Dict[str, Any]]] = None,\n    current_time_iso: Optional[str] = None,\n    pickup_location: str = "DEPOT",\n    user_id: Optional[str] = None,\n    depot_id: Optional[str] = None,\n) -> Dict[str, Any]:')
content = content.replace('if not draft_record:\n        raise HTTPException(status_code=404, detail="No active plan found for breakdown reallocation")\n\n    active_plan', 'if not draft_record:\n        raise HTTPException(status_code=404, detail="No active plan found for breakdown reallocation")\n    if depot_id and draft_record.depot_id != depot_id:\n        raise HTTPException(status_code=403, detail="Plan not in your depot scope")\n\n    active_plan')

with open('app/adapters/optimizer_adapter.py', 'w') as f:
    f.write(content)
