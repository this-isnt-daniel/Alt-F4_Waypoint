# Alt-F4 Waypoint

Waypoint is a logistics planning and delivery operations platform built for the 2026 Tech-Triathlon Hackathon. It models the full order-to-delivery lifecycle for a multi-brand wholesale grocery distribution business across Sri Lanka, connecting store managers, dispatchers, loaders, and drivers through one shared real-time backend.

---

## Contents

- [What the System Does](#what-the-system-does)
- [Repository Structure](#repository-structure)
- [Tech Stack](#tech-stack)
- [Full Stack Deployment (Docker Compose)](#full-stack-deployment-docker-compose)
- [Environment Configuration](#environment-configuration)
- [Seeded Accounts](#seeded-accounts)
- [Seeded Scenarios](#seeded-scenarios)
- [Role Portals](#role-portals)
- [Judge Walkthrough](#judge-walkthrough)
- [API Overview](#api-overview)
- [Operational Constraints Enforced](#operational-constraints-enforced)
- [Designathon Departures](#designathon-departures)
- [Testing](#testing)
- [CI Pipeline](#ci-pipeline)

---

## What the System Does

Waypoint manages an end-to-end wholesale delivery operation across three retail brands (Fresh, Style, Tech):

1. **Store Manager** — creates and confirms orders for their outlet; raises urgency flags; confirms physical receipt on delivery
2. **Dispatcher** — runs the hybrid optimizer to generate delivery plans; reviews, edits, and approves plans; handles incidents and recovery
3. **Loader** — verifies the manifest against physical stock at the depot before a vehicle departs
4. **Driver** — executes the trip on the road; operates offline-first with event sync on reconnection

Every action is stored as an immutable event and surfaced as a live operational audit trail.

---

## Repository Structure

```text
Alt-F4_Waypoint/
├── apps/
│   ├── backend/                 # FastAPI backend, SQLAlchemy models, routers, services, tests
│   │   ├── app/
│   │   │   ├── api/v1/          # Routers: auth, store-manager, dispatcher, loader, driver-platform, vehicles, orders
│   │   │   ├── core/            # Security (JWT, bcrypt), config
│   │   │   ├── db/              # SQLAlchemy session and base
│   │   │   ├── models/          # SQLAlchemy ORM models (18 models)
│   │   │   ├── schemas/         # Pydantic v2 schemas
│   │   │   ├── services/        # Domain services + dispatcher sub-services
│   │   │   └── adapters/        # Optimizer adapter
│   │   ├── optimization_engine/ # Hybrid optimizer: greedy + CP-SAT + recovery + validator
│   │   ├── alembic/             # Database migration versions
│   │   ├── tests/               # 20 test files covering all portals
│   │   └── seed.py              # Idempotent scenario seeder
│   └── frontend/                # React/Vite SPA with 5 portals
│       └── src/
│           ├── driver/          # Driver PWA (offline-first state machine)
│           └── pages/           # dispatcher/, loader/, storemanager/, storemanager_style/, storemanager_tech/
├── docs/                        # Architecture, schema, backend design, optimizer, testing docs
├── datathon/                    # Datathon notebooks and CSV submissions
├── designathon/                 # Designathon links and screens
├── docker-compose.yml           # Full 5-service orchestrator
├── .env.example                 # Environment variable template
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| ORM & Migrations | SQLAlchemy 2.0, Alembic |
| Authentication | BCrypt password hashing, JWT Bearer tokens (`python-jose`) |
| Database | PostgreSQL 15 |
| Optimizer | Google OR-Tools (CP-SAT), NumPy — multi-start greedy + targeted CP-SAT |
| Containerisation | Docker, Docker Compose v2 |
| CI | GitHub Actions (Python 3.11 + ephemeral PostgreSQL 15) |

---

## Full Stack Deployment (Docker Compose)

### Prerequisites

- Docker Engine and Docker Compose v2
- Git

### 1. Environment Setup

```bash
cp .env.example .env
```

No changes are required from the defaults for local testing.

### 2. Start the Stack

```bash
docker compose down -v       # wipe any previous state
docker compose build         # build backend + frontend images
docker compose up -d         # start all services
```

Services start in strict dependency order via Docker healthchecks:

```
postgres  →(healthy)→  migrate  →(exit 0)→  seed  →(exit 0)→  backend  →(healthy)→  frontend
```

### 3. Application URLs

| Service | URL |
|---|---|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000/api/v1 |
| **Backend Health** | http://localhost:8000/health |
| **API Docs (Swagger)** | http://localhost:8000/docs |

### 4. Resetting the Database

```bash
docker compose down -v && docker compose up -d
```

The `-v` flag removes the `postgres_data` volume, giving a clean slate. The seeder is idempotent and safe to run repeatedly without `-v`.

### 5. Checking Service Health

```bash
docker compose ps
docker compose logs backend
docker compose logs seed
```

---

## Environment Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@postgres:5432/waypoint` | PostgreSQL connection string |
| `SECRET_KEY` | `waypoint-driver-hackathon-secret-key-change-in-prod` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT token lifetime |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Allowed frontend origins |
| `VITE_API_URL` | `http://localhost:8000/api/v1` | API base URL baked into the frontend build |

> **Important:** `VITE_API_URL` is baked into the frontend at **build time** by Vite. Changing it in `.env` after the image is built has no effect — rebuild the frontend image if you change this value.

---

## Seeded Accounts

All accounts use password: **`password123`**

### Primary Demo Accounts

| Role | Username | Scope |
|---|---|---|
| **Store Manager (Fresh)** | `storemanager@waypoint.local` | Outlet: `OUT001` — Colpetty Fresh (Colombo) |
| **Store Manager (Style)** | `style@waypoint.local` | Outlet: `OUT015` — Style outlet |
| **Store Manager (Tech)** | `tech@waypoint.local` | Outlet: `OUT021` — Tech outlet |
| **Dispatcher** | `dispatcher@waypoint.local` | Depot: Peliyagoda Central |
| **Loader** | `loader@waypoint.local` | Depot: Peliyagoda Central |
| **Driver (Primary)** | `driver@waypoint.local` | Depot: Peliyagoda — assigned to `VEH-GOLDEN` |
| **Driver (Secondary)** | `driver2@waypoint.local` | Depot: Peliyagoda — Kamal Perera, assigned to `VEH-VAN-01` |

### Fleet Driver Accounts (from `vehicles.csv` if supplied)

When a canonical `vehicles.csv` is mounted at `/app/data/vehicles.csv`, the seeder automatically generates:

| Pattern | Example |
|---|---|
| `driver.{vehicle_id}@waypoint.local` | `driver.veh001@waypoint.local` |
| Password: `password123` | Covers `VEH001` – `VEH060` |

### Seeded Vehicles (Peliyagoda)

| Vehicle ID | Type | Temp | Capacity | Status |
|---|---|---|---|---|
| `VEH-GOLDEN` | Truck | Reefer | 5000 kg / 25 m³ | Available |
| `VEH-VAN-01` | Van | Ambient | 1500 kg / 8 m³ | Available |
| `VEH-FUEL-01` | Truck | Ambient | 5000 kg / 25 m³ | Available (low fuel quota — 10 L) |
| `VEH-WORKSHOP` | Truck | Reefer | 5000 kg / 25 m³ | In Workshop |

| Vehicle ID | Type | Temp | Depot |
|---|---|---|---|
| `VEH-KANDY` | Van | Ambient | Kandy Hub |

---

## Seeded Scenarios

The seeder provisions ready-to-use scenarios for each role's demo path. All scenarios use real model objects — no fake or mocked completion state.

| Scenario | Orders / Trips | Starting State | Demonstrates |
|---|---|---|---|
| **GOLDEN-001** | `GOLDEN-ORD-1` (chilled), `GOLDEN-ORD-2` (ambient) — both `confirmed` | No trip | Store Manager → Dispatcher planning handoff |
| **DRIVER-001** | `TRIP-DRIVER-READY` — `loaded`, 1 stop | Load check OK | Loader → Driver departure and stop execution |
| **LOADING-001** | `TRIP-LOAD-EXCEPTION` — `planned`, loaded qty 18 vs expected 20 | Shortfall discrepancy open | Pre-departure exception workflow |
| **RECOVERY-001** | `TRIP-RECOVERY` — uses `VEH-WORKSHOP` (in workshop) | Incident unresolved | Breakdown recovery dispatcher flow |
| **OFFLINE-001** | `TRIP-OFFLINE` — `loaded`, 1 stop (Kandy depot) | Upcoming | Driver offline execution + event sync |
| **CAPACITY-001** | 15 `confirmed` stress orders for Peliyagoda | No trips | Optimizer capacity and deferral decisions |

---

## Role Portals

The frontend is a single React SPA. The active portal is controlled by the `?portal=` query parameter. All portal URLs below point to [http://localhost:3000](http://localhost:3000).

| Portal | URL | Login Credentials |
|---|---|---|
| Central (role switcher) | `/?portal=central` | *(no login required)* |
| Store Manager – Fresh | `/?portal=grocery` or `/?portal=storemanager` | `storemanager@waypoint.local` / `password123` |
| Store Manager – Style | `/?portal=style` | `style@waypoint.local` / `password123` |
| Store Manager – Tech | `/?portal=tech` | `tech@waypoint.local` / `password123` |
| Dispatcher | `/?portal=dispatcher` | `dispatcher@waypoint.local` / `password123` |
| Loader | `/?portal=loader` | `loader@waypoint.local` / `password123` |
| Driver (PWA) | `/?portal=driver` | `driver@waypoint.local` / `password123` |

---

## Judge Walkthrough

Start at [http://localhost:3000](http://localhost:3000). The full lifecycle can be demonstrated in approximately 10 minutes.

---

### Step 1 — Store Manager: Place an Order

**URL:** `http://localhost:3000/?portal=grocery`  
**Login:** `storemanager@waypoint.local` / `password123`

1. Log in. The overview shows your outlet (`OUT001 — Colpetty Fresh`) with seeded confirmed orders.
2. Click **Place Order** → browse the Fresh product catalog.
3. Add chilled items (Fresh Milk) and ambient items (Rice) to the basket.
4. Select delivery date: **Tomorrow** (next available day; the 14:00 cutoff has passed for today).
5. Click **Review** → **Confirm Order**.
6. The order appears in the **My Orders** tab with status `confirmed`.
7. *(Optional)* Click the order and raise an **Urgency Request** with reason `stockout_risk`.

---

### Step 2 — Dispatcher: Plan and Approve Trips

**URL:** `http://localhost:3000/?portal=dispatcher`  
**Login:** `dispatcher@waypoint.local` / `password123`

1. Log in. The **Orders** tab shows all confirmed orders for Peliyagoda depot — including the one you just placed.
2. Go to **Planning** → click **Optimize** (or **Generate Plan**).
3. The hybrid optimizer runs and returns a `DraftPlan` with vehicle assignments, stop sequences, and capacity metrics.
4. Review the plan: verify vehicle utilisation, temperature compatibility, and any deferred orders.
5. Click **Approve Plan** (or **Confirm Allocations**). Orders transition to `planned`; `Trip` and `TripStop` records are created in the database.
6. Switch to **Roster/Fleet** to see live vehicle positions and active trips.
7. *(Optional)* Open a trip and use **Assign Driver** to assign a specific driver.
8. *(Optional)* Go to **Urgency Requests** → approve the urgency request raised by the store manager.

---

### Step 3 — Loader: Verify the Manifest

**URL:** `http://localhost:3000/?portal=loader`  
**Login:** `loader@waypoint.local` / `password123`

1. Log in. The **Queue** tab shows planned trips at Peliyagoda ready for loading.
2. Select a trip → click **Start Loading**.
3. The **Workbench** shows every stop and each line item with expected quantities.
4. Verify quantities for each item — click the count to mark as verified or enter an actual quantity.
5. *(Optional)* Enter a quantity shortfall on one item to trigger a `short_qty` discrepancy.
6. Click **Finalise Load**. The trip status advances to `loaded`.
7. *(Optional)* Click **Vehicle Unavailable** on a trip to send it back to dispatcher with a reason.

---

### Step 4 — Driver: Execute the Trip

**URL:** `http://localhost:3000/?portal=driver`  
**Login:** `driver@waypoint.local` / `password123`

1. Log in. The driver app shows today's assigned trips (`TRIP-DRIVER-READY` is ready at status `loaded`).
2. Open the trip → click **Depart**. Status → `out_for_delivery`.
3. Navigate to **Stop 1** → click **Arrive**.
4. Submit the delivery **Checklist** for the stop.
5. Tap **Submit POD** — enter delivery details (this generates an OTP code for the store manager).
6. Select **Outcome: Delivered** → confirm delivery units.
7. *(Optional)* Report a **Vehicle Incident** (breakdown) — this creates a `VehicleIncident` record for the dispatcher.
8. Complete all stops → click **Return to Depot** → **Complete Trip**.
9. *(Offline demo)* Toggle the browser to offline mode → complete a stop → reconnect → events automatically sync via `POST /events/sync`.

---

### Step 5 — Store Manager: Confirm Receipt

**URL:** `http://localhost:3000/?portal=grocery`  
**Login:** `storemanager@waypoint.local` / `password123`

1. Log in and go to **My Orders**.
2. The delivered order is visible with status `out_for_delivery`.
3. Click the order → **Confirm Receipt** → enter the OTP from the driver's POD screen.
4. Mark any discrepancies (damaged items, missing quantities).
5. Submit. The order status transitions to `delivered`. Lifecycle closed.

---

### Step 6 (Optional) — Dispatcher: Recovery Flow

**URL:** `http://localhost:3000/?portal=dispatcher`  
**Login:** `dispatcher@waypoint.local` / `password123`

1. Open the **Incidents** tab. The vehicle incident from the driver is listed.
2. Click **Reallocate** → `POST /dispatcher/breakdowns/{vehicle_id}/reallocate`.
3. The recovery optimizer identifies orphaned stops and proposes a rescue assignment using the remaining available fleet.
4. Review and approve the rescue plan. A `RouteChange` is issued to the rescue driver's app.

---

## API Overview

The full OpenAPI schema is available at `http://localhost:8000/docs` once the stack is running.

| Router | Mount Path | Role Required |
|---|---|---|
| Platform Auth | `/api/v1/auth` | Public (login), then authenticated |
| Store Manager | `/api/v1/store-manager` | `store_manager` |
| Dispatcher | `/api/v1/dispatcher` | `dispatcher` |
| Loader | `/api/v1/loader` | `loader` |
| Driver Platform | `/api/v1/driver-platform` | `driver` |
| Fleet | `/api/v1/vehicles` | `dispatcher` |
| Shared Orders | `/api/v1/orders` | Any authenticated role |

See [`docs/architecture.md`](docs/architecture.md) for the complete API surface table with all endpoints listed by router.

---

## Operational Constraints Enforced

All constraints are enforced by the optimizer and validated by the backend before plan approval:

| Constraint | Details |
|---|---|
| **Weight Capacity** | Trip cumulative load ≤ `vehicle.weight_cap_kg` |
| **Volumetric Capacity** | Trip cumulative load ≤ `vehicle.vol_cap_m3` |
| **Temperature Matching** | Chilled orders require reefer vehicles; ambient goods can ride in reefer with `forced_reefer=true` logged |
| **Van-Only Access** | Outlets with `park_constraint = van_only` reject truck assignments |
| **Mall Dock Rules** | `mall_dock` outlets enforce dedicated time windows and vehicle size restrictions |
| **No Order Splitting** | An order is always delivered in full by one vehicle in a single stop |
| **Delivery Time Windows** | All stops must arrive within `window_open` – `window_close` |
| **Weekly Fuel Quota** | Optimizer accounts for cumulative route distance vs `vehicle.fuel_quota_l` |
| **Order Cutoff** | Orders for the next delivery date must be submitted before **14:00 LKT** the day before |

---

## Designathon Departures

This hackathon implementation extends the Designathon submission in the following significant ways:

| Area | Designathon Submission | Hackathon Implementation |
|---|---|---|
| **Planning** | UI mockup and conceptual workflow | Full backend planning service with hybrid OR-Tools CP-SAT optimizer, draft plan persistence, and approval boundary |
| **Optimizer** | Not implemented | Multi-start greedy planner + targeted CP-SAT improvement pass + constraint validator + breakdown recovery engine |
| **Loader** | Basic concept screen | Full loader queue, manifest workbench, item-level identity (`line_item_id` based), verified quantity tracking, shortfall discrepancy creation, idempotent load submission |
| **Driver** | Mobile delivery concept | Offline-first event ledger (append-only), batch sync endpoint, optimistic concurrency via `row_version`, conflict forwarding, POD with photo upload + OTP, return custody, route change polling |
| **Dispatcher** | Allocation screens | Planning, approval, urgency escalation, vehicle incident management, recovery reallocations, route change dispatch, fleet visibility with live location |
| **Store Manager** | Order concept screen | Full multi-brand catalog (Fresh, Style, Tech), order cutoff enforcement, urgency request system with dispatcher approval, delivery OTP receipt confirmation, item-level discrepancy recording |
| **Data** | Conceptual entity diagram | PostgreSQL schema with 18 SQLAlchemy models, Alembic migrations, UNIQUE constraints, CHECK constraints, and foreign key integrity |
| **Audit Trail** | Not present | Immutable `delivery_events` and `driver_events` ledgers; every state change is an event row |
| **CI** | Not present | GitHub Actions workflow running 20 backend test files against an ephemeral PostgreSQL 15 service, plus a frontend Vite build check |

### Known Scope Limitations

The following items are **not** fully implemented and should not be evaluated as complete:

- **Weekly fuel accounting across multiple days** — fuel quota enforcement is per-day optimizer run only
- **Complete POD OTP verification loop** — the OTP is generated and returned in the API response but is not verified by the store manager portal against a backend endpoint in all code paths
- **Real-time push notifications** — route change polling uses client-side polling, not WebSockets
- **Driver portal offline persistence (full)** — the driver state machine is offline-aware but browser local storage sync is not fully hardened in all edge cases

---

## Testing

```bash
# Run all backend tests
cd apps/backend
pytest -q tests

# Compile check (syntax/import validation)
python -m compileall -q app
```

### Test Coverage by Area

| Test File | What It Covers |
|---|---|
| `test_auth_platform.py` | JWT login, role claims, invalid credentials |
| `test_store_manager.py` | Order CRUD, confirmation, receipt, urgency |
| `test_optimizer_backend_flow.py` | Full optimizer integration: plan → confirm → trips |
| `test_loader_backend.py` | Queue, workbench, load check, shortfall, vehicle unavailable |
| `test_driver_platform.py` | Depart, arrive, POD, outcome, sync, conflicts |
| `test_phase2_incidents_route_changes.py` | Vehicle incidents, route change dispatch |
| `test_phase3_recovery.py` | Breakdown recovery optimizer |
| `test_urgency_api_workflow.py` | Store manager escalation → dispatcher approval |
| `test_seed_integrity.py` | Validates seeded data model integrity |
| `test_planning_security_and_alembic.py` | Depot isolation, RBAC security boundary tests |
| `integration/test_golden_e2e.py` | End-to-end golden path: confirm → plan → approve → load → deliver |

---

## CI Pipeline

GitHub Actions workflow (`.github/workflows/tests.yml`) runs on every push and PR to `main`:

1. **Backend**: Python 3.11, installs `requirements.txt`, runs `alembic upgrade head` on an ephemeral PostgreSQL 15 service, then `pytest -q tests`
2. **Frontend**: Node.js 20, installs dependencies, runs `npm run build` to validate the Vite production build

See test result artifacts in `docs/testing/`.
