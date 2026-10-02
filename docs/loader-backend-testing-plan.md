# Loader Backend Testing Plan

This document captures the checklist used for the `bhavee/test/loader-backend`
branch. The goal is to prove the loader workflow without changing unrelated
frontend or dispatcher behavior.

## Reference Patterns

- FastAPI tests use dependency overrides and `TestClient`, matching the official
  FastAPI testing guidance.
- SQLite tests use one in-memory database with `StaticPool` so the same database
  is visible across the app and test session.
- Idempotent operations use `client_op_id` as the request key, so duplicate
  requests return the already-created result rather than creating duplicates.

## Entities and Statuses

| Entity | Statuses / states covered |
| --- | --- |
| Trip | `planned`, `loading`, `loaded`, `out_for_delivery`, `cancelled`, `vehicle_unavailable` |
| Stop | `upcoming`, `loading_complete`, `loaded`, `delivered` |
| Order | `draft`, `confirmed`, `planned`, `loading`, `loaded`, `out_for_delivery`, `deferred`, `delivered` |
| Order line | Manifested by `line_item_id`; never checked by `product_id` alone |
| Vehicle | `available`, `unavailable`; `ambient` and `reefer` temperature compatibility |
| Loader | Correct role, wrong role, own depot, wrong depot |
| Depot | Own depot and other depot authorization boundaries |
| Discrepancy | `open`, `resolved`; loading source stage |

## API Edge-Case Method

For each loader API, tests ask:

| Question | Coverage |
| --- | --- |
| What if the entity does not exist? | Trip not found and missing/extra line item tests |
| What if the role is wrong? | Dispatcher denied on loader queue |
| What if the depot is wrong? | Loader from another depot denied on workbench |
| What if the status is wrong? | Loaded, departed, cancelled, and vehicle-unavailable trips reject loader edits |
| What if the request is duplicated? | Duplicate `client_op_id` returns one `LoadCheck` |
| What if the request conflicts with server state? | Dispatcher defers/removes order while loader screen is stale |
| What if numbers are zero, negative, or too high? | Negative schema validation; zero verified rejection; shortage/overage discrepancy handling |
| What if two users act at the same time? | Idempotency and stale-manifest conflict tests represent retry and cross-role race conditions |

## Unit Tests Added

`apps/backend/tests/test_loader_backend.py` covers:

- Queue filtering and workbench response shape.
- Trip not found and wrong depot.
- Read-only statuses: loaded, departed, cancelled, vehicle unavailable.
- Empty trip and stop without items.
- Duplicate product across stops.
- Duplicate product inside one order.
- Missing, extra, and non-trip line item submissions.
- Rejection of stale `expected_qty` from client payloads.
- Negative quantity, zero quantity, overage, shortage, damaged, and reason rules.
- Discrepancy creation and audit event creation after load.
- Duplicate `client_op_id` idempotency.
- Partial save then final submit.
- Final submit with pending item.
- Temperature-sensitive item on incompatible vehicle.
- Dispatcher defers order while loader screen is open.
- Vehicle unavailable before and after loading.
- Driver cannot depart before loading and can depart after loading, including with discrepancies.

## Integration Tests

The full platform flow is covered in two places:

- `test_loader_backend.py`: store manager creates and confirms an order, dispatcher
  plans it, loader loads it, driver is blocked before loading, then driver departs
  after loading.
- `test_api_integration.py`: legacy integration flow updated to use
  `line_item_id` instead of `product_id` for loader submissions.

## Common Loader + Dispatcher Cases

| Case | Handling |
| --- | --- |
| Vehicle unavailable | Loader can mark before loaded; rejected after loaded/out for delivery |
| Order deferred or removed from trip | Loader detects stale manifest and returns conflict |
| Inventory shortage | Recorded as `short` discrepancy with reason |
| Capacity issue | Covered indirectly by server-manifest and vehicle compatibility boundaries |
| Trip status changes | Wrong-status tests cover read-only and terminal statuses |
| Route/stop sequence changes | Stale trip/order assignment detection blocks loader action |
| Load discrepancy requiring replanning | Discrepancy is persisted for dispatcher visibility |
| Wrong depot authorization | Queue/workbench tests enforce depot scope |
| Duplicate operation/idempotency | `client_op_id` test proves safe duplicate submit |
| Order already planned/loaded/out for delivery | Loader status and driver departure tests cover transitions |
| Audit trail and timeline events | Load and departure event assertions cover timeline records |
| Dispatcher changes plan while loader works | Deferral/stale screen test returns `409` conflict |

## Commands

```bash
/private/tmp/waypoint-loader-venv/bin/python -m pytest apps/backend/tests/test_loader_backend.py
/private/tmp/waypoint-loader-venv/bin/python -m pytest apps/backend/tests
```
