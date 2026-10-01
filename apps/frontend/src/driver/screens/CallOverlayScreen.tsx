import { useNavigator } from "@/router/navigator";

export function CallOverlayScreen() {
  const { route, back } = useNavigator();
  const isDispatch = route.params.recipient === "dispatch";
  const outletId = route.params.outletId ?? "OUT047";

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6">
      <div className="flex-1 flex flex-col justify-center max-w-sm mx-auto w-full">
        <h1 className="text-[24px] font-bold text-slate-900 mb-2">
          Call {isDispatch ? "Central Dispatch" : "Joseph Vijay"}?
        </h1>
        
        <p className="text-[15px] text-slate-500 mb-6">
          {isDispatch ? "Stephan Anthony · Kandy Hub" : `Store manager · ${outletId}`}
        </p>
        
        <div className="text-[18px] font-medium font-mono text-slate-900 bg-slate-50 px-4 py-3 rounded-lg border border-slate-200 mb-8 w-max">
          {isDispatch ? "+94 81 ••• ••10" : "+94 77 ••• ••42"}
        </div>
        
        <div className="flex gap-3 mt-4">
          <button
            type="button"
            onClick={back}
            className="flex-1 py-3.5 rounded-lg bg-slate-100 text-slate-700 font-semibold text-[15px] cursor-pointer"
          >
            CANCEL
          </button>
          <button
            type="button"
            onClick={back}
            className="flex-1 py-3.5 rounded-lg bg-[#059669] text-white font-semibold text-[15px] cursor-pointer"
          >
            CALL
          </button>
        </div>
      </div>
    </div>
  );
}
