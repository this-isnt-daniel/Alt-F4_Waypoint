# Waypoint — Schema Design Document (v2 — Reconciled)

> **Status: TEAM CONTRACT.**
> This document merges the original locked schema, the driver-back PR design, and all decisions made during the session audit.
> Every field has a defined, non-overlapping meaning. If a new field is needed, define it here first — don't add an undefined column and figure out its meaning later.
> Field names match the Challenge Booklet's own CSV vocabulary (`outlets.csv`, `vehicles.csv`, `calendar.csv`) wherever the booklet defines a term.

---

## 1. Enums

*(Agree on these first — nothing else can be built until these are fixed.)*

```
Brand               = fresh | style | tech
TempReq             = ambient | chilled          -- NOT "dry", NOT "mixed". Matches vehicles.csv / outlets.csv.
VehicleType         = truck | van
VehicleTemp         = reefer | ambient
DockType            = rear_dock | street | mall_bay
ParkConstraint      = normal | van_only | mall_dock
UserRole            = store_manager | dispatcher | loader | driver
OrderStatus         = draft | confirmed | planned | loaded | out_for_delivery | delivered | deferred
TripStatus          = planned | loaded | out_for_delivery | completed
StopStatus          = upcoming | arrived | delivered | skipped
                      -- partial delivery = 'delivered' with SUM(trip_stop_item.qty_returned) > 0
                      -- failed delivery  = 'skipped' with trip_stop.skip_reason set
ReturnStatus        = pending | confirmed
ConflictStatus      = in_review | forwarded | resolved | dismissed
ConflictResolution  = accept_driver | keep_server | dismiss
LoadCheckStatus     = ok | shortfall
LoadCheckItemStatus = ok | shortfall | damaged
DiscrepancyType     = missing | damaged | wrong_item | short_qty | other
DiscrepancyStatus   = open | resolved
DeliveryEventType   = order_confirmed | order_planned | order_loaded
                    | order_out_for_delivery | order_delivered | order_deferred
EventSyncStatus     = pending | applied | conflict | failed | already_applied
```

> **On `TempReq = ambient | chilled`:** An order is either ambient or chilled — never "mixed". The booklet rule is one ambient + one chilled order per outlet per delivery date, not a third "mixed" type. The `UNIQUE(outlet_id, order_date, temp_req)` constraint on `order` enforces this.

> **On ambient items in reefer vehicles:** A reefer vehicle CAN carry ambient goods (the reverse is not true — ambient vehicles cannot carry chilled goods). When this happens, `trip_stop.forced_reefer = TRUE` is set so the dispatcher has an audit trail of the override.

---

## 2. Reference Tables

*(Seeded once from the shared datasets — read-only to all four apps.)*

### Depot

```sql
depot (
  depot_id   TEXT PRIMARY KEY,   -- 'peliyagoda', 'kandy'
  name       TEXT NOT NULL,
  lat        NUMERIC,
  lng        NUMERIC
)
```

### Outlet — seeded from `outlets.csv`

```sql
outlet (
  outlet_id          TEXT PRIMARY KEY,  -- 'OUT001' … 'OUT120'
  name               TEXT NOT NULL,
  brand              TEXT NOT NULL CHECK (brand IN ('fresh', 'style', 'tech')),
  district           TEXT,
  depot_id           TEXT REFERENCES depot(depot_id),
  lat                NUMERIC,
  lng                NUMERIC,

  -- Delivery window (derived once at order creation — see Section 5)
  window_open        TEXT,              -- 'HH:MM'
  window_close       TEXT,             -- 'HH:MM'
  mall_window        TEXT,             -- 'HH:MM-HH:MM' | NULL (only for mall outlets)

  -- Access constraints (from outlets.csv)
  dock_type          TEXT CHECK (dock_type IN ('rear_dock', 'street', 'mall_bay')),
  park_constraint    TEXT CHECK (park_constraint IN ('normal', 'van_only', 'mall_dock'))
)
```

### Vehicle — seeded from `vehicles.csv`

```sql
vehicle (
  vehicle_id        TEXT PRIMARY KEY,  -- 'VEH001' … 'VEH060'
  depot_id          TEXT REFERENCES depot(depot_id) NOT NULL,
  type              TEXT NOT NULL CHECK (type IN ('truck', 'van')),
  temp              TEXT NOT NULL CHECK (temp IN ('reefer', 'ambient')),
  weight_cap_kg     NUMERIC NOT NULL,  -- payload capacity in kg
  vol_cap_m3        NUMERIC NOT NULL,  -- volume capacity in m³
  fuel_type         TEXT,              -- 'diesel' | 'petrol' | 'electric'
  km_per_l          NUMERIC,
  fuel_quota_l      INTEGER,           -- weekly fuel quota in litres
  plate             TEXT,

  -- Availability (edge case: vehicle in workshop today)
  status            TEXT NOT NULL DEFAULT 'available'
                      CHECK (status IN ('available', 'in_workshop')),

  -- Live location (updated by driver app)
  last_lat          NUMERIC,
  last_lng          NUMERIC,
  last_seen_at      TIMESTAMPTZ
)
```

