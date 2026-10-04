import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { ChoiceList } from "@/driver/components/ChoiceList";

export function OutletClosedScreen() {
  const { push, route } = useNavigator();
  const { completeStop, currentStopIndex, currentTripSequence, currentTripStops } = useDriverState();
  const [selected, setSelected] = useState<string | null>(null);

  const outletId = route.params.outletId ?? currentTripSequence[currentStopIndex] ?? "OUT042";

  const handleContinue = () => {
    completeStop(outletId, "failed");
    push("active-trip");
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6">
      <div className="flex-1 max-w-sm mx-auto w-full">
        <h1 className="text-[28px] font-bold text-slate-900 mb-1">
          OUTLET INACCESSIBLE
        </h1>
        <p className="text-[16px] text-slate-500 mb-8">
          {outletId}
        </p>

        <h2 className="text-[15px] font-bold text-slate-900 mb-4">
          What is the issue?
        </h2>

        <ChoiceList
          options={[
            { id: "Store closed", label: "Store closed" },
            { id: "Road blocked", label: "Road blocked" },
            { id: "Manager absent", label: "Manager absent" }
          ]}
          selectedId={selected}
          onSelect={(id) => setSelected(id)}
        />
      </div>

      <div className="mt-auto pb-safe">
        <button
          type="button"
          disabled={!selected}
          onClick={handleContinue}
          className="w-full bg-[#059669] text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        >
          REPORT
        </button>
      </div>
    </div>
  );
}
