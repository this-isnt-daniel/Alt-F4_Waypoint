import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { DRIVER, VEHICLE } from "@/driver/data/driverContent";

export function StartDayScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div className="space-y-1 pt-2">
        <span className="text-2xs font-bold text-green uppercase tracking-wider">
          {DRIVER.date}
        </span>
        <h1 className="text-xl font-extrabold text-ink">Good morning, Nimal</h1>
        <p className="text-xs text-ink-muted">Ready for your shift ({DRIVER.shift})</p>
      </div>

      <Card variant="surface" className="space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-line">
          <div>
            <div className="text-base font-extrabold text-ink">{VEHICLE.id} Assigned</div>
            <div className="text-xs text-ink-muted uppercase">Refrigerated van</div>
          </div>
          <span className="px-2.5 py-1 rounded-pill bg-success-fill text-success text-xs font-bold">
            READY
          </span>
        </div>

        <KeyValueRow label="Home depot" value={VEHICLE.depot} />
        <KeyValueRow label="Temperature" value="3°C · in range" />
        <KeyValueRow label="Fuel quota" value={`${VEHICLE.weeklyFuelQuotaL} L remaining`} />
      </Card>

      <Card variant="raised" className="text-xs text-ink-muted leading-relaxed">
        <span className="font-bold text-ink block mb-1">Pre-trip checklist:</span>
        Tyres, refrigeration seal, fuel card and phone mount confirmed.
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("today-trips")}>
          Start day
        </Button>
        <Button
          variant="secondary"
          size="md"
          onClick={() => push("contact-dispatch")}
        >
          Vehicle issue
        </Button>
      </div>
    </div>
  );
}
