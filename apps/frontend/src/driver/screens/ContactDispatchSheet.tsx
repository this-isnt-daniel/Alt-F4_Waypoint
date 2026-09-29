import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { AppIcon } from "@/driver/components/AppIcon";
import { VEHICLE, CONTACT_DISPATCH_PRESETS } from "@/driver/data/driverContent";

export function ContactDispatchSheet() {
  const { push, back } = useNavigator();
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Contact dispatch</h1>
        <p className="text-[13px] text-slate-500">{VEHICLE.id} · {VEHICLE.depot}</p>
      </div>
      <div className="text-[12px] font-semibold text-slate-500 uppercase tracking-wider">What do you need?</div>
      <div className="space-y-2">
        {CONTACT_DISPATCH_PRESETS.map((preset) => (
          <button key={preset} type="button" onClick={() => setSelected(preset)}
            className={`w-full flex items-center justify-between p-3 rounded-xl border transition-colors ${
              selected === preset ? "border-green/30 bg-green-fill" : "border-slate-200 bg-white"
            }`}>
            <span className="text-[13px] font-medium text-slate-900">{preset}</span>
            {selected === preset && <AppIcon name="check" size={18} className="text-green" />}
          </button>
        ))}
      </div>
      <div className="space-y-2 pt-2">
        <Button
          variant="primary"
          size="lg"
          onClick={() =>
            push("chat", { recipient: "dispatch", topic: selected ?? "" })
          }
          disabled={!selected}
        >
          <AppIcon name="send" size={16} className="mr-2" /> Send to dispatch
        </Button>
        <Button
          variant="secondary"
          size="md"
          onClick={() => push("call-overlay", { recipient: "dispatch" })}
        >
          <AppIcon name="phone" size={16} className="mr-2" /> Call dispatcher
        </Button>
        <Button variant="ghost" size="md" onClick={back}>
          <AppIcon name="arrow-left" size={16} className="mr-2" /> Back
        </Button>
      </div>
    </div>
  );
}