> **Fuel quota check:** `fuel_quota_l` alone cannot answer "how much is left this week." The Dispatcher backend sums `trip.est_fuel_l` per vehicle per week to check remaining quota before assigning a new trip. Once a trip completes, `trip.actual_fuel_l` (written by Driver) is used for real tracking.

### Product — seeded by Store Manager side, read by everyone

```sql
product (
  product_id    TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  brand         TEXT NOT NULL CHECK (brand IN ('fresh', 'style', 'tech')),
  category      TEXT,                  -- 'dry_groceries', 'chilled_frozen', etc.
  temp_req      TEXT NOT NULL CHECK (temp_req IN ('ambient', 'chilled')),
  unit          TEXT NOT NULL,         -- 'kg_case', 'l_bottle', 'crate', 'carton'
  unit_wt_kg    NUMERIC,               -- weight per unit
  unit_vol_m3   NUMERIC,              -- volume per unit
  active        BOOLEAN NOT NULL DEFAULT TRUE
)
```

---

## 3. Core Workflow Entities

*(Every role touches these — the shared backbone.)*

### User — unified table, roles enforced at creation

```sql
user (
  user_id         TEXT PRIMARY KEY,    -- 'USR001'
  username        TEXT NOT NULL UNIQUE, -- login identifier
  role            TEXT NOT NULL CHECK (role IN
                    ('store_manager', 'dispatcher', 'loader', 'driver')),
  outlet_id       TEXT REFERENCES outlet(outlet_id),
                  -- NOT NULL when role = store_manager; NULL otherwise
  depot_id        TEXT REFERENCES depot(depot_id),
                  -- NOT NULL when role IN (dispatcher, loader, driver); NULL otherwise
  name            TEXT NOT NULL,
  hashed_pw       TEXT NOT NULL
)
```

> **Constraint:** `role = store_manager` → `outlet_id` NOT NULL, `depot_id` NULL.
> `role IN (dispatcher, loader, driver)` → `depot_id` NOT NULL, `outlet_id` NULL.
> Enforce at creation — an account can never have both or neither set.

> **JWT payload on login:**
> ```json
> { "sub": "USR001", "role": "store_manager", "outlet_id": "OUT001" }
> ```

### Order

```sql
order (
  order_id        TEXT PRIMARY KEY,    -- 'ORD-1042'
  outlet_id       TEXT REFERENCES outlet(outlet_id) NOT NULL,
  created_by      TEXT REFERENCES user(user_id) NOT NULL,  -- store_manager
  brand           TEXT NOT NULL CHECK (brand IN ('fresh', 'style', 'tech')),
  temp_req        TEXT NOT NULL CHECK (temp_req IN ('ambient', 'chilled')),
  order_date      DATE NOT NULL,       -- requested delivery date
  submitted_at    TIMESTAMPTZ,         -- NULL while still a draft
  cutoff_at       TIMESTAMPTZ,         -- order_date − 1 day, 16:00 Asia/Colombo
  status          TEXT NOT NULL DEFAULT 'draft' CHECK (status IN (
                    'draft',           -- SM building order, not yet submitted
                    'confirmed',       -- SM submitted, not yet planned by dispatcher
                    'planned',         -- Dispatcher assigned to a trip
                    'loaded',          -- Loader verified cargo on truck
                    'out_for_delivery', -- Truck departed depot
                    'delivered',       -- Receipt confirmed by SM
                    'deferred'         -- Pushed to a future date
                  )),

  -- Calculated on confirm (see Section 4)
  order_units     INTEGER,             -- sum of line item quantities
  order_wt_kg     NUMERIC,             -- sum of line_item.qty × product.unit_wt_kg
  order_vol_m3    NUMERIC,

  -- Delivery window (derived once at creation — see Section 5)
  window_open     TEXT,               -- 'HH:MM'
  window_close    TEXT,               -- 'HH:MM'

  -- Written by Dispatcher during planning
  trip_id         TEXT REFERENCES trip(trip_id),    -- NULL until planned
  stop_seq        INTEGER,            -- position within the trip (1 = first)
  exp_arrival     TEXT,               -- 'HH:MM' estimate from Dispatcher

  -- Written by Driver on delivery
  actual_arrival  TEXT,               -- 'HH:MM' actual

  -- Priority flag: auto-set when this order has been deferred from the previous day
  -- Dispatcher allocation UI should surface these at the top of the unallocated queue
  deferred_prev   BOOLEAN NOT NULL DEFAULT FALSE,
  defer_count     INTEGER NOT NULL DEFAULT 0,  -- running total of times deferred

  UNIQUE (outlet_id, order_date, temp_req)
  -- Max one ambient + one chilled order per outlet per delivery date, any status
)
```

