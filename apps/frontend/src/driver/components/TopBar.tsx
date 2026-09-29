import { useEffect, useState } from "react";
import { ThemeToggle } from "@/theme/ThemeToggle";
import { ConnectionPill } from "./ConnectionPill";
import { SyncPill } from "./SyncPill";
import { type SyncState } from "@/driver/state/connection";
import { VEHICLE } from "@/driver/data/driverContent";

function useClock() {
  const [time, setTime] = useState<string>(() =>
    new Date().toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }),
  );

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(
        new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        }),
      );
    }, 10000);
    return () => clearInterval(timer);
  }, []);

  return time;
}

export function PreTripBar({ clock }: { clock?: string }) {
  const time = useClock();
  const displayClock = clock ?? time;

  return (
    <header className="flex items-center justify-between px-4 py-3 bg-surface border-b border-line">
      <div className="flex items-center gap-2">
        <ConnectionPill />
        <span className="text-xs font-bold text-ink-muted bg-raised px-2 py-1 rounded-pill">
          {VEHICLE.id}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs font-mono font-medium text-ink-muted">{displayClock}</span>
        <ThemeToggle />
      </div>
    </header>
  );
}

export function ActiveTripBar({
  tripLabel = "Trip 1",
  stopLabel = "Stop 2 of 8",
  syncTone,
  clock,
}: {
  tripLabel?: string;
  stopLabel?: string;
  syncTone?: SyncState;
  clock?: string;
}) {
  const time = useClock();
  const displayClock = clock ?? time;

  return (
    <header className="flex items-center justify-between px-3 py-2.5 bg-surface border-b border-line gap-2">
      <div className="flex flex-col min-w-0">
        <span className="text-xs font-bold text-ink truncate">{tripLabel}</span>
        <span className="text-2xs text-ink-muted truncate">{stopLabel}</span>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <ConnectionPill />
        <SyncPill tone={syncTone} />
        <span className="text-2xs font-mono font-medium text-ink-muted hidden xs:inline">{displayClock}</span>
        <ThemeToggle />
      </div>
    </header>
  );
}

