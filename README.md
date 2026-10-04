# Alt-F4 Waypoint / Tech-Triathlon 2026

## Full Stack Deployment Guide (Docker Compose)

This repository includes a complete `docker-compose.yml` to run the entire Waypoint application stack (PostgreSQL -> Migrations -> Seeding -> Backend API -> Frontend SPA) reproducibly. 

### 1. Prerequisites
- Docker Engine & Docker Compose (v2 recommended)
- Git

### 2. Environment Setup
Create the `.env` file from the example:
```bash
cp .env.example .env
```
(No modifications to the defaults are required for a local test).

### 3. Starting the Stack
Ensure you have a clean slate, then build and start all containers:
```bash
docker compose down -v
docker compose build
docker compose up -d
```
The startup process guarantees strict ordering using Docker healthchecks:
1. `postgres` boots and becomes healthy.
2. `migrate` runs `alembic upgrade head` and exits successfully.
3. `seed` runs the idempotent database seeder (`seed.py`) and exits successfully.
4. `backend` starts the FastAPI server and passes its `/health` check.
5. `frontend` starts the Vite production server (`serve`).

### 4. Application URLs
- **Frontend URL:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- **Backend Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

### 5. Seeded Accounts
The system is automatically seeded with four accounts (Password for all: `password123`):
- **Store Manager:** `storemanager` (Outlet: OUT-1001)
- **Dispatcher:** `dispatcher` (Depot: Peliyagoda)
- **Loader:** `loader` (Depot: Peliyagoda)
- **Driver:** `driver` (Depot: Peliyagoda)

### 6. Judge Walkthrough Flow
1. **Store Manager:** Log in as `storemanager`, create a new order, and submit it.
2. **Dispatcher:** Log in as `dispatcher`, review the new order, trigger the optimization planner, and review the route allocation.
3. **Loader:** Log in as `loader`, see the assigned load, and perform the load check.
4. **Driver:** Log in as `driver`, view the assigned trip, start the trip, execute stops, and submit Proof of Delivery (POD).
5. **Store Manager:** Verify receipt of the order.
6. **Dispatcher:** See the updated delivery state on the dashboard.

### 7. Database Initialization Mechanics
- **Migrations:** Managed by the `migrate` service which runs `alembic upgrade head`. It exits immediately upon success.
- **Seeding:** Managed by the `seed` service which executes `apps/backend/seed.py`. This script is strictly idempotent (uses `ON CONFLICT DO NOTHING`) so it is safe against multiple runs. It provisions all requisite users, depots, vehicles, products, and outlets.

### 8. Stack Management
To stop the stack:
```bash
docker compose down
```
To wipe the database entirely and reset everything from scratch:
```bash
docker compose down -v
docker compose up -d
```
