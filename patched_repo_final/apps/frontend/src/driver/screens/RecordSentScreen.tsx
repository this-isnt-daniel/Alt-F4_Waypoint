import { useNavigator } from "@/router/navigator";
import { SendHorizontal } from "lucide-react";
import { RECORD_SENT } from "@/driver/data/driverContent";

export function RecordSentScreen() {
  const { push } = useNavigator();

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6">
      <div className="flex flex-col items-center justify-center pt-8 mb-8 text-center">
        <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mb-4">
          <SendHorizontal size={28} className="text-emerald-600 ml-1" />
        </div>
        <h1 className="text-[20px] font-bold text-slate-900 mb-1">{RECORD_SENT.title}</h1>
        <p className="text-[14px] text-slate-500">{RECORD_SENT.subtitle}</p>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 mb-8 text-center">
        <p className="text-[14px] text-slate-700 leading-relaxed mb-4">
          {RECORD_SENT.body}
        </p>
        <p className="text-[13px] font-medium text-slate-500">
          {RECORD_SENT.continueLine}
        </p>
      </div>

      <div className="mt-auto space-y-3 pb-safe">
        <button 
          onClick={() => push("active-trip")}
          className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-xl hover:bg-emerald-700 transition-colors cursor-pointer"
          style={{ backgroundColor: "var(--c-green)" }}
        >
          {RECORD_SENT.primary}
        </button>
        <button 
          onClick={() => push("sync-centre")}
          className="w-full py-4 text-[14px] font-semibold text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
        >
          {RECORD_SENT.secondary}
        </button>
      </div>
    </div>
  );
}
