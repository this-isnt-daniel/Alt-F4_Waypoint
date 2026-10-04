import { useNavigator } from "@/router/navigator";
import { Building2 } from "lucide-react";

export function ReturnDepotScreen() {
  const { push } = useNavigator();

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-6">
      <div className="flex-1 flex flex-col justify-center max-w-sm mx-auto w-full">
        <div className="flex items-center gap-2 mb-3 text-slate-400">
          <Building2 size={24} strokeWidth={2} />
        </div>

        <h1 className="text-[28px] font-bold text-slate-900 mb-1">
          RETURN TO DEPOT
        </h1>
        <p className="text-[16px] text-slate-500 mb-8">
          Kandy Hub
        </p>

        <p className="text-[18px] font-bold text-slate-900">
          Trip complete
        </p>
        <p className="text-[16px] text-slate-500">
          All stops recorded
        </p>
      </div>

      <div className="mt-auto pb-safe">
        <button
          type="button"
          onClick={() => push("trip-complete")}
          className="w-full bg-[#059669] text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
        >
          CONFIRM RETURN
        </button>
      </div>
    </div>
  );
}
