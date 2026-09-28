# Dispatcher · Mid-Shift Recovery — Principal UI/UX Specification

**Design System:** Waypoint Fleet OS Enterprise Design System  
**Figma Section:** `Dispatcher · Mid-Shift Recovery`  
**Canvas:** `bg-slate-50` (`#F8FAFC`) | **Width:** `1536px` (Desktop Workstation)  
**Role:** Principal UI/UX Designer, Industrial B2B & Cold-Chain Logistics Enterprise

---

## 1. Executive Summary & Operational Axioms

Mid-shift vehicle breakdowns in temperature-sensitive FMCG and grocery logistics present high-stakes operational risks. If a reefer vehicle suffers a mechanical seizure, dispatched dispatchers face a critical operational dilemma:
1. **Dock Congestion Risk:** Reshuffling existing loaded trucks invalidates warehouse staging, triggers physical dock bottlenecks, and wastes driver shift hours.
2. **Fresh Window Perishability:** Chilled goods (dairy, meats, berries) have hard temperature-tolerance horizons (fresh windows). If not re-slotted before window closure, they become compromised and must be quarantined.

### Mid-Shift Recovery Axioms
- **Zero-Reshuffle Invariance:** Recovery **only** allocates orphaned orders into **empty vehicle trip slots** (e.g., Trip 2 slots of returning or completed vehicles, or idle standby assets). Departed trips, delivered stops, and loaded vehicles remain 100% immutable.
- **Traceable Forward Lineage:** Voided stops on broken vehicles must never vanish into a black hole; they maintain explicit forward links (`OUT-1029 → VEH014 · Trip 2`) or explicit deferral records.
- **Stakeholder Broadcast:** Publishing a recovery plan automatically generates updated digital loading manifests for dock loaders, turn manifests for drivers, and revised ETAs for store managers.

---

## 2. Design Tokens & Visual Hierarchy

| Element | Design Token | Tailwind Class | Hex Value | Usage |
|---|---|---|---|---|
| **Canvas** | Surface Ground | `bg-slate-50` | `#F8FAFC` | Workspace canvas backdrop |
| **Card / Container** | Surface Neutral | `bg-white border-slate-200` | `#FFFFFF / #E2E8F0` | Tables, cards, modals |
| **Confirmed / Success** | Brand Emerald | `bg-emerald-600 / text-emerald-700` | `#059669 / #047857` | Primary buttons, confirmed bars |
| **Disruption / Critical** | Rose Critical | `bg-rose-50 / text-rose-700 / border-rose-200` | `#FFE4E6 / #BE123C` | Disruption banner, out-of-service, voided |
| **Warning / Recovery** | Amber Warning | `bg-amber-50 / text-amber-700 / border-amber-200` | `#FEF3C7 / #B45309` | Recovery tags, orphaned chips, delayed |
| **Cold-Chain / Reefer** | Sky Active | `bg-sky-50 / text-sky-700 / border-sky-200` | `#E0F2FE / #0369A1` | Reefer badges, chilled tags |
| **Monospace Entities** | Tabular Mono | `font-mono` | `JetBrains Mono / monospace` | Entity IDs (`VEH011`, `ORD-30082`, `OUT-4089`), times, weights |

---

## 3. Five-Frame Architectural Breakdown

### Frame 1: Live Plan · Disruption Detected
*Base state matches the confirmed Live Plan table, modified strictly with non-disruptive disruption indicators.*

- **Disruption Banner (`bg-rose-50 border-rose-200 text-rose-800 rounded-xl px-4 py-3`):**
  - Replaces the green confirmation bar with identical height and radius.
  - Left: Alert triangle icon + Content: `"2 vehicles lost since Plan v1 · VEH011 (at dock, cargo staged) · VEH006 (en route, 4 stops undelivered) · 5 orders · 3,270 kg unassigned"`.
  - Right: Primary button `[ Start Recovery Plan → ]` (`bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-4 py-2 rounded-lg`).
- **Version Switcher Segmented Control:**
  - Segmented control chip: `v1 Initial 05:40` (active) | `v2 Recovery (draft)` (inactive).
