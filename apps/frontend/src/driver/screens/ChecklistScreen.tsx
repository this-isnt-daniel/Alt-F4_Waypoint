import { useMemo, useState } from "react";
import { Button } from "@/driver/components/Button";
import { ChoiceList } from "@/driver/components/ChoiceList";
import { BottomSheet } from "@/driver/components/BottomSheet";
import { ChecklistRow, type CheckState } from "@/driver/components/ChecklistRow";
import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { OUT047_CHECKLIST_ITEMS, TRIP_1_STOPS } from "@/driver/data/driverContent";

const HANDOVER_REASONS = [
  "Damaged",
  "Missing at loading",
  "Wrong item",
  "Store refused",
  "Access issue",
  "Other",
] as const;
type HandoverReason = (typeof HANDOVER_REASONS)[number];

interface Line {
  id: string;
  name: string;
  qty: number;
  meta: string;
  state: CheckState;
  reason: HandoverReason | null;
  note: string;
}

export function ChecklistScreen() {
  const { push } = useNavigator();
  const { currentStopIndex, trip1Sequence } = useDriverState();

  const currentOutletId = trip1Sequence[currentStopIndex] ?? "OUT047";
  const currentStop =
    TRIP_1_STOPS.find((s) => s.outletId === currentOutletId) ?? TRIP_1_STOPS[1]!;

  const [lines, setLines] = useState<Line[]>(() =>
    OUT047_CHECKLIST_ITEMS.map((i) => ({
      id: i.id,
      name: i.name,
      qty: i.quantity,
      meta: i.temp,
      state: "pending",
      reason: null,
      note: "",
    })),
  );
  const [flagging, setFlagging] = useState<Line | null>(null); // in-place reason sheet
  const [bulkOpen, setBulkOpen] = useState(false);

  const pending = useMemo(
    () => lines.filter((l) => l.state === "pending").length,
    [lines],
  );
  const hasFlagged = useMemo(
    () => lines.some((l) => l.state === "flagged"),
    [lines],
  );
  const allResolved = pending === 0;

  const toggleDelivered = (id: string) =>
    setLines((ls) =>
      ls.map((l) =>
        l.id === id
          ? {
              ...l,
              state: l.state === "delivered" ? "pending" : "delivered",
              reason: null,
            }
          : l,
      ),
    );

  // Open in-place reason sheet, mutate, and STAY on checklist.
  const openFlag = (l: Line) => setFlagging(l);

  const commitFlag = (reason: HandoverReason, note: string) => {
    setLines((ls) =>
      ls.map((l) =>
        l.id === flagging?.id
          ? { ...l, state: "flagged", reason, note }
          : l,
      ),
    );
    setFlagging(null); // returns to the checklist — does NOT navigate
  };

  const markAllDelivered = () => {
    setLines((ls) =>
      ls.map((l) =>
        l.state === "pending"
          ? { ...l, state: "delivered", reason: null }
          : l,
      ),
    );
    setBulkOpen(false);
  };

  return (
    <div className="flex min-h-full flex-col px-4 pb-6 pt-2 max-w-[430px] mx-auto">
      <p className="text-2xs font-semibold uppercase tracking-wide text-green">
        Unloading checklist
      </p>
      <h1 className="mt-1 text-2xl font-bold text-ink">
        {currentStop.name}
      </h1>
      <p className="mt-1 text-sm text-ink-muted">
        {currentOutletId} · arrived 06:18
      </p>
      <p className="mt-3 rounded-card border border-line bg-surface p-3 text-sm text-ink">
        Check each item, or flag what was not handed over.
      </p>

      <ul className="mt-3 space-y-2">
        {lines.map((l) => (
          <li key={l.id}>
            <ChecklistRow
              name={l.name}
              qty={l.qty}
              meta={l.meta}
              state={l.state}
              onRowTap={() => toggleDelivered(l.id)}
              onFlag={() => openFlag(l)}
            />
          </li>
        ))}
      </ul>

      {pending > 0 && (
        <button
          type="button"
          onClick={() => setBulkOpen(true)}
          className="mt-3 self-start text-sm font-medium text-green hover:underline"
        >
          Mark all items delivered
        </button>
      )}

      <div className="mt-auto pt-4 space-y-2">
        {/* Photo ONLY when items flagged / damaged; otherwise directly PIN */}
        <Button
          variant="primary"
          size="lg"
          fullWidth
          disabled={!allResolved}
          onClick={() => {
            if (hasFlagged) {
              push("pod-photo", { outletId: currentOutletId, photoRequired: "true" });
            } else {
              push("pod-pin", { outletId: currentOutletId, cleanHandover: "true" });
            }
          }}
        >
          {hasFlagged ? "Continue to photo (items flagged)" : "Continue to PIN"}
        </Button>
        {!allResolved && (
          <p className="text-center text-xs text-ink-muted">
            Resolve all {pending} item(s) to continue.
          </p>
        )}
        {allResolved && !hasFlagged && (
          <p className="text-center text-xs text-ink-muted">
            Clean handover · No photograph required.
          </p>
        )}
        {allResolved && hasFlagged && (
          <p className="text-center text-xs text-amber-600 font-medium">
            Photograph required: 1+ item damaged / returned.
          </p>
        )}
        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={() => push("active-trip")}
            className="text-sm font-medium text-green hover:underline"
          >
            ← Back to map
          </button>
          <button
            type="button"
            onClick={() => push("failed-reason", { outletId: currentOutletId })}
            className="text-xs font-semibold text-rose-600 hover:text-rose-700 hover:underline"
          >
            Report stop failure
          </button>
        </div>
      </div>

      {/* in-place reason capture */}
      <BottomSheet
        open={Boolean(flagging)}
        onClose={() => setFlagging(null)}
        title={flagging ? `${flagging.name} ×${flagging.qty}` : ""}
        subtitle="Why wasn't it handed over?"
      >
        {flagging && (
          <FlagReasonForm
            initial={flagging.reason}
            initialNote={flagging.note}
            onSubmit={commitFlag}
            onCancel={() => setFlagging(null)}
          />
        )}
      </BottomSheet>

      <BottomSheet
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        title="Mark all delivered?"
      >
        <p className="px-4 text-sm text-ink">
          This marks all {pending} remaining item(s) as handed over. You can still flag an item afterwards.
        </p>
        <div className="flex gap-2 p-4">
          <Button
            variant="secondary"
            fullWidth
            onClick={() => setBulkOpen(false)}
          >
            Cancel
          </Button>
          <Button variant="primary" fullWidth onClick={markAllDelivered}>
            Confirm all
          </Button>
        </div>
      </BottomSheet>
    </div>
  );
}

function FlagReasonForm({
  initial,
  initialNote,
  onSubmit,
  onCancel,
}: {
  initial: HandoverReason | null;
  initialNote: string;
  onSubmit: (r: HandoverReason, note: string) => void;
  onCancel: () => void;
}) {
  const [reason, setReason] = useState<HandoverReason>(initial ?? "Damaged");
  const [note, setNote] = useState(initialNote);

  return (
    <div className="space-y-4 p-4">
      <ChoiceList
        options={HANDOVER_REASONS.map((r) => ({ id: r, label: r }))}
        selectedId={reason}
        onSelect={(id) => setReason(id as HandoverReason)}
        allowOtherNote={false}
      />
      {reason === "Other" && (
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={2}
          placeholder="Add a short detail…"
          className="w-full rounded-btn border border-line bg-surface px-3 py-2 text-ink outline-none focus:border-green"
        />
      )}
      <div className="flex gap-2 pt-1">
        <Button variant="secondary" fullWidth onClick={onCancel}>
          Cancel
        </Button>
        <Button
          variant="primary"
          fullWidth
          onClick={() => onSubmit(reason, note)}
        >
          Save & back to list
        </Button>
      </div>
    </div>
  );
}
