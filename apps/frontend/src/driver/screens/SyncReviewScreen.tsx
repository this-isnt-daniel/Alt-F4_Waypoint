import { useNavigator } from "@/router/navigator";
import { SYNC_REVIEW } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";
import { Shield, Phone, Camera } from "lucide-react";

export function SyncReviewScreen() {
  const { push } = useNavigator();
  const { forwardSyncReview } = useDriverState();
  
  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white px-5 py-6 overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-[24px] font-bold text-slate-900 tracking-tight">Sync needs review</h1>
        <p className="text-[14px] text-slate-500 mt-1">{SYNC_REVIEW.outletId} · evidence protected</p>
      </div>
      
      <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-amber-50 border border-amber-100 text-[13px] text-amber-800 font-medium mb-6">
        <Shield size={18} className="shrink-0 mt-0.5 text-amber-500" />
        <p className="leading-relaxed">{SYNC_REVIEW.banner}</p>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 mb-4">
        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">{SYNC_REVIEW.yourRecord.label}</div>
        <div className="text-[12px] text-slate-500 mb-3">{SYNC_REVIEW.yourRecord.sublabel}</div>
        
        <div className="space-y-1.5 text-[14px] text-slate-900 font-medium">
          <div>Arrived {SYNC_REVIEW.yourRecord.arrived}</div>
          <div>{SYNC_REVIEW.yourRecord.items}</div>
          <div>{SYNC_REVIEW.yourRecord.proof}</div>
        </div>
      </div>
      
      <div className="bg-white border-2 border-amber-100 rounded-xl p-5 mb-6 shadow-sm">
        <div className="text-[11px] font-bold text-amber-500 uppercase tracking-wider mb-1">{SYNC_REVIEW.dispatcherView.label}</div>
        <div className="text-[12px] text-slate-500 mb-3">{SYNC_REVIEW.dispatcherView.sublabel}</div>
        
        <div className="space-y-1.5 text-[14px] text-slate-900 font-medium">
          <div>{SYNC_REVIEW.dispatcherView.assignment}</div>
          <div>{SYNC_REVIEW.dispatcherView.storeReport}</div>
        </div>
      </div>
      
      <p className="text-[14px] text-slate-600 leading-relaxed mb-8">
        {SYNC_REVIEW.body}
      </p>

      <div className="mt-auto space-y-3 pb-safe">
        <button 
          onClick={() => { forwardSyncReview(); push("record-sent"); }}
          className="w-full bg-slate-900 text-white font-bold text-[16px] py-4 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
        >
          {SYNC_REVIEW.primary}
        </button>
        
        <div className="flex gap-3">
          <button 
            onClick={() => push("pod-photo")}
            className="flex-1 py-3.5 rounded-xl border border-slate-200 text-[14px] font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer flex items-center justify-center gap-1.5"
          >
            <Camera size={16} /> Add photo
          </button>
          <button 
            onClick={() => push("call-overlay")}
            className="flex-1 py-3.5 rounded-xl border border-slate-200 text-[14px] font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer flex items-center justify-center gap-1.5"
          >
            <Phone size={16} /> Call
          </button>
        </div>
        
        <button 
          onClick={() => push("active-trip")}
          className="w-full text-center text-[13px] font-semibold text-slate-400 py-3 hover:text-slate-600 cursor-pointer transition-colors"
        >
          {SYNC_REVIEW.quietEscape}
        </button>
      </div>
    </div>
  );
}
