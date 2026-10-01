import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Check } from "lucide-react";

const REASONS = ["Damaged", "Missing at loading", "Wrong item", "Store refused", "Access issue", "Other"];

export function NotHandedOverReasonScreen() {
  const { push } = useNavigator();
  const [selected, setSelected] = useState<string | null>(null);
  const [note, setNote] = useState("");

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-slate-50 px-5 py-6">
      <div className="mb-6">
        <h1 className="text-[24px] font-bold text-slate-900 tracking-tight">Item not handed over</h1>
        <p className="text-[14px] text-slate-500 mt-1">Frozen produce · 2 items</p>
      </div>
      
      <p className="text-[13px] font-bold uppercase tracking-wider text-slate-400 mb-3">Why wasn't it handed over?</p>
      
      <div className="space-y-2 mb-6">
        {REASONS.map((reason) => (
          <button
            key={reason}
            type="button"
            onClick={() => setSelected(reason)}
            className={`w-full flex items-center justify-between p-4 rounded-xl border transition-colors cursor-pointer ${
              selected === reason 
                ? "border-emerald-500 bg-emerald-50" 
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <span className={`text-[15px] font-medium ${selected === reason ? "text-emerald-900" : "text-slate-700"}`}>
              {reason}
            </span>
            <span className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 ${
              selected === reason ? "border-emerald-500" : "border-slate-300"
            }`}>
              {selected === reason && (
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 block" />
              )}
            </span>
          </button>
        ))}
      </div>
      
      {selected === "Other" && (
        <div className="mb-6 animate-in fade-in slide-in-from-top-2 duration-200">
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Describe the issue..."
            className="w-full p-4 rounded-xl border border-slate-200 bg-white text-[15px] text-slate-900 resize-none h-24 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          />
        </div>
      )}
      
      <div className="mt-auto pt-4 pb-safe">
        <button 
          onClick={() => push("pod-photo")} 
          disabled={!selected}
          className="w-full bg-slate-900 text-white font-bold text-[16px] py-4 rounded-xl hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          Continue
        </button>
      </div>
    </div>
  );
}
