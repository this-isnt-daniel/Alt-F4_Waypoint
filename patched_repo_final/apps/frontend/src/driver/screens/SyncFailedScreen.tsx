import { useNavigator } from "@/router/navigator";
import { AlertCircle } from "lucide-react";

export function SyncFailedScreen() {
  const { push } = useNavigator();

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6">
      <div className="flex-1 flex flex-col justify-center max-w-sm mx-auto w-full">
        <div className="flex items-center gap-2 mb-3 text-rose-500">
          <AlertCircle size={28} />
        </div>
        
        <h1 className="text-[28px] font-bold text-slate-900 mb-6">
          SYNC FAILED
        </h1>
        
        <div className="space-y-4">
          <p className="text-[16px] text-slate-900 font-medium">
            Records are safe on this phone.
          </p>
          <p className="text-[16px] text-slate-500">
            Waypoint couldn't reach the server.
          </p>
          <p className="text-[16px] text-slate-500">
            4 records waiting to sync.
          </p>
        </div>
      </div>

      <div className="mt-auto space-y-3 pb-safe">
        <button 
          onClick={() => push("sync-centre")}
          className="w-full bg-[#059669] text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
        >
          RETRY SYNC
        </button>
        <button 
          onClick={() => push("active-trip")}
          className="w-full py-4 rounded-lg bg-slate-100 text-[15px] font-bold text-slate-700 cursor-pointer"
        >
          CONTINUE OFFLINE
        </button>
      </div>
    </div>
  );
}
