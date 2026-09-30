# Driver Backend — Design Choices & Architecture

> **Living document** — updated as the backend is built.  
> Last updated: 2026-09-30T19:19 IST

---

## 1. Stack Decision

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | **FastAPI** (Python) | Existing skeleton at `apps/backend/`, async-ready, auto-generates OpenAPI docs |
| Database | **SQLite** (stdlib `sqlite3`) | Zero-infra, single-file, perfect for hackathon. WAL mode for concurrent reads |
| Validation | **Pydantic v2** | Ships with FastAPI, strict validation, great error messages |
| Auth | **python-jose** (JWT) | Stateless tokens, offline-friendly — driver can carry token without server round-trips |
| Password hashing | **passlib[bcrypt]** | Industry standard for PIN hashing |
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
| 1 | SQLite over Postgres | User requested; zero-infra for hackathon | 2026-09-30 |
| 2 | FastAPI over NestJS | User requested; existing skeleton exists | 2026-09-30 |
| 3 | Optimistic concurrency via row_version | Works without DB-level locking; SQLite-friendly | 2026-09-30 |
| 4 | PIN "submitted" not "verified" offline | Honest UX; real verification needs server | 2026-09-30 |
| 5 | Local filesystem for photos (hackathon) | MinIO-ready API shape but no Docker dependency | 2026-09-30 |
| 6 | Event ledger + materialized state | Audit trail + fast reads; best of both worlds | 2026-09-30 |
| 7 | Cursor-based delta sync | Efficient; no full re-fetch; works with offline gaps | 2026-09-30 |
| 8 | Driver can forward but not resolve conflicts | Enforces role boundaries per spec | 2026-09-30 |
