import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { ChoiceList } from "@/driver/components/ChoiceList";

export function IssueWizardScreen() {
  const { push } = useNavigator();
  const { addSyncRecord, connection } = useDriverState();
  const [selected, setSelected] = useState<string | null>(null);

  const handleContinue = () => {
    addSyncRecord({
      type: "delay",
      outletId: "VEHICLE",
      state: connection === "online" ? "synced" : "pending",
      hasPhoto: false,
      pinVerified: false,
    });
    push("active-trip");
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6">
      <div className="flex-1 max-w-sm mx-auto w-full">
        <h1 className="text-[28px] font-bold text-slate-900 mb-8">
          VEHICLE ISSUE / DELAY
        </h1>

        <h2 className="text-[15px] font-bold text-slate-900 mb-4">
          What is the situation?
        </h2>

        <ChoiceList
          options={[
            { id: "Traffic / Road closure", label: "Traffic / Road closure" },
            { id: "Vehicle breakdown", label: "Vehicle breakdown" },
            { id: "Other", label: "Other" }
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
          CONTINUE
        </button>
      </div>
    </div>
  );
}
