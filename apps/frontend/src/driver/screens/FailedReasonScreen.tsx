import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { TRIP_1_STOPS, type DriverStop } from "@/driver/data/driverContent";
import { AlertTriangle, Check } from "lucide-react";

const REASONS = [
  "Outlet closed",
  "Mall bay unavailable",
  "Store refused delivery",
  "Unsafe access",
  "Receiver unavailable",
  "Vehicle breakdown en route",
  "Other issue",
];

export function FailedReasonScreen() {
  const { route, push, back } = useNavigator();
  const { currentStopIndex, currentTripStops, currentTripSequence } = useDriverState();
  const [selected, setSelected] = useState<string | null>(null);

  const outletId =
    route.params.outletId ??
    currentTripSequence[currentStopIndex] ??
    "OUT042";

  const fallbackStop: DriverStop = TRIP_1_STOPS[0]!;
  const stop: DriverStop =
    currentTripStops.find((s) => s.outletId === outletId) ??
    currentTripStops[currentStopIndex] ??
    fallbackStop;

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-6">
      <div className="flex items-center gap-2 mb-2 text-rose-500">
        <AlertTriangle size={24} strokeWidth={2.5} />
      </div>
      
      <h1 className="text-[24px] font-bold text-slate-900 mb-1">Report stop failure</h1>
      <p className="text-[15px] font-medium text-slate-600 mb-1">
        {stop.outletId} · {stop.name}
      </p>
      <p className="text-[13px] text-slate-500 mb-6">Why couldn't you deliver?</p>

      <div className="space-y-3 mb-8">
        {REASONS.map((reason) => (
          <button
            key={reason}
            type="button"
            onClick={() => setSelected(reason)}
            className={`w-full flex items-center justify-between p-4 rounded-xl border transition-colors cursor-pointer ${
              selected === reason
                ? "border-green bg-green/5 shadow-sm"
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <span className={`text-[15px] font-semibold ${selected === reason ? "text-slate-900" : "text-slate-700"}`}>
              {reason}
            </span>
            {selected === reason && (
              <Check size={20} className="text-green" style={{ color: "var(--c-green)" }} />
            )}
          </button>
        ))}
      </div>

      <div className="mt-auto pt-4 space-y-3">
        <button
          type="button"
          onClick={() =>
            push("outlet-closed", {
              outletId: stop.outletId,
              reason: selected ?? "Outlet closed",
            })
          }
          disabled={!selected}
          className="w-full bg-rose-600 text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Continue
        </button>
        
        <button
          type="button"
          onClick={back}
          className="w-full py-3 text-[14px] font-semibold text-slate-500 hover:text-slate-700 cursor-pointer"
        >
          Cancel & Back to route
        </button>
      </div>
    </div>
  );
}
