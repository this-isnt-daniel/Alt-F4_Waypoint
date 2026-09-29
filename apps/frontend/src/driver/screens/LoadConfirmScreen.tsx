import { useMemo, useState } from "react";
import { Check, Flag, ChevronDown, ChevronUp, Minus, Plus } from "lucide-react";
import { Button } from "@/driver/components/Button";
import { Chip } from "@/driver/components/Chip";
import { ChoiceList } from "@/driver/components/ChoiceList";
import { BottomSheet } from "@/driver/components/BottomSheet";
import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import {
  buildLoadRows,
  summariseLoad,
  type LoadRow,
} from "@/driver/data/loadRows";
import {
  LOAD_STATE,
  LOADING_REASONS,
  type LoadingReason,
} from "@/driver/data/labels";
import {
  TRIP_1_STOPS,
  TRIP_2_STOPS,
} from "@/driver/data/driverContent";
import { formatUnits } from "@/lib/derive";
import { cn } from "@/lib/cn";

export function LoadConfirmScreen() {
  const { route, push } = useNavigator();
  const { connection, startTrip1, startTrip2, activeTripId } = useDriverState();
  const isTrip2 = route.params.trip === "2" || activeTripId === 2;
  const offline = connection === "offline";

  const [rows, setRows] = useState<LoadRow[]>(() =>
    buildLoadRows(isTrip2 ? TRIP_2_STOPS : TRIP_1_STOPS),
  );
  const [editing, setEditing] = useState<LoadRow | null>(null);
  const [bulkOpen, setBulkOpen] = useState(false);

  const sum = useMemo(() => summariseLoad(rows), [rows]);
  const canDepart = sum.awaiting === 0; // every row is matches or flagged

  const setRowState = (outletId: string, next: LoadRow["state"]) =>
    setRows((rs) =>
      rs.map((r) => (r.outletId === outletId ? { ...r, state: next } : r)),
    );

  // tap a row: unconfirmed -> matches -> unconfirmed. Flagging is the flag button.
  const onRowTap = (r: LoadRow) =>
    setRowState(r.outletId, r.state === "matches" ? "unconfirmed" : "matches");

  const applyDiscrepancy = (
    patch: Pick<LoadRow, "vanUnits" | "reason" | "crate">,
  ) => {
    setRows((rs) =>
      rs.map((r) =>
        r.outletId === editing?.outletId
          ? {
              ...r,
              ...patch,
              state: "flagged",
              deliverableUnits: Math.min(patch.vanUnits, r.manifestUnits),
              returnUnits: Math.max(0, r.manifestUnits - patch.vanUnits),
            }
          : r,
      ),
    );
    setEditing(null);
  };

  const confirmAllMatch = () => {
    // bulk-confirm ONLY the unconfirmed rows; flagged/exception rows are never blind-passed.
    setRows((rs) =>
      rs.map((r) => (r.state === "unconfirmed" ? { ...r, state: "matches" } : r)),
    );
    setBulkOpen(false);
  };

  return (
    <div className="flex min-h-full flex-col px-4 pb-6 pt-2 max-w-[430px] mx-auto">
      <h1 className="text-2xl font-bold text-ink">Load confirmation</h1>
      <p className="mt-1 text-sm text-ink-muted">
        {isTrip2 ? "Trip 2 · Style · Kandy" : "Trip 1 · Fresh · Kandy"}
      </p>
      <p className="mt-3 rounded-card border border-line bg-surface p-3 text-sm text-ink">
        Match the van to the manifest. Tap a stop to confirm it matches, or flag anything short, extra or damaged.
      </p>

      <div className="mt-4 flex items-center justify-between">
        <p className="text-2xs font-semibold uppercase tracking-wide text-ink-muted">
          Manifest groups
        </p>
        <Chip
          kind="sync"
          tone={sum.flagged > 0 ? "inReview" : "online"}
          label={`${sum.flagged} flagged`}
        />
      </div>

      <ul className="mt-2 space-y-2">
        {rows.map((r) => (
          <li key={r.outletId}>
            <div
              className={cn(
                "flex items-center gap-3 rounded-card border p-4 transition-colors",
                r.state === "flagged"
                  ? "border-warning/40 bg-warning-fill/40"
                  : "border-line bg-surface",
              )}
            >
              <button
                type="button"
                onClick={() => onRowTap(r)}
                aria-label={`Confirm ${r.outletId} matches`}
                className="flex min-w-0 flex-1 items-center gap-3 text-left"
              >
                <span
                  aria-hidden="true"
                  className={cn(
                    "grid h-9 w-9 shrink-0 place-items-center rounded-btn",
                    r.state === "flagged"
                      ? "bg-warning-fill text-warning"
                      : r.state === "matches"
                        ? "bg-success-fill text-success"
                        : "border border-line bg-raised text-ink-muted",
                  )}
                >
                  {r.state === "flagged" ? (
                    <Flag size={18} />
                  ) : (
                    <Check
                      size={18}
                      strokeWidth={r.state === "matches" ? 3 : 1.5}
                    />
                  )}
                </span>
                <span className="min-w-0">
                  <span className="block truncate font-semibold text-ink">
                    {r.outletId} · {formatUnits(r.manifestUnits)}
                  </span>
                  {r.state === "flagged" && (
                    <span className="block text-sm text-ink-muted">
                      {formatUnits(r.deliverableUnits)} deliverable · {r.returnUnits} return
                      {r.preFlagged ? " · loader pre-flag" : ""}
                    </span>
                  )}
                </span>
              </button>
              <span
                className={cn(
                  "text-sm font-medium",
                  r.state === "flagged"
                    ? "text-warning"
                    : r.state === "matches"
                      ? "text-success"
                      : "text-ink-muted",
                )}
              >
                {LOAD_STATE[r.state]}
              </span>
              {r.state !== "flagged" && (
                <button
                  type="button"
                  onClick={() => setEditing(r)}
                  aria-label={`Flag ${r.outletId}`}
                  className="grid h-12 w-12 shrink-0 place-items-center rounded-btn text-ink-muted hover:bg-raised hover:text-ink transition-colors"
                >
                  <Flag size={18} />
                </button>
              )}
              {r.state === "flagged" && (
                <button
                  type="button"
                  onClick={() => setEditing(r)}
                  aria-label={`Edit ${r.outletId} discrepancy`}
                  className="grid h-12 w-12 shrink-0 place-items-center rounded-btn text-warning"
                >
                  {editing?.outletId === r.outletId ? (
                    <ChevronUp size={18} />
                  ) : (
                    <ChevronDown size={18} />
                  )}
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {/* derived footer — no hardcoded numbers */}
      <div className="mt-3 rounded-card border border-line bg-raised p-3 text-sm text-ink">
        <p>
          {rows.length} stops · manifest {formatUnits(sum.manifest)} · deliverable{" "}
          {formatUnits(sum.deliverable)}
        </p>
        <p className="text-ink-muted">
          return {sum.returnUnits} · {sum.discrepancies} discrepanc
          {sum.discrepancies === 1 ? "y" : "ies"} · {sum.awaiting} to check
        </p>
      </div>

      {sum.awaiting > 0 && (
        <button
          type="button"
          onClick={() => setBulkOpen(true)}
          className="mt-3 self-start text-sm font-medium text-green hover:underline"
        >
          Confirm all match
        </button>
      )}

      <div className="mt-auto pt-4 space-y-2">
        <Button
          variant="primary"
          size="lg"
          fullWidth
          disabled={!canDepart}
          onClick={() => {
            if (isTrip2) {
              startTrip2();
            } else {
              startTrip1();
            }
            push("active-trip");
          }}
        >
          {offline ? "Confirm & depart · saved offline" : "Confirm & depart"}
        </Button>
        {!canDepart && (
          <p className="text-center text-xs text-ink-muted">
            Resolve all {sum.awaiting} stop(s) to depart.
          </p>
        )}
        {offline && (
          <p className="text-center text-xs text-ink-muted">
            Saved on this phone. Dispatch notification is queued.
          </p>
        )}
      </div>

      {/* inline discrepancy sheet */}
      <BottomSheet
        open={Boolean(editing)}
        onClose={() => setEditing(null)}
        title={editing ? `${editing.outletId} discrepancy` : ""}
      >
        {editing && (
          <DiscrepancyForm
            row={editing}
            onSubmit={applyDiscrepancy}
            onCancel={() => setEditing(null)}
          />
        )}
      </BottomSheet>

      <BottomSheet
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        title="Confirm all match?"
      >
        <p className="px-4 text-sm text-ink">
          This marks every unchecked stop as matching the manifest. The{" "}
          {sum.flagged} flagged exception{sum.flagged === 1 ? "" : "s"} stay flagged and are not overwritten.
        </p>
        <div className="flex gap-2 p-4">
          <Button
            variant="secondary"
            fullWidth
            onClick={() => setBulkOpen(false)}
          >
            Cancel
          </Button>
          <Button variant="primary" fullWidth onClick={confirmAllMatch}>
            Confirm
          </Button>
        </div>
      </BottomSheet>
    </div>
  );
}

function DiscrepancyForm({
  row,
  onSubmit,
  onCancel,
}: {
  row: LoadRow;
  onSubmit: (p: Pick<LoadRow, "vanUnits" | "reason" | "crate">) => void;
  onCancel: () => void;
}) {
  const [van, setVan] = useState(row.vanUnits);
  const [reason, setReason] = useState<LoadingReason>(
    row.reason ?? "Short at loading",
  );
  const [crate, setCrate] = useState(row.crate ?? "");
  const short = row.manifestUnits - van;

  return (
    <div className="space-y-4 p-4">
      <p className="text-sm text-ink-muted">{row.name}</p>
      <div className="flex items-center justify-between rounded-card border border-line bg-raised p-3">
        <span className="text-sm text-ink">
          Van count · manifest {row.manifestUnits}
        </span>
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Decrease van count"
            onClick={() => setVan((v) => Math.max(0, v - 1))}
            className="grid h-11 w-11 place-items-center rounded-btn border border-line bg-surface text-ink hover:bg-raised"
          >
            <Minus size={18} />
          </button>
          <span className="w-8 text-center text-lg font-bold text-ink">
            {van}
          </span>
          <button
            type="button"
            aria-label="Increase van count"
            onClick={() => setVan((v) => Math.min(row.manifestUnits, v + 1))}
            className="grid h-11 w-11 place-items-center rounded-btn border border-line bg-surface text-ink hover:bg-raised"
          >
            <Plus size={18} />
          </button>
        </div>
      </div>
      {short !== 0 && (
        <p className="text-sm font-medium text-warning">
          {short > 0 ? `Short by ${short}` : `Extra by ${-short}`}
        </p>
      )}
      <div>
        <p className="mb-2 text-2xs font-semibold uppercase tracking-wide text-ink-muted">
          Reason
        </p>
        <ChoiceList
          options={LOADING_REASONS.map((r) => ({ id: r, label: r }))}
          selectedId={reason}
          onSelect={(id) => setReason(id as LoadingReason)}
          allowOtherNote={false}
        />
      </div>
      {short > 0 && (
        <label className="block">
          <span className="mb-1 block text-2xs font-semibold uppercase tracking-wide text-ink-muted">
            Return crate (if sealing goods)
          </span>
          <input
            value={crate}
            onChange={(e) => setCrate(e.target.value)}
            placeholder="e.g. R-04"
            className="w-full rounded-btn border border-line bg-surface px-3 py-3 text-ink outline-none focus:border-green"
          />
        </label>
      )}
      {row.loaderNote && (
        <p className="rounded-card bg-raised p-3 text-sm text-ink-muted">
          {row.loaderNote}
        </p>
      )}
      <div className="flex gap-2 pt-1">
        <Button variant="secondary" fullWidth onClick={onCancel}>
          Cancel
        </Button>
        <Button
          variant="primary"
          fullWidth
          onClick={() =>
            onSubmit({ vanUnits: van, reason, crate: crate || null })
          }
        >
          Save flag
        </Button>
      </div>
    </div>
  );
}
