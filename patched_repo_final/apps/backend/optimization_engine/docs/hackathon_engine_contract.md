# Waypoint Optimization Engine — Hackathon Application Contract

**Document Version:** 2.0.0  
**Target Environment:** Waypoint Multi-Role Web Application (Tech-Triathlon Hackathon)  
**Status:** Architecture Specification & Interface Contract (Proposed / Specification Only — No Code Changes)

---

## 1. Executive Summary & Architectural Scope

This document specifies the authoritative input, output, and behavioral contract for the **Waypoint Optimization Engine** as the calculation backend for the **Tech-Triathlon Hackathon Application**.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   WAYPOINT WEB BACKEND                                      │
│  (Database, Store Manager Orders, 4 PM Cutoff, Dispatcher Approval, Driver & Loader APIs)   │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                 In-Memory / JSON Payload
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                OPTIMIZATION ENGINE BOUNDARY                                 │
│                                                                                             │
│   [Input Normalization & Gateway: Authoritative Orders & Fleet Verification]                │
│         │                                                                                   │
│         ▼                                                                                   │
│   [Dynamic Scheduler & Feasibility Core: Windows, Fuel Quotas, Road Speed Indices]          │
│         │                                                                                   │
│         ▼                                                                                   │
│   [Allocation Core: Portfolio Search Guided by Window & Fuel Feasibility]                  │
│         │                                                                                   │
│         ▼                                                                                   │
│   [Operational Projections: Driver Chronological Itinerary & Loader LIFO Sequence]          │
│         │                                                                                   │
│         ▼                                                                                   │
│   [Independent Hard-Constraint Validator]                                                   │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                              Strict Plan Response (Non-Mutating)
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   DISPATCHER WORKFLOW                                       │
│          (Review Draft Plan ──► Interactive Overrides ──► Dispatcher Approves)              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Architectural Boundaries
1. **Stateless Computation**: The optimizer performs zero database queries, network calls, or disk mutations.
2. **Separation from Datathon Task 2B**: The frozen Task 2B benchmark engine remains isolated under `EngineMode.TASK2B_EXACT`. The Hackathon application executes under `EngineMode.HACKATHON_OPERATIONAL`.
3. **Dispatcher Authority**: The engine produces a **draft recommendation**. The Dispatcher reviews, optionally adjusts, and officially approves the plan before execution.
4. **Active Guidance**: Chronological window scheduling and cumulative fuel evaluation must actively guide candidate selection and repair, rather than running solely as passive post-allocation filters.

---

## 2. Input Contract

The backend invokes the optimization engine by providing the following typed parameters.

### 2.1 Planning Metadata
- `planning_date` (`string`, ISO-8601 `YYYY-MM-DD`): Target delivery date.
- `timezone` (`string`, default: `Asia/Colombo`, UTC+05:30): Authoritative timezone for all timestamps.
- `depot_filter` (`string`, optional): Target distribution center (`Peliyagoda` or `Kandy`). If omitted, all active depots are planned.
- `depot_turnaround_duration_min` (`float`, required or named policy): Unloading, inspection, and reloading duration between Trip 1 and Trip 2 at the depot. **Must be explicitly supplied by the caller or set to the documented named team policy `ESTIMATED_DEPOT_TURNAROUND_MIN` (e.g. 30.0 min). It must not be an unexplained implicit default.**
- `travel_policy` (`string`, default: `"static_freeflow"`): Chosen travel evaluation policy (`"static_freeflow"` or `"dynamic_conditions"`). If `"dynamic_conditions"` is chosen and planning date is outside reference data coverage, a structured missing-data error is returned; automatic silent fallback is prohibited.
- `window_policy` (`string`, default: `"arrival_before_close"`): Chosen delivery window enforcement rule (`"arrival_before_close"`, `"service_start_before_close"`, `"service_end_before_close"`).
- `departure_time_fresh_iso` (`string`, ISO-8601 timestamp): Standard dispatch release time for Fresh trips (e.g. `"2026-10-03T04:00:00+05:30"`).
- `departure_time_style_tech_iso` (`string`, ISO-8601 timestamp): Standard dispatch release time for Style/Tech trips (e.g. `"2026-10-03T06:30:00+05:30"`).

