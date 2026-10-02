# Waypoint Hybrid Optimization Engine

## 1. Purpose

The Waypoint optimizer is a competition prototype for generating a feasible daily delivery plan.

It receives:

- confirmed delivery orders;
- current vehicle availability;
- vehicle capacity and refrigeration information;
- depot and outlet restrictions;
- delivery windows;
- service allowances;
- supported travel-time data;
- fuel information;
- previous deferral information.

It returns a dispatcher-editable draft containing:

- assigned orders;
- deferred orders;
- vehicle assignments;
- trip numbers;
- ordered delivery stops;
- estimated arrival and service times;
- capacity and fuel information;
- validation results;
- structured deferral reasons;
- optimization-stage information.

The optimizer does not approve plans or write directly to the database. The backend stores the draft, and the Dispatcher approves it.

---

## 2. Competition Scope

This engine is designed for the Waypoint Hackathon application.

It is not the Datathon Task 2B submission and does not blindly inherit Task 2B assumptions.

The engine uses:

- real backend orders;
- real fleet state;
- real reference CSV data;
- multi-start greedy allocation;
- targeted CP-SAT improvement;
- independent operational validation;
- dispatcher review and approval.

The current travel data provides district/depot-level travel information. It is not a complete GPS road-network dataset.

Therefore, the engine supports:

- supported travel-time estimation;
- chronological delivery scheduling;
- fuel estimation based on supported travel data;
- delivery-window evaluation.

It does not claim exact GPS shortest-path routing unless verified geographic route data is available.

---

## 3. Authoritative Data

Production reference data consists of:

```text
outlets.csv
vehicles.csv
district_travel.csv
service_allowance.csv
calendar.csv
traffic_speed.csv
road_conditions.csv
```

Confirmed orders and live fleet state are supplied by the backend database.

Example files and synthetic fixtures are used only for testing and demonstrations. They are not used as production order input.

---

## 4. Why This Type of Engine Was Chosen

### 4.1 The problem is constrained operational optimization

The Waypoint problem is not mainly a prediction problem.

The engine must decide:

- which vehicle should serve each order;
- which orders can be served together;
- how trips should be formed;
- in what sequence stops should be visited;
- whether delivery windows can be satisfied;
- whether vehicle capacity and fuel are sufficient;
- which orders must be deferred.

These decisions are connected by hard operational constraints.

A plan is not useful if it:

- overloads a vehicle;
- assigns chilled goods to an incompatible vehicle;
- misses a delivery window;
- uses unavailable travel data;
- exceeds fuel quota;
- creates overlapping trips.

Therefore, the selected method must support constraint-aware allocation and scheduling.

---

## 5. Why Machine Learning Was Not Selected as the Main Optimizer

Machine learning is useful when historical labelled data exists for learning predictions or decisions.

The competition data does not contain a large historical dataset showing:

- the Dispatcher’s preferred plan;
- the correct priority for every order;
- historical vehicle assignment decisions;
- measured business penalties;
- enough examples of breakdown and recovery decisions.

A machine-learning model would therefore require unsupported assumptions.

A prediction model also cannot automatically guarantee hard constraints. It could suggest an assignment that is:

- over capacity;
- outside the delivery window;
- incompatible with refrigeration;
- invalid for the depot;
- over the fuel quota.

The current problem requires guaranteed feasibility and explainability more than prediction accuracy. Explicit optimization and independent validation are therefore more suitable.

---

## 6. Why a Single Greedy Algorithm Was Not Enough

A greedy algorithm is fast and easy to explain, but its result depends heavily on the order in which orders are processed.

For example:

1. a large order is assigned first;
2. the only compatible vehicle becomes full;
3. several smaller urgent orders cannot be assigned;
4. the final plan is feasible but operationally poor.

To reduce this weakness, the engine generates multiple greedy plans using different priority orderings.

However, greedy allocation still makes decisions incrementally and may fail to discover a better reassignment later.

Therefore, greedy is used as a fast and reliable baseline, not as the only optimization method.

---

## 7. Why a Full Global CP-SAT Model Was Not Used Alone

CP-SAT is powerful for assignment and scheduling problems, but a complete daily model can contain:

- many orders;
- many vehicles;
- multiple trips;
- delivery windows;
- service durations;
- fuel limits;
- capacity limits;
- vehicle restrictions;
- depot restrictions;
- sequencing relationships.

A global model may require more computation and a much more complex formulation.

