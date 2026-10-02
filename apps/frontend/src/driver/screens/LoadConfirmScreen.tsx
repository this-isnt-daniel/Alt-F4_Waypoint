import { useMemo } from "react";
import { Check, Flag, ArrowLeft } from "lucide-react";
import { Chip } from "@/driver/components/Chip";
import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { buildLoadRows, summariseLoad } from "@/driver/data/loadRows";
import { TRIP_1_STOPS, TRIP_2_STOPS } from "@/driver/data/driverContent";
import { formatUnits } from "@/lib/derive";
import { cn } from "@/lib/cn";

export function LoadConfirmScreen() {
  const { route, back } = useNavigator();
  const { activeTripId } = useDriverState();
  const isTrip2 = route.params.trip === "2" || activeTripId === 2;

  // We build the rows but don't need local state edits anymore 
  // since the Driver only inspects what the Loader did.
  const rows = useMemo(() => buildLoadRows(isTrip2 ? TRIP_2_STOPS : TRIP_1_STOPS), [isTrip2]);
  const sum = useMemo(() => summariseLoad(rows), [rows]);

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-slate-50">
      {/* Header */}
      <div className="bg-white px-5 py-4 border-b border-slate-200 sticky top-0 z-10 flex items-center gap-3">
        <button 
          onClick={back}
          className="p-1.5 -ml-1.5 rounded-full text-slate-500 hover:bg-slate-100"
        >
          <ArrowLeft size={22} />
        </button>
        <div>
          <h1 className="text-[18px] font-bold text-slate-900">Load Details</h1>
          <p className="text-[13px] text-slate-500">
            {isTrip2 ? "Trip 2 · Style · Kandy" : "Trip 1 · Fresh · Kandy"}
          </p>
        </div>
      </div>

      <div className="px-5 py-5 space-y-4">
        {/* Load Status Banner */}
        <div className={cn(
          "p-4 rounded-xl border",
          sum.flagged > 0 ? "bg-amber-50 border-amber-200" : "bg-emerald-50 border-emerald-200"
        )}>
          <div className="flex items-start gap-3">
            <div className={cn(
              "rounded-full p-1.5 shrink-0 text-white mt-0.5",
              sum.flagged > 0 ? "bg-amber-500" : "bg-emerald-500"
            )}>
              {sum.flagged > 0 ? <Flag size={16} strokeWidth={3} /> : <Check size={16} strokeWidth={3} />}
            </div>
            <div>
              <p className={cn("text-[15px] font-bold", sum.flagged > 0 ? "text-amber-900" : "text-emerald-900")}>
                {sum.flagged > 0 ? `${sum.flagged} load issue(s) flagged` : "Load verified"}
              </p>
              <p className={cn("text-[13px] mt-0.5", sum.flagged > 0 ? "text-amber-700" : "text-emerald-700")}>
                {sum.flagged > 0 
                  ? "Loader Kasun Kalhara flagged discrepancies during loading. See details below."
                  : "Loader Kasun Kalhara confirmed manifest matches van."}
              </p>
            </div>
          </div>
        </div>

        {/* Load Items List */}
        <div>
          <h2 className="text-[12px] font-bold uppercase tracking-wider text-slate-400 mb-3 ml-1">
            Manifest Groups
          </h2>
          <div className="space-y-3">
            {rows.map((r) => (
              <div 
                key={r.outletId} 
                className={cn(
                  "p-4 rounded-xl border bg-white",
                  r.state === "flagged" ? "border-amber-200 shadow-sm" : "border-slate-200"
                )}
              >
                <div className="flex justify-between items-start mb-1.5">
                  <span className="font-bold text-[15px] text-slate-900">{r.outletId}</span>
                  <span className={cn(
                    "text-[12px] font-bold px-2 py-0.5 rounded-full",
                    r.state === "flagged" ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"
                  )}>
                    {r.state === "flagged" ? "Flagged" : "Verified"}
                  </span>
                </div>
                
                <p className="text-[14px] text-slate-600 mb-2">
                  Manifest: <span className="font-semibold text-slate-900">{formatUnits(r.manifestUnits)}</span>
                </p>
                
                {r.state === "flagged" && (
                  <div className="mt-3 pt-3 border-t border-slate-100 space-y-2">
                    <p className="text-[13px] text-amber-800 font-medium">
                      Loaded: {formatUnits(r.deliverableUnits)} · Missing: {r.returnUnits}
                    </p>
                    {r.loaderNote && (
                      <p className="text-[13px] bg-amber-50 p-2.5 rounded-lg text-amber-900/80 italic">
                        "{r.loaderNote}"
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Summary Footer */}
        <div className="mt-2 bg-slate-100 p-4 rounded-xl border border-slate-200 text-[13px] text-slate-600 text-center">
          {rows.length} stops · {formatUnits(sum.manifest)} total · {sum.flagged} exceptions
        </div>
      </div>
    </div>
  );
}
