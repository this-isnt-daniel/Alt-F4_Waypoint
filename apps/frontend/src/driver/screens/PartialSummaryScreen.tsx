import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { ListRow } from "@/driver/components/ListRow";
import { OUT058_PARTIAL, VEHICLE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function PartialSummaryScreen() {
  const { push } = useNavigator();
  const { addSyncRecord, connection } = useDriverState();

  const handleContinue = () => {
    addSyncRecord({
      type: "partial",
      outletId: OUT058_PARTIAL.outletId,
      state: connection === "online" ? "synced" : "pending",
      hasPhoto: true,
      pinVerified: true,
    });
    push("return-depot");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-warning tracking-wider uppercase">
          Handover Summary
        </span>
        <h1 className="text-xl font-extrabold text-ink">Partial delivery</h1>
        <p className="text-xs font-semibold text-ink-muted">
          {OUT058_PARTIAL.outletId} · {OUT058_PARTIAL.outletName}
        </p>
      </div>

      <Card variant="surface" className="space-y-3">
        <p className="text-xs text-ink leading-relaxed">
          {OUT058_PARTIAL.handedOver} of {OUT058_PARTIAL.manifest} handed over. Two frozen items were marked damaged and will return to {VEHICLE.depot} depot.
        </p>

        <div className="space-y-2">
          <ListRow
            title={`${OUT058_PARTIAL.handedOver} items delivered`}
            subtitle="Delivered · Receiver confirmed"
            status="delivered"
            statusLabel="Handed over"
          />

          {OUT058_PARTIAL.returnItems.map((item, idx) => (
            <ListRow
              key={idx}
              title={`${item.name} ×${item.quantity}`}
              subtitle={`${item.reason} · return required · Crate ${item.returnCrate}`}
              status="partial"
              statusLabel="Return req."
            />
          ))}
        </div>
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={handleContinue}>
          Continue to return custody
        </Button>
        <Button
          variant="secondary"
          size="md"
          onClick={() => push("checklist", { outletId: OUT058_PARTIAL.outletId })}
        >
          Review items
        </Button>
      </div>
    </div>
  );
}