- **KPI Stat Chips:**
  - Standard chips: `Allocated Fleet: 14 Vehicles Active` · `Coverage: 24 Outlets Scheduled` · `Total Weight: 42,800 kg`.
  - **New Chip 1 (Rose):** `Vehicles Lost: 2` (`bg-rose-50 text-rose-700 border-rose-200`).
  - **New Chip 2 (Amber):** `Orphaned Orders: 5` (`bg-amber-50 text-amber-700 border-amber-200`).
- **Filter Group:**
  - Added filter pill: `Recovery` alongside `All`, `Reefers Only`, `Delayed Only`.
- **Live Table Row Modifications:**
  - `VEH011` & `VEH006` remain in place, dimmed (`opacity-60 bg-rose-50/20`), tagged with rose pill `Out of Service · 08:15 AM` / `Out of Service · 08:22 AM`.
  - Expanding row renders voided manifest with every stop marked `Voided` in bold rose.

---

### Frame 2: Recovery Stepper · Step 1 of 3 · Impact
*Triage modal/stepper to assess cargo safety and freshness window deadlines.*

- **Stepper Navigation Header:**
  - `← Back to Live Plan` link (top-left).
  - Progress indicator: `1. Impact Assessment` (emerald active) → `2. Recovery Capacity` (slate) → `3. Review & Publish` (slate).
- **Dual Triage Cards (Side by Side):**
  - **Card 1: At the Dock (`VEH011`):**
    - Reported by: Loader Lead S. Perera at 08:15 AM (hydraulic lift seizure at Bay 3).
    - Status: `Staged and safe` (emerald pill). Cargo remains in temperature-controlled anteroom.
    - Orphaned orders: `ORD-30114` (680 kg, 2.4 m³), `ORD-30119` (840 kg, 3.1 m³), `ORD-30125` (520 kg, 1.9 m³). Total: 2,040 kg.
  - **Card 2: En Route (`VEH006`):**
    - Reported by: Driver K. Silva at 08:22 AM (coolant leak / transmission overheat on A1 Highway).
    - Undelivered stops require manual cargo assessment:
      - `OUT-4089 Nugegoda Supermarket` (ORD-30082): Fresh window `44m left`. Toggle: `[ Recoverable ]` (emerald).
      - `OUT-2041 Wattala Mega Store` (ORD-30091): Fresh window `18m left`. Toggle: `[ Recoverable ]` (emerald).
      - `OUT-3012 Maharagama Central` (ORD-30088): Fresh window `0m left` (closed). Locked row with rose badge `Unrecoverable: window closed`.
      - `OUT-5021 Mount Lavinia Hub` (ORD-30095): Compromised cold-chain toggle selected with dropdown reason `Cold-chain breach`.
- **Footer Summary & Action:**
  - Summary: `"3 recoverable · 2 unrecoverable (1 window closed, 1 compromised cold-chain)"`.
  - Primary button: `[ Continue to Capacity → ]` (`bg-emerald-600 text-white`).

---

### Frame 3: Step 2 of 3 · Recovery Capacity
*Match validated recoverable orders against strictly empty, compliant vehicle trip slots.*

- **Left Panel (5 Columns): Recoverable Orders to Place:**
  - Lists the 3 validated recoverable orders (`ORD-30114`, `ORD-30119`, `ORD-30082`).
  - Displays weight (`kg`), volume (`m³`), temperature requirement (`Chilled` sky pill), and store access constraint (e.g., `"Max 10T rigid · Tail-lift required"`, `"Basement bay · Max vehicle height 3.2m"`).
- **Right Panel (7 Columns): Available Usable Vehicles:**
  - Grouped into 3 distinct operational buckets:
    1. **Idle at Depot:** `VEH016` (Truck, Reefer, 4,500 kg / 14 m³, 210 min time budget, 74% fuel) & `VEH008` (Ambient Van, 1,500 kg, flagged as ambient only).
    2. **Returning to Depot:** `VEH009` (Truck, Reefer, returning ETA 08:45 AM, 145 min budget).
    3. **Open Trip 2 Slot:** `VEH014` (Van, Reefer, finishing Trip 1 ~09:20 AM, Trip 2 slot completely open, 110 min budget, 88% fuel).
  - *Vehicles that have exhausted 2 trips (e.g., VEH041) are strictly omitted.*