### 2.2 Confirmed Orders & Line-Item Demand (`orders`)
Supplied as an iterable collection of confirmed order transactions received prior to the 4:00 PM cutoff.

| Field Name | Type | Required | Description & Constraints |
| :--- | :--- | :---: | :--- |
| `order_id` / `order_ref` | `string` | **Yes** | Stable unique order identifier (e.g. `"ORD0001"`). Preserves leading zeros. |
| `outlet_id` | `string` | **Yes** | Foreign key referencing authoritative `outlets.csv` (e.g. `"OUT001"`). |
| `temp_requirement` | `string` | **Yes** | `"ambient"` or `"chilled"`. (`chilled` requires a refrigerated vehicle). |
| `deferred_prev` | `boolean` | Optional (default: `false`) | `true` if order was deferred on the previous operating cycle. Accepts `deferred_yesterday` as deprecated alias. |
| `defer_count` | `integer` | Optional (default: `0`) | Total number of times this order has been deferred ($\ge 0$). |
| `is_urgent` | `boolean` | Optional (default: `false`) | `true` only if Dispatcher-approved urgency request exists. |
| `line_items` | `list[LineItem]` | Optional | Line-item breakdown. If omitted, the order is treated as an atomic single item. |

#### 2.2.1 Line-Item Specification (`LineItem`)
| Field Name | Type | Required | Description & Constraints |
| :--- | :--- | :---: | :--- |
| `line_item_id` | `string` | **Yes** | Stable identifier within the order (e.g. `"ITEM-001"`). |
| `description` | `string` | Optional | Product description (e.g. `"Fresh Milk 1L Crate"`). |
| `quantity` | `number` | **Yes** | Requested quantity ($\ge 0$). |
| `quantity_unit` | `string` | **Yes** | Units of measure (e.g. `"cases"`, `"crates"`, `"units"`). |
| `unit_weight_kg` | `float` | **Yes** | Weight per unit in kg ($> 0.0$, finite). |
| `unit_volume_m3` | `float` | **Yes** | Volume per unit in $\text{m}^3$ ($> 0.0$, finite). |

*Note on aggregated orders*: If `line_items` is omitted by the backend, the engine uses top-level `order_units`, `order_weight_kg`, and `order_volume_m3`. In this mode, only whole-order moves are permitted; item-level splits will be rejected.

### 2.3 Fleet State & Selection (`fleet`)
Represents the fleet status as known to the backend at dispatch planning time.

| Field Name | Type | Required | Description & Constraints |
| :--- | :--- | :---: | :--- |
| `vehicle_id` | `string` | **Yes** | Vehicle identifier (`"VEH001"` to `"VEH060"`). |
| `is_mechanically_available` | `boolean` | **Yes** | `true` if physical workshop status is `available`; `false` if `in_workshop`. |
| `is_selected_for_planning` | `boolean` | **Yes** | `true` if selected by dispatcher for today's run; `false` if excluded (e.g. driver unavailable). |
| `exclusion_reason` | `string` | Optional | Explanation if not selected (e.g. `"Driver shift deficit"`, `"Scheduled inspection"`). |
| `remaining_trips` | `integer` | **Yes** | Available trips for planning window ($0$, $1$, or $2$). |
| `earliest_availability_iso`| `string` | **Yes** | Timezone-aware ISO-8601 timestamp when vehicle is ready at depot. |
| `weekly_fuel_quota_l` | `float` | **Yes** | Vehicle weekly fuel quota in litres (from `vehicles.csv`). |
| `weekly_fuel_used_l` | `float` | **Yes** | Actual fuel consumed during current calendar week up to today. |
| `external_reservations_l` | `float` | **Yes** | Fuel committed to trips outside this draft (e.g. other days or already dispatched runs). **Must be explicitly provided (use `0.0` if none).** |

