import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { SYNC_REVIEW } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function SyncReviewScreen() {
  const { push } = useNavigator();
  const { forwardSyncReview } = useDriverState();
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Sync needs review</h1>
        <p className="text-[13px] text-slate-500">{SYNC_REVIEW.outletId} · evidence protected</p>
      </div>
      <div className="px-3 py-2 rounded-lg bg-amber-50 border border-amber-100 text-[13px] text-amber-700 font-medium">
        <AppIcon name="shield" size={16} className="inline mr-1" />
        {SYNC_REVIEW.banner}
      </div>
      <Card variant="surface" className="space-y-1">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{SYNC_REVIEW.yourRecord.label}</div>
        <div className="text-[11px] text-slate-500">{SYNC_REVIEW.yourRecord.sublabel}</div>
        <div className="text-[13px] text-slate-900 pt-1">Arrived {SYNC_REVIEW.yourRecord.arrived}</div>
        <div className="text-[13px] text-slate-900">{SYNC_REVIEW.yourRecord.items}</div>
        <div className="text-[13px] text-slate-900">{SYNC_REVIEW.yourRecord.proof}</div>
      </Card>
      <Card variant="raised" className="space-y-1">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{SYNC_REVIEW.dispatcherView.label}</div>
        <div className="text-[11px] text-slate-500">{SYNC_REVIEW.dispatcherView.sublabel}</div>
        <div className="text-[13px] text-slate-900 pt-1">{SYNC_REVIEW.dispatcherView.assignment}</div>
        <div className="text-[13px] text-slate-900">{SYNC_REVIEW.dispatcherView.storeReport}</div>
      </Card>
      <p className="text-[13px] text-slate-500">{SYNC_REVIEW.body}</p>
      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => { forwardSyncReview(); push("record-sent"); }}>
          {SYNC_REVIEW.primary}
        </Button>
        <div className="flex gap-2">
          <Button variant="secondary" size="md" fullWidth={false} className="flex-1" onClick={() => push("pod-photo")}>
            {SYNC_REVIEW.secondaryAdd}
          </Button>
          <Button variant="secondary" size="md" fullWidth={false} className="flex-1" onClick={() => push("call-overlay")}>
            {SYNC_REVIEW.secondaryCall}
          </Button>
        </div>
        <button type="button" onClick={() => push("active-trip")} className="w-full text-center text-[12px] text-slate-400 py-2 hover:text-slate-600">
          {SYNC_REVIEW.quietEscape}
        </button>
      </div>
    </div>
  );
}
