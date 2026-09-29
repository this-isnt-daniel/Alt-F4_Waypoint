import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { OUTLET_CLOSED, TRIP_1_STOPS, type DriverStop } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function OutletClosedScreen() {
  const { push, route } = useNavigator();
  const {
    completeStop,
    currentStopIndex,
    currentTripSequence,
    currentTripStops,
  } = useDriverState();

  const outletId =
    route.params.outletId ??
    currentTripSequence[currentStopIndex] ??
    OUTLET_CLOSED.outletId;

  const fallbackStop: DriverStop = TRIP_1_STOPS[0]!;
  const stop: DriverStop =
    currentTripStops.find((s) => s.outletId === outletId) ??
    currentTripStops[currentStopIndex] ??
    fallbackStop;

  const reason = route.params.reason ?? OUTLET_CLOSED.reason;
  const isLastStop = currentStopIndex >= currentTripSequence.length - 1;
  const nextOutletId = !isLastStop
    ? currentTripSequence[currentStopIndex + 1]
    : null;
  const nextStop = nextOutletId
    ? currentTripStops.find((s) => s.outletId === nextOutletId)
    : null;

  const handleContinue = () => {
    completeStop(outletId, "failed");
    if (isLastStop) {
      push("return-depot", { outletId });
    } else {
      // Driver continues route to next outlet, NOT back to depot!
      push("active-trip");
    }
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Stop unavailable</h1>
        <p className="text-[13px] text-slate-500">
          {stop.outletId} · {stop.name}
        </p>
      </div>

      <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-[13px] font-medium text-amber-900">
        Reason: {reason}
      </div>

      <Card variant="surface" className="space-y-2">
        <div className="text-[13px] font-semibold text-slate-800">
          Cargo retained for depot return
        </div>
        <div className="flex justify-between text-[13px] py-1 border-t border-slate-100">
          <span className="text-slate-900">Undelivered items ×{stop.units} units</span>
          <span className="text-amber-700 font-medium">Keep on vehicle</span>
        </div>
        <div className="text-[12px] text-slate-500 pt-1">
          Return crate: {stop.returnCrate ?? "R-07 (Sealed)"}
        </div>
        <div className="text-[12px] text-slate-500">
          Custody: Return to Kandy hub depot at end of trip
        </div>
      </Card>

      {!isLastStop ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/80 p-3 text-xs text-emerald-900 space-y-1">
          <div className="font-bold flex items-center gap-1.5 text-emerald-800">
            <AppIcon name="check-circle" size={15} className="text-emerald-600" />
            <span>Route continues to next outlet</span>
          </div>
          <p className="text-emerald-700">
            Cargo remains secured on vehicle. You do not return to the depot now — you will proceed directly to Stop {currentStopIndex + 2}:{" "}
            <span className="font-semibold">{nextStop?.outletId} ({nextStop?.name})</span>.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-xs text-blue-900">
          <span className="font-bold block">Final Stop of Trip</span>
          <p>
            All stops on this route are now concluded. Proceed back to Kandy hub depot to return secured crates.
          </p>
        </div>
      )}

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={handleContinue}>
          {!isLastStop
            ? `Proceed to next outlet (${nextStop?.outletId ?? "Next"})`
            : "Conclude route & return to depot"}
        </Button>
        <Button variant="ghost" size="md" onClick={() => push("active-trip")}>
          <AppIcon name="arrow-left" size={16} className="mr-2" /> Back to route overview
        </Button>
      </div>
    </div>
  );
}