### 2.4 Authoritative Reference Data
Pre-loaded into the engine via [ReferenceData](file:///d:/optimization%20engine/waypoint_optimizer/src/waypoint_optimizer/adapters/csv_adapter.py#L48):
- **Outlets**: `outlet_id`, `brand`, `district`, `depot`, `dock_type`, `parking_constraint`, `mall_window`, `window_open_time`, `window_close_time`.
- **District Travel**: `depot_to_district_km`, `depot_to_district_freeflow_min`, `inter_stop_km`, `inter_stop_freeflow_min`, `road_class`.
- **Service Allowance**: Standard handling minutes per `(brand, dock_type)`.
- **Operational Dynamic Data**:
  - `calendar.csv`: Identifies operating dates, day of week, monsoon season flag ($0$ or $1$). *Coverage: 2024-01-01 to 2026-06-28.*
  - `traffic_speed.csv`: Hourly speed index per district ($100$ = clear road; lower = congestion).
  - `road_conditions.csv`: Date-specific disruption index per district ($100$ = normal; lower = severe disruptions).

---

## 3. Output Contract

The engine produces an immutable, strict JSON-serializable draft plan containing operational allocations, chronologically scheduled itineraries, warehouse loading instructions, and evidence-based deferrals.

### 3.1 Draft Plan Summary
- `plan_id` (`string`, e.g. `"PLAN-20261003-PEL-V1"`): Scoped identifier for this planning execution.
- `status` (`string`): `"FEASIBLE"`, `"OPTIMAL"`, `"INVALID"`, or `"ERROR"`. *(Note: OPTIMAL refers only to local mathematical objective satisfaction, not proven global operational optimality).*
- `planning_date` (`string`): Target operating date.
- `engine_mode`: `"hackathon_operational"`.
- `runtime_seconds` (`float`): Elapsed execution time.
- `order_counts`:
  - `total_orders`: Total orders submitted.
  - `fully_served_orders`: Orders whose requested line-item quantities are $100\%$ assigned.
  - `partially_served_orders`: Orders with split allocations (some quantities served, some deferred).
  - `fully_deferred_orders`: Orders with $0\%$ quantity assigned.
- `quantity_totals`: Total requested, assigned, and deferred units across all line items.
- `metrics`: Total weight, volume, distance (km), fuel (L), vehicles used, and deferral penalty.
- `priority_boosted_orders`: Explicit list of orders receiving priority weighting, detailing the trigger (e.g. `deferred_prev`, `defer_count=N`, `approved_urgency`).

### 3.2 Trip Records (`trips`)
Each trip is an actionable route assigned to a specific vehicle:
- `trip_id` (`string`, scoped to plan, e.g. `"PLAN-20261003-PEL-V1-TRIP-VEH001-1"`).
- `vehicle_id` (`string`), `trip_number` (`integer`, $1$ or $2$).
- `brand` (`string`), `district` (`string`), `depot` (`string`).
- **Vehicle Load Utilization**:
  - `total_weight_kg`, `weight_capacity_kg`, `weight_utilization_pct`.
  - `total_volume_m3`, `volume_capacity_m3`, `volume_utilization_pct`.
- **Fuel & Travel Metrics**:
  - `estimated_distance_km`: Depot $\rightarrow$ District $\rightarrow$ Inter-stops $\rightarrow$ Depot return.
  - `estimated_fuel_litres`: Calculated fuel consumption for this trip.
  - `cumulative_weekly_fuel_litres`: `weekly_fuel_used_l` $+$ `external_reservations_l` $+$ fuel for all proposed trips of this vehicle in this plan.
  - `fuel_compliant` (`boolean`): `true` if cumulative fuel $\le$ `weekly_fuel_quota_l`.
- **Vehicle Next Availability**:
  - `depot_return_arrival_iso`: Timestamp vehicle returns to depot.
  - `next_available_time_iso`: `depot_return_arrival_iso` $+$ `depot_turnaround_duration_min`.
- **Chronological Stop Itinerary (for Driver)**:
  An ordered sequence of delivery stops with timezone-aware ISO-8601 timestamps:
  - `stop_number` ($1, 2, \dots, N$).
  - `order_ref`, `outlet_id`, `line_items_delivered` (`list[{"line_item_id": str, "quantity": num}]`).
  - `dock_type`, `parking_constraint`.
  - `arrival_time_iso`: Vehicle arrival at outlet.
  - `waiting_duration_min`: Minutes vehicle waits if arriving before window opens.
  - `service_start_time_iso`: Time unloading begins. **Cannot precede window opening time.**
  - `service_duration_min`: Handling minutes from `service_allowance.csv`.
  - `service_end_time_iso` / `departure_time_iso`: Service start time $+$ service duration.
  - `delivery_window`: `{"open_iso": str, "close_iso": str}`.
  - `window_compliant` (`boolean`): `true` if $\text{arrival} \le \text{close}$.
  - `lateness_margin_min` (`float`): Margin before window close ($> 0$) or minutes late ($< 0$).
- **Reverse Loading Sequence (for Warehouse Loader)**:
  Dock loading instructions ordered in Last-In, First-Out (LIFO) order:
  - `loading_step` ($1, 2, \dots, N$): Physical loading sequence onto vehicle.
  - `delivering_stop_number`: Matches the driver's stop number ($N, \dots, 2, 1$).
  - `order_ref`, `outlet_id`, `line_item_id`, `quantity`, `quantity_unit`, `weight_kg`, `volume_m3`.
  - `temp_requirement`: Prominently flagged for loaders to verify reefer pre-cooling.

### 3.3 Deferred Quantities & Orders (`deferred_orders`)
Detailed records for every order or split quantity not placed in the draft plan:
- `order_ref`, `outlet_id`, `line_item_id`, `deferred_quantity`, `deferred_weight_kg`, `deferred_volume_m3`.
- `reason` (Structured Code):
  - `NO_COMPATIBLE_VEHICLE`: Hard constraint — no available vehicle matches temp, access, or depot.
  - `REEFER_CAPACITY_EXHAUSTED`: Chilled demand exceeds available refrigerated vehicle payloads.
  - `VAN_CAPACITY_EXHAUSTED`: `van_only` demand exceeds small van capacity.
  - `DELIVERY_WINDOW_UNFEASIBLE`: Delivery cannot reach outlet before window closes.
  - `FUEL_QUOTA_EXCEEDED`: Route distance exceeds remaining vehicle weekly fuel quota.
  - `WEIGHT_CAPACITY`: Heavy orders saturated vehicle payload.
  - `VOLUME_CAPACITY`: Bulky orders saturated vehicle volume capacity.
  - `TRIP_LIMIT`: Fleet vehicles already scheduled for maximum 2 trips.
  - `LOWER_PRIORITY_THAN_SELECTED_ORDERS`: Order not chosen by portfolio heuristic within fleet constraints.
  - `NOT_SELECTED_BY_HEURISTIC`: Candidate was left unassigned by greedy search; global infeasibility is unproven.
- `evidence_detail` (`string`): Quantitative evidence supporting deferral.

### 3.4 Independent Validation Result (`validation`)
Recomputed independently by the hard-constraint validator:
- `valid` (`boolean`): `true` if and only if all physical and operational hard constraints are satisfied.
- `errors` (`list[ValidationError]`): Specific constraint violations, if any.
- `recomputed_served_count`, `recomputed_deferred_count`, `recomputed_penalty`.

---

## 4. Behavioral & Business Rules

### 4.1 Conservation of Demand & Quantity Splits
1. **Conservation per Line Item**:
   For every original line item $(o, i)$:
   $$\sum_{\text{trips}} \text{assigned\_quantity}(o, i) + \text{deferred\_quantity}(o, i) = \text{requested\_quantity}(o, i)$$
   For dynamic recovery:
   $$\sum_{\text{trips}} \text{assigned\_quantity}(o, i) + \text{deferred\_quantity}(o, i) + \text{already\_delivered\_quantity}(o, i) = \text{requested\_quantity}(o, i)$$
   *Rule: Order-count conservation cannot be used as proof of demand conservation. Quantity conservation is required.*
2. **Whole Orders by Default**: Automatic allocation never splits orders or line items.
3. **Dispatcher Split Policy**: Line-item splits are permitted exclusively via explicit Dispatcher edit actions. Original `order_id` and `line_item_id` are strictly preserved across split allocations.
4. **Order Status Definitions (Evaluated Per Line Item)**:
   Do NOT sum quantities across incompatible units (e.g. summing crates and units). Order status is determined per original line item:
   - **Fully Served**: For every line item $i \in \text{order}$, $\text{assigned\_quantity}(i) == \text{requested\_quantity}(i)$.
   - **Partially Served**: At least one line item has $0 < \text{assigned\_quantity}(i) < \text{requested\_quantity}(i)$, or some line items are fully served while others are fully deferred.
   - **Fully Deferred**: For every line item $i \in \text{order}$, $\text{assigned\_quantity}(i) == 0$.
   *Recovery distinction*: Planned allocation is strictly separated from executed delivery (`already_delivered_quantity`).

### 4.2 Brand & District Homogeneity Policy
1. **Chosen Design Policy**: As an operational policy for efficient clustering, all stops within a trip share the same brand and district.
2. **District Travel Limitation**: The reference dataset provides travel only between depots and individual districts, and average inter-stop travel within a district. Cross-district travel is unsupported by the reference data and therefore disabled in this implementation.
3. **Operational Separation**:
   - Fresh trips operate in the early morning window (dispatch $\sim$ 03:30–04:00 AM, arriving before 08:00 AM).
   - Style and Tech trips operate during standard retail hours ($\sim$ 06:30 AM to late afternoon).
   - A vehicle may execute Trip 1 as Fresh, return to depot, reload, and execute Trip 2 as Style or Tech.

### 4.3 Hackathon Feasibility Criteria
An allocation plan is feasible under `HACKATHON_OPERATIONAL` mode if and only if:
1. **Refrigeration**: Chilled goods are carried only by refrigerated vehicles (`temp == "reefer"`).
2. **Access**: Outlets marked `van_only` are served only by vans (`type == "van"`).
3. **Depot Containment**: A vehicle serves only outlets belonging to its home depot.
4. **Payload Constraints**: Weight and volume on each trip do not exceed vehicle ratings.
5. **Trip Limits**: A vehicle runs at most 2 trips per operating day.
6. **Chronological Feasibility**:
   $$\text{Trip 1 Departure} \rightarrow \text{Stops} \rightarrow \text{Depot Return} + \text{Turnaround} \le \text{Trip 2 Departure}$$
7. **Delivery Window Compliance**:
   Evaluated under the caller's chosen `WindowPolicy`:
   - `ARRIVAL_BEFORE_CLOSE` (default): $\text{Arrival}_k \le \text{Window Close}_k$. Notice that under this arrival-deadline policy, unloading may extend beyond window close if arrival occurred before closing.
   - `SERVICE_START_BEFORE_CLOSE`: $\text{Service Start}_k \le \text{Window Close}_k$.
   - `SERVICE_END_BEFORE_CLOSE`: $\text{Service End}_k \le \text{Window Close}_k$.
   In all policies, early arrival waits: $\text{Service Start}_k = \max(\text{Arrival}_k, \text{Window Open}_k)$. For Fresh outlets, arrival must precede store opening at 08:00 AM.
8. **Cumulative Weekly Fuel Quota**:
   $$\text{weekly\_fuel\_used\_l} + \text{external\_reservations\_l} + \sum_{\text{plan trips}} \text{trip\_fuel\_litres} \le \text{weekly\_fuel\_quota\_l}$$
9. **Elimination of Task 2B 270/480 Min Budgets**: In Hackathon mode, arbitrary flat minute budgets (270/480) are not imposed; feasibility is determined by window compliance and physical vehicle chronology.

### 4.4 Unresolved Operational Policies & Required Backend Inputs
1. **Dynamic Congestion Formula**: The Challenge Booklet defines `traffic_speed.csv` ($100$ = clear road) and `road_conditions.csv` ($100$ = normal), but does not prescribe an official mathematical formula combining them. **Until formally agreed with the backend/domain owners, this formula is marked UNRESOLVED.** The engine provides a pluggable speed factor interface:
   $$\text{speed\_factor} = f(\text{district}, \text{hour}, \text{monsoon}, \text{date})$$
2. **Return Travel & Turnaround Estimation**: Return travel from the district to the depot and depot turnaround duration are required inputs or documented estimation policies (`depot_turnaround_duration_min`). In this implementation, return distance and free-flow duration from a district to its depot mirror the outbound `DistrictTravel` values (`depot_to_district_km` and `depot_to_district_freeflow_min`) as an explicit estimation policy. Turnaround duration requires an explicit input or the named policy `ESTIMATED_DEPOT_TURNAROUND_MIN` (e.g. 30.0 min); unexplained defaults are prohibited.
3. **Coverage Boundaries & No Automatic Fallback**: `calendar.csv` and `road_conditions.csv` span `2024-01-01` to `2026-06-28`. If a caller selects `travel_policy="dynamic_conditions"` and the planning date is outside this horizon, the engine returns a structured missing-data error (`MISSING_OPERATIONAL_DATA`); automatic silent fallback to clear-road data is forbidden. A static estimated-travel policy (`travel_policy="static_freeflow"`) is allowed only when explicitly requested, and its assumptions and limitations must be clearly indicated in the result. Travel data covers only the 12 documented districts from Peliyagoda and Kandy; unsupported districts or cross-district routes are rejected due to lack of travel data.

---

## 5. Proposed Python API Entry Points (Specification Only)

*(The following entry points are proposed interfaces; they are not yet implemented in engine code).*

### Entry Point 1: Generate Daily Draft Plan
```python
def generate_daily_draft_plan(
    orders: list[Order],
    fleet: list[Vehicle],
    reference_data: ReferenceData,
    operational_context: OperationalContext,
    config: Optional[OptimizerConfig] = None,
) -> PlanResponse:
    """
    Generate an automated daily draft allocation plan from confirmed orders.

    Executed by the backend after the 4:00 PM order cutoff. Runs portfolio search
    actively guided by delivery windows and fuel quotas.

    Guarantees:
      - Does not perform database operations.
      - Produces an independently validated PlanResponse.
      - Returns whole-order assignments and evidence-based deferrals.
    """
```

### Entry Point 2: Evaluate Edited Draft Plan (Assisted Planning)
```python
def evaluate_edited_draft(
    base_plan: PlanResponse,
    edit_actions: list[PlanEditAction],
    authoritative_orders: list[Order],
    authoritative_fleet: list[Vehicle],
    reference_data: ReferenceData,
    operational_context: OperationalContext,
) -> PlanResponse:
    """
    Evaluate manual adjustments made by the Dispatcher without mutating base_plan.

    Supported Edit Actions:
      - MoveWholeOrderAction(order_ref, target_vehicle_id, target_trip_number)
      - MoveLineItemAction(order_ref, line_item_id, quantity, target_vehicle_id, target_trip_number)
      - SplitLineItemAction(order_ref, line_item_id, splits=[{"target_vehicle_id": str, "target_trip_number": int, "quantity": num}])
      - DeferLineItemAction(order_ref, line_item_id, quantity, manual_reason)
      - ReinstateLineItemAction(order_ref, line_item_id, quantity, target_vehicle_id, target_trip_number)
      - ReorderStopsAction(trip_id, new_stop_sequence)

    Guarantees:
      - Non-mutating: Evaluates against authoritative orders and fleet state, returning a new PlanResponse.
      - Recomputes stop arrival times, waiting times, service windows, and cumulative fuel.
      - If order lacks line-item breakdown, line-item actions raise ITEM_LEVEL_EDITS_UNSUPPORTED.
    """
```

### Entry Point 3: Dynamic Breakdown Recovery
```python
def reallocate_broken_vehicle(
    active_plan: PlanResponse,
    recovery_time_iso: str,
    broken_vehicle_id: str,
    undelivered_line_items: list[UndeliveredItemDemand],
    goods_pickup_location: str,
    available_fleet: list[Vehicle],
    locked_commitments: list[str],
    reference_data: ReferenceData,
    operational_context: OperationalContext,
) -> PlanResponse:
    """
    Reallocate undelivered quantities from an immobilised vehicle during the dispatch day.

    Preserves unaffected commitments:
      - In-flight or completed trips on other vehicles (listed in locked_commitments) remain frozen.
      - Attempts insertion into vehicles with remaining trip capacity or uncommitted Trip 2 slots.
      - goods_pickup_location specifies where stock is located:
        - "DEPOT": Standard reload at depot.
        - "ROADSIDE:{outlet_id}": Requires roadside transfer geometry. If unsupported by travel data,
          the engine explicitly returns UNSUPPORTED_TRANSFER_GEOMETRY and marks items deferred.
    """
```

---

## 6. Separation of Responsibilities

| Capability / Concern | Implemented in Optimizer | To Be Added to Optimizer | Handled by Web Backend |
| :--- | :---: | :---: | :---: |
| Immutable domain entities (`Order`, `Vehicle`, `Outlet`, `TripResult`) | ✅ Yes | | |
| Static vehicle compatibility (van access, reefer, depot matching) | ✅ Yes | | |
| Portfolio Greedy heuristic & Targeted CP-SAT (Task 2B core) | ✅ Yes | | |
| Reference CSV loaders (`outlets`, `travel`, `allowance`, `vehicles`) | ✅ Yes | | |
| Strict JSON serialization (`allow_nan=False`) | ✅ Yes | | |
| Line-item data model & quantity-level split conservation | | ⏳ Needed | |
| Chronological stop scheduler (Arrival, Waiting, Service Start/End, Propagation) | | ⏳ Needed | |
| Outlet delivery window validation & lateness margin calculation | | ⏳ Needed | |
| Cumulative fuel quota tracker with external reservation subtraction | | ⏳ Needed | |
| LIFO warehouse loading sequence projection (for Loaders) | | ⏳ Needed | |
| Non-mutating manual plan edit evaluator (`evaluate_edited_draft`) | | ⏳ Needed | |
| Breakdown recovery entry point (`reallocate_broken_vehicle`) | | ⏳ Needed | |
| Database persistence (PostgreSQL / SQLite ORM) | | | ✅ Backend |
| User authentication & role-based permissions (4 roles) | | | ✅ Backend |
| 4:00 PM order cutoff enforcement & order status transitions | | | ✅ Backend |
| Dispatcher plan approval & official commit action | | | ✅ Backend |
| Driver mobile offline synchronization & POD capture | | | ✅ Backend |
| Warehouse Loader tablet interface & discrepancy logging | | | ✅ Backend |

---

## 7. Illustrative Request & Response Example (Internally Consistent)

*(The following payloads are illustrative examples showing the target interface format).*

### Example 7.1: Illustrative `PlanRequest` Payload
```json
{
  "planning_date": "2026-10-03",
  "timezone": "Asia/Colombo",
  "depot": "Peliyagoda",
  "departure_time_fresh_iso": "2026-10-03T04:00:00+05:30",
  "depot_turnaround_duration_min": 30.0,
  "orders": [
    {
      "order_ref": "ORD0001",
      "outlet_id": "OUT001",
      "temp_requirement": "ambient",
      "deferred_prev": false,
      "defer_count": 0,
      "is_urgent": false,
      "line_items": [
        {
          "line_item_id": "ITEM-001-A",
          "description": "Dry Groceries Assorted Crate",
          "quantity": 15,
          "quantity_unit": "crates",
          "unit_weight_kg": 16.7,
          "unit_volume_m3": 0.213
        }
      ]
    },
    {
      "order_ref": "ORD0002",
      "outlet_id": "OUT002",
      "temp_requirement": "chilled",
      "deferred_prev": true,
      "defer_count": 2,
      "is_urgent": true,
      "line_items": [
        {
          "line_item_id": "ITEM-002-A",
          "description": "Fresh Dairy & Chilled Juice",
          "quantity": 10,
          "quantity_unit": "crates",
          "unit_weight_kg": 18.0,
          "unit_volume_m3": 0.180
        }
      ]
    }
  ],
  "fleet": [
    {
      "vehicle_id": "VEH001",
      "is_mechanically_available": true,
      "is_selected_for_planning": true,
      "remaining_trips": 2,
      "earliest_availability_iso": "2026-10-03T03:30:00+05:30",
      "weekly_fuel_quota_l": 340.0,
      "weekly_fuel_used_l": 185.5,
      "external_reservations_l": 0.0
    }
  ]
}
```

### Example 7.2: Illustrative `PlanResponse` Payload
```json
{
  "plan_id": "PLAN-20261003-PEL-V1",
  "status": "FEASIBLE",
  "planning_date": "2026-10-03",
  "engine_mode": "hackathon_operational",
  "runtime_seconds": 0.84,
  "order_counts": {
    "total_orders": 2,
    "fully_served_orders": 2,
    "partially_served_orders": 0,
    "fully_deferred_orders": 0
  },
  "quantity_totals": {
    "requested_units": 25,
    "assigned_units": 25,
    "deferred_units": 0
  },
  "priority_boosted_orders": [
    {
      "order_ref": "ORD0002",
      "reason": "deferred_prev; defer_count=2; approved_urgency"
    }
  ],
  "metrics": {
    "total_weight_kg": 430.5,
    "total_volume_m3": 5.0,
    "total_distance_km": 48.0,
    "total_fuel_litres": 10.21,
    "trips_created": 1,
    "vehicles_used": 1
  },
  "trips": [
    {
      "trip_id": "PLAN-20261003-PEL-V1-TRIP-VEH001-1",
      "vehicle_id": "VEH001",
      "trip_number": 1,
      "brand": "fresh",
      "district": "Colombo",
      "depot": "Peliyagoda",
      "departure_time_iso": "2026-10-03T04:00:00+05:30",
      "depot_return_arrival_iso": "2026-10-03T06:10:00+05:30",
      "vehicle_next_available_iso": "2026-10-03T06:40:00+05:30",
      "load_utilization": {
        "weight_kg": 430.5,
        "weight_cap_kg": 5510.0,
        "volume_m3": 5.0,
        "volume_cap_m3": 26.4
      },
      "fuel": {
        "distance_km": 48.0,
        "fuel_consumed_l": 10.21,
        "weekly_quota_l": 340.0,
        "prior_used_l": 185.5,
        "external_reservations_l": 0.0,
        "cumulative_fuel_used_l": 195.71,
        "fuel_compliant": true
      },
      "driver_itinerary": [
        {
          "stop_number": 1,
          "order_ref": "ORD0001",
          "outlet_id": "OUT001",
          "line_items_delivered": [
            { "line_item_id": "ITEM-001-A", "quantity": 15 }
          ],
          "dock_type": "street",
          "parking_constraint": "van_only",
          "arrival_time_iso": "2026-10-03T04:24:00+05:30",
          "waiting_duration_min": 36.0,
          "service_start_time_iso": "2026-10-03T05:00:00+05:30",
          "service_duration_min": 16.0,
          "departure_time_iso": "2026-10-03T05:16:00+05:30",
          "delivery_window": {
            "open_iso": "2026-10-03T05:00:00+05:30",
            "close_iso": "2026-10-03T07:30:00+05:30"
          },
          "window_compliant": true,
          "lateness_margin_min": 150.0
        },
        {
          "stop_number": 2,
          "order_ref": "ORD0002",
          "outlet_id": "OUT002",
          "line_items_delivered": [
            { "line_item_id": "ITEM-002-A", "quantity": 10 }
          ],
          "dock_type": "street",
          "parking_constraint": "van_only",
          "arrival_time_iso": "2026-10-03T05:24:00+05:30",
          "waiting_duration_min": 6.0,
          "service_start_time_iso": "2026-10-03T05:30:00+05:30",
          "service_duration_min": 16.0,
          "departure_time_iso": "2026-10-03T05:46:00+05:30",
          "delivery_window": {
            "open_iso": "2026-10-03T05:30:00+05:30",
            "close_iso": "2026-10-03T08:00:00+05:30"
          },
          "window_compliant": true,
          "lateness_margin_min": 150.0
        }
      ],
      "loader_manifest": [
        {
          "loading_step": 1,
          "delivering_stop_number": 2,
          "order_ref": "ORD0002",
          "outlet_id": "OUT002",
          "line_item_id": "ITEM-002-A",
          "quantity": 10,
          "quantity_unit": "crates",
          "weight_kg": 180.0,
          "volume_m3": 1.8,
          "temp_requirement": "chilled"
        },
        {
          "loading_step": 2,
          "delivering_stop_number": 1,
          "order_ref": "ORD0001",
          "outlet_id": "OUT001",
          "line_item_id": "ITEM-001-A",
          "quantity": 15,
          "quantity_unit": "crates",
          "weight_kg": 250.5,
          "volume_m3": 3.2,
          "temp_requirement": "ambient"
        }
      ]
    }
  ],
  "deferred_orders": [],
  "validation": {
    "valid": true,
    "errors": [],
    "recomputed_served_count": 2,
    "recomputed_deferred_count": 0,
    "recomputed_penalty": 0.0
  }
}
```
