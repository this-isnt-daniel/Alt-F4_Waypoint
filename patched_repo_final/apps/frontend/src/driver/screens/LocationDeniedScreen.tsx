import { useNavigator } from "@/router/navigator";
import { Navigation } from "lucide-react";

export function LocationDeniedScreen() {
  const { push } = useNavigator();

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6">
      <div className="flex flex-col items-center justify-center pt-8 mb-6 text-center">
        <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mb-4">
          <Navigation size={28} className="text-amber-500" />
        </div>
        <h1 className="text-[20px] font-bold text-slate-900 mb-2">Location access needed</h1>
        <p className="text-[14px] text-slate-500 max-w-[260px] leading-relaxed">
          Location keeps ETA, arrival confirmation, and route changes accurate while a trip is active.
        </p>
      </div>
      
      <div className="bg-slate-50 border border-slate-100 rounded-xl p-5 mb-8">
        <div className="space-y-3">
          <div className="flex gap-2.5 text-[14px] text-slate-700">
            <span className="text-slate-400">•</span>
            <span>Route and ETA calculation</span>
          </div>
          <div className="flex gap-2.5 text-[14px] text-slate-700">
            <span className="text-slate-400">•</span>
            <span>Arrival confirmation</span>
          </div>
          <div className="flex gap-2.5 text-[14px] text-slate-700">
            <span className="text-slate-400">•</span>
            <span>Tracking automatically stops after trip</span>
          </div>
        </div>
      </div>

      <div className="mt-auto space-y-3 pb-safe">
        <button 
          onClick={() => push("active-trip")}
          className="w-full bg-slate-900 text-white font-bold text-[16px] py-4 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
        >
          Turn on precise location
        </button>
        <button 
          onClick={() => push("active-trip")}
          className="w-full py-4 rounded-xl border border-slate-200 text-[15px] font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
        >
          Continue offline
        </button>
      </div>
    </div>
  );
}
