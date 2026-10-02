import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { VEHICLE, CONTACT_DISPATCH_PRESETS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";
import { AlertTriangle, Phone, MessageSquare, ArrowLeft } from "lucide-react";
import { ChoiceList } from "@/driver/components/ChoiceList";

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
    route.params.topic ?? null,
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
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6">
      <div className="flex-1 flex flex-col max-w-sm mx-auto w-full">
        <div className="flex items-center gap-3 mb-6">
          <button type="button" onClick={back} className="p-1.5 -ml-1.5 rounded-full text-slate-500 hover:bg-slate-100 transition-colors">
            <ArrowLeft size={22} />
          </button>
          <div>
            <h1 className="text-[20px] font-bold text-slate-900 leading-tight">Contact Dispatch</h1>
            <p className="text-[13px] text-slate-500">
              {VEHICLE.id} · {VEHICLE.depot}
            </p>
          </div>
        </div>

        {vehicleBreakdown && (
          <div className="flex items-start gap-2.5 mb-6 px-4 py-3 bg-rose-50 border border-rose-200 rounded-lg">
            <AlertTriangle size={16} className="text-rose-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-[13px] font-bold text-rose-800">Breakdown alert active</p>
              <p className="text-[12px] text-rose-700 mt-0.5">
                Dispatch has logged {VEHICLE.id}. Roadside assistance is coordinating.
              </p>
            </div>
          </div>
        )}

        <h2 className="text-[14px] font-bold text-slate-900 mb-4">
          What do you need?
        </h2>

        <div className="mb-6">
          <ChoiceList
            options={CONTACT_DISPATCH_PRESETS.map((preset) => ({
              id: preset,
              label: preset
            }))}
            selectedId={selected}
            onSelect={(id) => setSelected(id)}
            allowOtherNote={false}
          />
        </div>

        {selected === "Outlet inaccessible" && currentStop && (
          <div className="mb-4 px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg">
            <p className="text-[13px] text-slate-500 mb-2">
              Current stop: <strong className="text-slate-800">{currentStop.outletId} · {currentStop.name}</strong>
            </p>
            <button
              type="button"
              onClick={() =>
                push("failed-reason", {
                  outletId: currentStop.outletId,
                  seq: String(currentStop.seq),
                })
              }
              className="text-[13px] font-bold text-[#059669] cursor-pointer"
            >
              Report stop failure →
            </button>
          </div>
        )}

        {selected === "Vehicle issue" && (
          <div className="mb-4 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-[13px] text-amber-800 mb-3">
              Report immediate breakdown — engine, reefer, or tyre. Dispatch and fleet maintenance will be notified.
            </p>
            <button
              type="button"
              onClick={handleTriggerBreakdown}
              className="text-[13px] font-bold text-rose-600 cursor-pointer"
            >
              Trigger breakdown &amp; request assistance →
            </button>
          </div>
        )}
      </div>

      <div className="mt-auto space-y-3 pb-safe">
        <button
          type="button"
          disabled={!selected}
          onClick={() => push("chat", { recipient: "dispatch", topic: selected ?? "" })}
          className="w-full bg-[#059669] text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <MessageSquare size={18} />
          MESSAGE DISPATCH
        </button>

        <button
          type="button"
          onClick={() => push("call-overlay", { recipient: "dispatch" })}
          className="w-full py-4 rounded-lg bg-slate-100 text-[15px] font-bold text-slate-700 cursor-pointer flex items-center justify-center gap-2"
        >
          <Phone size={17} />
          CALL DISPATCHER
        </button>
      </div>
    </div>
  );
}
