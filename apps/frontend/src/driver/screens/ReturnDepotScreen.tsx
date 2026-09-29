import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { ListRow } from "@/driver/components/ListRow";
import { RETURN_DEPOT, VEHICLE } from "@/driver/data/driverContent";

export function ReturnDepotScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-offline tracking-wider uppercase">
          Depot Return Custody
        </span>
        <h1 className="text-xl font-extrabold text-ink">Return to depot</h1>
        <p className="text-xs font-semibold text-ink-muted">
          2 items · {VEHICLE.depot}
        </p>
      </div>

      <Card variant="surface" className="space-y-3">
        <p className="text-xs text-ink leading-relaxed">
          Return items are secured. Keep damaged frozen items in the marked return crate until depot handover.
        </p>

        <ListRow
          title="Frozen produce ×2"
          subtitle={`Source: ${RETURN_DEPOT.sourceOutletId} · Reason: ${RETURN_DEPOT.reason}`}
          status="returned"
          statusLabel="Return pending"
        />

        <KeyValueRow label="Storage" value={`Return crate ${RETURN_DEPOT.returnCrate}`} />
        <KeyValueRow label="Destination" value={RETURN_DEPOT.destination} />
        <KeyValueRow label="Return ETA" value={RETURN_DEPOT.eta} />
        <KeyValueRow label="Handover Bay" value={RETURN_DEPOT.handover} />
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("depot-return")}>
          Navigate to depot
        </Button>
        <Button variant="locked" size="md">
          Start Trip 2 (Locked until depot return)
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("day-summary")}>
          End day
        </Button>
      </div>
    </div>
  );
}
