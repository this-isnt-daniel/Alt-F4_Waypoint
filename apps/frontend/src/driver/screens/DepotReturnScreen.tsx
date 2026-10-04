import { useNavigator } from "@/router/navigator";
import { DEPOT_RETURN } from "@/driver/data/driverContent";
import { CheckCircle2, Package, ShieldCheck } from "lucide-react";

export function DepotReturnScreen() {
  const { push } = useNavigator();

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-8 text-center">
      <div className="flex flex-col items-center mb-8">
        <div className="w-16 h-16 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center mb-4">
          <CheckCircle2 size={32} className="text-emerald-600" />
        </div>
        <h1 className="text-[24px] font-bold text-slate-900 mb-1">Depot return</h1>
        <p className="text-[15px] text-slate-500">{DEPOT_RETURN.location}</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-left mb-8">
        <div className="flex items-center gap-2 mb-3">
          <Package size={18} className="text-slate-600" />
          <h2 className="text-[16px] font-bold text-slate-900">Return handed over</h2>
        </div>
        
        <div className="text-[14px] text-slate-600 mb-4 pb-4 border-b border-slate-200">
          Officer <span className="font-semibold text-slate-900">{DEPOT_RETURN.officer}</span> confirmed at <span className="font-semibold text-slate-900">{DEPOT_RETURN.confirmedAt}</span>
        </div>

        <div className="space-y-2 mb-4 pb-4 border-b border-slate-200">
          {DEPOT_RETURN.items.map((item, i) => (
            <div key={i} className="flex justify-between items-center">
              <span className="text-[14px] font-medium text-slate-900">{item.name}</span>
              <span className="text-[14px] font-bold text-slate-500">×{item.quantity}</span>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-y-2 text-[13px] text-slate-500">
          <span><span className="text-slate-400">Crate:</span> {DEPOT_RETURN.returnCrate}</span>
          <span><span className="text-slate-400">Condition:</span> {DEPOT_RETURN.condition}</span>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-200 flex items-center gap-2 text-emerald-700 font-medium text-[13px]">
          <ShieldCheck size={16} />
          Officer PIN verified
        </div>
      </div>

      <div className="mt-auto">
        <button
          type="button"
          onClick={() => push("trip-complete")}
          className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
          style={{ backgroundColor: "var(--c-green)" }}
        >
          Continue to summary
        </button>
      </div>
    </div>
  );
}
