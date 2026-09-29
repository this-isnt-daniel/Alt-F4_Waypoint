import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { AppIcon } from "@/driver/components/AppIcon";
import { VEHICLE, CONTACT_DISPATCH_PRESETS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";
import { AlertTriangle, Wrench } from "lucide-react";

export function ContactDispatchSheet() {
  const { route, push, back } = useNavigator();
  const {
    reportBreakdown,
    currentStopIndex,
    currentTripSequence,
    currentTripStops,
    vehicleBreakdown,
  } = useDriverState();

  const [selected, setSelected] = useState<string | null>(
    route.params.topic ?? "Vehicle issue",
  );

  const currentOutletId =
    currentTripSequence[currentStopIndex] ?? currentTripSequence[0];
  const currentStop =
    currentTripStops.find((s) => s.outletId === currentOutletId) ??
    currentTripStops[0];

  const handleTriggerBreakdown = () => {
    reportBreakdown("Vehicle breakdown reported: Immediate roadside assistance requested");
    push("chat", {
      recipient: "dispatch",
      topic: "Vehicle Breakdown · Assistance Dispatched",
    });
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-6">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Contact Central Dispatch</h1>
        <p className="text-[13px] text-slate-500">
          Vehicle {VEHICLE.id} ({VEHICLE.type}) · {VEHICLE.depot}
        </p>
      </div>

      {vehicleBreakdown && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 flex items-start gap-2">
          <AlertTriangle size={16} className="text-rose-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block">Vehicle Breakdown Alert Active</span>
            <span>Dispatch has logged incident for {VEHICLE.id}. Roadside assistance is coordinating.</span>
          </div>
        </div>
      )}

      <div className="text-[12px] font-semibold text-slate-500 uppercase tracking-wider">
        Select reason / situation
      </div>
      <div className="space-y-2">
        {CONTACT_DISPATCH_PRESETS.map((preset) => (
          <button
            key={preset}
            type="button"
            onClick={() => setSelected(preset)}
            className={`w-full flex items-center justify-between p-3 rounded-xl border transition-colors cursor-pointer ${
              selected === preset
                ? "border-green/30 bg-green-fill ring-1 ring-green/20"
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <div className="flex items-center gap-2">
              {preset === "Vehicle issue" && (
                <Wrench size={16} className="text-amber-600" />
              )}
              <span className="text-[13px] font-medium text-slate-900">{preset}</span>
            </div>
            {selected === preset && (
              <AppIcon name="check" size={18} className="text-green" />
            )}
          </button>
        ))}
      </div>

      {/* Scenario / Emergency Failure Triggers */}
      {selected === "Vehicle issue" && (
        <div className="rounded-xl border border-amber-300 bg-amber-50/70 p-3 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900">
            <AlertTriangle size={15} className="text-amber-600" />
            <span>Vehicle Breakdown / Failure Scenario</span>
          </div>
          <p className="text-xs text-amber-800 leading-relaxed">
            Report an immediate vehicle breakdown (engine fault, reefer failure, tyre puncture). This notifies fleet maintenance and logs the event.
          </p>
          <Button
            variant="secondary"
            size="md"
            className="w-full border-rose-300 text-rose-700 bg-white hover:bg-rose-50"
            onClick={handleTriggerBreakdown}
          >
            <AlertTriangle size={14} className="mr-1.5 text-rose-600" />
            Trigger Breakdown & Request Assistance
          </Button>
        </div>
      )}

      {selected === "Outlet inaccessible" && (
        <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-3 space-y-2">
          <div className="text-xs font-bold text-blue-900">
            Current Stop: {currentStop?.outletId} ({currentStop?.name})
          </div>
          <p className="text-xs text-blue-800">
            If the current outlet is closed or the loading bay is blocked, report the stop failure directly to advance to the next outlet.
          </p>
          <Button
            variant="secondary"
            size="md"
            className="w-full border-blue-300 text-blue-700 bg-white hover:bg-blue-50"
            onClick={() =>
              push("failed-reason", {
                outletId: currentStop?.outletId ?? currentOutletId ?? "OUT042",
                seq: String(currentStop?.seq ?? 1),
              })
            }
          >
            Report Stop Unavailable & Next Outlet
          </Button>
        </div>
      )}

      <div className="space-y-2 pt-2">
        <Button
          variant="primary"
          size="lg"
          onClick={() =>
            push("chat", { recipient: "dispatch", topic: selected ?? "" })
          }
          disabled={!selected}
        >
          <AppIcon name="send" size={16} className="mr-2" /> Message dispatch
        </Button>
        <Button
          variant="secondary"
          size="md"
          onClick={() => push("call-overlay", { recipient: "dispatch" })}
        >
          <AppIcon name="phone" size={16} className="mr-2 text-green" /> Call dispatcher hotline
        </Button>
        <Button variant="ghost" size="md" onClick={back}>
          <AppIcon name="arrow-left" size={16} className="mr-2" /> Back to route
        </Button>
      </div>
    </div>
  );
}
