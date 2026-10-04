# Dispatcher & Optimizer Testing Architecture (Person 2)

**Competition:** Tech-Triathlon 2026 — Hackathon  
**Team:** Alt-F4  
**Branch:** `dispatcher-test`  
**Target:** Dispatcher Portal, Fleet Allocation, Optimization Engine Adapter, Incident Recovery, & Urgency Workflows

---

## 1. Executive Summary

This document specifies the verification framework and test suite implemented for **Person 2 (Dispatcher / Optimizer)** within the Waypoint Hackathon platform.

The testing architecture guarantees:
1. **Hard Mathematical Constraints**: Capacity bounds, refrigeration compatibility, physical parking restrictions, single-brand and single-district trip purity, and driver operational time budgets are unconditionally enforced.
2. **Optimizer Stability & Fair Allocation**: The optimizer generates deterministic, valid draft plans, prioritizes repeat deferrals fairly, and never overcommits vehicle trips.
3. **Draft Plan Lifecycle & Idempotency**: Drafts are persisted in SQLite/PostgreSQL, editable via manual operational actions, and approved idempotently into canonical `Trip`, `TripStop`, and `Order` status transitions.
4. **Resilience & Incident Management**: Vehicle breakdowns dynamically trigger partial reallocations to surviving fleet vehicles, and urgency requests are reviewed under strict depot-level isolation.
5. **Security & Role Isolation**: Store managers, loaders, and drivers are strictly forbidden from accessing dispatcher endpoints (HTTP 403 Forbidden).

---

## 2. Test Suite Structure & File Map

The primary Person 2 tests reside in `apps/backend/tests/test_dispatcher.py`, alongside connected integration modules:

```
apps/backend/tests/
├── test_dispatcher.py                     # [37 Tests] Canonical Person 2 Test Suite
│   ├── TestHardConstraints               # P2-U-001 - P2-U-007 (HC1 - HC6b)
│   ├── TestOptimizerScenarios             # P2-U-008 - P2-U-012 (Single/multi-trip, deferrals)
│   ├── TestAdapterConverters              # P2-U-013 - P2-U-018 (DB <-> Optimizer domain)
│   ├── TestPlanLifecycleIntegration       # P2-I-001 - P2-I-013 (Draft/Edit/Approve APIs)
│   └── TestSchemaAndStateIntegrity        # P2-S-001 - P2-S-006 (DraftPlan, Deferral, Urgency)
├── test_optimizer_backend_flow.py         # End-to-end Draft -> Edit -> Approve -> Breakdown
├── test_phase2_incidents_route_changes.py # Incidents, breakdowns, and route change delta logs
├── test_phase3_recovery.py                # Breakdown recovery proposal workflow
├── test_phase5_hardening.py               # Deferred carryover and urgency derivation tests
├── test_urgency_api_workflow.py           # Store manager urgency request & dispatcher review
└── test_urgency_schema_model.py           # Urgency models, reason codes, and constraints
```

---

## 3. Coverage Breakdown

### 3.1 Hard Constraints (Unit Verification)
* **P2-U-001 (HC6a Weight Cap)**: Rejects trips where aggregated order weight exceeds vehicle capacity (`WEIGHT_OVERFLOW`).
* **P2-U-002 (HC6b Volume Cap)**: Rejects trips exceeding vehicle cubic volume capacity (`VOLUME_OVERFLOW`).
* **P2-U-003 (HC2 Refrigeration)**: Rejects chilled order assignment to ambient vehicles (`TEMP_INCOMPATIBLE`).
* **P2-U-004 (HC3 Parking & Access)**: Rejects truck assignment to outlets marked `van_only` (`ACCESS_INCOMPATIBLE`).
* **P2-U-005 (HC1 Brand Purity)**: Rejects trips mixing distinct brands (e.g. Fresh + Style) (`MIXED_BRAND`).
* **P2-U-006 (HC1 District Purity)**: Rejects trips mixing delivery districts (e.g. Colombo + Gampaha) (`MIXED_DISTRICT`).
* **P2-U-007 (Daily Time Budget)**: Enforces daily operating budgets (Fresh $\le 270$ min, Style/Tech $\le 480$ min) (`FRESH_BUDGET_EXCEEDED`).

