import { formatUnits, formatVolume } from "@/lib/derive";
import { useDriverState } from "@/driver/state/useDriverState";
import { useNavigator } from "@/router/navigator";
import { TRIP_1, TRIP_2, RUN_TARGETS } from "@/driver/data/driverContent";
import { Button } from "@/driver/components/Button";
import { Chip } from "@/driver/components/Chip";
import { HeroBand } from "@/driver/components/HeroBand";
import { Lock, Phone } from "lucide-react";

function TripSpecRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1.5">
      <span className="text-sm text-ink-muted">{label}</span>
      <span className="text-sm font-semibold text-ink">{value}</span>
    </div>
  );
}

export function TodayTripsScreen() {
  const { trip2Unlocked } = useDriverState();
  const { push } = useNavigator();

  return (
    <div className="pb-6">
      <HeroBand
        label="TODAY'S RUN TARGETS"
        title={`${RUN_TARGETS.stopCount} Stops · ${formatUnits(RUN_TARGETS.unitCount)}`}
      />

      <div className="px-4">
        <p className="mb-2 mt-4 text-2xs font-semibold uppercase tracking-wide text-ink-muted">
          Trips
        </p>

        {/* Trip 1 — active */}
        <section className="rounded-card border-[1.5px] border-green bg-surface p-4 shadow-[var(--shadow-1)]">
          <header className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-bold text-ink">Fresh — Kandy</h2>
            <Chip kind="capability" label="CHILLED REEFER" />
          </header>
          <div className="mt-2 divide-y divide-line">
            <TripSpecRow label="Stops" value={`${TRIP_1.stopCount}`} />
            <TripSpecRow label="Load" value={formatUnits(TRIP_1.manifestUnits)} />
            <TripSpecRow
              label="Weight / Volume"
              value={`${TRIP_1.weightKg} kg · ${formatVolume(TRIP_1.volumeM3)}`}
            />
            <TripSpecRow
              label="Depart / Return"
              value={`${TRIP_1.depart} · ${TRIP_1.etaReturn}`}
            />
          </div>
          <Button
            variant="primary"
            size="lg"
            fullWidth
            className="mt-3"
            onClick={() => push("load-confirm")}
          >
            Start trip 1
          </Button>
        </section>

        {/* Trip 2 — locked until trip1 + depot return */}
        <section className="mt-3 rounded-card border border-line bg-surface p-4">
          <header className="flex items-center justify-between gap-2">
            <h2
              className={
                "text-lg font-bold " + (trip2Unlocked ? "text-ink" : "text-ink-muted")
              }
            >
              Style — Kandy
            </h2>
            <Chip
              kind="capability"
              label={trip2Unlocked ? "AMBIENT" : "LOCKED"}
            />
          </header>
          <div className="mt-2 divide-y divide-line">
            <TripSpecRow label="Stops" value={`${TRIP_2.stopCount}`} />
            <TripSpecRow label="Load" value={formatUnits(TRIP_2.manifestUnits)} />
            <TripSpecRow
              label="Weight / Volume"
              value={`${TRIP_2.weightKg} kg · ${formatVolume(TRIP_2.volumeM3)}`}
            />
          </div>
          {trip2Unlocked ? (
            <Button
              variant="primary"
              size="lg"
              fullWidth
              className="mt-3"
              onClick={() => push("load-confirm", { trip: "2" })}
            >
              Start trip 2
            </Button>
          ) : (
            <div className="mt-3 flex min-h-12 items-center justify-center gap-2 rounded-btn bg-raised text-sm font-medium text-ink-muted">
              <Lock size={16} aria-hidden="true" /> Locked until trip 1 done
            </div>
          )}
        </section>

        <button
          type="button"
          onClick={() => push("contact-dispatch")}
          className="mx-auto mt-4 flex items-center gap-1.5 text-sm font-medium text-green hover:underline"
        >
          <Phone size={16} aria-hidden="true" /> Contact dispatch
        </button>
      </div>
    </div>
  );
}
