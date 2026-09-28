import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { ListRow } from "@/driver/components/ListRow";
import { OUTLET_CLOSED, VEHICLE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function OutletClosedScreen() {
  const { push } = useNavigator();
  const { addSyncRecord, connection } = useDriverState();

  const handleReturnToDepot = () => {
    addSyncRecord({
      type: "failed",
      outletId: OUTLET_CLOSED.outletId,
      state: connection === "online" ? "synced" : "pending",
      hasPhoto: true,
      pinVerified: false,
    });
    push("return-depot");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-danger tracking-wider uppercase">
          Outlet Closed Degradation
        </span>
        <h1 className="text-xl font-extrabold text-ink">Outlet unavailable</h1>
        <p className="text-xs font-semibold text-ink-muted">
          {OUTLET_CLOSED.outletId} · {OUTLET_CLOSED.outletName}
        </p>
      </div>

      <Card variant="surface" className="space-y-3">
        <div className="p-3 bg-danger-fill text-danger rounded-btn text-xs font-medium">
          Reason: {OUTLET_CLOSED.reason} — {OUTLET_CLOSED.body}
        </div>

        <div className="space-y-2 pt-1">
          <div className="text-xs font-bold text-ink-muted uppercase">Affected Return Items</div>
          {OUTLET_CLOSED.affectedItems.map((item, idx) => (
            <ListRow
              key={idx}
              title={`${item.name} ×${item.quantity}`}
              subtitle={item.action}
              status="returned"
              statusLabel="Return req."
            />
          ))}
        </div>

        <KeyValueRow label="Return Crate" value={OUTLET_CLOSED.returnCrate} />
        <KeyValueRow label="Depot Destination" value={VEHICLE.depot} />
        <KeyValueRow label="Handover Desk" value={OUTLET_CLOSED.handover} />
        <KeyValueRow label="Sync Status" value={connection === "online" ? "Ready" : "Pending offline"} />
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={handleReturnToDepot}>
          Return {OUTLET_CLOSED.affectedItems.reduce((acc, i) => acc + i.quantity, 0)} items to depot
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("active-trip")}>
          Back to route
        </Button>
      </div>
    </div>
  );
}
