import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function MarkArrivedScreen() {
  const { route, push } = useNavigator();
  const { addSyncRecord, connection } = useDriverState();
  const seqParam = Number(route.params.seq ?? "2");
  const stop = TRIP_1_STOPS.find((s) => s.seq === seqParam) ?? TRIP_1_STOPS[1]!;

  const handleConfirm = () => {
    addSyncRecord({
      type: "arrival",
      outletId: stop.outletId,
      state: connection === "online" ? "synced" : "pending",
      hasPhoto: false,
      pinVerified: false,
    });
    push("checklist", { outletId: stop.outletId });
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-green tracking-wider uppercase">
          Arrival Confirmation
        </span>
        <h1 className="text-xl font-extrabold text-ink">Confirm arrival</h1>
        <p className="text-xs font-semibold text-ink-muted">
          {stop.outletId} · {stop.name}
        </p>
      </div>

      <Card variant="surface" className="space-y-3">
        <div className="p-3 bg-raised rounded-btn text-xs text-ink-muted leading-relaxed">
          <span className="font-bold text-ink block mb-0.5">Safety Rule:</span>
          You’re within the delivery window. Confirm only when safely parked at the outlet.
        </div>

        <KeyValueRow label="Delivery Window" value={stop.window} />
        <KeyValueRow label="Arrival Time" value="06:18 · on time" emphasis="strong" />
        <KeyValueRow label="Location" value={`${stop.dock}${stop.dockDetail ? ` · ${stop.dockDetail}` : ""}`} />
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={handleConfirm}>
          Confirm arrival
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("active-trip")}>
          Back to map
        </Button>
      </div>
    </div>
  );
}
