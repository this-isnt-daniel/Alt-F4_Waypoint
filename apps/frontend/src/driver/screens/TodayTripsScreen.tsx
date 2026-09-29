import { formatUnits, formatVolume } from "@/lib/derive";
import { useDriverState } from "@/driver/state/useDriverState";
import { useNavigator } from "@/router/navigator";
import { TRIP_1, TRIP_2, RUN_TARGETS } from "@/driver/data/driverContent";
import { Button } from "@/driver/components/Button";
import { Chip } from "@/driver/components/Chip";
import { HeroBand } from "@/driver/components/HeroBand";
import { Lock, Phone, Check } from "lucide-react";

function TripSpecRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1.5">
      <span className="text-sm text-ink-muted">{label}</span>
      <span className="text-sm font-semibold text-ink">{value}</span>
    </div>
  );
}

export function TodayTripsScreen() {
  const {
    trip1Started,
    trip1Completed,
    trip2Unlocked,
    trip2Started,
  } = useDriverState();
  const { push } = useNavigator();

  const isTrip1Done = trip1Completed || trip2Started;

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

        {/* Trip 1 — active or completed/unavailable */}
        <section
          className={
            "rounded-card p-4 shadow-[var(--shadow-1)] " +
            (isTrip1Done
              ? "border border-line bg-surface/85 opacity-80"
              : "border-[1.5px] border-green bg-surface")
          }
        >
          <header className="flex items-center justify-between gap-2">
            <h2 className={"text-lg font-bold " + (isTrip1Done ? "text-ink-muted" : "text-ink")}>
              Fresh — Kandy
            </h2>
            <Chip
              kind="capability"
              label={isTrip1Done ? "COMPLETED" : "CHILLED REEFER"}
            />
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
          {isTrip1Done ? (
            <div className="mt-3 flex min-h-12 items-center justify-center gap-2 rounded-btn bg-raised text-sm font-semibold text-ink-muted border border-line">
              <Check size={16} className="text-success" /> Trip 1 Completed · Unavailable
            </div>
          ) : trip1Started ? (
            <Button
              variant="primary"
              size="lg"
              fullWidth
              className="mt-3"
              onClick={() => push("active-trip")}
            >
              Resume trip 1
            </Button>
          ) : (
            <Button
              variant="primary"
              size="lg"
              fullWidth
              className="mt-3"
              onClick={() => push("load-confirm", { trip: "1" })}
            >
              Start trip 1
            </Button>
          )}
        </section>

        {/* Trip 2 — locked until trip1 done; active once started */}
        <section
          className={
            "mt-3 rounded-card p-4 " +
            (trip2Unlocked || trip2Started
              ? "border-[1.5px] border-green bg-surface shadow-[var(--shadow-1)]"
              : "border border-line bg-surface opacity-80")
          }
        >
          <header className="flex items-center justify-between gap-2">
            <h2
              className={
                "text-lg font-bold " + (trip2Unlocked || trip2Started ? "text-ink" : "text-ink-muted")
              }
            >
              Style — Kandy
            </h2>
            <Chip
              kind="capability"
              label={
                trip2Started
                  ? "ACTIVE · AMBIENT"
                  : trip2Unlocked
                    ? "AMBIENT"
                    : "LOCKED"
              }
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
          {trip2Started ? (
            <Button
              variant="primary"
              size="lg"
              fullWidth
              className="mt-3"
              onClick={() => push("active-trip")}
            >
              Resume trip 2
            </Button>
          ) : trip2Unlocked ? (
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
