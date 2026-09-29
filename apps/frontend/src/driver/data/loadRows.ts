import { TRIP_1_STOPS, type DriverStop } from "./driverContent";
import type { LoadingReason, LoadState } from "./labels";

export interface LoadRow {
  outletId: string;
  name: string;
  manifestUnits: number;
  deliverableUnits: number;
  returnUnits: number;
  state: LoadState; // starts "unconfirmed" unless pre-flagged
  reason: LoadingReason | null;
  crate: string | null;
  loaderNote: string | null;
  vanUnits: number; // what the driver/observer counts in the van
  preFlagged: boolean; // came from the loader, driver confirms/edits, doesn't re-derive
}

// The loader's hand-off, keyed by outlet. This is the cross-role continuity made visible.
export const LOADER_PRE_FLAGS: Record<
  string,
  {
    deliverableUnits: number;
    returnUnits: number;
    reason: LoadingReason;
    crate: string;
    note: string;
  }
> = {
  OUT058: {
    deliverableUnits: 10,
    returnUnits: 2,
    reason: "Damaged in staging",
    crate: "R-04",
    note: "S. Fernando: 2 damaged in staging. Sealed in return crate R-04.",
  },
};

export function buildLoadRows(stops: DriverStop[] = TRIP_1_STOPS): LoadRow[] {
  return stops.map((s) => {
    const pre = LOADER_PRE_FLAGS[s.outletId];
    return {
      outletId: s.outletId,
      name: s.name,
      manifestUnits: s.units,
      deliverableUnits: pre ? pre.deliverableUnits : s.deliverableUnits,
      returnUnits: pre ? pre.returnUnits : s.returnUnits,
      vanUnits: pre ? pre.deliverableUnits + pre.returnUnits : s.units, // van holds deliverable+return
      state: pre ? ("flagged" as LoadState) : ("unconfirmed" as LoadState),
      reason: pre ? pre.reason : null,
      crate: pre ? pre.crate : null,
      loaderNote: pre ? pre.note : null,
      preFlagged: Boolean(pre),
    };
  });
}

export function summariseLoad(rows: LoadRow[]) {
  return {
    manifest: rows.reduce((t, r) => t + r.manifestUnits, 0),
    deliverable: rows.reduce((t, r) => t + r.deliverableUnits, 0),
    returnUnits: rows.reduce((t, r) => t + r.returnUnits, 0),
    confirmed: rows.filter((r) => r.state === "matches").length,
    flagged: rows.filter((r) => r.state === "flagged").length,
    awaiting: rows.filter((r) => r.state === "unconfirmed").length,
    discrepancies: rows.filter((r) => r.state === "flagged").length,
  };
}
