import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { KeyValueRow } from "@/driver/components/KeyValueRow";

export function CameraDeniedScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 pt-4">
      <div className="text-center space-y-1">
        <div className="grid h-16 w-16 place-items-center rounded-circle bg-warning-fill text-warning text-3xl mx-auto mb-2">
          📷
        </div>
        <span className="text-2xs font-extrabold text-warning tracking-wider uppercase">
          Permission Required
        </span>
        <h1 className="text-xl font-extrabold text-ink">Camera access needed</h1>
        <p className="text-xs text-ink-muted">
          Waypoint Driver needs the camera only to capture delivery and issue evidence.
        </p>
      </div>

      <Card variant="surface" className="space-y-2">
        <KeyValueRow label="Used for" value="POD and issue photos" />
        <KeyValueRow label="Stored" value="Encrypted in Waypoint" />
        <KeyValueRow label="Not used for" value="Background recording" />
      </Card>

      <Card variant="raised" className="text-xs text-ink-muted leading-relaxed">
        <span className="font-bold text-ink block mb-0.5">Can’t enable it now?</span>
        Save the stop as pending evidence and contact dispatch.
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("pod-photo")}>
          Allow camera access
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("pod-pin")}>
          Save without photo
        </Button>
      </div>
    </div>
  );
}
