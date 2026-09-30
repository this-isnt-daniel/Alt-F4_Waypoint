# Driver Backend — Design Choices & Architecture

> **Living document** — updated as the backend is built.  
> Last updated: 2026-09-30T19:29 IST

---

## 1. Stack Decision

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | **FastAPI** (Python) | Existing skeleton at `apps/backend/`, async-ready, auto-generates OpenAPI docs |
| Database | **SQLite** (stdlib `sqlite3`) | Zero-infra for testing; Postgres for deployment |
| Validation | **Pydantic v2** | Ships with FastAPI, strict validation, great error messages |
| Auth | **python-jose** (JWT) | Stateless tokens, offline-friendly -- driver can carry token without server round-trips |
| PIN hashing | **SHA-256 + salt** (hackathon) | bcrypt had version conflicts with passlib; SHA-256 sufficient for demo, swap to bcrypt for prod |
| Photo storage | **Local filesystem** (hackathon) / MinIO-ready API shape | API returns presigned-style URLs; actual storage is local for now |

### SQLite (testing) → Postgres (deployment)

SQLite is used for **local development and testing only**. Production deployment targets **PostgreSQL**.

**Why this dual approach:**
- ✅ SQLite: Zero setup, instant local dev, no Docker needed to start coding
- ✅ Postgres: Full `jsonb`, row-level locking, production-grade concurrency
- ✅ Code uses raw SQL compatible with both (standard SQL, no SQLite-specific syntax)
- ✅ `row_version` optimistic concurrency works identically on both
- ⚠️ JSON stored as TEXT in SQLite, `jsonb` in Postgres — abstracted in service layer
- 🔄 Switch: change `DATABASE_PATH` env var to a Postgres connection string + swap driver

---

## 2. Architectural Principles

### 2.1 Append-Only Event Ledger

Every driver action is stored as a row in `driver_events`. We **never UPDATE or DELETE** driver evidence. The state of a stop is materialized from the event history.

```
Driver taps "Arrived" → INSERT into driver_events (kind='stop.arrived')
                       → UPDATE stops SET status='arrived' (materialized state)
```

Both the event AND the materialized state exist. The event is the source of truth; the stop status is a convenience view.

### 2.2 Idempotent Writes

Every driver event carries a `client_event_id` (UUID generated on the device). The `driver_events` table has a `UNIQUE` constraint on `client_event_id`.

If the driver retries (offline → reconnect), the server returns `{"status": "already_applied"}` instead of creating a duplicate. This is enforced at the database level.

### 2.3 Optimistic Concurrency via `row_version`

Each stop has a `row_version` integer. When the driver sends an event, they include `base_row_version`. The server checks:

```
if event.base_row_version == stop.row_version:
    apply event, increment row_version
else:
    create conflict record, return status="conflict"
```

This replaces database-level locking and works perfectly with SQLite.

### 2.4 Offline-Safe Design

The backend **never** blocks the driver. The API is designed so the frontend can:

1. Save the action locally
2. Queue the event
3. Sync when connectivity returns

The `/api/driver/sync` endpoint accepts batches of events and processes them idempotently. The `/api/driver/changes` endpoint returns deltas since a cursor.

### 2.5 Driver Can't Resolve Conflicts

The driver can **forward** a conflict for review but cannot **resolve** it. Resolution belongs to dispatcher/store manager roles. This is enforced at the API level — no `POST /conflicts/:id/resolve` endpoint exists in the driver API.

---

## 3. Database Schema

### 3.1 Core Tables

```
drivers              — Driver identity + hashed PIN
driver_sessions      — JWT sessions bound to device_id
devices              — Registered driver devices

trips                — Today's planned trips (frozen snapshot)
stops                — Delivery stops with materialized state + row_version
manifest_lines       — Loader → driver line items (pre-flagged items)
route_legs           — Distance/time between stops

driver_events        — THE HEART: append-only event ledger
evidence_objects     — Photo metadata (not bytes)
checklist_results    — Per-line delivery checklist
pod_records          — Proof of delivery (photo ref + PIN state)
return_custody       — Return items chain of custody
conflicts            — Version mismatch records
route_changes        — Dispatcher-issued deltas
messages             — Driver ↔ store manager chat
call_sessions        — Call intent records (masked numbers)
audit_log            — System-level audit trail
```

