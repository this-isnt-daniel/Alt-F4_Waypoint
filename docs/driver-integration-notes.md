# Waypoint Driver App - Integration Notes

## 1. Overview & Branch
- **Branch**: `driver`
- **Portal URL**: `http://localhost:5173/?portal=driver`
- **Judge / Demo Explorer**: `http://localhost:5173/?portal=driver&demo=1`
- **Design System**: Waypoint clean palette — light mode page background `#F8FAF9`, clean white cards with `border-slate-200`, brand green `#059669`, Inter typography, and theme toggle.

## 2. Repository & Portal Resolution
- Monorepo structure with frontend located at `apps/frontend/`.
- Portal routing in `apps/frontend/src/App.tsx` checks `?portal=driver` to mount `<DriverApp />`.
- Hash router in `src/router/navigator.tsx` provides deterministic routing across all 33 screens with parameter support (`#/?screen=<id>&scenario=<scenario>&outletId=<outlet>`).

## 3. Map System (OpenStreetMap via Leaflet)
- Embedded interactive OpenStreetMap rendered using Leaflet (`src/driver/components/DriverMap.tsx` and `DriverMap.css`).
- Depot marker placed at Kandy Hub (`7.2906, 80.6337`).
- Dynamic numbered pins reflect stop sequence and delivery status (upcoming, current, delivered, partial, failed).
- Route polyline fitted to bounds. Accessible fallback toggle for list view on mobile.
- OpenStreetMap attribution preserved; CSP in `index.html` configured for OSM tile servers.

## 4. UI Components & Iconography
- Zero emoji policy enforced: All icons are rendered via SVG using `lucide-react` through `src/driver/components/AppIcon.tsx`.
- `ConnectionIndicator.tsx` provides quiet connection states: small green dot for online/synced; text pills only for attention states (`offline`, `pending`, `syncing`, `failed`, `inReview`, `routeUpdated`).
- TopBar standardizes the status indicator placement consistently across all screens (`[ConnectionIndicator] [Clock] [ThemeToggle]`).
- Buttons use modest rounding (`rounded-lg`), 48–56px tap targets, and clear active/disabled states.
- ChoiceList and BottomSheet components provide accessible touch-friendly workflows.

## 5. Canonical Narrative & Terminology
- **Units Terminology**: Centralized in `src/driver/data/labels.ts` as `cases` (reflecting physical crates/cases counted by drivers).
- **Volume**: Formatted as `m³` (`formatVolume(m3)` in `src/lib/derive.ts`).
- **Driver**: Nimal Perera (Saturday · 26 September, Shift 05:10–14:22).
- **Vehicle**: VEH014 (Refrigerated van, Kandy hub depot, 42 L fuel quota).
- **Trip 1**: Fresh · Kandy (8 stops, 1,240 manifest cases, 1,238 deliverable, 2 return, 890 kg, 4.2 m³).
- **Trip 2**: Style · Kandy (5 stops, 860 cases, 540 kg, 2.8 m³, locked until Trip 1 & depot return complete).
- **Day Totals**: 13 Stops • 2,100 Cases.

## 6. Key Workflows & Patches
1. **Start Day**: Read-only orientation showing assigned vehicle facts (`VEH014`, 3°C, 42 L). Direct start day button.
2. **Load Confirmation**: Interactive per-stop rows (3-state: *To check → Matches → Flagged*). OUT058 arrives pre-flagged with loader note ("S. Fernando: 2 damaged in staging. Sealed in return crate R-04.") and crate R-04. Bulk "Confirm all match" button with confirmation sheet.
3. **Unloading Checklist**: Flagging opens an in-place bottom sheet that mutates the line and stays on the checklist (preventing premature jumping to POD). "Continue to proof" is the sole exit, enabled only when all lines are resolved.
4. **Proof of Delivery (POD)**: Strict photo capture (no skip photo primary button). Manager PIN confirmation with Anjali Silva.
5. **Delivery Complete**: Compact 40px success marker, neutral slate inline sync status, and automatic route sequence progression to the next stop.

## 7. Scenario Engine & Demo Explorer
Append `&demo=1` to the URL (`http://localhost:5173/?portal=driver&demo=1`) to display the **Scenarios** explorer in the header. Judges can jump straight into any of the 12 canonical scenarios:
- `happy` (Happy path)
- `load-discrepancy` (Pre-departure load flag)
- `partial-return` (Partial + return custody)
- `outlet-closed` (Degradation · outlet closed)
- `offline-sync-conflict` (Degradation · sync conflict)
- `route-resequence` (Dispatcher resequencing)
- `chat-call` (Chat / call)
- `return-depot` (Return to depot)
- `errors-camera` (Error · camera denied)
- `errors-location` (Error · location denied)
- `errors-sync-failed` (Error · sync failed)
- `no-trips` (Empty · no trips)

## 8. Verification & Test Suite
Run tests with `npm run test`, `npm run typecheck`, and `npm run build`:
- `tests/portal.test.ts`: Routing and portal resolution.
- `tests/security.test.ts`: Text sanitization, external link safety, masked PIN integrity.
- `tests/derive.test.ts`: Arithmetic, case units, and number formatting.
- `tests/theme.test.tsx`: Theme persistence and dark/light switching.
- `tests/scenarios.test.ts`: Proves reachability of all 33 screen IDs (zero-orphan guarantee).
- `tests/no-legacy.test.ts`: Validates absence of legacy strings and verifies 0 emojis across UI code.
- `tests/load-confirm.test.tsx`: Validates interactive load confirmation and departure gating.
