# Waypoint Optimizer — Hackathon Daily Dispatch Planner

Production-grade **hybrid** operational dispatch optimization engine for the
Tech-Triathlon Hackathon **Waypoint** application.

---

## 1. Overview & Architecture

The engine generates feasible daily draft dispatch plans from explicit confirmed orders, current live fleet availability, and official reference data.

```
  CONFIRMED ORDERS + LIVE FLEET STATE + REFERENCE DATA (CSV)
                             │
                             ▼
                 [Input Validation Boundary]
                             │
                             ▼
              [Multi-Start Greedy Portfolio Planner]
             (5 candidate orderings, chronological window
              & fuel feasibility, best baseline selected)
                             │
                             ▼
             [Targeted CP-SAT Improvement Stage]
             (Bounded neighborhood: top-3 deferred orders,
              ≤4 vehicles; delivery windows, capacity,
              brand/district, fuel modelled explicitly)
                             │
                             ▼
             [Independent Operational Validator]
             (Accept only if: valid AND strictly improves
              objective over greedy baseline)
                             │
                     ┌───────┴────────┐
                     ▼                ▼
              CP-SAT ACCEPTED    FALLBACK TO GREEDY
                             │
                             ▼
               DRAFT DISPATCH PLAN (Strict JSON)
```


---

## 2. Reusable Python API

### 2a. Load reference and order data

```python
from waypoint_optimizer.adapters.csv_adapter import (
    load_reference_data,        # loads all CSVs from a directory
    load_orders_with_outlets,   # maps order CSV rows to confirmed Order objects
    load_fleet_state_from_csv,  # applies live fleet state over vehicle reference
)

# Load authoritative reference data (outlets, vehicles, districts, …)
ref_data = load_reference_data("../data/")

# Load confirmed orders and resolve outlet records
orders = load_orders_with_outlets(
    orders_source="examples/orders_test_real_ref.csv",
    outlets=ref_data.outlets,
)

# Load live fleet state (remaining trips, fuel, etc.) over vehicle reference
fleet = load_fleet_state_from_csv(
    fleet_state_csv="examples/fleet_state_test.csv",
    vehicle_reference=ref_data.vehicles,
)
```

### 2b. Configure operational context

```python
from waypoint_optimizer.operational import OperationalContext
from waypoint_optimizer.operational.models import TravelPolicy, WindowPolicy

context = OperationalContext(
    planning_date="2026-10-03",
    timezone="Asia/Colombo",
    travel_policy=TravelPolicy.STATIC_FREEFLOW,
    window_policy=WindowPolicy.ARRIVAL_BEFORE_CLOSE,
    depot_turnaround_duration_min=30.0,
)
```

### 2c. Generate validated draft plan (hybrid engine)

```python
from waypoint_optimizer import generate_daily_draft_plan

# Runs greedy + targeted CP-SAT improvement (default: enable_targeted_cpsat=True)
plan = generate_daily_draft_plan(
    orders=orders,
    fleet=fleet,
    reference_data=ref_data,
    context=context,
    enable_targeted_cpsat=True,       # default; set False for greedy-only
    targeted_cpsat_time_limit_s=5.0,  # per-invocation budget
)

print(plan["algorithm"])                                   # "hybrid_greedy_targeted_cpsat"
                                                           # or "multistart_greedy_operational"
print(plan["targeted_cpsat_stage"]["executed"])            # True / False
print(plan["targeted_cpsat_stage"]["improvement_accepted"]) # True / False
```

---

## 3. Working CLI Command

The engine provides the `plan-daily` CLI command with explicit operational fleet state and orders:

```powershell
# From the waypoint_optimizer directory:
python -m waypoint_optimizer.cli plan-daily `
  --orders-file examples/orders_test_real_ref.csv `
  --fleet-file  examples/fleet_state_test.csv `
  --ref-dir     ../data `
  --date        2026-10-03 `
  --timezone    Asia/Colombo `
  --travel-policy    static_freeflow `
  --window-policy    arrival_before_close `
  --turnaround       30.0 `
  --output      draft_plan.json
