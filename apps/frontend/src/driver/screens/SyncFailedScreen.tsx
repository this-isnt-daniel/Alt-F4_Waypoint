import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { ErrorState } from "@/driver/components/ErrorState";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { ListRow } from "@/driver/components/ListRow";
import { useDriverState } from "@/driver/state/useDriverState";

export function SyncFailedScreen() {
  const { push } = useNavigator();
  const { setConnection } = useDriverState();

  const handleRetry = () => {
    setConnection("online");
    push("sync-centre");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 pt-2">
      <ErrorState
        icon="⚡"
        title="Sync failed"
        description="Records are safe on this phone. Waypoint couldn’t reach the server. Nothing was lost and you can continue working."
        action={
          <Button variant="primary" size="lg" onClick={handleRetry}>
            Retry sync
          </Button>
        }
        secondaryAction={
          <Button variant="secondary" size="md" onClick={() => push("active-trip")}>
            Continue offline
          </Button>
        }
      />

      <Card variant="surface" className="space-y-2">
        <div className="text-xs font-bold text-ink-muted uppercase pb-1">Queued Unsynced Records (4)</div>
        <ListRow title="OUT047 delivery" subtitle="Ready to retry" status="failed" statusLabel="Paused" />
        <ListRow title="OUT052 photo" subtitle="Upload paused" status="failed" statusLabel="Paused" />
        <ListRow title="OUT058 issue" subtitle="Saved offline" status="returned" statusLabel="Offline" />
        <ListRow title="Route update" subtitle="Needs connection" status="returned" statusLabel="Offline" />

        <KeyValueRow label="Last attempt" value="07:02" />
        <KeyValueRow label="Next automatic retry" value="In 2 minutes" />
        <KeyValueRow label="Storage" value="Encrypted locally" emphasis="strong" />
      </Card>

      <div className="pt-2">
        <Button
          variant="ghost"
          size="md"
          onClick={() => push("contact-dispatch")}
        >
          Call support
        </Button>
      </div>
    </div>
  );
}
