# Waypoint Fleet OS — Tech-Triathlon 2026 Hackathon Solution

An intelligent, multi-tenant delivery planning and execution platform for **Waypoint Group**, seamlessly connecting **Dispatcher**, **Loader**, **Driver**, and **Store Manager** across 120 retail outlets and 60 multi-category fleet vehicles in Sri Lanka.

---

## 1. Quickstart & Local Setup

### Prerequisites
- **Node.js**: v18+ or v20+
- **npm**: v9+

### Installation & Launch
```bash
# 1. Clone repository
git clone https://github.com/this-isnt-daniel/Alt-F4_Waypoint.git
cd Alt-F4_Waypoint

# 2. Install dependencies
cd apps/frontend
npm install

# 3. Start local development server
npm run dev
```

The application will be running at `http://localhost:5173/` (or `5174` if 5173 is in use).

---

## 2. Seeded Accounts & Portals

The application features instant role-switching via the URL parameter or the floating **Role Switcher Dock** at the bottom-right corner of the screen:

| Role | Portal URL | Seeded Persona | Focus Responsibilities |
|---|---|---|---|
| **Dispatcher** | `/?portal=dispatcher` | **K. Jayawardena** (Peliyagoda Planning Office) | Fleet capacity allocation, multi-depot monitoring, constraint validation, deferral tracking, mid-shift recovery. |
| **Loader** | `/?portal=loader` | **S. Perera** (Bay Lead A, Peliyagoda DC) | Reverse-stop sequence packing ("back first, doors last"), item check-off, dock shortfalls & damage logging. |
| **Driver** | `/?portal=driver` | **Nimal Perera** (`VEH014`, Kandy Hub) | Phone viewport UI, pre-trip inspection, turn-by-turn navigation, digital PoD (PIN + Photo), offline sync queue. |
| **Store Manager** | `/?portal=storemanager` | **Anjali Silva** (`OUT047`, Fresh Kandy Town) | Digital order placement before 4 PM, dry/chilled dispatch calculation, live ETA tracking, split-truck delivery receipt. |

---

## 3. Numbered Judge Walkthrough (All 4 Roles)

Follow these steps to experience the complete operational cycle from ordering to delivery and exception recovery:

### Step 1: Dispatcher Route Allocation & Mid-Shift Disruption (`/?portal=dispatcher`)
1. Open `http://localhost:5173/?portal=dispatcher`.
2. **Overview Tab:**
   - Inspect the **Hub Schematic Visual Map** showing expressway corridors across Peliyagoda, Kandy, and Galle.
   - Review live fleet KPI chips: *Fleet Utilization (34/60)*, *Reefer Cold Chain status*, and *Fleet Fuel Quota burn (68%)*.
3. **Route Allocation & Capacity:**
   - Switch to **Fleet Availability**: filter by `Reefer` or `Van` and inspect payload limits and weekly fuel allowances.
   - Switch to **Allocation Workbench**: inspect vehicle `VEH014` (Kandy Hub) with dual progress bars for weight (kg) and volume (m³), and review the expandable stop sequence and item manifests.
4. **Mid-Shift Recovery Scenario:**
   - Notice the amber notification for disruption: 2 vehicles out of service (`VEH011` hydraulic seizure at dock, `VEH006` coolant leak en route).
   - Click **Start Recovery Plan** or verify the **Recovery Plan Modal**:
     - Step 1: Impact Assessment (3 orders recoverable, 2 deferred).
     - Step 2: Capacity Allocation (placing orphaned orders into empty Trip 2 slots without reshuffling committed trucks).
     - Step 3: Review & Publish v2 plan with automatic notifications pushed to loader manifests and driver routes.

### Step 2: Warehouse Dock Loading (`/?portal=loader`)
1. Click **Loader** in the floating Role Dock (or navigate to `/?portal=loader`).
2. **Queue Tab:** Review trucks docked at Bay A with departure countdowns.
3. **Workbench Tab:**
   - Note the **Reverse Stop Packing Sequence**: Stop 3 (Kandana Express, delivers last) is loaded first at the back of the cargo bed, and Stop 1 is loaded nearest to the doors for fast unloading.
   - Check off cargo crates (Fresh Milk, Chilled Chicken).
   - Test the **Discrepancy Reporting Modal**: flag a shortfall or damage at dock (e.g. 2 damaged cartons of Chilled Butter) before vehicle departure.
   - Click **Complete Loading & Sign-off**.