### 3.2 Key Design Details

**`driver_events.status` enum:**
```
pending | applied | conflict | failed | already_applied
```

**`stops.status` enum:**
```
upcoming | arrived | in_progress | delivered | partial | failed | return_pending | returned | skipped
```

**`conflicts.status` enum:**
```
in_review | forwarded | resolved | dismissed
```

**`pod_records.pin_state` enum:**
```
not_started | submitted | verified | failed | pending_verification
```

**`evidence_objects.status` enum:**
```
pending_upload | stored | failed | quarantined
```

---

## 4. API Structure

All driver endpoints live under `/api/driver/`.

### 4.1 Module A — Auth (`/api/driver/auth/*`)
```
POST /api/driver/auth/login      — Driver ID + PIN → JWT tokens
GET  /api/driver/me               — Current driver profile
POST /api/driver/auth/refresh     — Refresh access token
POST /api/driver/auth/logout      — Invalidate session
```

**Key decisions:**
- PIN is hashed with bcrypt, never stored or returned raw
- Session is bound to `device_id` — one driver, one device at a time
- Access token is short-lived (8h = one shift), refresh token is 24h
- Token payload includes `driver_id` and `device_id`
- All other endpoints require valid JWT via `Authorization: Bearer <token>`

### 4.2 Module B — Trips (`/api/driver/trips/*`)
```
GET /api/driver/trips/today           — All trips for today
GET /api/driver/trips/:tripId         — Single trip detail
GET /api/driver/trips/:tripId/briefing — Pre-departure briefing
GET /api/driver/trips/:tripId/manifest — Full manifest with stops, lines, legs
```

**Key decision:** The manifest endpoint returns a **frozen snapshot**. The driver app caches this locally before departure. Mid-route changes arrive via the delta endpoint, not by mutating the snapshot.

### 4.3 Module C — Departure (`/api/driver/trips/:tripId/depart`)
```
POST /api/driver/trips/:tripId/depart — Load confirmation + departure
```

**Key decision:** Accepts load confirmation groups per stop. If any group is `flagged`, emits a `load_shortfall_flagged` event for the dispatcher. The trip status changes to `departed`.

### 4.4 Module D — Stop Lifecycle (`/api/driver/stops/:stopId/*`)
```
POST /arrive          — GPS + timestamp
POST /checklist       — Per-line delivery state
POST /pod/photo-intent    — Get upload URL
POST /pod/photo-complete  — Confirm upload
POST /pod/pin         — Submit manager PIN (pending verification)
POST /outcome         — delivered | partial | failed
POST /return          — Return custody record
POST /returns/:id/depot-confirm — Depot officer confirms return
```

**Key decisions:**
- All writes go through the event ledger
- Checklist is versioned, never overwritten
- PIN is "submitted" not "verified" — verification happens server-side on sync
- Photo metadata only in DB; actual image in filesystem/MinIO
- Outcome validation checks against checklist + POD state

### 4.5 Module E — Offline Sync (`/api/driver/sync`)
```
POST /api/driver/sync                 — Batch event upload
GET  /api/driver/changes?since=cursor — Delta download
```

**Key decisions:**
- Sync accepts array of events, processes each idempotently
- Each event result: `applied | conflict | already_applied | failed`
- Conflicts are created, never auto-resolved
- Cursor is ISO 8601 timestamp-based
- Non-blocking: server processes what it can, returns results for all

### 4.6 Module F — Dispatcher Deltas (`/api/driver/changes`)
```
GET  /api/driver/changes?since=cursor — Fetch deltas
POST /api/driver/changes/:changeId/ack — Acknowledge change
```

**Key decisions:**
- Resequencing changes only `seq`, never `order_units` or `deliverable_units`
- Completed stops are never reordered
- Driver must acknowledge changes

### 4.7 Module G — Chat/Call (`/api/driver/stops/:stopId/*`)
```
GET  /messages        — Chat history
POST /messages        — Send message (supports quick replies)
POST /call-intent     — Get masked dial number
```

