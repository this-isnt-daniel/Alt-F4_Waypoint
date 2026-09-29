import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { useDriverState } from "@/driver/state/useDriverState";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";

export function DeliveryCompleteScreen() {
  const { push } = useNavigator();
  const { currentStopIndex, trip1Sequence, completeStop, connection } =
    useDriverState();

  const currentOutletId = trip1Sequence[currentStopIndex] ?? "OUT047";
  const stop =
    TRIP_1_STOPS.find((s) => s.outletId === currentOutletId) ?? TRIP_1_STOPS[1]!;

  const handleContinue = () => {
    completeStop(currentOutletId, "delivered");
    // If last stop, route to trip-complete
    if (currentStopIndex >= trip1Sequence.length - 1) {
      push("trip-complete");
    } else {
      push("active-trip");
    }
  };

  const isOffline = connection === "offline";

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto text-center pb-8">
      <div className="pt-6">
        {/* Compact 40px marker instead of 96px tile */}
        <div className="w-10 h-10 rounded-full bg-green-fill mx-auto flex items-center justify-center mb-3 border border-green/20">
          <AppIcon name="check" size={20} className="text-green" />
        </div>
        <h1 className="text-lg font-bold text-slate-900">Delivery complete</h1>
        <p className="text-[13px] text-slate-500">
          {stop.outletId} · 06:34
        </p>
      </div>

      <Card variant="surface" className="text-left space-y-2.5">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <span className="text-[14px] font-semibold text-slate-900">
            Handover confirmed
          </span>
          <span className="text-[12px] font-medium text-green">
            {stop.deliverableUnits} items received
          </span>
        </div>

        <div className="space-y-1.5 text-[13px]">
          <div className="flex justify-between">
            <span className="text-slate-500">Arrival</span>
            <span className="font-medium text-slate-900">06:18</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Finished</span>
            <span className="font-medium text-slate-900">06:34</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Photo</span>
            <span className="font-medium text-slate-900">Attached</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Manager PIN</span>
            <span className="font-medium text-slate-900">Confirmed</span>
          </div>
        </div>

        {/* Neutral slate inline sync note */}
        <div className="pt-2 border-t border-slate-100 text-[12px] text-slate-500 flex items-center gap-1.5">
          {isOffline ? (
            <>
              <AppIcon name="cloud-off" size={14} className="text-slate-400" />
              <span>Saved offline · will sync when connected</span>
            </>
          ) : (
            <>
              <AppIcon name="refresh" size={14} className="animate-spin text-slate-400" />
              <span>Photo uploading</span>
            </>
          )}
        </div>
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={handleContinue}>
          Continue to next stop
        </Button>
        <Button
          variant="ghost"
          size="md"
          onClick={() => push("sync-centre")}
        >
          View record in queue
        </Button>
      </div>
    </div>
  );
}
