import { useMemo, useState } from "react";
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
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 pb-6 pt-5">
      <p className="text-[12px] font-bold uppercase tracking-wider text-green mb-1">
        Unloading checklist
      </p>
      <h1 className="text-[22px] font-bold text-slate-900">
        {currentStop.name}
      </h1>
      <p className="mt-1 text-[13px] text-slate-500 mb-4">
        {currentOutletId} · arrived 06:18
      </p>
      <p className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-[13px] text-slate-700">
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
          className="mt-3 self-start text-[14px] font-medium text-green hover:underline cursor-pointer"
        >
          Mark all items delivered
        </button>
      )}

      <div className="mt-auto pt-4 space-y-2">
        <button
          type="button"
          disabled={!allResolved}
          onClick={() => {
            if (hasFlagged) {
              push("pod-photo", { outletId: currentOutletId, photoRequired: "true" });
            } else {
              push("pod-pin", { outletId: currentOutletId, cleanHandover: "true" });
            }
          }}
          className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ backgroundColor: "var(--c-green)" }}
        >
          {hasFlagged ? "Continue — items flagged" : "Continue to POD"}
        </button>
        {!allResolved && (
          <p className="text-center text-[12px] text-slate-400">
            Resolve all {pending} item(s) to continue.
          </p>
        )}
        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={() => push("active-trip")}
            className="text-[13px] font-medium text-slate-400 hover:text-slate-700 cursor-pointer"
          >
            ← Back to map
          </button>
          <button
            type="button"
            onClick={() => push("failed-reason", { outletId: currentOutletId })}
            className="text-[13px] font-semibold text-slate-400 hover:text-rose-600 cursor-pointer"
          >
            Report failure
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
        <p className="px-5 text-[14px] text-slate-700">
          This marks all {pending} remaining item(s) as handed over. You can still flag an item afterwards.
        </p>
        <div className="flex gap-3 p-5">
          <button
            type="button"
            className="flex-1 py-3.5 rounded-lg bg-slate-100 text-slate-700 font-semibold text-[15px] cursor-pointer"
            onClick={() => setBulkOpen(false)}
          >
            Cancel
          </button>
          <button 
            type="button"
            className="flex-1 py-3.5 rounded-lg bg-green text-white font-semibold text-[15px] cursor-pointer"
            style={{ backgroundColor: "var(--c-green)" }}
            onClick={markAllDelivered}
          >
            Confirm all
          </button>
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
    <div className="space-y-4 px-5 pb-5">
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
          className="w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-[14px] text-slate-900 outline-none focus:border-green"
        />
      )}
      <div className="flex gap-3 pt-2">
        <button
          type="button"
          className="flex-1 py-3.5 rounded-lg bg-slate-100 text-slate-700 font-semibold text-[15px] cursor-pointer"
          onClick={onCancel}
        >
          Cancel
        </button>
        <button
          type="button"
          className="flex-1 py-3.5 rounded-lg bg-green text-white font-semibold text-[15px] cursor-pointer"
          style={{ backgroundColor: "var(--c-green)" }}
          onClick={() => onSubmit(reason, note)}
        >
          Save flag
        </button>
      </div>
    </div>
  );
}
