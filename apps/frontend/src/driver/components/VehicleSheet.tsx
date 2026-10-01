import { useDriverState } from "@/driver/state/useDriverState";
import { VEHICLE } from "@/driver/data/driverContent";
import { X, Truck, Thermometer, Fuel, CheckCircle, AlertTriangle } from "lucide-react";
import { useNavigator } from "@/router/navigator";

export function VehicleSheet({ 
  open, 
  onClose 
}: { 
  open: boolean; 
  onClose: () => void 
}) {
  const { push } = useNavigator();

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="absolute inset-0 z-[2000] bg-slate-900/20 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Floating Panel (Top Right) */}
      <div className="absolute top-16 right-4 z-[2010] w-64 bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-4 border-b border-slate-100">
          <div>
            <h2 className="text-[16px] font-bold text-slate-900 leading-tight">{VEHICLE.id}</h2>
            <p className="text-[13px] text-slate-500 mt-0.5">Refrigerated van</p>
          </div>
          <button 
            onClick={onClose}
            className="p-1 -mr-1 -mt-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full cursor-pointer transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Details */}
        <div className="p-4 space-y-4">
          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-0.5">
              <Truck size={14} />
              <span className="text-[11px] font-bold uppercase tracking-wider">Home depot</span>
            </div>
            <p className="text-[13px] font-semibold text-slate-900">{VEHICLE.depot}</p>
          </div>
          
          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-0.5">
              <Thermometer size={14} />
              <span className="text-[11px] font-bold uppercase tracking-wider">Temperature</span>
            </div>
            <p className="text-[13px] font-semibold text-[#059669]">3°C · In range</p>
          </div>

          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-0.5">
              <Fuel size={14} />
              <span className="text-[11px] font-bold uppercase tracking-wider">Fuel</span>
            </div>
            <p className="text-[13px] font-semibold text-slate-900">42 L remaining</p>
          </div>

          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-0.5">
              <CheckCircle size={14} />
              <span className="text-[11px] font-bold uppercase tracking-wider">Load</span>
            </div>
            <p className="text-[13px] font-semibold text-slate-900">Verified by Loader</p>
          </div>
        </div>

        {/* Action */}
        <div className="p-3 border-t border-slate-100 bg-slate-50">
          <button
            type="button"
            onClick={() => {
              onClose();
              push("contact-dispatch", { topic: "Vehicle issue" });
            }}
            className="w-full flex items-center justify-between py-2 px-3 bg-white border border-slate-200 rounded-lg text-[13px] font-bold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
          >
            <span className="flex items-center gap-2">
              <AlertTriangle size={14} className="text-rose-500" />
              Report vehicle issue
            </span>
            <span className="text-slate-400 font-normal">›</span>
          </button>
        </div>
      </div>
    </>
  );
}
