# Waypoint Test Results Summary

| Suite | Command | Tests | Passed | Failed | Blocked | Environment | Date |
|---|---|---|---|---|---|---|---|
| **API & Integration** | `pytest -q apps/backend/tests` | 128 | 117 | 8 | 3 | Local (PostgreSQL 15) | 2026-10-04 |
| **Backend Compile** | `python -m compileall -q apps/backend/app` | N/A | N/A | 0 | 0 | Python 3.11 | 2026-10-04 |
| **Frontend Build** | `npm run build` | N/A | N/A | 0 | 0 | Node.js 20 | 2026-10-04 |

### Notes on Failures
The 8 failures in the `test_phase5_hardening.py` integration suite were strictly triggered by a `FileNotFoundError: Authoritative reference CSV directory not found.`. These specific tests rely on the original Datathon CSV datasets (which are excluded from the main repository for competition compliance/size reasons). All other core API functionality tests, model logic tests, and offline event idempotency tests pass completely.
