import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { HeroBand } from "@/driver/components/HeroBand";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { TRIP_1, TRIP_2, RUN_TARGETS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";
import { formatNumber } from "@/lib/derive";

export function TodayTripsScreen() {
  const { push } = useNavigator();
  const { trip2Unlocked } = useDriverState();

  return (
    <div className="pb-8 max-w-[430px] mx-auto">
      <HeroBand
        label="TODAY'S RUN TARGETS"
        title={`${RUN_TARGETS.stopCount} Stops • ${formatNumber(RUN_TARGETS.unitCount)} Units`}
        subline="Kandy Hub Route • 2 Trips Scheduled"
      />

      <div className="px-4 space-y-4">
        <h2 className="text-xs font-extrabold tracking-wider uppercase text-ink-muted">
          ASSIGNED TRIPS (2)
        </h2>

        {/* Trip 1 Card */}
        <Card variant="surface" className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-extrabold text-ink">
              {TRIP_1.brand} — {TRIP_1.district}
            </h3>
            <Chip kind="capability" label={TRIP_1.capability} />
          </div>

          <div className="space-y-1">
            <KeyValueRow label="Stops" value={`${TRIP_1.stopCount} Deliveries`} />
            <KeyValueRow label="Weight / Volume" value={`${TRIP_1.weightKg} kg · ${TRIP_1.volumeM3} m³`} />
            <KeyValueRow label="Manifest load" value={`${formatNumber(TRIP_1.manifestUnits)} Units`} />
            <KeyValueRow label="Depart / Return ETA" value={`${TRIP_1.depart} · ${TRIP_1.etaReturn}`} />
          </div>

          <Button
            variant="primary"
            size="lg"
            onClick={() => push("load-confirm")}
          >
            START TRIP 1
          </Button>
        </Card>

        {/* Trip 2 Card */}
        <Card variant="surface" className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-extrabold text-ink">
              {TRIP_2.brand} — {TRIP_2.district}
            </h3>
            <Chip
              kind="capability"
              label={trip2Unlocked ? TRIP_2.capability : "LOCKED"}
            />
          </div>

          <div className="space-y-1 opacity-90">
            <KeyValueRow label="Stops" value={`${TRIP_2.stopCount} Deliveries`} />
            <KeyValueRow label="Weight / Volume" value={`${TRIP_2.weightKg} kg · ${TRIP_2.volumeM3} m³`} />
            <KeyValueRow label="Manifest load" value={`${formatNumber(TRIP_2.manifestUnits)} Units`} />
            <KeyValueRow label="Depart" value={TRIP_2.depart} />
          </div>

          {trip2Unlocked ? (
            <Button
              variant="primary"
              size="lg"
              onClick={() => push("active-trip", { trip: "2" })}
            >
              START TRIP 2
            </Button>
          ) : (
            <div className="w-full py-3 bg-raised text-center text-xs font-bold text-ink-muted rounded-btn border border-line">
              🔒 LOCKED UNTIL TRIP 1 DONE
            </div>
          )}
        </Card>

        {/* Dispatch link */}
        <div className="text-center pt-2">
          <button
            type="button"
            onClick={() => push("contact-dispatch")}
            className="text-xs text-green font-semibold underline hover:opacity-80"
          >
            Need Dispatch Assistance? Tap here
          </button>
        </div>
      </div>
    </div>
  );
}
