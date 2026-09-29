# Waypoint Driver App - Integration Notes

## 1. Overview & Branch
- **Branch**: `driver`
- **Portal URL**: `http://localhost:5173/?portal=driver`
- **Theme**: Dark mode default, theme toggle available on every screen.

## 2. Repository & Portal Resolution
- An existing portal mechanism was found in `apps/frontend/src/App.jsx` using `URLSearchParams` (`?portal=...`).
- Extended `portal` handling with `driver` to mount `<DriverApp />`.
- Unrecognized or absent `portal` query params fall back to existing default behavior (Dispatcher portal).

## 3. Theme & Design Tokens
- Design tokens from SECTION 4 were introduced into `src/global.css`.
- Theme system implemented via `ThemeProvider.tsx`, supporting `dark` (default) and `light` modes.
- Inline pre-paint script in `index.html` sets `data-theme` attribute before rendering to eliminate flash of unstyled content (FOUC).
- Semantic colour laws enforced across all components.

## 4. Canonical Narrative Summary & Arithmetic
- **Driver**: Nimal Perera (Saturday · 26 September, Shift 05:10–14:22)
- **Vehicle**: VEH014 (Van, Reefer, Kandy hub depot, 42L fuel quota)
- **Trip 1**: Fresh · Kandy (8 stops, 1,240 manifest units, 1,238 deliverable, 2 return, 890 kg, 4.2 m³)
- **Trip 2**: Style · Kandy (5 stops, 860 units, 540 kg, 2.8 m³, locked until Trip 1 & depot return complete)
- **Day Totals**: 13 Stops • 2,100 Units (Hero Band displays "13 Stops • 2,100 Units")

## 5. Sync Conflict & Resequencing Models
- **Sync Conflict**: Non-destructive preserve-and-forward model (`sync-review` / `record-sent`). Driver evidence is preserved; driver never acts as referee.
- **Route Resequencing**: Dispatcher route update (`route-changed`) is represented as resequencing, not adding/removing load after departure.
- **Offline Model**: Non-blocking sync queue (`syncQueue.ts`). Sensitive evidence (PIN/Photo Blobs) handled in-memory only.

## 6. CSP & Production Notes
- `index.html` includes CSP for development. In production, inline script should use a nonce/hash or external asset.
- PDFs and exported image assets were excluded from repository commits per project policy.
