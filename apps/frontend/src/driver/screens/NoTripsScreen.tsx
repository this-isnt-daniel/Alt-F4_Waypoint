import { useNavigator } from "@/router/navigator";
import { PackageX, RefreshCw } from "lucide-react";

export function NoTripsScreen() {
  const { push } = useNavigator();

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6">
      <div className="flex flex-col items-center justify-center pt-12 mb-8 text-center">
        <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-5">
          <PackageX size={32} className="text-slate-400" />
        </div>
        <h1 className="text-[20px] font-bold text-slate-900 mb-2">No trips assigned</h1>
        <p className="text-[14px] text-slate-500 max-w-[280px] leading-relaxed mx-auto">
          There are no trips scheduled for you right now. Refresh to check again or contact dispatch if you're expecting a route.
        </p>
      </div>
      
      <div className="mt-auto space-y-3 pb-safe">
        <button 
          onClick={() => push("today-trips")}
          className="w-full bg-slate-900 text-white font-bold text-[16px] py-4 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer flex items-center justify-center gap-2"
        >
          <RefreshCw size={18} /> Refresh trips
        </button>
        <button 
          onClick={() => push("contact-dispatch")}
          className="w-full py-4 rounded-xl border border-slate-200 text-[15px] font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
        >
          Call dispatch
        </button>
      </div>
    </div>
  );
}