There is also a modelling risk: if one operational rule is missing from the mathematical model, the solver may return a mathematically valid but operationally invalid plan.

For a competition application that must remain responsive and explainable, using global CP-SAT as the only planner would create unnecessary risk.

---

## 8. Why the Hybrid Architecture Was Selected

The hybrid architecture combines the strengths of both methods:

| Requirement                      | Design response             |
| -------------------------------- | --------------------------- |
| Fast initial planning            | Multi-start greedy baseline |
| Better use of remaining capacity | Targeted CP-SAT improvement |
| Operational safety               | Independent validator       |
| Failure resilience               | Greedy fallback             |
| Dispatcher trust                 | Explainable draft output    |

The complete workflow is:

```text
Input validation
      ↓
Multi-start greedy allocation
      ↓
Best feasible greedy baseline
      ↓
Targeted CP-SAT improvement
      ↓
Independent operational validation
      ↓
Accept improvement or retain greedy
      ↓
Dispatcher-editable draft
```

---

## 9. Multi-Start Greedy Allocation

The greedy stage generates several candidate plans using different order-priority strategies.

Possible strategies include:

- urgent orders first;
- earliest delivery-window closing first;
- previously deferred orders first;
- longest service gap first;
- fresh/window-sensitive orders first.

Each candidate is checked against all hard operational constraints.

The best valid candidate becomes the baseline plan.

This is stronger than relying on one arbitrary order because the planner explores several reasonable starting policies.

---

## 10. Targeted CP-SAT Improvement

The CP-SAT stage does not rebuild the entire daily plan.

It focuses on a local neighbourhood containing:

- high-priority deferred orders;
- relevant compatible vehicles;
- relevant trips;
- local reassignment opportunities.

The CP-SAT candidate replaces the greedy baseline only when:

1. it satisfies every hard constraint;
2. it passes independent operational validation;
3. it strictly improves the baseline objective.

The CP-SAT result is rejected when:

- the solver times out;
- the model is infeasible;
- required travel or allowance data is missing;
- the reconstructed schedule is invalid;
- the objective is not better;
- an exception occurs.

When rejected, the original greedy plan is returned.

---

## 11. Feasibility Before Preference

The optimizer separates feasibility from preference.

### Feasibility checks

A candidate is rejected if it violates:

- vehicle weight capacity;
- vehicle volume capacity;
- refrigeration compatibility;
- vehicle access restrictions;
- depot compatibility;
- vehicle availability;
- delivery windows;
- service allowances;
- trip chronology;
- remaining trips;
- fuel quota;
- supported travel coverage;
- line-item conservation;
- configured brand/district policy.

### Preference comparison

Only valid candidates are compared using:

- urgency;
- delivery-window pressure;
- deferral history;
- service gap;
- number of orders served;
- fuel;
- travel;
- deterministic tie-breaking.

A priority score can never compensate for an invalid assignment.

---

## 12. Priority Hierarchy

Because this is a competition prototype and historical production decisions are not available, the optimizer uses a transparent policy hierarchy:

```text
1. Hard feasibility
2. Urgent and delivery-window-critical orders
3. Repeatedly deferred or long-unserved orders
4. Maximum number of valid deliveries
5. Fuel and travel efficiency
6. Deterministic tie-breaking
```

This hierarchy reflects operational reasoning:

- an invalid plan cannot be dispatched;
- urgent windows may create immediate service risk;
- repeated deferrals create unfair service;
- serving more valid orders improves coverage;
- fuel and travel efficiency matter after service requirements are protected.

---

## 13. Context-Aware Priority Score

The optimizer does not permanently assume that urgent orders always come first or that deferred orders always come first.

Priority depends on the current planning situation.

A general score is:

```text
priority_score =
      urgency_weight
    × urgency_score

    + window_weight
    × window_pressure_score

    + deferral_weight
    × deferral_debt_score

    + service_gap_weight
    × service_gap_score

    + business_weight
    × business_priority_score
```

The factors are normalized before being combined.

| Factor            | Meaning                                                 |
| ----------------- | ------------------------------------------------------- |
| Urgency           | Whether the order requires immediate attention          |
| Window pressure   | How close the delivery window is to closing             |
| Deferral debt     | How often the order has previously been deferred        |
| Service gap       | How long the outlet has gone without service            |
| Business priority | Explicit priority supplied by the backend or Dispatcher |

The same order may receive a different score on a later planning day because its urgency, service gap, or deferral history can change.

---

## 14. Basis for Costs and Weights

