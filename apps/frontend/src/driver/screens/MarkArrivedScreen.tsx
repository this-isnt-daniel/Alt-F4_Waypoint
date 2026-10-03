import { useNavigator } from "@/router/navigator";
import { DriverMap } from "@/driver/components/DriverMap";
import { useDriverState } from "@/driver/state/useDriverState";

// ── MARK ARRIVED ─────────────────────────────────────────────────
// Keeps the map visible. Only the bottom sheet changes state.
// New label: "AT STOP" · Primary action: START DELIVERY
export function MarkArrivedScreen() {
  const { push, route } = useNavigator();
  const seq = Number(route.params.seq) || 2;

  const {
    currentTripSequence,
    currentTripStops,
    currentStopIndex,
    completedStopIds,
    flaggedStopIds,
    failedStopIds,
  } = useDriverState();

  const stop =
    currentTripStops.find((s) => s.seq === seq) ??
    currentTripStops[currentStopIndex];
  const currentOutletId =
    stop?.outletId ?? currentTripSequence[currentStopIndex];

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-slate-100">

      {/* MAP – identical to ActiveTripScreen, giving spatial continuity */}
      <div className="flex-1 min-h-0 relative">
        <DriverMap
          stopIds={currentTripSequence}
          currentStopId={currentOutletId}
          completedStopIds={completedStopIds}
          flaggedStopIds={flaggedStopIds}
          failedStopIds={failedStopIds}
          className="absolute inset-0"
        />
      </div>

      {/* BOTTOM SHEET – "AT STOP" state */}
      {stop && (
        <div className="shrink-0 bg-white border-t border-slate-200">
          <div className="flex justify-center pt-2.5 pb-1">
            <div className="w-8 h-1 rounded-full bg-slate-300" />
          </div>

          <div className="px-5 pb-6 pt-1">
            {/* Status label */}
            <div className="flex items-center gap-1.5 mb-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
              <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-600">
                At Stop
              </p>
            </div>

            {/* Outlet identity */}
            <p className="text-[20px] font-bold text-slate-900 leading-tight">
              {stop.outletId}
            </p>
            <p className="text-[15px] text-slate-500 mt-0.5 mb-3">{stop.name}</p>

            {/* Delivery window */}
            <p className="text-[13px] text-slate-500 mb-5">
              Delivery window {stop.window}
            </p>

            {/* PRIMARY ACTION */}
            <button
              type="button"
              onClick={() => push("checklist", { seq: String(seq) })}
              className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
              style={{ backgroundColor: "var(--c-green)" }}
            >
              Start Delivery
            </button>

            {/* Secondary */}
            <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => push("call-overlay", { outletId: stop.outletId })}
                className="text-[14px] font-semibold text-slate-500 hover:text-slate-800 cursor-pointer py-1"
              >
                Call
              </button>
              <button
                type="button"
                onClick={() => push("stop-detail", { seq: String(stop.seq) })}
                className="text-[14px] font-semibold text-slate-500 hover:text-slate-800 cursor-pointer py-1"
              >
                Details
              </button>
              <button
                type="button"
                onClick={() =>
                  push("failed-reason", { outletId: stop.outletId, seq: String(stop.seq) })
                }
                className="text-[14px] font-semibold text-slate-400 hover:text-rose-600 cursor-pointer py-1"
              >
                Issue
              </button>
              <button
                type="button"
                onClick={() => push("active-trip")}
                className="text-[14px] font-semibold text-slate-400 hover:text-slate-700 cursor-pointer py-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
