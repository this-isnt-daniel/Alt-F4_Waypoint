import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";

export function StopDetailScreen() {
  const { route, push } = useNavigator();
  const seqParam = Number(route.params.seq ?? "2");
  const stop = TRIP_1_STOPS.find((s) => s.seq === seqParam) ?? TRIP_1_STOPS[1]!;

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="flex items-center justify-between">
        <span className="text-2xs font-extrabold text-green tracking-wider uppercase">
          Stop {stop.seq} of 8
        </span>
        <Chip kind="status" tone="onTime" label="ETA 12 min · on time" />
      </div>

      <div className="space-y-1">
        <span className="text-xs font-bold text-ink-muted">{stop.outletId}</span>
        <h1 className="text-xl font-extrabold text-ink">{stop.name}</h1>
        <p className="text-xs text-ink-muted">{stop.address}</p>
      </div>

      <Card variant="surface" className="space-y-2">
        <div className="flex justify-between items-center text-xs pb-2 border-b border-line">
          <span className="text-ink-muted">Delivery Window:</span>
          <span className="font-bold text-ink">{stop.window}</span>
        </div>

        <KeyValueRow label="Dock Access" value={`${stop.dock}${stop.dockDetail ? ` · ${stop.dockDetail}` : ""}`} />
        <KeyValueRow label="Parking Constraint" value={stop.parking} />
        <KeyValueRow label="Temperature" value={stop.temp} />
        <KeyValueRow label="Service Time" value={`${stop.serviceMin} min`} />
      </Card>

      {stop.instructions && (
        <Card variant="raised" className="text-xs text-ink leading-relaxed">
          <span className="font-bold text-ink-muted block mb-1">Special Instructions:</span>
          {stop.instructions}
        </Card>
      )}

      <Card variant="surface" className="grid grid-cols-3 gap-2 text-center p-3 text-xs">
        <div>
          <span className="text-ink-muted block">Stops left</span>
          <span className="font-extrabold text-ink text-sm">6</span>
        </div>
        <div>
          <span className="text-ink-muted block">Remaining</span>
          <span className="font-extrabold text-ink text-sm">96 km</span>
        </div>
        <div>
          <span className="text-ink-muted block">Fuel quota</span>
          <span className="font-extrabold text-ink text-sm">39 L</span>
        </div>
      </Card>

      <div className="space-y-2 pt-2">
        <Button
          variant="primary"
          size="lg"
          onClick={() => push("mark-arrived", { seq: String(stop.seq) })}
        >
          Mark arrived
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("active-trip")}>
          Back to map
        </Button>
      </div>
    </div>
  );
}