The exact numerical weights are not claimed to be universal constants or learned from historical production data.

The supplied competition data contains operational reference information such as:

- vehicle capacity;
- travel estimates;
- outlet restrictions;
- service allowances;
- traffic and road conditions.

It does not contain:

- historical Dispatcher decisions;
- labelled correct priorities;
- historical deferral outcomes;
- measured business penalties;
- agreed monetary trade-offs between urgency and fuel.

Therefore, the numerical weights are treated as:

```text
transparent, configurable competition-policy parameters
```

Their design basis is the operational hierarchy:

- feasibility is mandatory;
- urgent and window-critical deliveries need protection;
- repeated deferrals need to be reduced;
- valid service coverage should be maximized;
- fuel and travel should be optimized after service obligations.

These weights are therefore policy defaults, not arbitrary claims of universal optimality.

They are validated through controlled competition scenarios and edge-case tests.

Future calibration could use:

- Dispatcher decisions;
- historical deferral records;
- delivery-window performance;
- service gaps;
- fuel usage;
- agreed service-level targets.

That future calibration is outside the current competition prototype scope.

---

## 15. Why Urgency and Deferral History Can Both Matter

### Example A: urgent order receives priority

```text
Order A:
- urgent;
- delivery window closes soon;
- never deferred.

Order B:
- normal;
- deferred once;
- flexible delivery window.
```

Order A should normally be preferred because missing its delivery window creates immediate service risk.

### Example B: repeated deferral receives priority

```text
Order A:
- moderately urgent;
- flexible delivery window.

Order B:
- deferred several times;
- outlet has not been served for several days.
```

Order B may receive greater priority because continuously ignoring the same outlet creates a fairness problem.

The optimizer therefore evaluates the current normalized factors rather than enforcing one permanent precedence rule.

---

## 16. Cost Components

Costs are considered only after hard feasibility has been satisfied.

| Cost or reward                     | Purpose                                  |
| ---------------------------------- | ---------------------------------------- |
| Served-order reward                | Encourages serving more valid orders     |
| Priority-adjusted deferral penalty | Penalizes deferring important orders     |
| Repeated-deferral penalty          | Prevents starvation of the same outlet   |
| Fuel cost                          | Encourages efficient fuel usage          |
| Travel cost                        | Encourages efficient supported travel    |
| Window-risk cost                   | Discourages plans close to late delivery |
| Deterministic tie-breaker          | Produces stable repeatable output        |

Fuel and travel costs must not dominate urgent service requirements.

Conceptually:

```text
invalid plan → reject
valid plans → compare using priorities and costs
```

---

## 17. Deferral Decision Process

An order is deferred only after feasible placement options have been tested.

```text
1. Find compatible vehicles.
2. Test weight and volume.
3. Test refrigeration.
4. Test depot and access restrictions.
5. Test delivery-window feasibility.
6. Test service duration and chronology.
7. Test fuel and trip availability.
8. Assign if a valid option exists.
9. Defer only if no valid option remains.
```

### Deferral categories

#### Structurally unavoidable

The required capability is unavailable.

```text
NO_COMPATIBLE_VEHICLE
UNSUPPORTED_TRAVEL_DATA
DELIVERY_WINDOW_UNFEASIBLE
```

#### Resource limitation

The order could be served in principle, but current resources are insufficient.

```text
CAPACITY_EXHAUSTED
FUEL_QUOTA_EXCEEDED
TRIPS_EXHAUSTED
```

#### Heuristic trade-off

The order was feasible, but another combination produced a better current plan.

```text
NOT_SELECTED_BY_HEURISTIC
```

This must not be presented as proof that the order was globally impossible to serve.

---

## 18. Edge-Case Behaviour

### No compatible vehicle

A chilled order with no available reefer vehicle is deferred with:

```text
NO_COMPATIBLE_VEHICLE
```

### Capacity exceeded

The optimizer tries another compatible vehicle or trip. If no valid option remains, it defers the order.

### Early arrival

The vehicle waits until the delivery window opens:

```text
service_start = max(arrival_time, window_open_time)
```

### Late arrival

The candidate is rejected. If every option is late, the order is deferred.

### Fuel quota exhausted

The vehicle is rejected for that assignment. Another compatible vehicle is attempted.

### Repeated deferral

The order accumulates deferral debt and receives higher future priority.

### Multiple orders at one outlet

Multiple orders may share one physical stop when supported by the operational data. Order count must not automatically be treated as physical-stop count.

### CP-SAT timeout or failure