**Key decisions:**
- Never expose driver's personal phone number
- Never expose full store manager number
- Masked dial number has TTL (expires_at)
- For hackathon, numbers are fake but API shape is production-ready

---

## 5. File Structure

```
apps/backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    ← FastAPI app + CORS + lifespan
│   ├── config.py                  ← Env-based configuration
│   ├── database.py                ← SQLite setup, all CREATE TABLEs, get_db()
│   ├── seed.py                    ← Canonical Day 5 seed data
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          ← Assembles all sub-routers
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py        ← Module A
│   │           ├── trips.py       ← Module B
│   │           ├── departure.py   ← Module C
│   │           ├── stops.py       ← Module D
│   │           ├── sync.py        ← Module E
│   │           ├── changes.py     ← Module F
│   │           ├── conflicts.py   ← Conflict forwarding
│   │           └── chat.py        ← Module G
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             ← ALL Pydantic request/response models
│   ├── services/                  ← Business logic (not in endpoints)
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── trip_service.py
│   │   ├── event_service.py
│   │   ├── stop_service.py
│   │   ├── sync_service.py
│   │   ├── conflict_service.py
│   │   └── chat_service.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py     ← JWT validation dependency
│   └── repositories/             ← Direct DB access (thin layer)
│       └── __init__.py
├── requirements.txt
└── waypoint_driver.db             ← Auto-created SQLite file
```

---

## 6. Seed Data (Canonical Day 5)

The seed data matches the frontend's `driverContent.ts` exactly:

| Entity | Details |
|--------|---------|
| Driver | Daniru Dinsara, VEH014, Kandy hub |
| Trip 1 | Fresh · Kandy · 8 stops · CHILLED REEFER |
| Trip 2 | Style · Kandy · 5 stops · AMBIENT (locked until Trip 1 complete) |
| Flagged stop | OUT058: 2 frozen produce damaged in staging, return crate R-04 |
| Closed stop | OUT052: Mall bay unavailable scenario |
| Conflict | OUT058: Driver delivered 10, dispatcher reassigned to VEH021, store says not received |

---

## 7. How to Run

```bash
cd apps/backend
pip install -r requirements.txt
python -m app.seed          # Seed the database
uvicorn app.main:app --reload --port 8000
```

API docs auto-generated at: `http://localhost:8000/docs`

---

## 8. Frontend Integration Notes

The frontend currently imports mock data from `driver/data/driverContent.ts`. To switch to real API:

1. Replace static imports with `fetch('/api/driver/trips/today')` etc.
2. The API response shapes match the frontend's existing TypeScript interfaces
3. Auth: store JWT in localStorage, send as `Authorization: Bearer <token>`
4. Offline: queue events locally, POST to `/api/driver/sync` when online
5. Deltas: poll `/api/driver/changes?since=cursor` periodically

---

## 9. What This Backend Does NOT Own

| Not our job | Belongs to |
|-------------|------------|
| Allocation engine | Dispatcher service |
| Deferral decisions | Dispatcher service |
| Capacity planning | Planner service |
| Conflict resolution | Dispatcher / Store manager |
| Store manager receipt UI | Store manager service |
| Loader manifest creation | Loader service |
| Route planning from scratch | Planner / allocator |

We **consume**: planned trips, stop sequences, manifest lines, loader flags, dispatcher deltas.  
We **emit**: driver events, evidence, conflicts forwarded, progress updates.

---

## 10. Decisions Log

| # | Decision | Rationale | Date |
|---|----------|-----------|------|
| 1 | SQLite over Postgres (for testing) | Zero-infra for hackathon; Postgres for deployment | 2026-09-30 |
| 2 | FastAPI over NestJS | User requested; existing skeleton exists | 2026-09-30 |
| 3 | Optimistic concurrency via row_version | Works without DB-level locking; SQLite-friendly | 2026-09-30 |
| 4 | PIN "submitted" not "verified" offline | Honest UX; real verification needs server | 2026-09-30 |
| 5 | Local filesystem for photos (hackathon) | MinIO-ready API shape but no Docker dependency | 2026-09-30 |
| 6 | Event ledger + materialized state | Audit trail + fast reads; best of both worlds | 2026-09-30 |
| 7 | Cursor-based delta sync | Efficient; no full re-fetch; works with offline gaps | 2026-09-30 |
| 8 | Driver can forward but not resolve conflicts | Enforces role boundaries per spec | 2026-09-30 |
| 9 | SHA-256 + salt instead of bcrypt | passlib/bcrypt version conflict on Python 3.13; SHA-256 sufficient for hackathon | 2026-09-30 |

