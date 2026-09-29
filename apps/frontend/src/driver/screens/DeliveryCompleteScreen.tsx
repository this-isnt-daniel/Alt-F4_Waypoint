import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function DeliveryCompleteScreen() {
  const { route, push } = useNavigator();
  const { setCurrentStopSeq, connection } = useDriverState();
  const outletId = route.params.outletId ?? "OUT047";
  const stop = TRIP_1_STOPS.find((s) => s.outletId === outletId) ?? TRIP_1_STOPS[1]!;

  const handleNext = () => {
    if (stop.seq === 8) {
      push("trip-complete");
    } else {
      setCurrentStopSeq(stop.seq + 1);
      push("active-trip");
    }
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="text-center space-y-1 pt-4">
        <div className="grid h-16 w-16 place-items-center rounded-circle bg-success-fill text-success text-3xl mx-auto mb-2">
          ✓
        </div>
        <span className="text-2xs font-extrabold text-success tracking-wider uppercase">
          Handover Confirmed
        </span>
        <h1 className="text-xl font-extrabold text-ink">Delivery complete</h1>
        <p className="text-xs font-semibold text-ink-muted">
          {stop.outletId} · 06:34
        </p>
      </div>

      <Card variant="surface" className="space-y-3">
        <p className="text-xs text-ink leading-relaxed">
          All {stop.units} items were received by {stop.manager}.
        </p>

        <KeyValueRow label="Arrival" value="06:18 · on time" />
        <KeyValueRow label="Photo Evidence" value="Attached" />
        <KeyValueRow label="Manager PIN" value="Confirmed" />
        <KeyValueRow label="Finished" value="06:34" emphasis="strong" />

        <div className="pt-1 flex items-center justify-between">
          <span className="text-2xs text-ink-muted">Sync state:</span>
          <Chip
            kind="sync"
            tone={connection === "online" ? "success" : "pending"}
            label={connection === "online" ? "Uploading photo securely" : "Saved offline"}
          />
        </div>
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={handleNext}>
          {stop.seq === 8 ? "Finish trip" : "Continue to next stop"}
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("sync-centre")}>
          View record in queue
        </Button>
      </div>
    </div>
  );
}