### Step 3: Driver Execution, PoD & Offline Sync (`/?portal=driver`)
1. Click **Driver** in the floating Role Dock (or navigate to `/?portal=driver`).
2. **Pre-Trip Briefing:**
   - Sign in as **Nimal Perera** (Driver ID `DRV-8802`).
   - Inspect assigned vehicle `VEH014` (Reefer Van, Kandy Hub): verify cold-chain temperature (3°C Normal) and 42L fuel quota.
   - Start Day and review today's schedule (13 stops, 2,100 units across Trip 1 and Trip 2).
3. **Load Confirmation:** Review Bay manifest (1,240 units manifest, 1 flagged group), click **Confirm & Depart**.
4. **Active Route & Map:**
   - Follow Trip 1 (Fresh - Kandy). View interactive route map with stop nodes and live vehicle position.
   - Stop 2: *Waypoint Fresh Kandy Town* (`OUT047`). Review outlet instructions ("Use service lane. Keep chilled crates sealed until handover").
5. **Offline Mode Simulation (Hill Country Signal Drop):**
   - Tap the green `ONLINE` Connection Pill in the top bar to toggle to `OFFLINE`.
   - Notice the sync pill automatically changes to amber `QUEUED`.
   - Complete arrival and offloading checklist offline.
   - **Digital Proof of Delivery (PoD):** Store Manager enters 4-digit PIN on driver's screen, and driver takes photo of delivered goods.
   - Tap the sync pill to enter **Sync Centre** (`#/sync-centre`): inspect the 4 queued records preserved safely in local memory.
   - Tap the Connection Pill to toggle back to `ONLINE`: witness background synchronization flush all records to the server.
6. **Mid-Shift Reroute:** In the Sync Centre, inspect the **Dispatcher Route Update** and view the `Route Changed` screen showing stop #7 moved next with reassurance that no load was altered.
7. **2-Trip Daily Lifecycle:** Complete Trip 1, perform depot return with empty return crates, and unlock Trip 2 (Style Kandy).

### Step 4: Store Manager Delivery Receipt & Ordering (`/?portal=storemanager`)
1. Click **Store Manager** in the floating Role Dock (or navigate to `/?portal=storemanager`).
2. **Overview Tab:**
   - Track incoming shipments for *Waypoint Fresh Colombo / Kandy*.
   - **Split-Delivery Support:** Review how the store receives both ambient dry goods (`VH-30302`) and chilled produce (`VH-20211`) with separate delivery windows and driver contacts.
   - Confirm receipt of delivered goods.
3. **Place Order Tab:**
   - Browse the product catalog with clear Dry vs Chilled tags.
   - Adjust quantities and observe real-time calculation of total weight (kg), volume (m³), and **Dispatch Count** (automatically indicates if 1 or 2 dispatches are required based on temperature categories).
   - Verify 4:00 PM cutoff notice and submit order.
4. **Receipts & Deferrals Tab:**
   - Inspect historical orders.
   - Review transparent deferral explanations (e.g. *"Fleet capacity short — moved to Friday. Priority rollover active"*).

---

## 4. Engineering Quality & Architectural Highlights

1. **Enterprise Design System & Dark Mode:**
   - Tailored HSL color palette with high-contrast daytime and dark mode support for in-cab driving safety.
   - Semantic color tokens: Brand Emerald (`#059669`), Warning Amber (`#C77D0A`), Danger Rose (`#B3261E`), Cold-chain Sky (`#E0F2FE`).
2. **Non-Destructive Offline Sync Queue:**
   - Local buffer (`syncQueue.ts`) prevents field data loss during Central Province network dropouts.
   - Reconnection preserves driver evidence and handles conflict resolution non-destructively.
3. **Zero-Reshuffle Mid-Shift Recovery Engine:**
   - Respects warehouse dock staging constraints by never reshuffling loaded or departed vehicles.
   - Automatically utilizes idle assets or open Trip 2 slots.
4. **Automated Unit Tests:**
   Run unit tests covering domain assertions, arithmetic invariants, and security helpers:
   ```bash
   npm run test
   ```