> **`deferred_prev` / `defer_count`:** replaces the old `UrgentNeed` table. When a `DeferralRecord` is created, the backend increments `order.defer_count` and sets `order.deferred_prev = TRUE` if `DeferralRecord.original_date = today`. The Dispatcher's allocation screen sorts unallocated orders by `deferred_prev DESC, defer_count DESC` so repeat-deferred orders surface first.

> **Draft lifecycle rule for `POST /orders`:**
> - Matching **draft** exists → update / reuse that draft.
> - Matching **non-draft** exists (confirmed … deferred) → return a **409 Conflict**.
> - No match → create a new draft.
>
> The DB constraint stays simple and absolute; the application prevents unsafe overwrites.

> **No `order.vehicle_id`:** Vehicle is always derived via `order.trip_id → trip.vehicle_id` — one source of truth, nothing to keep in sync.

### OrderLineItem

```sql
order_line (
  line_item_id   TEXT PRIMARY KEY,
  order_id       TEXT REFERENCES order(order_id) NOT NULL,
  product_id     TEXT REFERENCES product(product_id) NOT NULL,
  quantity       INTEGER NOT NULL
)
```

---

## 4. Logistics Planning

> **C.5 resolved:** Multiple orders per vehicle are supported via `trip_stop`, but a **single order cannot be split across trips or vehicles**.
> Enforced by `UNIQUE (order_id)` on `trip_stop`. Max 2 trips per vehicle per day is enforced by `CHECK(trip_no IN (1,2))`.

### Trip

```sql
trip (
  trip_id         TEXT PRIMARY KEY,    -- 'TRIP-P01-04'
  vehicle_id      TEXT REFERENCES vehicle(vehicle_id) NOT NULL,
  driver_id       TEXT REFERENCES user(user_id),
                  -- NULL until the Dispatcher assigns a driver
                  -- (POST /dispatcher/trips/{trip_id}/assign-driver).
                  -- Every Driver API call checks trip.driver_id = JWT sub.
  dispatcher_id   TEXT REFERENCES user(user_id) NOT NULL,  -- who created the trip
  depot_id        TEXT REFERENCES depot(depot_id) NOT NULL,
  trip_date       DATE NOT NULL,
  trip_no         INTEGER NOT NULL CHECK (trip_no IN (1, 2)),
                  -- max 2 trips per vehicle per day
  brand           TEXT CHECK (brand IN ('fresh', 'style', 'tech')),
                  -- target NOT NULL; nullable until every planning path writes it
  district        TEXT,
  status          TEXT NOT NULL DEFAULT 'planned' CHECK (status IN (
                    'planned', 'loaded', 'out_for_delivery', 'completed'
                  )),

  -- Planned fields (written by Dispatcher)
  plan_depart     TEXT,                -- 'HH:MM' planned departure
  plan_return     TEXT,                -- 'HH:MM' estimated return
  dist_km         NUMERIC,             -- planned route distance
  est_fuel_l      NUMERIC,             -- dist_km ÷ vehicle.km_per_l

  -- Actual fields (written by Driver)
  actual_depart   TIMESTAMPTZ,
  actual_return   TIMESTAMPTZ,
  actual_dist_km  NUMERIC,
  actual_fuel_l   NUMERIC,             -- use this for real quota tracking post-trip

  UNIQUE (vehicle_id, trip_date, trip_no)
)
```

> **Status transitions — one role per transition:**
> | Role | Transition |
> |---|---|
> | Dispatcher | (created) → `planned` |
> | Loader | `planned` → `loaded` |
> | Driver | `loaded` → `out_for_delivery` |
> | Driver | `out_for_delivery` → `completed` |
>
> **Driver trip rules:**
> - `loaded → out_for_delivery` (depart) is rejected for `trip_no = 2` until the same driver's `trip_no = 1` on the same `trip_date` is `completed`. The Driver API exposes this as a derived `locked` flag — there is no `locked` status.
> - `out_for_delivery → completed` (return to depot) requires every stop to be `delivered` or `skipped` and every `return_custody` row for the trip to be `confirmed`.

> **`trip.brand` / `trip.district` constraint:** The Dispatcher's allocation logic must reject assigning an order whose brand/district doesn't match the trip. Don't trust the caller — validate on write.

### TripStop