```

### Output Plan Contents

The generated `draft_plan.json` strictly adheres to the Hackathon v2.0 contract:

- **`plan_id` & `status`**: Unique plan ID and `FEASIBLE` / `INVALID` status.
- **`algorithm` & `targeted_cpsat_stage`**: Reports `hybrid_greedy_targeted_cpsat`
  when CP-SAT improved the plan, or `multistart_greedy_operational` otherwise.
  Full diagnostics include `executed`, `outcome`, `improvement_accepted`,
  `neighborhood_size`, incumbent vs final objective, and `runtime_seconds`.
- **`order_counts` & `quantity_totals`**: Line-item quantity and order-level
  counts reconciling demand conservation.
- **`priority_boosted_orders`**: Transparent reasons (`deferred_yesterday`,
  `days_since_last_served`).
- **`trips`**:
  - `load_utilization`: Weight and volume utilization against vehicle ratings.
  - `fuel`: Trip distance, fuel burned, prior weekly fuel used, reservations,
    and weekly cumulative quota compliance.
  - `driver_itinerary`: Ordered stops with arrival, waiting, service, and
    departure timestamps in `Asia/Colombo`.
  - `loader_manifest`: Reverse LIFO loading sequence for physical loading.
- **`deferred_orders`**: Unassigned orders with diagnostic deferral reasons
  and evidence.
- **`validation`**: Independent operational validation summary labeled
  `DRAFT — REQUIRES DISPATCHER APPROVAL`.

---

## 4. Operational Rules & Explicit Policies

- **Delivery Windows**: Evaluated per stop. Supported policies:
  `arrival_before_close` (default), `service_start_before_close`,
  `service_end_before_close`.
- **Vehicle Chronology**: Vehicles can perform up to 2 trips (subject to
  `remaining_trips`). Trip 2 departs after Trip 1 returns plus depot
  turnaround (default 30.0 min).
- **Physical Consolidation Service Policy**: Multiple orders for the same
  outlet on a trip are consolidated into a single physical stop with **one
  docking service allowance** (from `service_allowance.csv` for that brand
  and dock type) applied per visit.
- **Cumulative Weekly Fuel**: Prior fuel used and external reservations from
  the daily fleet state are tracked; proposed trip fuel additions exceeding
  `weekly_fuel_quota_l` are rejected.
- **Explicit Travel Estimates**: Travel times and distances are based on
  static district averages from `district_travel.csv`. Depot return distance
  mirrors outbound distance. Cross-district trips are unsupported.

---

## 5. Algorithm Status — Hybrid Operational Engine

| Stage | Status |
|---|---|
| Multi-start greedy portfolio | **Active — operational output** |
| Targeted CP-SAT improvement | **Active — executes when deferred orders exist** |

**How the hybrid engine works**:

1. Greedy portfolio builds the best feasible baseline.
2. CP-SAT improvement targets the top-3 deferred orders and ≤4 compatible
   vehicles using a full operational model (capacity, windows, brand/district
   homogeneity, fuel, departure times, outlet service intervals).
3. The candidate plan is independently validated by `validate_operational_plan()`.
4. The candidate is accepted only when it is both valid and strictly improves
   the lexicographic objective `(deferral_penalty, -served_count, fuel)`.
5. Any failure — infeasibility, validation rejection, no improvement, timeout,
   or exception — returns the greedy baseline unchanged.

**Typical `targeted_cpsat_stage` output**:
```json
{
  "executed": true,
  "outcome": "REJECTED_NO_IMPROVEMENT",
  "improvement_accepted": false,
  "neighborhood_size": {"target_deferred_orders": 3, "vehicles": 1},
  "runtime_seconds": 0.68
}
```
or when accepted:
```json
{
  "executed": true,
  "outcome": "ACCEPTED",
  "improvement_accepted": true,
  "algorithm": "hybrid_greedy_targeted_cpsat"
}
```

---

## 6. Vehicle-Breakdown Recovery

A pure recovery function reassigns undelivered quantities when a vehicle
breaks down mid-route, without mutating the active plan or authoritative data:

```python
from waypoint_optimizer.operational.breakdown_recovery import (
    reallocate_broken_vehicle,
)