---

## 11. Codebase Research Findings

> This section documents the existing repository structure and frontend architecture discovered during research, to provide context for anyone continuing the backend work.

### 11.1 Repository Structure

```
Alt-F4_Waypoint/
├── apps/
│   ├── frontend/          ← Vite + React + TypeScript (main UI)
│   └── backend/           ← FastAPI Python (driver API lives here)
├── datathon/              ← ML notebooks + submissions (separate concern)
├── designathon/           ← Design assets + screen links
├── docs/                  ← Architecture docs (including this file)
├── docker-compose.yml     ← Currently empty
├── .env.example           ← Currently empty
└── package.json           ← NPM workspace root (frontend only)
```

### 11.2 Existing Backend Before This Work

The backend at `apps/backend/` was a **bare scaffold** -- empty `__init__.py` files in every package with a minimal FastAPI main.py and an empty router. No endpoints, no database, no models. The `.gitkeep` says: `# FastAPI Store Manager backend placeholder`.

**Pre-existing package structure (all empty):**
```
app/api/v1/endpoints/
app/core/
app/db/
app/domain/
app/models/
app/repositories/
app/schemas/
app/services/
```

We kept the structure and added our files alongside these empty packages.

### 11.3 Frontend Architecture (163 files)

The frontend is a **multi-portal single-page app**. Portal is selected via `?portal=driver|dispatcher|loader|storemanager` URL param.

**Portal routing** in `apps/frontend/src/App.jsx`:
- `?portal=driver` -> mounts `<DriverApp />`
- `?portal=dispatcher` -> dispatcher pages
- `?portal=loader` -> loader workbench
- `?portal=storemanager` -> store manager (3 variants: grocery, style, tech)

**Driver app** (`apps/frontend/src/driver/`) has:
- **33 screens** covering the full delivery lifecycle
- **26 UI components** (custom design system, no external UI lib)
- **5 data files** with mock data + types
- **6 state management files** (scenario engine, sync queue, connection state)
- **Hash router** with parameter support: `#/?screen=<id>&scenario=<scenario>&outletId=<outlet>`

### 11.4 Frontend Data Model (What Backend Must Match)

#### Core Types from `driverContent.ts`:

```typescript
type Brand = "Fresh" | "Style"
type District = "Kandy"
type Depot = "Kandy hub"
type DockType = "Rear dock" | "Street" | "Mall bay"
type ParkingConstraint = "Normal" | "Van only" | "Mall dock"
type TempRequirement = "Chilled" | "Ambient" | "Chilled + ambient"
type StopOutcome = "delivered" | "partial" | "failed"

interface DriverStop {
  seq, outletId, name, address, window, mallWindow?,
  dock, dockDetail?, parking, temp, units, deliverableUnits,
  returnUnits, returnCrate?, manager, phoneMasked,
  serviceMin, instructions?, outcome, brand?, district?, depot?
}
```

#### Load System from `loadRows.ts`:

```typescript
type LoadState = "unconfirmed" | "matches" | "flagged"
type LoadingReason = "Short at loading" | "Extra loaded" | "Damaged in staging" | "Wrong item" | "Other"

interface LoadRow {
  outletId, name, manifestUnits, deliverableUnits, returnUnits,
  state: LoadState, reason, crate, loaderNote, vanUnits, preFlagged
}
```

The `LOADER_PRE_FLAGS` map pre-seeds OUT058 as flagged with 2 damaged frozen items in crate R-04.

#### Sync System from `syncQueue.ts`:

```typescript
type SyncRecordType = "load-confirmation" | "arrival" | "delivery" | "partial" | "failed" | "issue" | "return" | "chat-message"
type SyncState = "pending" | "syncing" | "synced" | "failed" | "inReview" | "forwarded"

interface SyncRecord {
  id, type, outletId?, createdAt, state, hasPhoto, pinVerified, sizeLabel?
}
```