The valid greedy baseline is returned.

### Invalid CP-SAT result

The independent validator rejects the result, and the greedy baseline remains final.

### Equal-priority orders

Deterministic tie-breakers are used, such as:

1. earlier delivery-window closing time;
2. higher deferral debt;
3. stable order reference.

---

## 19. Independent Operational Validation

The final candidate is independently checked after reconstruction.

Validation includes:

- assignments;
- capacity totals;
- refrigeration;
- depot compatibility;
- access restrictions;
- stop sequence;
- arrival timestamps;
- waiting times;
- service times;
- delivery windows;
- vehicle chronology;
- fuel usage;
- line-item conservation;
- deferred quantities.

The process is:

```text
solver candidate
→ reconstruct operational schedule
→ independently validate
→ accept or reject
```

This provides a safety boundary between optimization and dispatch readiness.

---

## 20. Dispatcher-in-the-Loop Design

The optimizer returns a draft rather than making an irreversible decision.

The Dispatcher can:

- review vehicle assignments;
- inspect priority scores;
- inspect deferral reasons;
- move orders;
- defer or reinstate orders;
- split supported line items;
- review capacity and fuel;
- approve the final plan.

Every manual edit is re-evaluated against authoritative data.

This makes the system an assisted-planning engine rather than an opaque automatic decision-maker.

---

## 21. Explainability Output

The final plan should expose:

- selected algorithm;
- whether CP-SAT was attempted;
- whether CP-SAT was accepted;
- baseline objective;
- final objective;
- priority score;
- priority factors;
- deferral reason;
- validation result;
- approval status.

Example:

```json
{
  "algorithm": "hybrid_greedy_targeted_cpsat",
  "cpsat_attempted": true,
  "cpsat_accepted": true,
  "validation_valid": true,
  "approval_status": "DRAFT_REQUIRES_DISPATCHER_APPROVAL",
  "deferred_orders": [
    {
      "order_ref": "ORD014",
      "priority_score": 82,
      "reason": "FUEL_QUOTA_EXCEEDED"
    }
  ]
}
```

---

## 22. Competition Evaluation

The engine should be evaluated using controlled scenarios.

Important cases include:

- urgent order versus repeatedly deferred order;
- unavailable refrigerated vehicle;
- narrow delivery window;
- capacity overload;
- fuel quota exhaustion;
- vehicle breakdown;
- missing travel data;
- CP-SAT improvement;
- CP-SAT timeout;
- invalid CP-SAT candidate.

Useful metrics include:

- orders served;
- orders deferred;
- urgent orders served;
- repeated deferrals;
- on-time delivery rate;
- fuel usage;
- number of vehicles used;
- planning runtime;
- validation failures.

The main comparison is:

```text
multi-start greedy baseline
versus
hybrid greedy + targeted CP-SAT
```

The hybrid result is reported as better only when it is both valid and objectively improved.

---

## 23. Current Strengths

The engine provides:

- real-data integration;
- constraint-aware allocation;
- multiple greedy starting strategies;
- targeted mathematical improvement;
- independent validation;
- explainable deferral reasons;
- context-aware priority handling;
- dispatcher editing;
- breakdown recovery;
- safe fallback behaviour;
- database draft persistence;
- authentication-protected planning routes.

Current verification includes:

```text
218 optimizer tests passed
47 backend tests passed
Alembic check passed
Optimizer imports passed
FastAPI imports passed
```

---

## 24. Limitations

The engine does not claim:

- global mathematical optimality;
- learned priority weights from historical production data;
- universal business-cost values;
- automatic Dispatcher approval.

These limitations are explicit because this is a competition prototype.

The numerical weights are transparent policy assumptions validated through controlled scenarios. They can be recalibrated later if historical planning decisions become available.

---

## 25. Final Competition Statement

The Waypoint optimizer is a policy-governed hybrid operational planning engine.

It generates multiple feasible greedy plans, selects the strongest baseline, applies targeted CP-SAT improvement to difficult deferred cases, independently validates the result, and safely falls back to the greedy plan whenever the improvement is invalid or not beneficial.

Its priorities are transparent:

```text
feasibility first;
urgency and delivery windows next;
fairness for repeatedly deferred outlets;
maximum valid service;
then fuel and travel efficiency.
```

The engine is strong because it combines optimization quality with operational safety, explainability, and human control.

Its design is not based on an unsupported claim of perfect global optimality. It is designed to produce a fast, valid, explainable, and improvable delivery plan for the Waypoint competition.