```sql
trip_stop (
  stop_id          TEXT PRIMARY KEY,
  trip_id          TEXT REFERENCES trip(trip_id) NOT NULL,
  outlet_id        TEXT REFERENCES outlet(outlet_id) NOT NULL,
  order_id         TEXT REFERENCES order(order_id) NOT NULL,
  stop_seq         INTEGER NOT NULL,  -- delivery order (1 = first stop)
  pack_seq         INTEGER,           -- loading order (1 = last loaded = first off)
                                      -- target NOT NULL; nullable until every planning path writes it
  eta              TEXT,              -- 'HH:MM' estimate
  wt_kg            NUMERIC,
  vol_m3           NUMERIC,
  temp_req         TEXT CHECK (temp_req IN ('ambient', 'chilled')),
  forced_reefer    BOOLEAN NOT NULL DEFAULT FALSE,
                   -- TRUE when ambient goods are loaded into a reefer vehicle
                   -- as a fallback (capacity constraint). Audit trail only.
  status           TEXT NOT NULL DEFAULT 'upcoming' CHECK (status IN (
                     'upcoming', 'arrived', 'delivered', 'skipped'
                   )),
  row_version      INTEGER NOT NULL DEFAULT 1,
                   -- optimistic concurrency for driver offline sync.
                   -- Bumped by every Driver state change and by route-change resequencing.

  -- Written by Driver
  arrived_at       TIMESTAMPTZ,       -- actual arrival (order.actual_arrival is the 'HH:MM' Asia/Colombo copy)
  arrival_lat      NUMERIC,           -- GPS at arrival, when the device supplies it
  arrival_lng      NUMERIC,
  completed_at     TIMESTAMPTZ,       -- when the outcome (delivered / skipped) was recorded
  skip_reason      TEXT,              -- NOT NULL when status = 'skipped'

  UNIQUE (order_id)
  -- A single order cannot be split across multiple trips or vehicles
)
```

### TripStopItem

```sql
trip_stop_item (
  item_id         TEXT PRIMARY KEY,
  stop_id         TEXT REFERENCES trip_stop(stop_id) NOT NULL,
  line_item_id    TEXT REFERENCES order_line(line_item_id) NOT NULL,
  qty_assigned    NUMERIC NOT NULL,
  qty_loaded      NUMERIC,            -- NULL until Loader records it
  qty_delivered   NUMERIC,            -- NULL until Driver records checklist / outcome
  qty_returned    NUMERIC,            -- NULL until Driver records checklist / outcome
                                      -- invariant: qty_delivered + qty_returned = qty_loaded
                                      -- (falls back to load_check_item.loaded_qty, then qty_assigned)
  unit            TEXT NOT NULL,
  sku             TEXT,
  handling_note   TEXT                -- 'Fragile', 'Stack max 3' etc.
)
```

> If a planning path created a `trip_stop` without `trip_stop_item` rows, the Driver backend materialises them from `order_line` on departure so the driver manifest is frozen at the moment the van leaves.

---

## 5. Delivery Window Derivation Rule

*(Applied once at order creation by the Store Manager backend — never re-derived downstream.)*

```python
if outlet.brand == "fresh":
    window_open, window_close = "03:30", "08:00"
elif outlet.mall_window is not None:
    window_open, window_close = outlet.mall_window.split("-")
else:
    window_open, window_close = outlet.window_open, outlet.window_close
```

Every downstream role (Dispatcher, Loader, Driver) trusts `order.window_open` / `order.window_close` as already correct. No one re-derives this.

---

## 6. Loader Verification

> **LoadCheck is the Loader's sign-off before departure.** A shortfall or damaged item does NOT automatically defer the order — the Dispatcher actively decides whether to ship partially or raise a `DeferralRecord`.

### LoadCheck — one per trip

```sql
load_check (
  check_id        TEXT PRIMARY KEY,
  trip_id         TEXT REFERENCES trip(trip_id) NOT NULL UNIQUE,
  checked_by      TEXT REFERENCES user(user_id) NOT NULL, -- loader
  checked_at      TIMESTAMPTZ NOT NULL,
  status          TEXT NOT NULL CHECK (status IN ('ok', 'shortfall')),
  note            TEXT,
  client_op_id    TEXT UNIQUE          -- idempotency key
)
```

### LoadCheckItem — one per order line within the trip

```sql
load_check_item (
  chk_item_id     TEXT PRIMARY KEY,
  check_id        TEXT REFERENCES load_check(check_id) NOT NULL,
  line_item_id    TEXT REFERENCES order_line(line_item_id) NOT NULL,
  exp_qty         INTEGER NOT NULL,    -- what the manifest expected
  loaded_qty      INTEGER NOT NULL,    -- what actually went on the truck
  status          TEXT NOT NULL CHECK (status IN ('ok', 'shortfall', 'damaged')),
  note            TEXT
)
```

---

## 7. Delivery Handover & Proof

> **C.2 resolved:** `DeliveryReceipt` is entirely separate from `order`. `order.status = 'delivered'` is only set after `ReceiptConfirmation` is created.
> **C.3 resolved:** OTP is generated by the Driver and entered by the Store Manager — one shared row per stop.
> **Driver-side POD** (`proof_of_delivery`) and **SM-side confirmation** (`receipt_confirmation`) are separate tables; each has its own concerns.

