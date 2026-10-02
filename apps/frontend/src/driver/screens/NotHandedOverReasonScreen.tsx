import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { AppIcon } from "@/driver/components/AppIcon";

const REASONS = ["Damaged", "Missing at loading", "Wrong item", "Store refused", "Access issue", "Other"];

export function NotHandedOverReasonScreen() {
  const { push } = useNavigator();
  const [selected, setSelected] = useState<string | null>(null);
  const [note, setNote] = useState("");

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Item not handed over</h1>
        <p className="text-[13px] text-slate-500">Frozen produce · 2 items</p>
      </div>
      <p className="text-[13px] text-slate-500">Why wasn't it handed over?</p>
      <div className="space-y-2">
        {REASONS.map((reason) => (
          <button
            key={reason}
            type="button"
            onClick={() => setSelected(reason)}
            className={`w-full flex items-center justify-between p-3 rounded-xl border transition-colors ${
              selected === reason ? "border-green/30 bg-green-fill" : "border-slate-200 bg-white"
            }`}
          >
            <span className="text-[13px] font-medium text-slate-900">{reason}</span>
            {selected === reason && <AppIcon name="check" size={18} className="text-green" />}
          </button>
        ))}
      </div>
      {selected === "Other" && (
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Describe the issue..."
          className="w-full p-3 rounded-lg border border-slate-200 bg-white text-[13px] text-slate-900 resize-none h-20"
        />
      )}
      <Button variant="primary" size="lg" onClick={() => push("pod-photo")} disabled={!selected}>
        Continue
      </Button>
    </div>
  );
}