result = reallocate_broken_vehicle(
    active_plan=plan,
    broken_vehicle_id="VH-001",
    undelivered_quantities=[
        {
            "order_ref": "ORD-001",
            "line_item_id": "LI-001",
            "quantity": 10,
            "quantity_unit": "cases",
        }
    ],
    available_fleet=fleet,
    reference_data=ref_data,
    authoritative_orders=orders,
    operational_context=context,
    current_time_iso="2026-10-03T10:30:00+05:30",
)
# result.status is "REALLOCATED", "PARTIAL", or "INVALID"
# result.replacement_trips contains new trip assignments
# result.validation contains independent validation outcome
```

---

## 7. Clean-up & Recoverable Backup

Obsolete datathon benchmark code, unreferenced comparison scripts, and
superseded helpers were removed from the active source tree after creating a
full, recoverable backup.

### Backup Location

Path: `d:\optimization engine\backup_obsolete\`

### Files Removed & Rationale

1. `src/waypoint_optimizer/full_cpsat.py`: Obsolete full CP-SAT benchmark
   solver serving only the discarded datathon scope.
2. `src/waypoint_optimizer/benchmark.py`: Standalone comparison benchmark
   script unreferenced by the production workflow.
3. `src/waypoint_optimizer/operational/windows.py`: Superseded by
   `timeline.py` and `schedule_evaluator.py`.
4. `src/waypoint_optimizer/operational/fuel.py`: Superseded by `timeline.py`
   and `schedule_evaluator.py`.
5. `src/waypoint_optimizer/operational/trip_metrics.py`: Superseded by
   `timeline.py` and `schedule_evaluator.py`.
6. `examples/sample_data/plan_output.json`: Stale generated sample plan.
7. `examples/plan_test_real_ref.json`: Stale test output file.

### Retained Core Components

- `src/waypoint_optimizer/domain.py`, `config.py`, `enums.py`,
  `trip_math.py`, `compatibility.py`: Core domain logic and physical checks.
- `src/waypoint_optimizer/operational/`: `models.py`,
  `schedule_evaluator.py`, `timeline.py`, `validator.py`,
  `targeted_cpsat.py` (operational CP-SAT), and `breakdown_recovery.py`.
- `src/waypoint_optimizer/hackathon_planner.py`: Operational daily draft
  planner orchestrating multi-start greedy baseline and targeted CP-SAT improvement.
- `src/waypoint_optimizer/targeted_cpsat.py`: Datathon-era targeted CP-SAT solver
  retained for reference.

---

## 8. Running the Test Suite

```bash
pytest tests/ -v
```

**218 tests** execute in under 3 seconds.

Test coverage includes:

| Area | Tests |
|---|---|
| Input validation & boundary conditions | Unit tests with synthetic fixtures |
| Multi-start greedy portfolio | Integration with real CSV reference data |
| **Hybrid CP-SAT operational** | **23 focused hardening tests** |
| Targeted CP-SAT (datathon API) | 4 unit tests |
| Operational scheduling & timeline | Real Peliyagoda & Kandy depot scenarios |
| Draft editor & schedule evaluator | Missing-data diagnostics, regression |
| Vehicle breakdown recovery | Depot pickup, partial recovery, invalid inputs |
| Independent validator | Chronology, capacity, fuel, window checks |
| Real-data reference integration | Real outlets, vehicles, district travel CSVs |

