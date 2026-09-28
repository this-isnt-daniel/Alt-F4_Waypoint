import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { DEPOT_RETURN } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function DepotReturnScreen() {
  const { push } = useNavigator();
  const { completeTrip1 } = useDriverState();

  const handleComplete = () => {
    completeTrip1();
    push("trip-complete");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 pt-6">
      <div className="text-center space-y-1">
        <div className="grid h-16 w-16 place-items-center rounded-circle bg-success-fill text-success text-3xl mx-auto mb-2">
          ✓
        </div>
        <span className="text-2xs font-extrabold text-success tracking-wider uppercase">
          Custody Handed Over
        </span>
        <h1 className="text-xl font-extrabold text-ink">Depot return</h1>
        <p className="text-xs font-semibold text-ink-muted">{DEPOT_RETURN.location}</p>
      </div>

      <Card variant="surface" className="space-y-3">
        <p className="text-xs text-ink leading-relaxed">
          Depot officer {DEPOT_RETURN.officer} confirmed the return at {DEPOT_RETURN.confirmedAt}.
        </p>

        <KeyValueRow label="Returned Items" value="Frozen produce ×2" />
        <KeyValueRow label="Return Crate" value={DEPOT_RETURN.returnCrate} />
        <KeyValueRow label="Condition" value={DEPOT_RETURN.condition} />
        <KeyValueRow label="Officer Confirmation" value={DEPOT_RETURN.officerPin} emphasis="strong" />
      </Card>

      <div className="pt-2">
        <Button variant="primary" size="lg" onClick={handleComplete}>
          Record synced · Finish Trip 1
        </Button>
      </div>
    </div>
  );
}