### ProofOfDelivery — written by Driver at outlet

```sql
proof_of_delivery (
  pod_id            TEXT PRIMARY KEY,
  order_id          TEXT REFERENCES order(order_id) NOT NULL UNIQUE,
  stop_id           TEXT REFERENCES trip_stop(stop_id) NOT NULL,
  delivered_by      TEXT REFERENCES user(user_id) NOT NULL,  -- driver
  delivered_at      TIMESTAMPTZ NOT NULL,
  otp_code          TEXT NOT NULL,           -- 6-digit PIN shown to SM; generated server-side
                                             -- when the Driver opens the POD (first POD call)
  otp_verified      BOOLEAN NOT NULL DEFAULT FALSE,
                                             -- set TRUE by the SM receipt flow when the entered OTP matches
  signature_url     TEXT,
  photo_url         TEXT,                    -- object key of the POD photo ('pod/{stop_id}/…')
  notes             TEXT,
  recorded_offline  BOOLEAN NOT NULL DEFAULT FALSE,
  synced_at         TIMESTAMPTZ,
  client_op_id      TEXT UNIQUE             -- idempotency key
)
```

### ReceiptConfirmation — written by Store Manager

```sql
receipt_confirmation (
  confirm_id      TEXT PRIMARY KEY,
  order_id        TEXT REFERENCES order(order_id) NOT NULL UNIQUE,
  pod_id          TEXT REFERENCES proof_of_delivery(pod_id) NOT NULL,
  confirmed_by    TEXT REFERENCES user(user_id) NOT NULL,  -- store_manager
  confirmed_at    TIMESTAMPTZ NOT NULL,
  items_ok        BOOLEAN NOT NULL,         -- FALSE if any discrepancy raised
  client_op_id    TEXT UNIQUE
)
```

---

## 8. Discrepancy

> **C.6 + C.7 resolved:** One table covers all reporters — Loader (pre-departure) and Store Manager (post-delivery). Every row is attributed to an authenticated user. Driver discrepancies are captured via the event ledger (`driver_events`) rather than this table, since the driver is offline-first.

```sql
discrepancy (
  disc_id           TEXT PRIMARY KEY,
  order_id          TEXT REFERENCES order(order_id) NOT NULL,
  line_item_id      TEXT REFERENCES order_line(line_item_id),
  raised_by         TEXT REFERENCES user(user_id) NOT NULL,  -- loader | store_manager
  source_stage      TEXT NOT NULL CHECK (source_stage IN ('loading', 'receipt')),

  -- Source link (exactly one of these is set)
  chk_item_id       TEXT REFERENCES load_check_item(chk_item_id),
                    -- set when raised during loading
  confirm_id        TEXT REFERENCES receipt_confirmation(confirm_id),
                    -- set when raised at receipt

  type              TEXT NOT NULL CHECK (type IN (
                      'missing', 'damaged', 'wrong_item', 'short_qty', 'other'
                    )),
  exp_qty           INTEGER,
  recv_qty          INTEGER,
  description       TEXT,
  status            TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved')),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at       TIMESTAMPTZ,
  resolved_by       TEXT REFERENCES user(user_id),
  resolution_note   TEXT,
  client_op_id      TEXT UNIQUE
)
```

> **Cardinality:** One `receipt_confirmation` → 0..many `discrepancy`. Don't cap at one.

---

## 9. Deferrals

> **Deferred-order lifecycle:** `DeferralRecord.new_date` is the next planned service date. The order row is **not** duplicated.
> On `new_date`, Dispatcher assigns the order to a trip and moves `order.status` from `deferred` → `planned`.
> If deferred again, create another `DeferralRecord` and increment `order.defer_count`.

```sql
deferral (
  deferral_id       TEXT PRIMARY KEY,
  order_id          TEXT REFERENCES order(order_id) NOT NULL,
  outlet_id         TEXT REFERENCES outlet(outlet_id) NOT NULL,
  original_date     DATE NOT NULL,
  new_date          DATE,              -- NULL until dispatcher reschedules
  reason            TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by        TEXT REFERENCES user(user_id) NOT NULL, -- dispatcher
  trip_id           TEXT REFERENCES trip(trip_id),           -- NULL for pre-departure deferrals
  client_op_id      TEXT UNIQUE
)
```

> **`order.deferred_prev` flag:** when a `DeferralRecord` is inserted, the backend must:
> 1. Increment `order.defer_count`.
> 2. Set `order.deferred_prev = TRUE` if `original_date = today`.
> This surfaces the order at the top of the Dispatcher's unallocated queue the next day.

---

## 10. Global Delivery Event Timeline

> An append-only timeline covering every role's status transitions. Distinct from `driver_events` (which is driver-only, offline-first). This table is the backbone of every "in progress" screen and history view.

