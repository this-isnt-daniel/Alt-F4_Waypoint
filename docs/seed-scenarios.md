# Waypoint Seed Scenarios

The Waypoint database seed (`apps/backend/seed.py`) implements a deterministic, competition-grade scenario matrix designed to validate all core system capabilities during the Tech-Triathlon 2026.

## Matrix Overview

The seed produces a single consistent state incorporating multiple parallel workflows:

### 1. Golden Scenario (`GOLDEN-001`)
- **Objective:** Validates the happy-path flow for a typical delivery lifecycle.
- **Components:** Order creation -> Dispatch planning -> Load verification -> Driver execution -> Final receipt.
- **Constraints Exercised:** Standard capacity limitations, standard time windows.
- **Expected Outcome:** Seamless progression through all four portals.

### 2. Capacity Stress (`CAPACITY-001`)
- **Objective:** Forces the optimization engine to demonstrate correct deferral logic.
- **Components:** 15 simultaneous high-volume orders placed on the exact same date for similar outlets.
- **Constraints Exercised:** Vehicle weight and volume limits, total fleet availability.
- **Expected Outcome:** The dispatcher portal should successfully plan some orders while accurately moving the overflow into a "deferred" state, retaining data integrity for the next operational window.

### 3. Edge Cases Matrix
The seed incorporates multiple targeted data states to validate specific business rules:
- **`WEIGHT-001` / `VOLUME-001`:** Tests constraint validation for exceptionally heavy or bulky products on standard vans.
- **`VAN-001`:** Tests vehicle-access restrictions (`park_constraint='van_only'`) preventing trucks from being assigned.
- **`MALL-ORD-1`:** Tests time window enforcement on specific `dock_type` restrictions.
- **`CUTOFF-001`:** Asserts date-boundary logic for orders placed for the next calendar day.
- **Refrigeration Bottleneck:** Includes a mix of `chilled` items that mandate `reefer` vehicle assignments.

### 4. Active Trip & Offline Sync (`OFFLINE-001`)
- **Objective:** Validates the offline-first execution capability of the Driver portal and the synchronization mechanism.
- **Components:** A pre-dispatched `out_for_delivery` trip assigned to the driver.
- **Constraints Exercised:** IndexedDB offline mode, background synchronization.
- **Expected Outcome:** Driver can execute drops offline, with correct conflict resolution upon reconnection.

### 5. Recovery & Discrepancies (`RECOVERY-001`)
- **Objective:** Validates discrepancy workflows across roles.
- **Components:** A predefined loading shortfall (reported by loader) affecting an active trip.
- **Constraints Exercised:** Receipt adjustments, discrepancy resolution.
- **Expected Outcome:** The Store Manager or Dispatcher correctly acknowledges and resolves the discrepancy without halting unaffected deliveries.

## Validation

A deterministic validation script is provided.

```bash
docker exec alt-f4_waypoint-backend-1 python validate_seed.py
```

This will confirm the precise item counts and state alignment matching the documented scenario matrix.
