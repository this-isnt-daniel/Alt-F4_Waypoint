import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { AppIcon } from "@/driver/components/AppIcon";

const REASONS = ["Outlet closed", "Mall bay unavailable", "Store refused delivery", "Unsafe access", "Receiver unavailable", "Other"];

export function FailedReasonScreen() {
  const { push } = useNavigator();
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Failed delivery</h1>
        <p className="text-[13px] text-slate-500">OUT052 · Waypoint Fresh Kandy City Centre</p>
      </div>
      <p className="text-[13px] text-slate-500">Why couldn't you deliver?</p>
      <div className="space-y-2">
        {REASONS.map((reason) => (
          <button key={reason} type="button" onClick={() => setSelected(reason)}
            className={`w-full flex items-center justify-between p-3 rounded-xl border transition-colors ${
              selected === reason ? "border-green/30 bg-green-fill" : "border-slate-200 bg-white"
            }`}>
            <span className="text-[13px] font-medium text-slate-900">{reason}</span>
            {selected === reason && <AppIcon name="check" size={18} className="text-green" />}
          </button>
        ))}
      </div>
      <Button variant="primary" size="lg" onClick={() => push("outlet-closed")} disabled={!selected}>
        Continue
      </Button>
    </div>
  );
}