```sql
delivery_event (
  event_id        TEXT PRIMARY KEY,
  order_id        TEXT REFERENCES order(order_id) NOT NULL,
  event_type      TEXT NOT NULL CHECK (event_type IN (
                    'order_confirmed', 'order_planned', 'order_loaded',
                    'order_out_for_delivery', 'order_delivered', 'order_deferred'
                  )),
  occurred_at     TIMESTAMPTZ NOT NULL,
  actor_role      TEXT NOT NULL,        -- which role triggered this event
  actor_id        TEXT REFERENCES user(user_id),
  note            TEXT,
  offline         BOOLEAN NOT NULL DEFAULT FALSE,
  synced_at       TIMESTAMPTZ,          -- NULL if not yet synced
  client_op_id    TEXT UNIQUE           -- idempotency for offline/retry-safe writes
)
```

---

## 11. Driver Offline Sync & Event Ledger

> **Architectural note:** The Driver portal is offline-first. Instead of mutating state directly (which fails with no signal), driver actions are appended to `driver_events`. State (`trip_stop.status`) is materialised from these events. Optimistic concurrency via `row_version` on `trip_stop` prevents corruption during sync.

### Driver Event Ledger

```sql
driver_events (
  event_id            TEXT PRIMARY KEY,
  driver_id           TEXT NOT NULL REFERENCES user(user_id),
  device_id           TEXT,
  client_event_id     TEXT NOT NULL UNIQUE, -- idempotency on retry
  kind                TEXT NOT NULL,        -- 'stop.arrived', 'stop.delivered', 'breakdown', etc.
  stop_id             TEXT REFERENCES trip_stop(stop_id),
  trip_id             TEXT REFERENCES trip(trip_id),
  payload             TEXT,                 -- JSON blob
  occurred_at         TIMESTAMPTZ,          -- device-local time of the event
  received_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  applied_at          TIMESTAMPTZ,
  status              TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
                        'pending', 'applied', 'conflict', 'failed', 'already_applied'
                      )),
  row_version_before  INTEGER,              -- the version the driver expected
  row_version_after   INTEGER,
  error               TEXT
)
```

> **Supported `kind` values** (the same handlers serve the REST endpoints and `/events/sync`):
> `trip.departed`, `trip.completed`, `stop.arrived`, `checklist.submitted`, `pod.photo.completed`,
> `pod.submitted`, `stop.outcome.submitted`, `return.created`, `depot_return.confirmed`, `route_change.acknowledged`.
> Checklist lines and photo evidence live in `payload`; their effect is materialised onto
> `trip_stop_item.qty_delivered / qty_returned` and `proof_of_delivery.photo_url`.
>
> **Idempotency:** a repeated `client_event_id` returns `already_applied` (or the original `conflict`)
> and never re-applies. A `failed` event may be retried with the same `client_event_id`.

### Conflicts — raised when offline sync hits a version mismatch

```sql
conflict (
  conflict_id         TEXT PRIMARY KEY,
  stop_id             TEXT REFERENCES trip_stop(stop_id),
  driver_event_id     TEXT REFERENCES driver_events(event_id),
  driver_json         TEXT,             -- state the driver thought they were editing
  system_json         TEXT,             -- actual server state at sync time
  status              TEXT NOT NULL DEFAULT 'in_review' CHECK (status IN (
                        'in_review', 'forwarded', 'resolved', 'dismissed'
                      )),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  forwarded_at        TIMESTAMPTZ,
  resolved_at         TIMESTAMPTZ,
  resolved_by         TEXT REFERENCES user(user_id),
  resolved_by_role    TEXT,
  resolution          TEXT CHECK (resolution IN ('accept_driver', 'keep_server', 'dismiss')),
  resolution_note     TEXT
)
```

> **Resolution:** `accept_driver` re-applies the driver's event against the current `row_version`;
> `keep_server` closes the conflict without changing the entity; `dismiss` sets status `dismissed`.
> Driver may forward (`in_review → forwarded`); Dispatcher of the trip's depot resolves.

### Return Custody — goods travelling back to the depot

```sql
return_custody (
  return_id           TEXT PRIMARY KEY,
  trip_id             TEXT NOT NULL REFERENCES trip(trip_id),
  stop_id             TEXT NOT NULL REFERENCES trip_stop(stop_id),
  driver_id           TEXT NOT NULL REFERENCES user(user_id),
  items               TEXT NOT NULL,      -- JSON [{item_id, line_item_id, product_id, qty}]
  reason              TEXT,
  return_crate        TEXT,
  status              TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed')),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_event_id    TEXT REFERENCES driver_events(event_id),
  confirmed_at        TIMESTAMPTZ,
  confirmed_event_id  TEXT REFERENCES driver_events(event_id),
  officer_name        TEXT,               -- depot officer who received the goods
  condition           TEXT                -- 'seal_intact', 'damaged', …
)
```

