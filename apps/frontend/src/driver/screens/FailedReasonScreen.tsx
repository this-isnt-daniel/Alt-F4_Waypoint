import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { AppIcon } from "@/driver/components/AppIcon";
import { useDriverState } from "@/driver/state/useDriverState";
import { TRIP_1_STOPS, type DriverStop } from "@/driver/data/driverContent";

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
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Report stop failure</h1>
        <p className="text-[13px] font-medium text-slate-600">
          {stop.outletId} · {stop.name}
        </p>
      </div>
      <p className="text-[13px] text-slate-500">Why couldn't you deliver?</p>
      <div className="space-y-2">
        {REASONS.map((reason) => (
          <button
            key={reason}
            type="button"
            onClick={() => setSelected(reason)}
            className={`w-full flex items-center justify-between p-3 rounded-xl border transition-colors cursor-pointer ${
              selected === reason
                ? "border-green/30 bg-green-fill ring-1 ring-green/20"
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <span className="text-[13px] font-medium text-slate-900">{reason}</span>
            {selected === reason && (
              <AppIcon name="check" size={18} className="text-green" />
            )}
          </button>
        ))}
      </div>
      <div className="space-y-2 pt-2">
        <Button
          variant="primary"
          size="lg"
          onClick={() =>
            push("outlet-closed", {
              outletId: stop.outletId,
              reason: selected ?? "Outlet closed",
            })
          }
          disabled={!selected}
        >
          Continue
        </Button>
        <Button variant="ghost" size="md" onClick={back}>
          <AppIcon name="arrow-left" size={16} className="mr-2" /> Cancel & Back to route
        </Button>
      </div>
    </div>
  );
}
