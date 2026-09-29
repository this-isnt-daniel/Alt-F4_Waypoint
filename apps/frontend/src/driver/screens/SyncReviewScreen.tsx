import { useNavigator } from "@/router/navigator";
import { Banner } from "@/driver/components/Banner";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { SYNC_REVIEW } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function SyncReviewScreen() {
  const { push } = useNavigator();
  const { forwardSyncReview } = useDriverState();

  const handleSendForReview = () => {
    forwardSyncReview();
    push("record-sent");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="flex items-center justify-between">
        <span className="text-2xs font-extrabold text-warning tracking-wider uppercase">
          Conflict Resolution
        </span>
        <Chip kind="sync" tone="inReview" label="IN REVIEW" />
      </div>

      <Banner
        tone="warning"
        title="NON-DESTRUCTIVE"
        body={SYNC_REVIEW.banner}
      />

      <div className="space-y-1">
        <h1 className="text-xl font-extrabold text-ink">Sync needs review</h1>
        <p className="text-xs font-semibold text-ink-muted">
          {SYNC_REVIEW.outletId} · {SYNC_REVIEW.outletName}
        </p>
      </div>

      <p className="text-xs text-ink leading-relaxed">
        {SYNC_REVIEW.body}
      </p>

      {/* Driver Record Card */}
      <Card variant="surface" className="space-y-2 border-green/40 bg-green-fill/30">
        <div className="flex justify-between items-center text-xs pb-1 border-b border-green/20">
          <span className="font-extrabold text-green-ink">{SYNC_REVIEW.yourRecord.label}</span>
          <span className="text-2xs font-bold text-green">{SYNC_REVIEW.yourRecord.sublabel}</span>
        </div>
        <KeyValueRow label="Arrival" value={SYNC_REVIEW.yourRecord.arrived} />
        <KeyValueRow label="Handover" value={SYNC_REVIEW.yourRecord.items} />
        <KeyValueRow label="Evidence" value={SYNC_REVIEW.yourRecord.proof} emphasis="strong" />
      </Card>

      {/* Dispatcher / Store View Card */}
      <Card variant="raised" className="space-y-2">
        <div className="flex justify-between items-center text-xs pb-1 border-b border-line">
          <span className="font-extrabold text-ink">{SYNC_REVIEW.dispatcherView.label}</span>
          <span className="text-2xs text-ink-muted">{SYNC_REVIEW.dispatcherView.sublabel}</span>
        </div>
        <KeyValueRow label="System assignment" value={SYNC_REVIEW.dispatcherView.assignment} />
        <KeyValueRow label="Store feedback" value={SYNC_REVIEW.dispatcherView.storeReport} />
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={handleSendForReview}>
          {SYNC_REVIEW.primary}
        </Button>
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="secondary"
            size="md"
            onClick={() => push("issue-wizard", { outletId: SYNC_REVIEW.outletId })}
          >
            {SYNC_REVIEW.secondaryAdd}
          </Button>
          <Button
            variant="secondary"
            size="md"
            onClick={() => push("call-overlay", { role: "dispatcher" })}
          >
            {SYNC_REVIEW.secondaryCall}
          </Button>
        </div>

        {/* Quiet Escape Link */}
        <div className="text-center pt-2">
          <button
            type="button"
            onClick={() => push("failed-reason")}
            className="text-xs text-ink-muted hover:text-ink underline"
          >
            {SYNC_REVIEW.quietEscape}
          </button>
        </div>
      </div>
    </div>
  );
}
