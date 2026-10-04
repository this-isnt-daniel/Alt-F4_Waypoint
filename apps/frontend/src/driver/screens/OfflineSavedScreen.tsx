import { useNavigator } from "@/router/navigator";
import { CloudOff } from "lucide-react";

export function OfflineSavedScreen() {
  const { push } = useNavigator();

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6">
      <div className="flex-1 flex flex-col justify-center max-w-sm mx-auto w-full">
        <div className="flex items-center gap-2 mb-3 text-amber-500">
          <CloudOff size={28} />
        </div>

        <h1 className="text-[28px] font-bold text-slate-900 mb-1">
          OFFLINE
        </h1>
        <p className="text-[16px] text-slate-500 mb-8">
          Delivery saved
        </p>

        <p className="text-[16px] text-slate-900 font-medium mb-4">
          Actions will be saved on this device and synced when connection returns.
        </p>
      </div>

      <div className="mt-auto space-y-3 pb-safe">
        <button 
          onClick={() => push("active-trip")}
          className="w-full bg-[#059669] text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
        >
          CONTINUE TO NEXT STOP
        </button>
        <button 
          onClick={() => push("sync-centre")}
          className="w-full py-4 rounded-lg bg-slate-100 text-[15px] font-bold text-slate-700 cursor-pointer"
        >
          OPEN SYNC CENTRE
        </button>
      </div>
    </div>
  );
}
