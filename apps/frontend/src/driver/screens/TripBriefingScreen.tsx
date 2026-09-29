import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { TRIP_1, TRIP_2, VEHICLE } from "@/driver/data/driverContent";

export function TripBriefingScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-green tracking-wider uppercase">
          Trip 1 Briefing
        </span>
        <h1 className="text-xl font-extrabold text-ink">{TRIP_1.brand} · {TRIP_1.district}</h1>
        <p className="text-xs text-ink-muted">
          {TRIP_1.stopCount} stops · first window 05:30
        </p>
      </div>

      <Card variant="surface" className="grid grid-cols-3 gap-2 text-center p-3">
        <div>
          <div className="text-xs text-ink-muted">Route</div>
          <div className="text-sm font-extrabold text-ink">{TRIP_1.distanceKm} km</div>
        </div>
        <div>
          <div className="text-xs text-ink-muted">Drive Time</div>
          <div className="text-sm font-extrabold text-ink">{TRIP_1.driveTime}</div>
        </div>
        <div>
          <div className="text-xs text-ink-muted">Fuel Quota</div>
          <div className="text-sm font-extrabold text-ink">{VEHICLE.weeklyFuelQuotaL} L</div>
        </div>
      </Card>

      <Card variant="surface" className="space-y-2">
        <div className="text-2xs font-extrabold text-green uppercase tracking-wider">
          First Stop · {TRIP_1.stops[0]?.outletId}
        </div>
        <h2 className="text-base font-bold text-ink">{TRIP_1.stops[0]?.name}</h2>
        <KeyValueRow label="Window" value={TRIP_1.stops[0]?.window} />
        <KeyValueRow label="Access" value={`${TRIP_1.stops[0]?.dock} · ${TRIP_1.stops[0]?.parking}`} />

        <div className="flex gap-2 pt-1">
          <Chip kind="restriction" category="temperature" label="Chilled" glyph="❄" />
          <Chip kind="restriction" category="access" label="Van only" glyph="🅿" />
        </div>
      </Card>

      <Card variant="raised" className="text-xs text-ink-muted leading-relaxed">
        <span className="font-bold text-ink block mb-1">Route Instruction:</span>
        Keep chilled crates sealed. Confirm rear-dock access before each mall stop.
      </Card>

      <Card variant="surface" className="space-y-1">
        <div className="text-2xs font-extrabold text-ink-muted uppercase">
          TRIP 2 PREVIEW · {TRIP_2.brand}
        </div>
        <div className="text-sm font-bold text-ink">{TRIP_2.brand} · {TRIP_2.district} (Later)</div>
        <p className="text-xs text-ink-muted">Stops {TRIP_2.stopCount} outlets · Start after Trip 1 + depot check</p>
      </Card>

      <Button
        variant="primary"
        size="lg"
        onClick={() => push("load-confirm")}
      >
        Start Trip 1
      </Button>

      <div className="text-center text-2xs text-ink-muted">
        {VEHICLE.id} · {VEHICLE.depot} depot
      </div>
    </div>
  );
}
