import { useNavigator } from "@/router/navigator";
import { ROUTE_UPDATE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";
import { Map, Phone, ArrowUp, ArrowDown } from "lucide-react";

export function RouteChangedScreen() {
  const { push } = useNavigator();
  const { acceptRouteUpdate } = useDriverState();
  
  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6 overflow-y-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
            <Map size={16} />
          </div>
          <div>
            <h1 className="text-[18px] font-bold text-slate-900 leading-tight">Route updated</h1>
            <p className="text-[12px] text-slate-500">Dispatcher · {ROUTE_UPDATE.dispatcherTime}</p>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <div className="text-[18px] font-bold text-slate-900 mb-2">{ROUTE_UPDATE.headline}</div>
        <p className="text-[14px] text-slate-600 leading-relaxed">{ROUTE_UPDATE.body}</p>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6">
        <div className="space-y-3 mb-4">
          {ROUTE_UPDATE.changes.map((c) => (
            <div key={c.outletId} className="flex items-start gap-3 text-[14px]">
              {c.type === 'moved_next' ? (
                <ArrowUp size={18} className="text-emerald-500 shrink-0 mt-0.5" />
              ) : (
                <ArrowDown size={18} className="text-slate-400 shrink-0 mt-0.5" />
              )}
              <span className="text-slate-900 font-medium">
                <span className="text-slate-500 font-normal">{c.type === 'moved_next' ? 'Moved next: ' : 'Moved later: '}</span>
                {c.outletId}
              </span>
            </div>
          ))}
        </div>
        <div className="pt-4 border-t border-slate-200">
          <div className="text-[13px] text-slate-500 flex justify-between items-center">
            <span>New ETA</span>
            <span className="font-bold text-slate-900">{ROUTE_UPDATE.newEta}</span>
          </div>
        </div>
      </div>

      <p className="text-[13px] text-slate-500 leading-relaxed mb-8">
        {ROUTE_UPDATE.reassurance}
      </p>

      <div className="mt-auto space-y-3 pb-safe">
        <button 
          onClick={() => { acceptRouteUpdate(); push("active-trip"); }}
          className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-xl hover:bg-emerald-700 transition-colors cursor-pointer"
          style={{ backgroundColor: "var(--c-green)" }}
        >
          {ROUTE_UPDATE.primary}
        </button>
        <button 
          onClick={() => push("call-overlay", { recipient: "dispatch" })}
          className="w-full py-4 rounded-xl border border-slate-200 text-[15px] font-semibold text-slate-700 cursor-pointer flex items-center justify-center gap-2 hover:bg-slate-50 transition-colors"
        >
          <Phone size={18} /> Call dispatcher
        </button>
      </div>
    </div>
  );
}
