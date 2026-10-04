# Architecture Overview

## High-Level Architecture Diagram

```mermaid
flowchart TD
    Browser[Browser / User]
    
    subgraph Frontend [React/Vite SPA]
        StorePortal[Store Manager Portal]
        DispPortal[Dispatcher Portal]
        LoaderPortal[Loader Portal]
        DriverPortal[Driver Portal (PWA Offline Capability)]
    end
    
    subgraph Backend [FastAPI Backend]
        API_GW[REST API Routers]
        Auth[Auth / RBAC]
        
        subgraph DomainServices [Domain Services]
            OrderSvc[Order Service]
            PlanSvc[Planning Service]
            LoadSvc[Loader Service]
            DriverSvc[Driver Service]
            RecoverSvc[Recovery / Incident Service]
        end
        
        subgraph Optimizer [Optimizer Engine]
            Adapter[Optimizer Adapter]
            CPSAT[Google OR-Tools CP-SAT Planner]
        end
    end
    
    subgraph Infrastructure [Docker Compose]
        Postgres[(PostgreSQL)]
        Migrate[Alembic Migration]
        Seed[Seeder]
    end
    
    Browser --> |HTTP/React| Frontend
    Frontend --> |HTTPS/REST| API_GW
    API_GW --> Auth
    Auth --> DomainServices
    DomainServices <--> |Optimizer Integration| Adapter
    Adapter <--> CPSAT
    
    DomainServices --> |SQLAlchemy| Postgres
    Migrate --> |Schema setup| Postgres
    Seed --> |Base records| Postgres
```

## Boundaries & Roles

**Store Manager**
- Creates and submits wholesale orders.
- Has visibility over order status (upcoming deliveries).
- Performs final Receipt Confirmation when goods are physically delivered.

**Dispatcher**
- Primary hub for fleet operational management.
- Validates confirmed orders and submits them to the Optimizer.
- Receives Draft Plans, reviews allocations (respecting capacities, time windows, temp requirements, fuel constraints, and dock constraints).
- Manages contingencies such as Route Changes, Deferrals, and Vehicle Breakdowns using the Recovery Optimizer.

**Loader**
- Uses mobile-first portal to select upcoming planned trips.
- Iterates over the assigned manifest (Trip Stops -> Trip Stop Items).
- Submits Load Checks. A discrepancy (Shortfall) instantly logs an issue in the operational state.

**Driver**
- Primary execution engine on the road.
- Capable of Offline operation for event syncing.
- Departs from depot, drives to locations, and sequentially records Arrivals and PODs.
- Posts vehicle incidents directly.

## Data Flow (Core Path)

1. **Order Capture:** Store Manager -> Order API -> Postgres (Order Status: confirmed).
2. **Planning:** Dispatcher -> Planning Service -> Optimizer Adapter -> OR-Tools CP-SAT Engine proposes a DraftPlan.
3. **Allocation:** Dispatcher reviews the draft. If approved -> `Trip` & `TripStop` entities are materialized into Postgres.
4. **Loading:** Loader selects the `Trip` -> Submits `LoadCheck` -> Validated.
5. **Execution:** Driver selects the `Trip` -> Commences driving. Submits chronological `DeliveryEvent` (offline resilient) -> Postgres synchronized.
6. **Delivery:** Driver submits Proof of Delivery (POD).
7. **Confirmation:** Store Manager views the POD -> Submits `ReceiptConfirmation` -> Closes lifecycle.

## Data Flow (Recovery Path)

1. **Incident:** Driver reports `Vehicle Breakdown` (VehicleIncident entity).
2. **Detection:** Dispatcher sees Incident on the Recovery dashboard.
3. **Re-planning:** Recovery Service analyzes orphaned stops -> Optimizer produces a rescue Draft Plan.
4. **Rescue:** Dispatcher approves -> `RouteChange` issued -> Orphaned stops assigned to a new rescue trip/vehicle.

## Deployment Architecture
- Deployed via **Docker Compose**.
- Services strictly ordered by native Healthchecks: `postgres` -> `migrate` -> `seed` -> `backend` -> `frontend`.
- Exposes port `3000` for the React/Vite web host and port `8000` for FastAPI.
- Employs a single robust persistent volume for PostgreSQL.

## Engineering Boundaries
- **Authentication:** Standard JWT-based bearer authentication with strictly enforced RBAC per role portal.
- **Database:** Canonical truth is completely owned by PostgreSQL (via SQLAlchemy / Alembic).
- **Idempotency:** Core actions (especially Offline Driver Events and Seed Data) utilize robust idempotency logic (`on_conflict_do_nothing`, unique constraint hashes) ensuring safe replays.
