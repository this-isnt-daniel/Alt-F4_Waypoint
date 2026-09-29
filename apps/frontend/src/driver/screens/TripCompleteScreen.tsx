import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { HeroBand } from "@/driver/components/HeroBand";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { ListRow } from "@/driver/components/ListRow";
import { TRIP_COMPLETE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function TripCompleteScreen() {
  const { push } = useNavigator();
  const { completeTrip1 } = useDriverState();

  const handleStartTrip2Prep = () => {
    completeTrip1();
    push("today-trips");
  };

  return (
    <div className="pb-8 max-w-[430px] mx-auto">
      <HeroBand
        label="TRIP COMPLETE"
        title={TRIP_COMPLETE.title}
        subline={TRIP_COMPLETE.subtitle}
      />

      <div className="px-4 space-y-4">
        {/* Tri-count Chips */}
        <div className="flex gap-2 justify-between">
          <Chip kind="outcome" tone="delivered" label="DELIVERED" count={TRIP_COMPLETE.delivered} />
          <Chip kind="outcome" tone="partial" label="PARTIAL" count={TRIP_COMPLETE.partial} />
          {/* 0 FAILED must be slate/neutral, not red */}
          <Chip kind="outcome" tone="failed" label="FAILED" count={TRIP_COMPLETE.failed} />
        </div>

        {/* Operational Metrics */}
        <Card variant="surface" className="space-y-2">
          <div className="text-2xs font-extrabold uppercase text-ink-muted tracking-wider">
            TRIP PERFORMANCE
          </div>
          <p className="text-2xs text-ink-muted pb-1">
            Time, distance and fuel against plan — recorded for dispatch.
          </p>

          <KeyValueRow label="Total Trip Time" value={TRIP_COMPLETE.totalTripTime} trailing={
            <span className="text-2xs font-bold text-success bg-success-fill px-2 py-0.5 rounded-pill">
              {TRIP_COMPLETE.budgetStatus}
            </span>
          } />
          <KeyValueRow label="Total Distance" value={TRIP_COMPLETE.distance} />
          <KeyValueRow label="Fuel Economy" value={`${TRIP_COMPLETE.fuelEconomy} · ${TRIP_COMPLETE.fuelUsed} used`} />
          <KeyValueRow label="Remaining Fuel" value={TRIP_COMPLETE.remainingFuel} emphasis="strong" />
        </Card>

        {/* Route Recap */}
        <Card variant="surface" className="space-y-2">
          <div className="text-2xs font-extrabold uppercase text-ink-muted tracking-wider">
            ROUTE RECAP
          </div>

          <div className="space-y-1">
            {TRIP_COMPLETE.routeRecap.map((recap, idx) => (
              <ListRow
                key={idx}
                title={`${recap.outletId} ${recap.outletName}`}
                subtitle={`Finished ${recap.time}${recap.suffix ? ` · ${recap.suffix}` : ""}`}
                status={recap.outcome === "Delivered" ? "delivered" : "partial"}
                statusLabel={recap.outcome}
              />
            ))}
            <div className="p-2.5 bg-raised text-center text-xs font-semibold text-ink-muted rounded-btn">
              +{TRIP_COMPLETE.remainingRecapCount} additional stops — Delivered ✓
            </div>
          </div>
        </Card>

        {/* Return Guidance Box */}
        <Card variant="raised" className="text-xs text-ink leading-relaxed">
          <span className="font-bold text-ink-muted block mb-0.5">Depot Guidance:</span>
          {TRIP_COMPLETE.returnGuidance}
        </Card>

        {/* Forward CTA */}
        <div className="space-y-1 pt-2">
          <Button variant="primary" size="lg" onClick={handleStartTrip2Prep}>
            {TRIP_COMPLETE.forwardCta}
          </Button>
          <div className="text-2xs text-ink-muted text-center font-medium">
            {TRIP_COMPLETE.forwardCaption}
          </div>
        </div>
      </div>
    </div>
  );
}
