import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { KeyValueRow } from "@/driver/components/KeyValueRow";

export function OfflineSavedScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 pt-6">
      <div className="text-center space-y-1">
        <div className="grid h-16 w-16 place-items-center rounded-circle bg-offline-fill text-offline text-3xl mx-auto mb-2">
          💾
        </div>
        <span className="text-2xs font-extrabold text-offline tracking-wider uppercase">
          Offline Buffer Safe
        </span>
        <h1 className="text-xl font-extrabold text-ink">Delivery saved</h1>
        <p className="text-xs font-semibold text-ink-muted">
          OUT047 · 06:34 · Saved safely on this phone
        </p>
      </div>

      <Card variant="surface" className="space-y-3">
        <p className="text-xs text-ink leading-relaxed">
          You can continue the route. The photo and PIN will sync automatically when connection returns.
        </p>

        <KeyValueRow label="Delivery Record" value="OUT047 · complete" />
        <KeyValueRow label="Photo Evidence" value="Saved locally" />
        <KeyValueRow label="Manager PIN" value="Confirmed" />
        <KeyValueRow label="Queue Position" value="1 of 3" emphasis="strong" />
      </Card>

      <Card variant="raised" className="text-xs text-ink-muted leading-relaxed">
        <span className="font-bold text-ink block mb-0.5">Reassurance:</span>
        No work will be lost. Keep Waypoint Driver open. Records remain encrypted and available after a restart.
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("active-trip")}>
          Continue to next stop
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("sync-centre")}>
          Open Sync Centre
        </Button>
      </div>
    </div>
  );
}
