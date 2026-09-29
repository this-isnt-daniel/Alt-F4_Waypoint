import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { EmptyState } from "@/driver/components/EmptyState";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { DRIVER, VEHICLE } from "@/driver/data/driverContent";

export function NoTripsScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 pt-4">
      <EmptyState
        icon="🚛"
        title="No trips assigned"
        description="There’s nothing scheduled for this shift yet. Dispatch will notify you when a trip is ready."
      />

      <Card variant="surface" className="space-y-2">
        <KeyValueRow label="Driver" value={DRIVER.name} />
        <KeyValueRow label="Assigned Vehicle" value={VEHICLE.id} />
        <KeyValueRow label="Home Depot" value={VEHICLE.depot} />
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("today-trips")}>
          Refresh trips
        </Button>
        <Button
          variant="secondary"
          size="md"
          onClick={() => push("contact-dispatch")}
        >
          Call dispatch
        </Button>
      </div>
    </div>
  );
}
