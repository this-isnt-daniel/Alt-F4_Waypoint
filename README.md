# Alt-F4 Waypoint

Waypoint is a logistics planning and delivery operations platform for the Hackathon stage of the competition. It connects store managers, dispatchers, loaders, and drivers through one shared workflow.

The system is built as a monorepo with:

- a FastAPI backend,
- a React/Vite frontend,
- a PostgreSQL data model,
- a hybrid optimizer module,
- role-based portals for each operational user.

> Repository name note: the competition brief asks for a `TeamName_SolutionName` GitHub monorepo. This repo currently uses `Alt-F4_Waypoint`.

---

## Contents

- [What The System Does](#what-the-system-does)
- [Repository Structure](#repository-structure)
- [Architecture](#architecture)
- [Core Workflow](#core-workflow)
- [Feature Matrix](#feature-matrix)
- [Role Portals](#role-portals)
- [Backend Services](#backend-services)
- [API Surface](#api-surface)
- [Data Model](#data-model)
- [Figures And Screenshots](#figures-and-screenshots)
- [Setup](#setup)
- [Environment Configuration](#environment-configuration)
- [Seeded Accounts](#seeded-accounts)
- [Judge Walkthrough](#judge-walkthrough)
- [Verification Status](#verification-status)
- [Unique Features](#unique-features)
- [Designathon Departures](#designathon-departures)
- [Documentation Map](#documentation-map)
- [Known Gaps Before Final Submission](#known-gaps-before-final-submission)

---

## What The System Does

Waypoint manages the full order-to-delivery lifecycle:

1. Store manager creates and confirms orders.
2. Dispatcher plans trips and handles exceptions.
3. Loader verifies the vehicle manifest before departure.
4. Driver completes the trip and syncs delivery events.
5. Store manager confirms receipt and raises issues if needed.

The platform focuses on operational correctness, auditability, and edge-case handling.

---

## Repository Structure

```text
Alt-F4_Waypoint/
├── apps/
│   ├── backend/                 # FastAPI backend, models, routers, services, tests
│   └── frontend/                # React/Vite frontend for all role portals
├── datathon/                    # Datathon notebooks and CSV submissions
├── designathon/                 # Designathon links and AI disclosure
├── docs/                        # Architecture, schema, backend, optimizer, loader docs
├── docker-compose.yml           # Current DB-only compose file
├── .env.example                 # Environment variable template
├── package.json                 # Root frontend workspace scripts
└── README.md
```

---

## Architecture

![Waypoint workflow overview](docs/readme-assets/workflow-overview.svg)

```mermaid
flowchart TB
    subgraph Frontend["React Frontend"]
        Central["Central Portal"]
        SM["Store Manager Portal"]
        Dispatcher["Dispatcher Portal"]
        Loader["Loader Portal"]
        Driver["Driver Portal"]
    end

    subgraph Backend["FastAPI Backend"]
        Auth["Auth API"]
        Orders["Order API"]
        Planning["Dispatcher Planning API"]
        LoaderAPI["Loader API"]
        DriverAPI["Driver API"]
        Recovery["Incident & Recovery API"]
        OptimizerAdapter["Optimizer Adapter"]
    end

    subgraph Engine["Optimization Engine"]
        Greedy["Greedy Allocation"]
        CPSAT["Targeted CP-SAT"]
        Validator["Constraint Validator"]
        RecoveryEngine["Breakdown Recovery"]
    end

    subgraph Data["PostgreSQL"]
        Users["users"]
        OrdersDB["orders / order_lines"]
        Trips["trips / stops / stop_items"]
        Vehicles["vehicles"]
        Events["delivery_events / driver_events"]
        Issues["discrepancies / incidents / urgency"]
    end

    Central --> SM
    Central --> Dispatcher
    Central --> Loader
    Central --> Driver

    SM --> Orders
    Dispatcher --> Planning
    Loader --> LoaderAPI
    Driver --> DriverAPI

    Orders --> Data
    Planning --> OptimizerAdapter
    LoaderAPI --> Data
    DriverAPI --> Data
    Recovery --> Data
    OptimizerAdapter --> Engine
    Engine --> Data
```

### Main Design Choice

The backend keeps business logic in service modules, not directly inside routers. Routers handle HTTP boundaries. Services enforce workflow rules, role checks, depot ownership, idempotency, and state transitions.

---

## Service Map

![Waypoint service map](docs/readme-assets/service-map.svg)

| Layer | What It Contains | Why It Exists |
|---|---|---|
| Frontend | Central, Store Manager, Dispatcher, Loader, Driver portals | Gives each role a focused workflow |
| API routers | Auth, orders, dispatcher, loader, driver, vehicles | Keeps HTTP boundaries clear |
| Services | Order, planning, loader, driver, recovery services | Holds business rules and state transitions |
| Optimizer | Greedy, CP-SAT, validator, recovery logic | Builds and checks feasible delivery plans |
| Data | PostgreSQL tables and event ledgers | Stores the shared operational truth |

---

## Core Workflow

```mermaid
sequenceDiagram
    participant SM as Store Manager
    participant API as Backend API
    participant DISP as Dispatcher
    participant OPT as Optimizer
    participant LOAD as Loader
    participant DRV as Driver

    SM->>API: Create draft order
    SM->>API: Confirm order
    API->>DISP: Confirmed order appears in planning queue
    DISP->>OPT: Generate draft plan
    OPT-->>DISP: Trips, stops, constraints, validation
    DISP->>API: Approve plan
    LOAD->>API: Open loader queue
    LOAD->>API: Verify line items
    LOAD->>API: Submit load check
    API->>DRV: Trip becomes ready for departure
    DRV->>API: Depart, arrive, deliver, sync events
    SM->>API: Confirm receipt
```

---

## Feature Matrix

| Feature | Store Manager | Dispatcher | Loader | Driver | Backend Support |
|---|---:|---:|---:|---:|---|
| Login and role scope | Yes | Yes | Yes | Yes | JWT role checks |
| Create order | Yes | No | No | No | `order_service` |
| Confirm order | Yes | No | No | No | Order status transition |
| Generate plan | No | Yes | No | No | Optimizer adapter |
| Approve plan | No | Yes | No | No | Trip creation |
| Mark vehicle unavailable | No | Yes | Yes | No | Recovery and loader services |
| Verify load item | No | No | Yes | No | `line_item_id` based checks |
| Submit final load | No | No | Yes | No | Load checks and discrepancies |
| Depart trip | No | No | No | Yes | Driver event ledger |
| Record delivery outcome | No | No | No | Yes | Driver sync API |
| Confirm receipt | Yes | No | No | No | Receipt and discrepancy flow |
| Raise urgency | Yes | Review | No | No | Urgency workflow |

### What Makes The Solution Stand Out

| Area | Baseline Expectation | Our Added Value |
|---|---|---|
| Loader workflow | Mark trip loaded | Item-level verification, discrepancy creation, idempotent submission |
| Dispatcher workflow | Allocate trips | Optimizer draft, approval boundary, recovery workflows |
| Driver workflow | Show route and stops | Event sync, offline-aware ledger, conflict pathway |
| Auditability | Basic status updates | Shared delivery events, driver events, load checks, route changes |
| Operations | Happy path only | Vehicle unavailable, deferrals, shortage, damaged item, urgency, recovery |

---

## Role Portals

| Role | Portal Route | Main Responsibility |
|---|---|---|
| Central access | `/?portal=central` | Opens role-specific portals |
| Store Manager | `/?portal=grocery`, `/?portal=tech`, `/?portal=style` | Create orders, confirm receipt, raise urgency |
| Dispatcher | `/?portal=dispatcher` | Plan trips, approve plans, handle incidents |
| Loader | `/?portal=loader` | Verify manifest and complete load checks |
| Driver | `/?portal=driver` | Execute trip, sync events, record proof of delivery |

---

## Backend Services

| Service Area | Key Files | Purpose |
|---|---|---|
| Auth | `app/api/v1/endpoints/platform_auth.py`, `app/core/security.py` | JWT login and role profile |
| Store Manager | `app/api/v1/store_manager/router.py`, `app/services/order_service.py` | Order creation, confirmation, receipt flow |
| Dispatcher | `app/api/v1/dispatcher/router.py`, `app/services/planning_service.py` | Planning, approval, deferral, urgency review |
| Loader | `app/api/v1/loader/router.py`, `app/services/loader_service.py` | Queue, workbench, load checks, discrepancies |
| Driver | `app/api/v1/driver/router.py`, `app/services/driver_service.py` | Trip execution, event sync, conflict handling |
| Optimizer | `app/adapters/optimizer_adapter.py`, `optimization_engine/` | Allocation, validation, recovery proposals |

---

## API Surface

### Core Auth

| Method | Endpoint | Used By | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | All roles | Authenticate and receive JWT |
| `GET` | `/api/v1/auth/me` | All roles | Load current user profile |

### Store Manager

| Method | Endpoint Group | Purpose |
|---|---|---|
| `GET/POST/PATCH` | `/api/v1/store-manager/...` | Draft, update, and confirm store orders |
| `POST` | `/api/v1/store-manager/orders/{order_id}/receipt` | Confirm delivery receipt |
| `POST` | `/api/v1/store-manager/urgency-requests` | Raise urgent stock or business need |

### Dispatcher

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/dispatcher/plans/draft` | Generate optimizer-backed draft plan |
| `GET` | `/api/v1/dispatcher/plans/{plan_id}` | Inspect draft plan |
| `POST` | `/api/v1/dispatcher/plans/{plan_id}/edit` | Revalidate manual plan edits |
| `POST` | `/api/v1/dispatcher/plans/{plan_id}/approve` | Approve draft and create trips |
| `POST` | `/api/v1/dispatcher/breakdowns/{vehicle_id}/reallocate` | Reallocate after vehicle breakdown |
| `GET/POST` | `/api/v1/dispatcher/urgency-requests` | Review urgency requests |

### Loader

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/loader/queue` | Show trips ready for loading |
| `GET` | `/api/v1/loader/trips/{trip_id}/workbench` | Show stops and load items |
| `POST` | `/api/v1/loader/trips/{trip_id}/start` | Move trip into loading |
| `PATCH` | `/api/v1/loader/trips/{trip_id}/items/{line_item_id}` | Save item-level loaded quantity |
| `POST` | `/api/v1/loader/trips/{trip_id}/complete-stop/{stop_id}` | Complete a stop manifest |
| `POST` | `/api/v1/loader/trips/{trip_id}/load` | Submit final load check |
| `POST` | `/api/v1/loader/trips/{trip_id}/vehicle-unavailable` | Send vehicle issue back to dispatcher |
| `GET` | `/api/v1/loader/deferrals` | See deferred or exception orders |

### Driver

| Method | Endpoint Group | Purpose |
|---|---|---|
| `GET` | `/api/v1/driver-platform/trips/today` | Load assigned trips |
| `GET` | `/api/v1/driver-platform/trips/{trip_id}` | Load full trip detail |
| `POST` | `/api/v1/driver-platform/events` | Sync driver event |
| `POST` | `/api/v1/driver-platform/sync` | Submit offline event batch |
| `GET` | `/api/v1/driver-platform/changes` | Poll route or plan changes |
| `GET/POST` | `/api/v1/driver-platform/conflicts` | View or forward sync conflicts |

---

## Data Model

```mermaid
erDiagram
    USER ||--o{ ORDER : creates
    OUTLET ||--o{ ORDER : receives
    ORDER ||--o{ ORDER_LINE : contains
    ORDER ||--o| TRIP_STOP : planned_as
    TRIP ||--o{ TRIP_STOP : has
    TRIP_STOP ||--o{ TRIP_STOP_ITEM : carries
    VEHICLE ||--o{ TRIP : assigned_to
    TRIP ||--o{ DELIVERY_EVENT : emits
    TRIP ||--o{ LOAD_CHECK : verified_by
    LOAD_CHECK ||--o{ LOAD_CHECK_ITEM : contains
    LOAD_CHECK ||--o{ DISCREPANCY : may_create
    TRIP ||--o{ DRIVER_EVENT : syncs
    ORDER ||--o{ URGENCY_REQUEST : may_raise
```

### Important State Rules

| Entity | Main Statuses |
|---|---|
| Order | `draft`, `confirmed`, `planned`, `loaded`, `out_for_delivery`, `delivered`, `deferred` |
| Trip | `planned`, `loading`, `loaded`, `out_for_delivery`, `completed`, `cancelled`, `vehicle_unavailable` |
| Load item | `pending`, `verified`, `short`, `over`, `damaged`, `missing`, `substituted` |
| Driver event | `pending`, `applied`, `conflict`, `failed`, `already_applied` |
| Urgency request | `pending`, `approved`, `rejected`, `resolved` |

---

## Figures And Screenshots

### Static Figures Included Locally

| Figure | File | Purpose |
|---|---|---|
| Workflow overview | `docs/readme-assets/workflow-overview.svg` | Explains the end-to-end process |
| Service map | `docs/readme-assets/service-map.svg` | Shows frontend, API, services, optimizer, and data |
| Readiness chart | `docs/readme-assets/readiness-chart.svg` | Shows what is ready and what needs work |

### Runtime Screenshot Plan

Real screenshots should be added after the runtime blockers are fixed.

| Screenshot | Target URL | Current Status |
|---|---|---|
| Central portal | `http://localhost:5173/?portal=central` | Blocked by frontend runtime import issue |
| Dispatcher portal | `http://localhost:5173/?portal=dispatcher` | Blocked by frontend runtime import issue |
| Loader workbench | `http://localhost:5173/?portal=loader` | Blocked by frontend runtime import issue |
| Driver trip view | `http://localhost:5173/?portal=driver` | Blocked by frontend runtime import issue |
| Swagger docs | `http://localhost:8000/docs` | Blocked by local PostgreSQL role setup |

Recommended final image locations:

```text
docs/readme-assets/screenshots/central.png
docs/readme-assets/screenshots/dispatcher.png
docs/readme-assets/screenshots/loader.png
docs/readme-assets/screenshots/driver.png
docs/readme-assets/screenshots/swagger.png
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Docker, if using the provided compose file

### Backend

```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file from `.env.example` at the repository root.

Then run migrations and start the API after PostgreSQL is ready:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

API docs should be available at:

```text
http://localhost:8000/docs
```

### Frontend

```bash
npm install
npm --prefix apps/frontend run dev
```

Frontend should be available at:

```text
http://localhost:5173
```

### Docker Compose

The current `docker-compose.yml` starts PostgreSQL only.

```bash
docker compose up
```

Expected final submission behavior:

- start PostgreSQL,
- run migrations,
- seed demo data,
- start backend,
- start frontend.

This full-stack compose wiring is still a required improvement before final submission.

---

## Environment Configuration

Root `.env.example` contains:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | Refresh token lifetime |
| `MINIO_ENDPOINT` | Evidence/photo object storage endpoint |
| `MINIO_BUCKET` | Evidence/photo storage bucket |
| `CORS_ORIGINS` | Allowed frontend origins |

Example:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint
SECRET_KEY=replace-with-a-secure-random-secret-key
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Seeded Accounts

The frontend login forms currently use these demo defaults.

| Role | Username | Password | Notes |
|---|---|---|---|
| Dispatcher | `disp_colombo_1` | `password123` | Dispatcher portal default |
| Store Manager | `fresh_manager` | `password123` | Store manager portal default |
| Driver | `driver_daniru` | `password123` | Driver portal default |
| Loader DEP1 | `loader1` | `pass` | Loader quick-fill |
| Loader DEP2 | `loader2` | `pass` | Loader quick-fill |

Backend tests also seed role-specific users such as `manager1`, `disp1`, `sm1`, and `sm2`. Final demo data should align the frontend defaults, backend seed scripts, and README table.

---

## Judge Walkthrough

Use this route order for a compact demonstration.

### 1. Central Access

Open:

```text
http://localhost:5173/?portal=central
```

Show that all portals are reachable from one entry point.

### 2. Store Manager

Open:

```text
http://localhost:5173/?portal=grocery
```

Demonstrate:

- login,
- outlet context,
- order creation,
- order confirmation,
- receipt confirmation.

### 3. Dispatcher

Open:

```text
http://localhost:5173/?portal=dispatcher
```

Demonstrate:

- confirmed order queue,
- optimizer-backed plan generation,
- draft approval,
- urgency review,
- vehicle incident and recovery flow.

### 4. Loader

Open:

```text
http://localhost:5173/?portal=loader
```

Demonstrate:

- depot-specific loader queue,
- workbench manifest,
- line-item verification by `line_item_id`,
- discrepancy creation,
- vehicle unavailable flow,
- final load submission.

### 5. Driver

Open:

```text
http://localhost:5173/?portal=driver
```

Demonstrate:

- today trips,
- route map,
- departure,
- stop arrival,
- delivery outcome,
- offline event sync,
- conflict handling.

---

## Verification Status

![Submission readiness chart](docs/readme-assets/readiness-chart.svg)

### Completed Locally

| Check | Result |
|---|---|
| Loader backend focused tests | Passed: `22 passed` |
| Frontend production build | Passed after merge repair |
| README file creation | Completed locally |

### Runtime Blockers Found During README Preparation

| Area | Current Result | Explanation |
|---|---|---|
| Docker | Blocked | `docker` command is not installed on this machine |
| Backend API docs | Blocked | Backend requires PostgreSQL; local Postgres rejected the configured `postgres` role |
| Frontend screenshot | Blocked | Built browser page fails on unresolved `@react-leaflet/core` module import |

Because of these blockers, real screenshots are not embedded yet. Add screenshots after:

1. Docker/full-stack startup is fixed.
2. PostgreSQL seed data is confirmed.
3. Frontend runtime dependency issue is resolved.

Recommended screenshot list:

| Screenshot | Page |
|---|---|
| Central portal | `/?portal=central` |
| Dispatcher roster | `/?portal=dispatcher` |
| Loader workbench | `/?portal=loader` |
| Driver trip view | `/?portal=driver` |
| Swagger API docs | `/docs` |

---

## Unique Features

| Feature | Why It Matters |
|---|---|
| Role-based portals | Each user sees the workflow they actually operate |
| Loader line-item identity | Load checks use item identity, not only `product_id`, so duplicate products are safe |
| Idempotent operations | Duplicate client operations can return existing results safely |
| Discrepancy trail | Every mismatch can create a discrepancy for later review |
| Delivery event ledger | Successful load and driver events preserve audit history |
| Hybrid optimizer | Combines greedy planning, validation, and targeted CP-SAT improvement |
| Recovery module | Supports vehicle breakdown and route replanning scenarios |
| Offline-aware driver flow | Driver actions can be synced as events and checked for conflicts |
| Urgency workflow | Store managers can raise urgent business-impact requests |
| Depot authorization | Loaders and dispatchers are restricted to their depot scope |

---

## Operational Risk Coverage

| Risk / Edge Case | Covered In System | Evidence |
|---|---:|---|
| Wrong depot access | Yes | Role/depot checks in services |
| Duplicate load request | Yes | `client_op_id` idempotency |
| Duplicate product in multiple stops | Yes | Uses `line_item_id`, not only `product_id` |
| Missing item | Yes | Loader discrepancy flow |
| Damaged item | Yes | Loader item status and reason |
| Vehicle unavailable | Yes | Loader and dispatcher recovery paths |
| Driver departs too early | Yes | Trip status gates |
| Dispatcher changes during loading | Partial | Route/recovery model exists; final UI sync needs verification |
| Offline driver action | Yes | Driver event sync and conflict model |
| Optimizer infeasible plan | Partial | Validator exists; final dataset path must be verified |

---

## Loader Workflow Detail

```mermaid
flowchart TD
    A["GET /loader/queue"] --> B["Select planned trip"]
    B --> C["GET /loader/trips/{trip_id}/workbench"]
    C --> D["POST /loader/trips/{trip_id}/start"]
    D --> E["PATCH /loader/trips/{trip_id}/items/{line_item_id}"]
    E --> F{"All items resolved?"}
    F -- No --> E
    F -- Yes --> G["POST /loader/trips/{trip_id}/complete-stop/{stop_id}"]
    G --> H["POST /loader/trips/{trip_id}/load"]
    H --> I["Trip becomes loaded"]
    I --> J["Driver can depart"]
```

### Loader Edge Cases Covered

- trip not found,
- wrong depot,
- already loaded trip,
- departed trip,
- cancelled or deferred trip,
- empty trip,
- stop with no items,
- duplicate products across stops,
- duplicate products within an order,
- item not part of trip,
- missing required item,
- negative, zero, short, over, damaged, and missing quantities,
- duplicate `client_op_id`,
- partial save then final submit,
- unresolved pending items,
- vehicle unavailable flows,
- dispatcher-driver-loader timing conflicts.

---

## Designathon Departures

This implementation extends the Designathon concept in several ways:

| Area | Designathon Direction | Current Hackathon Implementation |
|---|---|---|
| Planning | Mainly UI and workflow concept | Backend planning services and optimizer adapter |
| Loader | Basic operational idea | Full loader queue, workbench, item verification, discrepancy handling |
| Driver | Mobile delivery concept | Event-ledger model, offline sync, route geometry, conflict handling |
| Dispatcher | Allocation screens | Draft plan generation, approval, urgency, incidents, recovery |
| Data | Conceptual entities | PostgreSQL-oriented schema with tests and migrations |

---

## Documentation Map

| File | Purpose |
|---|---|
| `docs/schema_design.md` | Main schema and entity contract |
| `docs/backend-design.md` | Backend architecture notes |
| `docs/optimizer.md` | Optimizer approach and planning logic |
| `docs/loader-backend-testing-plan.md` | Loader edge-case plan |
| `docs/dispatcher_portal_workflow_spec.md` | Dispatcher UI workflow notes |
| `docs/driver-integration-notes.md` | Driver integration notes |
| `docs/ai-disclosure.md` | AI disclosure placeholder |
| `docs/architecture.md` | Architecture placeholder |
| `docs/data-model.md` | Data model placeholder |

---

## Testing

Focused loader backend validation:

```bash
cd apps/backend
python -m pytest tests/test_api_integration.py tests/test_loader_backend.py
```

Frontend build:

```bash
npm --prefix apps/frontend run build
```

Full backend test suite:

```bash
cd apps/backend
python -m pytest tests
```

Note: full-suite success depends on complete optimizer data fixtures and PostgreSQL configuration.

---

## Known Gaps Before Final Submission

These are important because the competition brief explicitly asks for them.

| Gap | Priority | Required Action |
|---|---:|---|
| Empty root README | Fixed locally in this draft | Review and push after approval |
| Full-stack Docker Compose | High | Add backend, frontend, migrations, and seed services |
| Seed data command | High | Provide one repeatable seed path for judges |
| `docs/architecture.md` placeholder | High | Replace with final architecture and diagrams |
| `docs/data-model.md` placeholder | High | Replace with final ERD and table descriptions |
| `docs/ai-disclosure.md` placeholder | High | Document AI-assisted and non-AI-assisted work |
| Frontend runtime dependency issue | High | Fix unresolved `@react-leaflet/core` browser import |
| Backend local startup | High | Ensure PostgreSQL role/db/seed instructions work cleanly |
| Screenshots | Medium | Add real screenshots after runtime blockers are fixed |

---

## AI Disclosure

An AI disclosure file exists at:

```text
docs/ai-disclosure.md
```

It should be expanded before final submission to include:

- AI tools used,
- tasks assisted by AI,
- tasks completed manually,
- prompts or prompt categories,
- human review process,
- files or modules where AI assistance was used.

---

## Current Status

This README is a local draft. It should be reviewed by the team before pushing to GitHub.

Recommended next review items:

1. Confirm final seeded account names and passwords.
2. Confirm the final compose/startup approach.
3. Fix runtime blockers.
4. Capture real screenshots.
5. Replace placeholder docs with final architecture, data model, and AI disclosure.
