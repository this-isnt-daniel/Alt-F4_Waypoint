import { useNavigator } from "@/router/navigator";
import { OUT058_PARTIAL } from "@/driver/data/driverContent";
import { AlertCircle } from "lucide-react";

export function PartialSummaryScreen() {
  const { push } = useNavigator();
  const returnCount = OUT058_PARTIAL.manifest - OUT058_PARTIAL.handedOver;

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-6">
      <div className="flex items-center gap-2 mb-2 text-amber-500">
        <AlertCircle size={24} strokeWidth={2.5} />
      </div>
      
      <h1 className="text-[24px] font-bold text-slate-900 mb-1">Partial delivery</h1>
      <p className="text-[15px] text-slate-500 mb-6">
        {OUT058_PARTIAL.outletId} · {OUT058_PARTIAL.outletName}
      </p>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
        <p className="text-[16px] font-bold text-amber-900 mb-1">
          {OUT058_PARTIAL.handedOver} of {OUT058_PARTIAL.manifest} handed over
        </p>
        <p className="text-[14px] text-amber-700">
          {returnCount} frozen item{returnCount !== 1 ? 's' : ''} returning to Kandy hub.
        </p>
      </div>

      <h2 className="text-[12px] font-bold uppercase tracking-wider text-slate-400 mb-3 ml-1">
        Returning items
      </h2>
      <div className="space-y-3 mb-8">
        {OUT058_PARTIAL.returnItems.map((item, i) => (
          <div key={i} className="flex flex-col p-4 rounded-xl border border-slate-200 bg-slate-50">
            <div className="flex justify-between items-start mb-2">
              <span className="text-[15px] font-bold text-slate-900">{item.name}</span>
              <span className="text-[15px] font-bold text-slate-500">×{item.quantity}</span>
            </div>
            <div className="flex gap-2 text-[13px]">
              <span className="px-2 py-1 bg-amber-100 text-amber-800 rounded-md font-medium">
                {item.reason}
              </span>
              <span className="px-2 py-1 bg-slate-200 text-slate-700 rounded-md font-medium">
                Crate {item.returnCrate}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-auto">
        <button
          type="button"
          onClick={() => push("return-depot")}
          className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
          style={{ backgroundColor: "var(--c-green)" }}
        >
          Continue
        </button>
      </div>
    </div>
  );
}