> Created automatically by a partial / failed outcome, or explicitly by `POST /driver/stops/{id}/return`.
> Confirmed at the depot by `POST /driver/returns/{id}/depot-confirm`.

### Route Changes — Dispatcher → Driver push

```sql
route_change (
  change_id       TEXT PRIMARY KEY,
  trip_id         TEXT NOT NULL REFERENCES trip(trip_id),
  change_type     TEXT NOT NULL,        -- 'stop_added', 'stop_cancelled', 'resequence', etc.
  payload         TEXT NOT NULL,        -- JSON blob of the change
  issued_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  issued_by       TEXT REFERENCES user(user_id),
  acknowledged    BOOLEAN NOT NULL DEFAULT FALSE,
  ack_at          TIMESTAMPTZ
)
```

---

## 12. Vehicle Incidents

```sql
vehicle_incident (
  incident_id     TEXT PRIMARY KEY,
  vehicle_id      TEXT REFERENCES vehicle(vehicle_id) NOT NULL,
  trip_id         TEXT REFERENCES trip(trip_id),
  type            TEXT NOT NULL CHECK (type IN (
                    'breakdown', 'pre_trip_failure', 'reefer_failure', 'other'
                  )),
  detail          TEXT,
  reported_by     TEXT REFERENCES user(user_id),
  reported_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at     TIMESTAMPTZ
)
```

---

## 13. Calculated Fields — Where They Are Computed, and by Whom

| Field | Computed by | When |
|---|---|---|
| `order.order_units` / `order_wt_kg` / `order_vol_m3` | Store Manager backend | `POST /orders/{id}/confirm` — sum of `line_item.qty × product.unit_wt_kg / unit_vol_m3` |
| `order.window_open` / `window_close` | Store Manager backend | Order creation — Section 5 rule |
| `order.exp_arrival` | Dispatcher backend | During trip/route planning |
| `trip.est_fuel_l` | Dispatcher backend | `trip.dist_km ÷ vehicle.km_per_l` |
| `order.deferred_prev` / `defer_count` | Any backend creating a `deferral` row | On `DeferralRecord` insert |
| Trip capacity / time totals | Dispatcher backend | When assigning orders to a trip |

**Derived at read-time — do NOT add these as columns:**

| Derived field | Rule |
|---|---|
| **"Flagged" history badge** | `order.status = 'delivered' AND discrepancy count > 0` → show as Flagged |
| **Open-flags scorecard count** | sum of `discrepancy.status = 'open'` + unresolved conflicts |
| **Repeat-deferral warning** | `order.defer_count > 1` or `deferred_prev = TRUE` — compute at read-time |
| **Remaining weekly fuel** | `vehicle.fuel_quota_l − SUM(trip.est_fuel_l)` per vehicle per week |

---

## 14. Relationships at a Glance

```
Outlet ──< Order >── Trip >── Vehicle
   │       (vehicle derived only via order.trip_id → trip.vehicle_id;
   │        no separate order.vehicle_id)
   │
   ├──< OrderLine >── Product
   ├──< DeliveryEvent
   ├──< DeferralRecord
   ├──< ProofOfDelivery ── ReceiptConfirmation ──< Discrepancy
   └──< Discrepancy >── OrderLine

Trip ── TripStop ──< TripStopItem >── OrderLine
Trip ── 0..1 LoadCheck ──< LoadCheckItem >── OrderLine
Trip ──< RouteChange
Trip ──< DriverEvents >── TripStop
TripStop ──< ReturnCustody
TripStop ──< Conflict >── DriverEvents
LoadCheckItem ── 0..many Discrepancy
ReceiptConfirmation ── 0..many Discrepancy

User ──(role)── store_manager | dispatcher | loader | driver
User ──< Order.created_by
User ──< Trip.driver_id
User ──< Trip.dispatcher_id
User ──< DriverEvents.driver_id
User ──< ReturnCustody.driver_id
User ──< DeferralRecord.created_by
User ──< LoadCheck.checked_by
User ──< ProofOfDelivery.delivered_by
User ──< ReceiptConfirmation.confirmed_by
User ──< Discrepancy.raised_by
User ──< Discrepancy.resolved_by
```

---

## 15. Derived / UI-Only Fields (Not Persisted)

| Field | Reason |
|---|---|
| `vehicle.checked` | Dispatcher session toggle — resets each day |
| `vehicle.status_badge` | Computed from `trip.status` for map display |
| Trip delay label `"Delayed (+14m)"` | Computed from `trip_stop.eta` vs. current time |
| `outlet.totalDemand` | Aggregate of `trip_stop_item.qty_assigned` rows |
| `outlet.status_badge` | Computed from all assigned `trip_stop.status` values |
| `product.showImages` | Per-subcategory UI hint — stays in frontend config |
| `category.icon` | Lucide icon name — stays in frontend config |
| `activeStage` integer | Derived by mapping `order.status` through the 5-step UI array |
| UI expand/collapse state | Pure UI interaction state |
| `isAllocationConfirmed`, toast flags | UI feedback state |