### 3.2 Optimization Scenarios & Fairness
* **P2-U-008 (Single-Trip Allocation)**: Validates clean single-trip clustering when orders fit within single-run parameters.
* **P2-U-009 (Multi-Trip Allocation)**: Verifies vehicles perform up to 2 distinct trips without exceeding limits.
* **P2-U-010 (Graceful Deferral)**: When fleet capacity is saturated, unserved orders are deferred with structured reason codes.
* **P2-U-011 (Fairness Debt / Prior Deferrals)**: Orders deferred in prior cycles (`deferred_prev=True`, `defer_count >= 1`) receive priority over new orders.
* **P2-U-012 (Empty Order Handling)**: Safely handles empty input batches without solver crashes.

### 3.3 Persistence, API Lifecycle & Concurrency
* **P2-I-001 (Draft Generation)**: `POST /api/v1/dispatcher/plans/draft` builds and stores drafts in the database without modifying active trips.
* **P2-I-002 (Draft Retrieval)**: `GET /api/v1/dispatcher/plans/{plan_id}` returns full JSON plan data.
* **P2-I-003 (Draft Editing)**: `POST /api/v1/dispatcher/plans/{plan_id}/edit` supports operational edit actions (`move_whole_order`, `defer_whole_order`, `reinstate_whole_order`).
* **P2-I-004 (Approval Boundary)**: `POST /api/v1/dispatcher/plans/{plan_id}/approve` converts drafts into immutable `Trip` and `TripStop` rows and transitions orders to `planned`.
* **P2-I-005 (Idempotency Safeguard)**: Re-submitting approval with identical `client_op_id` returns HTTP 200 without duplicating trips or stop records.
* **P2-I-006 (Manual Order Deferral)**: `POST /api/v1/dispatcher/orders/{order_id}/defer` creates structured `Deferral` records.
* **P2-I-008 (Route Changes / Resequencing)**: Emits `route.resequenced` events recorded in the append-only ledger for drivers.
* **P2-I-009 (Urgency Workflow)**: Dispatchers review depot urgency requests. Mandatory notes are strictly required on rejection.
* **P2-I-010 (Breakdown Reallocation)**: `POST /api/v1/dispatcher/breakdowns/{vehicle_id}/reallocate` moves undelivered stops to available replacement vehicles and marks the broken vehicle `in_workshop`.

### 3.4 Security & Multi-Tenancy
* **P2-I-012 (Cross-Depot Isolation)**: Dispatchers attempting to view or approve plans outside their assigned depot receive HTTP 403 Forbidden.
* **P2-I-013 (Role Guards)**: Unauthorized roles (`store_manager`, `loader`, `driver`) are blocked with HTTP 403 Forbidden.

---

## 4. Test Execution & Verification

Run the entire Person 2 and connected dispatcher suite:

```powershell
$env:PYTHONPATH="apps/backend/optimization_engine/src;apps/backend"
pytest apps/backend/tests/test_dispatcher.py -v
```

Run all connected integration test suites:

```powershell
$env:PYTHONPATH="apps/backend/optimization_engine/src;apps/backend"
pytest `
  apps/backend/tests/test_dispatcher.py `
  apps/backend/tests/test_optimizer_backend_flow.py `
  apps/backend/tests/test_phase2_incidents_route_changes.py `
  apps/backend/tests/test_phase3_recovery.py `
  apps/backend/tests/test_phase5_hardening.py `
  apps/backend/tests/test_urgency_api_workflow.py `
  apps/backend/tests/test_urgency_schema_model.py `
  apps/backend/tests/test_store_manager.py `
  apps/backend/tests/test_auth_platform.py
```

**Verification Status:**
* `test_dispatcher.py`: **37 / 37 PASSED**
* Complete Connected Suite: **118 / 118 PASSED** (0 failures)
