import { useState } from "react";
import { X, Map as MapIcon, ListChecks } from "lucide-react";
import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { SCENARIO_META } from "@/driver/data/scenarioMeta";
import { cn } from "@/lib/cn";

const TAG_CLASS: Record<string, string> = {
  FC: "text-success bg-success-fill border border-success/30",
  DEG: "text-warning bg-warning-fill border border-warning/30",
  FID: "text-offline bg-offline-fill border border-line",
  ENG: "text-offline bg-offline-fill border border-line",
};

const EDGE_MAP: Record<string, string[]> = {
  "active-trip": ["mark-arrived", "stop-detail", "chat", "call-overlay", "issue-wizard", "route-changed"],
  checklist: ["pod-photo", "not-handed-over", "active-trip"],
  "sync-review": ["record-sent", "active-trip"],
  "outlet-closed": ["return-depot", "active-trip"],
  "route-changed": ["active-trip", "call-overlay"],
  "camera-denied": ["pod-photo", "pod-pin"],
};

export function ScenarioPanel({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { push } = useNavigator();
  const { applyScenario } = useDriverState();
  const [view, setView] = useState<"list" | "map">("list");

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40"
      onClick={onClose}
    >
      <div
        className="max-h-[82vh] w-full max-w-[430px] overflow-y-auto rounded-t-2xl border-t border-line bg-surface p-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between pb-2 border-b border-line">
          <h2 className="text-lg font-bold text-ink">Scenario Explorer</h2>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => setView(view === "list" ? "map" : "list")}
              className="grid h-9 w-9 place-items-center rounded-btn border border-line text-ink-muted hover:bg-raised"
              aria-label="Toggle flow map"
            >
              {view === "list" ? <MapIcon size={18} /> : <ListChecks size={18} />}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="grid h-9 w-9 place-items-center rounded-btn text-ink-muted hover:bg-raised"
              aria-label="Close"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {view === "list" ? (
          <ul className="mt-3 space-y-2">
            {SCENARIO_META.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => {
                    applyScenario(s.id, s.params);
                    push(s.entry, s.params);
                    onClose();
                  }}
                  className="w-full rounded-card border border-line bg-raised p-3 text-left hover:border-green/40 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-ink text-sm">
                      {s.title}
                    </span>
                    <span className="flex gap-1">
                      {s.tags.map((t) => (
                        <span
                          key={t}
                          className={cn(
                            "rounded-pill px-1.5 py-0.5 text-[10px] font-bold",
                            TAG_CLASS[t],
                          )}
                        >
                          {t}
                        </span>
                      ))}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-ink-muted leading-relaxed">
                    {s.blurb}
                  </p>
                  <p className="mt-1 text-[10px] uppercase tracking-wide text-green font-semibold">
                    opens → {s.entry}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <div className="mt-3 space-y-2.5">
            {Object.entries(EDGE_MAP).map(([root, targets]) => (
              <div
                key={root}
                className="rounded-card border border-line bg-raised p-3"
              >
                <p className="text-sm font-semibold text-ink">{root}</p>
                <p className="mt-1 text-xs text-ink-muted">
                  → {targets.join(" · ") || "end"}
                </p>
              </div>
            ))}
            <p className="text-2xs text-ink-muted pt-1">
              Edges mirror tests/scenarios.test.ts (zero-orphan guarantee).
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