---

## 16. `client_op_id` Idempotency Pattern

> A flaky connection (driver taps "Delivered," times out, and retries) can create duplicate rows.
> **Rule:** Every table where a flaky connection could cause a retry-duplicate has a `client_op_id TEXT UNIQUE` column. The client generates this once and sends it with the request; the server checks for an existing row with that ID before inserting.

**Tables carrying `client_op_id`:**
`deferral`, `load_check`, `proof_of_delivery`, `receipt_confirmation`, `discrepancy`, `delivery_event`

`driver_events` uses the same pattern under the name `client_event_id` (every Driver write — REST or offline sync — carries one).

---

## 17. One Database or Four?

**Recommended:** one shared Postgres database, one schema, all four FastAPI services connecting to it. Each service owns writing to its tables but all read from the same source. This avoids sync problems and is simpler to seed and demo for judges with one `docker compose up`.

SQLite is used for local development and tests only. Standard SQL is used throughout (no SQLite-specific syntax) so the switch to Postgres is just a connection string change.

> The Driver API now runs on this shared database (`/api/v1/driver-platform/*`). The legacy SQLite driver-back routes (`/api/driver/*`, `/api/v1/driver/*`, schema in `app/database.py`) are deprecated and will be removed once the frontend has moved over.

---

## 18. ⚑ Flags — Open Decisions & Implementation Risks

> These are not schema problems — they are application-logic decisions that must be made before writing the FastAPI services.

| # | Flag | Detail |
|---|---|---|
| F1 | **`forced_reefer` enforcement** | The schema records when ambient goods go into a reefer vehicle via `trip_stop.forced_reefer = TRUE`, but the Dispatcher UI must warn the user before allowing the override. Define the exact UX trigger (tooltip, modal, or hard block). |
| F2 | **`deferred_prev` reset timing** | `order.deferred_prev` should be reset to FALSE once the order is successfully re-planned. Decide: reset on `order.status → planned`, or only on `status → delivered`? |
| F3 | **Cutoff boundary race** | Orders submitted at exactly 16:00:00 Asia/Colombo — is that in or out? Define as `submitted_at < cutoff_at` (strictly before) and document it. |
| F4 | **Concurrent status-transition writes** | Two dispatchers could try to assign the same order simultaneously. The `UNIQUE(order_id)` on `trip_stop` will cause a DB error on the second write — the API must return a clean 409, not a 500. |
| F5 | **`trip.brand` / `trip.district` validation** | The constraint that all orders on a trip must match `trip.brand` / `trip.district` is application-level, not a DB constraint. Every `POST /trips/{id}/assign-order` must validate this explicitly. |
| F6 | **OTP expiry on SQLite** | `BOOLEAN GENERATED ALWAYS AS (now() > expires_at) STORED` is Postgres syntax. On SQLite, compute `is_expired` in the application layer, not as a generated column. |
| F7 | **Loader discrepancy vs. driver discrepancy** | Loader discrepancies use the `discrepancy` table. Driver discrepancies use `driver_events` (kind = `discrepancy_raised`). Downstream consumers (Dispatcher dashboard) must aggregate from both sources to get the full picture. |
| F8 | **`order.actual_arrival` time zone** | **Decided:** `order.actual_arrival` is `HH:MM` in Asia/Colombo local time (same clock as `window_open` / `window_close`). The exact instant is in `trip_stop.arrived_at` (TIMESTAMPTZ). |
| F9 | **`stop_seq` duplication** | `order.stop_seq` and `trip_stop.stop_seq` both exist. `trip_stop.stop_seq` is canonical; `order.stop_seq` is a denormalized copy written at the same time by the Dispatcher for convenience (avoids a join on the SM tracking screen). If they ever diverge, `trip_stop` wins. Any code that updates one must update the other in the same transaction. |
| F10 | **OTP verification on receipt** | The Driver backend generates `proof_of_delivery.otp_code`. The Store Manager `confirm_receipt` flow does not yet compare the entered OTP or set `otp_verified = TRUE` — Store Manager team to add. |
| F11 | **Statuses written outside the enums** | Loader writes trip `loading` / `vehicle_unavailable`, stop `loading_complete` / `loaded`, vehicle `unavailable`; Dispatcher recovery writes trip / stop `failed`; Store Manager writes order `delivered_with_discrepancy`. None of these are in Section 1 — owning teams to either add them here or stop writing them before CHECK constraints are introduced. |
| F12 | **Trip planning fields** | `planning_service.confirm_plan` and recovery always write `trip_no = 1`, never write `driver_id`, `brand`, `district`, `pack_seq`. Dispatcher team to populate them. |
