import { useEffect, useState } from "react";
import { ThemeToggle } from "@/theme/ThemeToggle";
import { ConnectionIndicator, type ConnectionTone } from "./ConnectionIndicator";
import { VEHICLE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

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
  const { connection, syncRecords } = useDriverState();
  const displayClock = clock ?? time;
  const tone: ConnectionTone = connection === "offline" ? "offline" : "online";

  return (
    <header className="flex items-center justify-between px-4 py-3 bg-surface border-b border-line">
      <div className="flex items-center gap-2">
        <span className="text-[11px] font-semibold text-slate-500 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200">
          {VEHICLE.id}
        </span>
      </div>
      <div className="flex items-center gap-2.5">
        <ConnectionIndicator tone={tone} count={syncRecords.length} />
        <span className="text-[11px] font-mono font-medium text-slate-400">
          {displayClock}
        </span>
        <ThemeToggle />
      </div>
    </header>
  );
}

export function ActiveTripBar({
  tripLabel = "Trip 1 · Fresh",
  stopLabel = "Stop 2 of 8",
  syncTone,
  clock,
}: {
  tripLabel?: string;
  stopLabel?: string;
  syncTone?: ConnectionTone;
  clock?: string;
}) {
  const time = useClock();
  const { connection, syncRecords } = useDriverState();
  const displayClock = clock ?? time;

  const resolvedTone: ConnectionTone =
    connection === "offline"
      ? "offline"
      : syncTone ?? "online";

  return (
    <header className="flex items-center justify-between px-4 py-3 bg-surface border-b border-line">
      <div className="flex flex-col">
        <span className="text-[13px] font-bold text-slate-900">{tripLabel}</span>
        <span className="text-[11px] text-slate-500">{stopLabel}</span>
      </div>
      <div className="flex items-center gap-2.5">
        <ConnectionIndicator tone={resolvedTone} count={syncRecords.length} />
        <span className="text-[11px] font-mono font-medium text-slate-400">
          {displayClock}
        </span>
        <ThemeToggle />
      </div>
    </header>
  );
}