- **Non-Editable Scope Note:**
  - Slate callout box: `"Scope Note (Locked): Departed trips, delivered stops, loaded vehicles. Recovery fills empty trip slots only. No reshuffle allowed on committed manifests."`
- **Action:** `[ Run Recovery Plan ]` (`bg-emerald-600 text-white`).

---

### Frame 4: Step 3 of 3 · Review Changes
*Enterprise diff view verifying that committed plans are untouched while newly assigned trips are validated.*

- **Summary Strip:**
  - `"5 orphaned → 3 recovered · 2 deferred · 0 existing loading lists changed."`
- **Diff Structure (Three Semantic Groups):**
  1. **Added (Emerald):**
     - `ORD-30114` (Liberty Plaza) → Assigned to `VEH014 · Trip 2` (New ETA: 09:45 AM).
     - `ORD-30119` (Kollupitiya) → Assigned to `VEH016 · Trip 1` (New ETA: 09:15 AM).
     - `ORD-30082` (Nugegoda) → Assigned to `VEH014 · Trip 2` (New ETA: 10:15 AM).
  2. **Deferred (Rose, Editable Reasons):**
     - `ORD-30088` (Maharagama Central): Input initialized to `"Fresh window closed before available departure slot (08:30 AM deadline passed)"`.
     - `ORD-30095` (Mount Lavinia Hub): Input initialized to `"Cold-chain breach reported en route; quarantined at Depot QA cold bay"`.
  3. **Unchanged (Slate Accordion):**
     - `"12 vehicles · 22 trips · 78 stops untouched"` (expandable list confirming zero side-effects).
- **Broadcast Notification Notice:**
  - Informs dispatcher that clicking publish will automatically push new loading manifests to Bay 3/4 loaders, route sheets to driver mobile terminals, and revised ETAs/deferral notices to store managers.
- **Action Buttons:**
  - `[ Back ]` & `[ Publish Recovery Plan v2 ]` (`bg-emerald-600 text-white font-bold`).

---

### Frame 5: Live Plan · After Publishing v2 (Merged View)
*Unified live plan showing seamlessly merged recovery trips alongside operational baseline.*

- **Confirmed Banner Re-established:**
  - Green confirmed bar: `"Recovery Plan v2 published 08:31 · Loader, Driver and Store Managers notified."`
  - Version switcher toggles to: `v2 Recovery (active)`.
- **Merged Trip Rows in Vehicle Table:**
  - `VEH014` now renders `Trip 2 of 2` with an amber tag: `Recovery · v2` placed directly adjacent to trip lock text.
  - `VEH016` renders `Trip 1 of 2` with an amber tag: `Recovery · v2`.
- **Traceable Broken Vehicle Lineage:**
  - `VEH011` and `VEH006` remain dimmed (`opacity-60`) with `Out of Service` tags.
  - In their expanded manifest, each voided stop displays its forward lineage link:
    - `OUT-1029 Liberty Plaza Express → VEH014 · Trip 2 (New ETA 09:45 AM)`
    - `OUT-1044 Kollupitiya Central → VEH016 · Trip 1 (New ETA 09:15 AM)`
    - `OUT-4089 Nugegoda Supermarket → VEH014 · Trip 2 (New ETA 10:45 AM)`
    - `OUT-3012 Maharagama Central → Deferred · Window Closed`
- **Deferral Log Synchronized:**
  - The `Deferrals (5)` segment button automatically updates to `Deferrals (7)`, appending the two new disruption deferrals tagged `Recovery · VEH006`.

---

## 4. Figma Layer Structure & Copy-Paste Tree

