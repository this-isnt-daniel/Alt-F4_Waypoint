import re

with open('app/services/planning_service.py', 'r') as f:
    content = f.read()

content = content.replace('def get_optimization_run(run_id: str) -> ProposedPlanResponse:', 'def get_optimization_run(db: Session, run_id: str, depot_id: str) -> ProposedPlanResponse:')
content = content.replace('    return plan\n\ndef confirm_plan', '    if plan.depot_id != depot_id:\n        raise HTTPException(status_code=403, detail="Cannot access plan for a different depot")\n    return plan\n\ndef confirm_plan')
content = content.replace('plan = get_optimization_run(run_id)', 'plan = get_optimization_run(db, run_id, dispatcher_depot)')

with open('app/services/planning_service.py', 'w') as f:
    f.write(content)
