import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";
import { Check, CloudOff } from "lucide-react";

// ── DELIVERY COMPLETE SCREEN ─────────────────────────────────────
// Concise confirmation then immediate next-stop prompt.
// Does not stay here long – driver needs to move on quickly.
export function DeliveryCompleteScreen() {
  const { push } = useNavigator();
  const { currentStopIndex, trip1Sequence, completeStop, connection } =
    useDriverState();

  const currentOutletId = trip1Sequence[currentStopIndex] ?? "OUT047";
  const stop =
    TRIP_1_STOPS.find((s) => s.outletId === currentOutletId) ?? TRIP_1_STOPS[1]!;

  const isLastStop = currentStopIndex >= trip1Sequence.length - 1;
  const isOffline = connection === "offline";

  const handleContinue = () => {
    completeStop(currentOutletId, "delivered");
    if (isLastStop) {
      push("trip-complete");
    } else {
      push("active-trip");
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-8">

      {/* Confirmation mark */}
      <div className="flex flex-col items-center mb-8">
        <div className="w-12 h-12 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center mb-4">
          <Check size={22} className="text-emerald-600" />
        </div>
        <p className="text-[12px] font-bold uppercase tracking-wider text-emerald-600 mb-1">
          Delivered
        </p>
        <h1 className="text-[22px] font-bold text-slate-900">{stop.outletId}</h1>
        <p className="text-[14px] text-slate-500 mt-0.5">{stop.name}</p>
      </div>

      {/* Summary rows */}
      <div className="mb-6 border-t border-slate-100">
        <div className="flex items-center justify-between py-3 border-b border-slate-100">
          <span className="text-[13px] text-slate-500">Items received</span>
          <span className="text-[13px] font-semibold text-slate-900">{stop.deliverableUnits}</span>
        </div>
        <div className="flex items-center justify-between py-3 border-b border-slate-100">
          <span className="text-[13px] text-slate-500">Arrival</span>
          <span className="text-[13px] font-semibold text-slate-900">06:18</span>
        </div>
        <div className="flex items-center justify-between py-3 border-b border-slate-100">
          <span className="text-[13px] text-slate-500">Completed</span>
          <span className="text-[13px] font-semibold text-slate-900">06:34</span>
        </div>
        <div className="flex items-center justify-between py-3">
          <span className="text-[13px] text-slate-500">Photo</span>
          <span className="text-[13px] font-semibold text-slate-900">Saved</span>
        </div>
      </div>

      {/* Offline note – quiet and informational */}
      {isOffline && (
        <div className="flex items-center gap-2 mb-4 text-[12px] text-slate-400">
          <CloudOff size={13} />
          <span>Offline — saved locally. Will sync when connection returns.</span>
        </div>
      )}

      {/* Primary action */}
      <button
        type="button"
        onClick={handleContinue}
        className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer mb-3"
        style={{ backgroundColor: "var(--c-green)" }}
      >
        {isLastStop ? "Complete Trip" : "Next Stop"}
      </button>

      {/* Queue link – very quiet */}
      <button
        type="button"
        onClick={() => push("sync-centre")}
        className="w-full py-2 text-[13px] text-slate-400 hover:text-slate-700 cursor-pointer"
      >
        View sync queue
      </button>
    </div>
  );
}