To build these frames inside Figma:
```
Section: "Dispatcher · Mid-Shift Recovery"
├── Frame 1: "Live Plan · Disruption Detected" (1536 x 980, Fill: #F8FAFC)
│   ├── TopNav_Global (Sticky 64px, Fill: #FFFFFF, Stroke: #F1F5F9)
│   ├── Hub_And_Version_Controls (AutoLayout Horizontal, Gap: 12)
│   ├── Banner_Disruption_Rose (Fill: #FFF1F2, Stroke: #FECDD3, Radius: 12)
│   │   ├── Icon_AlertTriangle (20px, Stroke: #BE123C)
│   │   ├── Text_DisruptionCopy (Inter 12px Medium, Fill: #881337)
│   │   └── Btn_StartRecovery (Fill: #059669, Radius: 8, Text: Inter 12px Bold #FFF)
│   ├── KPI_Stats_Row (AutoLayout Horizontal, Gap: 8)
│   │   ├── Chip_VehiclesLost (Fill: #FFF1F2, Stroke: #FECDD3, Text: #BE123C)
│   │   └── Chip_OrphanedOrders (Fill: #FEF3C7, Stroke: #FDE68A, Text: #B45309)
│   └── Table_LivePlan_Vehicles (Fill: #FFFFFF, Stroke: #E2E8F0, Radius: 16)
│       ├── Row_VEH011_Dimmed (Opacity: 60%, Badge: Out of Service 08:15 AM)
│       └── Row_VEH006_Dimmed (Opacity: 60%, Badge: Out of Service 08:22 AM)
│
├── Frame 2: "Recovery Stepper · Step 1 Impact" (1536 x 980, Fill: #F8FAFC)
│   ├── Header_Stepper (Steps: 1 Active, 2 Inactive, 3 Inactive)
│   ├── Grid_TwoColumn_Impact (AutoLayout Horizontal, Gap: 20)
│   │   ├── Card_AtTheDock_VEH011 (Fill: #FFFFFF, Stroke: #E2E8F0, Radius: 16)
│   │   └── Card_EnRoute_VEH006 (Fill: #FFFFFF, Stroke: #E2E8F0, Radius: 16)
│   └── Footer_Action_Step1 (Summary Text + Btn_ContinueToCapacity)
│
├── Frame 3: "Recovery Stepper · Step 2 Capacity" (1536 x 980, Fill: #F8FAFC)
│   ├── Header_Stepper (Steps: 1 Checked, 2 Active, 3 Inactive)
│   ├── Grid_TwoColumn_Capacity (Left: 5 Cols, Right: 7 Cols)
│   │   ├── Panel_RecoverableOrders (3 Chilled Orders with Height/Dock Access Notes)
│   │   └── Panel_UsableVehicles (Idle at Depot, Returning, Open Trip 2 Slot)
│   │       └── Callout_ScopeNote_Slate (Fill: #F1F5F9, Stroke: #E2E8F0, Lock Icon)
│   └── Footer_Action_Step2 (Btn_RunRecoveryPlan)
│
├── Frame 4: "Recovery Stepper · Step 3 Review" (1536 x 980, Fill: #F8FAFC)
│   ├── Header_Stepper (Steps: 1 Checked, 2 Checked, 3 Active)
│   ├── Strip_Summary_Diff ("5 orphaned → 3 recovered · 2 deferred · 0 loading lists changed")
│   ├── Group_Added_Emerald (Fill: #ECFDF5, Stroke: #A7F3D0)
│   ├── Group_Deferred_Rose (Fill: #FFF1F2, Stroke: #FECDD3, Editable Reason Inputs)
│   ├── Group_Unchanged_Slate (Fill: #FFFFFF, Stroke: #E2E8F0, Collapsible)
│   └── Footer_Action_Step3 (Btn_Back + Btn_PublishRecoveryPlanV2)
│
└── Frame 5: "Live Plan · After Publishing v2 (Merged View)" (1536 x 980, Fill: #F8FAFC)
    ├── Banner_Confirmed_Green (Fill: #EAF7EE, Stroke: #CDEED6, "Recovery Plan v2 published")
    ├── Switcher_PlanVersion (Active: "v2 Recovery (active)")
    └── Table_LivePlan_Merged
        ├── Row_VEH014_Trip2 (Badge: "Recovery · v2" #FEF3C7/#B45309)
        ├── Row_VEH016_Trip1 (Badge: "Recovery · v2" #FEF3C7/#B45309)
        ├── Row_VEH011_Dimmed (Forward links to VEH014 & VEH016)
        └── Segment_Deferrals_7 (Count updated from 5 to 7)
```
