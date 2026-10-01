import { useNavigator } from "@/router/navigator";

export function DaySummaryScreen() {
  const { push } = useNavigator();
  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6 overflow-y-auto">
      <div className="flex-1 flex flex-col justify-center max-w-sm mx-auto w-full">
        <h1 className="text-[28px] font-bold text-slate-900 mb-1">
          DAY COMPLETE
        </h1>
        <p className="text-[16px] text-slate-500 mb-8">
          Daniru · 26 September
        </p>

        <div className="space-y-4 mb-8">
          <div className="flex justify-between items-baseline border-b border-slate-100 pb-3">
            <span className="text-[15px] font-medium text-slate-600">Stops visited</span>
            <span className="text-[18px] font-bold text-slate-900">21</span>
          </div>
          
          <div className="flex justify-between items-baseline border-b border-slate-100 pb-3">
            <span className="text-[15px] font-medium text-slate-600">Deliveries</span>
            <span className="text-[18px] font-bold text-slate-900">20</span>
          </div>
          
          <div className="flex justify-between items-baseline border-b border-slate-100 pb-3">
            <span className="text-[15px] font-medium text-slate-600">Returns</span>
            <span className="text-[18px] font-bold text-slate-900">1</span>
          </div>

          <div className="flex justify-between items-baseline pb-3">
            <span className="text-[15px] font-medium text-slate-600">Data synced</span>
            <span className="text-[18px] font-bold text-emerald-600">✓</span>
          </div>
        </div>
      </div>

      <div className="mt-auto pb-safe">
        <button 
          onClick={() => push("signin")}
          className="w-full bg-[#059669] text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
        >
          SIGN OUT
        </button>
      </div>
    </div>
  );
}