#### Connection States from `connection.ts`:

```typescript
type ConnectionState = "online" | "offline"
type SyncState = "idle" | "saving" | "pending" | "syncing" | "success" | "failed" | "inReview" | "routeUpdated" | "forwarded"
```

### 11.5 Scenario Engine (12 Demo Scenarios)

The frontend has a **scenario engine** (`apps/frontend/src/driver/state/scenarios.ts`) that lets judges jump to any scenario via `?demo=1`. Each scenario sets specific state:

| Scenario ID | Description | Backend Relevance |
|---|---|---|
| `happy` | Full happy path delivery | Basic CRUD flow |
| `load-discrepancy` | Pre-departure load flag at OUT058 | Load confirmation API must handle flagged groups |
| `partial-return` | Partial delivery + return custody | Outcome API + return custody chain |
| `outlet-closed` | OUT052 mall bay unavailable | Failed outcome with reason |
| `offline-sync-conflict` | OUT058 sync mismatch | Conflict detection + forward API |
| `route-resequence` | Dispatcher resequences route | Changes/delta API + ack |
| `chat-call` | Driver-manager messaging | Chat + call-intent API |
| `return-depot` | Return to depot flow | Return custody + depot confirm |
| `errors-camera` | Camera denied | No backend impact |
| `errors-location` | Location denied | No backend impact |
| `errors-sync-failed` | Sync failure | Sync API error handling |
| `no-trips` | Empty trip list | `/trips/today` returns empty |

### 11.6 Canonical Seed Data (Day 5 Delivery Day)

All values sourced from `driverContent.ts` -- backend seed data matches exactly:

| Entity | Key | Details |
|---|---|---|
| Driver | `DRV-DANIRU` | Daniru Dinsara, PIN: 1234, Kandy hub |
| Vehicle | `VEH014` | Van, reefer, 9.4 km/L, 42L fuel quota |
| Reassign vehicle | `VEH021` | Truck, reefer (used in conflict scenario) |
| Loader | `Kasun Kalhara` | Kandy hub depot |
| Trip 1 | `TRIP-VEH014-2026-09-26-1` | Fresh, Kandy, 8 stops, 1240 units, 890kg, CHILLED_REEFER |
| Trip 2 | `TRIP-VEH014-2026-09-26-2` | Style, Kandy, 5 stops, 860 units, 540kg, AMBIENT, **locked** |

**Trip 1 Stops (8):**

| Stop | Outlet | Name | Units | Window | Special |
|---|---|---|---|---|---|
| STOP-001 | OUT042 | Waypoint Fresh Gampola | 120 | 05:30-06:30 | -- |
| STOP-002 | OUT047 | Waypoint Fresh Kandy Town | 25 | 05:45-07:01 | Service lane, bay B |
| STOP-003 | OUT049 | Waypoint Fresh Kandy Fort | 18 | 06:00-07:30 | -- |
| STOP-004 | OUT052 | Waypoint Fresh Kandy City Centre | 160 | 05:45-07:30 | **Mall bay, outlet-closed scenario** |
| STOP-005 | OUT055 | Waypoint Fresh Kandy East | 8 | 06:15-07:45 | -- |
| STOP-006 | OUT058 | Waypoint Fresh Kandy Hills | 12 (10+2) | 06:45-08:00 | **Flagged: 2 frozen damaged, R-04** |
| STOP-007 | OUT061 | Waypoint Fresh Peradeniya | 210 | 06:45-08:00 | **Resequenced to 3rd in route change** |
| STOP-008 | OUT064 | Waypoint Fresh Nawalapitiya | 687 | 07:00-08:00 | -- |

**Trip 2 Stops (5):** OUT070-OUT074, all Style brand, ambient, 860 total units.

**GPS Coordinates (from frontend STOP_COORDS):**

