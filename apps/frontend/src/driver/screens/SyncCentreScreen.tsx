import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { ListRow } from "@/driver/components/ListRow";
import { useDriverState } from "@/driver/state/useDriverState";

export function SyncCentreScreen() {
  const { push } = useNavigator();
  const { connection, setConnection, syncReviewForwarded } = useDriverState();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-green tracking-wider uppercase">
          Sync Centre
        </span>
        <h1 className="text-xl font-extrabold text-ink">Sync Centre</h1>
        <p className="text-xs text-ink-muted">
          {connection === "online" ? "Connection restored syncing · 2 of 4 updates complete" : "Working offline · 4 updates queued"}
        </p>
      </div>

      <Card variant="surface" className="space-y-2">
        <div className="flex justify-between items-center text-xs font-bold text-ink-muted uppercase pb-1">
          <span>Queued Records</span>
          <span>4 updates</span>
        </div>

        <ListRow
          title="OUT047 delivery"
          subtitle="Queued · photo + PIN"
          status={connection === "online" ? "delivered" : "pending"}
          statusLabel={connection === "online" ? "Synced" : "Ready"}
        />

        <ListRow
          title="OUT052 photo upload"
          subtitle="1.8 MB · 67%"
          status={connection === "online" ? "syncing" : "pending"}
          statusLabel={connection === "online" ? "Uploading" : "Queued"}
        />

        <ListRow
          title="OUT058 delivery record conflict"
          subtitle="Detected discrepancy · Evidence preserved"
          status={syncReviewForwarded ? "returned" : "flagged"}
          statusLabel={syncReviewForwarded ? "Forwarded" : "Needs review"}
          onClick={() => push(syncReviewForwarded ? "record-sent" : "sync-review")}
        />

        <ListRow
          title="Dispatcher route update"
          subtitle="OUT061 moved next"
          status="flagged"
          statusLabel="Route change"
          onClick={() => push("route-changed")}
        />
      </Card>

      <div className="space-y-2 pt-2">
        <Button
          variant="primary"
          size="lg"
          onClick={() => {
            setConnection("online");
          }}
        >
          Sync now
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("active-trip")}>
          View map
        </Button>
        <Button variant="ghost" size="md" onClick={() => push("sync-failed")}>
          Simulate sync error test state
        </Button>
      </div>
    </div>
  );
}
