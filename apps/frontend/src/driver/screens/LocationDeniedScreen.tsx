import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { KeyValueRow } from "@/driver/components/KeyValueRow";

export function LocationDeniedScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 pt-4">
      <div className="text-center space-y-1">
        <div className="grid h-16 w-16 place-items-center rounded-circle bg-warning-fill text-warning text-3xl mx-auto mb-2">
          📍
        </div>
        <span className="text-2xs font-extrabold text-warning tracking-wider uppercase">
          Permission Required
        </span>
        <h1 className="text-xl font-extrabold text-ink">Location access needed</h1>
        <p className="text-xs text-ink-muted">
          Location keeps ETA, arrival confirmation, and route changes accurate while a trip is active.
        </p>
      </div>

      <Card variant="surface" className="space-y-2">
        <KeyValueRow label="While driving" value="Route + ETA calculation" />
        <KeyValueRow label="At the stop" value="Arrival confirmation" />
        <KeyValueRow label="After trip" value="Tracking automatically stops" />
      </Card>

      <Card variant="raised" className="text-xs text-ink-muted leading-relaxed">
        <span className="font-bold text-ink block mb-0.5">Safety Rule:</span>
        Stop safely to continue. Do not change permissions while the vehicle is moving.
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("active-trip")}>
          Turn on precise location
        </Button>
        <Button
          variant="secondary"
          size="md"
          onClick={() => push("contact-dispatch")}
        >
          Call dispatcher
        </Button>
        <Button variant="ghost" size="md" onClick={() => push("active-trip")}>
          Continue offline
        </Button>
      </div>
    </div>
  );
}