| Outlet | Lat | Lng |
|---|---|---|
| Kandy Hub (depot) | 7.2906 | 80.6337 |
| OUT042 | 7.1666 | 80.5666 |
| OUT047 | 7.2931 | 80.6350 |
| OUT049 | 7.2936 | 80.6360 |
| OUT052 | 7.2941 | 80.6380 |
| OUT055 | 7.2880 | 80.6200 |
| OUT058 | 7.2850 | 80.6250 |
| OUT061 | 7.2667 | 80.6000 |
| OUT064 | 7.0500 | 80.5333 |

### 11.7 Cross-Portal Entities

The backend should be aware that **other portals exist** and share data:

| Portal | Role | Shared Entities |
|---|---|---|
| **Dispatcher** | Route planning, vehicle assignment, breakdown recovery | Trips, stops, vehicles, driver assignments, route changes |
| **Loader** | Depot staging, manifest creation | Manifest lines, loader flags, crate assignments |
| **Store Manager** | Order placement, delivery receipts, OTP verification | Outlets, orders, delivery confirmation, PIN/OTP |

**Key integration points:**
- Dispatcher creates trips and route changes -> driver backend consumes them
- Loader creates manifest lines and pre-flags -> driver backend serves them
- Store manager verifies PIN/OTP -> driver backend stores PIN state, verification happens cross-service
- Driver events (progress, arrival, POD) -> dispatcher/store manager read views

### 11.8 UI Component Conventions

These conventions should be maintained in API response design:

- **Zero emoji policy** -- all icons are SVG via `lucide-react`
- **Units** are called "cases" (from `labels.ts`: `UNIT_WORD = "cases"`)
- **Volume** formatted as `m3` (cubic meters)
- **Phone numbers** always masked: `+94 7* *** **XX` format
- **Connection indicator** is a small green dot for online/synced; text pills only for attention states
- **Quick replies** in chat: predefined message list `["On my way.", "5 minutes away.", "I've arrived.", ...]`

### 11.9 Existing Test Coverage

The frontend has tests that validate:
- Portal routing and resolution
- Text sanitization and external link safety
- Masked PIN integrity
- Arithmetic and number formatting
- Theme persistence
- **All 33 screens are reachable** (zero-orphan guarantee)
- No legacy strings, zero emojis in UI code
- Interactive load confirmation and departure gating

Run: `npm run test`, `npm run typecheck`, `npm run build`

---

## 12. How Other Portals Connect to Driver Backend

```
┌─────────────┐     creates      ┌──────────────┐
│ Dispatcher   │ ──────────────> │ trips        │
│ Portal       │     creates     │ stops        │
│              │ ──────────────> │ route_changes│
└─────────────┘                  └──────┬───────┘
                                        │
┌─────────────┐     creates      ┌──────┴───────┐
│ Loader       │ ──────────────> │manifest_lines│
│ Portal       │     flags       │ (pre_flagged)│
└─────────────┘                  └──────┬───────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │ DRIVER       │
                                 │ BACKEND      │
                                 │              │
                                 │ reads: trips,│
                                 │ stops,       │
                                 │ manifests,   │
                                 │ changes      │
                                 │              │
                                 │ writes:      │
                                 │ events,      │
                                 │ evidence,    │
                                 │ conflicts    │
                                 └──────┬───────┘
                                        │
                                        ▼
┌─────────────┐     reads        ┌──────────────┐
│ Store Mgr    │ <────────────── │ driver_events│
│ Portal       │     reads       │ pod_records  │
│              │ <────────────── │ conflicts    │
└─────────────┘                  └──────────────┘
```

---

## 13. Known Limitations & Future Work

| Limitation | Impact | Future Fix |
|---|---|---|
| SQLite single-writer | Only one driver can write at a time | Swap to Postgres for deployment |
| SHA-256 PIN hashing | Weaker than bcrypt | Use bcrypt when passlib compatibility fixed |
| No real photo storage | Photos referenced but not stored | Add MinIO container to docker-compose |
| No WebSocket push | Driver polls for changes | Add WebSocket for real-time dispatcher deltas |
| No real routing engine | Polyline/distance from seed data | Integrate OSRM or Google Maps API |
| No rate limiting | Auth endpoints unprotected | Add slowapi or similar |
| docker-compose.yml empty | No containerized deployment | Add services: api, postgres, minio |

