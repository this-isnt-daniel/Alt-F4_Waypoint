# Waypoint Hackathon Audit

Reviewed against the Hackathon requirements in Challenge Booklet(2).pdf and the uploaded repository.

## Score estimate

| Criterion | Weight | Score | Comment |
|---|---:|---:|---|
| Functional completeness across all four roles | 20 | 13 | All four API surfaces exist. Fresh ordering/receipt are API-backed after the patch; Style/Tech now share the live portal. A full browser/Postgres walkthrough was unavailable because PostgreSQL was not running in the audit environment. |
| Planning and allocation engine | 20 | 14 | Strong hybrid optimizer and 232 passing optimizer tests. The board now submits displayed placements for backend validation. A legacy in-memory planning boundary and hardcoded dispatcher contingency views remain. |
| Degradation, offline operation, and recovery | 10 | 5 | Incidents, recovery, conflicts and offline states are represented. Driver queue is React state only, not durable across refresh; POD storage has a MinIO TODO. |
| Fidelity to the Day 5 design | 10 | 5 | Design files exist, but prototype data was used in live screens. The patch intentionally replaces order/receipt pages with simpler API-backed screens and documents the departure. |
| Engineering quality and architecture | 25 | 17 | Good service separation, role checks, migrations, idempotency and tests. API prefix/schema mismatches, seed collisions, missing driver assignment and invalid test assumptions were fixed. |
| Creativity | 5 | 4 | Hybrid optimization, loader checks, recovery planning and conflict handling are meaningful additions. |
| Demo video | 10 | — | Not scored from repository contents. |

**Estimated score excluding video: 58/90.** This is an engineering estimate, not an official judge score.

## Patched defects

- Fixed loader `/api/v1/api/v1/...` requests.
- Passed `VITE_API_URL` into the frontend Docker build and switched the image to `npm ci`.
- Replaced `httpx2` with `httpx` in backend dependencies.
- Removed duplicate dispatcher vehicle route; response now exposes capacities used by the board.
- Added ORM/response aliases for trip-stop item fields.
- Added outlet-brand, active-product, and chilled-product validation.
- Enforced 16:00 Asia/Colombo previous-day cutoff and saved `cutoff_at`.
- Applied mall delivery windows before outlet fallback windows.
- Required delivery status and matching server POD for receipt confirmation; validated discrepancy products and zero quantities.
- Copied vehicle drivers and plan metadata into newly approved trips; rejected stale fleet/order state.
- Made reseeding preserve canonical outlet rows, operational orders and vehicle state; added Style/Tech accounts and CSV driver assignments.
- Driver sync now checks server acknowledgement instead of marking rejected events synced.
- Fresh, Style and Tech order/receipt paths use live catalogue/order APIs.
- Allocation board now submits its displayed placements to backend draft editing/approval.
- CI installs the optimizer package, runs optimizer tests, uses `npm ci`, and runs frontend tests.

## Validation

- Frontend: **29 tests passed** and production build passed.
- Optimizer: **232 tests passed**.
- Focused backend/API regressions: **144 passed, 1 deselected**; planning regressions **3 passed**.
- Isolated SQLite seed smoke test passed and confirmed reseeding preserves delivered/workshop state.
- Full PostgreSQL integration could not be claimed because PostgreSQL was unavailable; original DB-backed tests showed connection-refused failures.

## Remaining high-risk findings

1. `planning_service.py` still exposes an in-memory legacy mock endpoint. Remove or mark it deprecated.
2. Driver offline records are not durable across refresh; add IndexedDB or a service worker queue.
3. POD photo intent still returns a constructed MinIO URL with a storage TODO, not a completed presigned upload.
4. Dispatcher recovery/contingency views still contain hardcoded vehicles, outlets, ETAs and cargo examples.
5. Legacy Style/Tech fixture data remains in the repository and can be mistaken for live data.
6. README needs a real deployed URL, deployment credentials and demo-video link; `designathon/links.md` is blank.
7. Frontend bundle is about 816 kB minified before gzip; code splitting would improve loading.

Use a future operating date in the final walkthrough because today’s cutoff has passed. Demonstrate order, dispatcher deferral, loader shortfall, driver offline/reconnect, receipt discrepancy and recovery, then show the persisted state after each role.
