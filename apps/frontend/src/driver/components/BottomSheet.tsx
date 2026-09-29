import { useState } from "react";
import { type DriverStop } from "@/driver/data/driverContent";
import { Button } from "./Button";
import { Chip } from "./Chip";
import { cn } from "@/lib/cn";
import { useNavigator } from "@/router/navigator";

export interface BottomSheetProps {
  stop: DriverStop;
  etaMin?: number;
  windowClosingMin?: number;
  onMarkArrived: () => void;
  className?: string;
}

export function BottomSheet({
  stop,
  etaMin = 12,
  windowClosingMin = 43,
  onMarkArrived,
  className,
}: BottomSheetProps) {
  const [expanded, setExpanded] = useState<boolean>(false);
  const { push } = useNavigator();

  return (
    <div
      className={cn(
        "fixed bottom-0 left-0 right-0 max-w-[430px] mx-auto bg-surface border-t border-line rounded-t-[24px] shadow-2 z-40 transition-all duration-300",
        expanded ? "max-h-[85vh] overflow-y-auto" : "max-h-[320px]",
        className,
      )}
    >
      {/* Handle bar */}
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-label={expanded ? "Collapse stop details" : "Expand stop details"}
        className="w-full py-2.5 flex items-center justify-center cursor-pointer hover:opacity-80 focus:outline-none"
      >
        <div className="h-1.5 w-12 rounded-pill bg-line" />
      </button>

      <div className="px-5 pb-6 space-y-4">
        {/* Header line */}
        <div className="flex items-center justify-between">
          <span className="text-2xs font-extrabold tracking-wider text-green uppercase">
            NEXT · {stop.outletId}
          </span>
          <Chip
            kind="status"
            tone={windowClosingMin <= 15 ? "windowClosing" : "onTime"}
            label={`Closes in ${windowClosingMin} min`}
          />
        </div>

        {/* Title & Address */}
        <div>
          <h2 className="text-lg font-bold text-ink leading-tight">{stop.name}</h2>
          <p className="text-xs text-ink-muted mt-0.5">{stop.address}</p>
        </div>

        {/* Restriction chips */}
        <div className="flex flex-wrap gap-2">
          <Chip kind="restriction" category="dock" label={stop.dock} glyph="🚛" />
          <Chip kind="restriction" category="access" label={stop.parking} glyph="🅿" />
          <Chip kind="restriction" category="temperature" label={stop.temp} glyph="❄" />
        </div>

        {/* Primary CTA */}
        <div className="pt-1">
          <Button variant="primary" size="lg" onClick={onMarkArrived}>
            Mark arrived
          </Button>
        </div>

        {/* Secondary actions */}
        <div className="grid grid-cols-3 gap-2">
          <Button
            variant="secondary"
            size="md"
            onClick={() => push("chat", { outletId: stop.outletId })}
          >
            💬 Chat
          </Button>
          <Button
            variant="secondary"
            size="md"
            onClick={() => push("call-overlay", { outletId: stop.outletId })}
          >
            📞 Call
          </Button>
          <Button
            variant="secondary"
            size="md"
            onClick={() => push("stop-detail", { seq: String(stop.seq) })}
          >
            📋 Details
          </Button>
        </div>

        {/* Expanded Content */}
        {expanded && (
          <div className="pt-4 border-t border-line space-y-3.5 text-sm">
            <div className="bg-raised p-3.5 rounded-btn space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-ink-muted">Dock Detail:</span>
                <span className="font-semibold text-ink">{stop.dockDetail ?? stop.dock}</span>
              </div>
              {stop.mallWindow && (
                <div className="flex justify-between text-xs">
                  <span className="text-ink-muted">Mall Access Window:</span>
                  <span className="font-semibold text-ink">{stop.mallWindow}</span>
                </div>
              )}
              <div className="flex justify-between text-xs">
                <span className="text-ink-muted">Expected Service Time:</span>
                <span className="font-semibold text-ink">{stop.serviceMin} min</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-ink-muted">Remaining Route:</span>
                <span className="font-semibold text-ink">6 stops · 96 km left</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-ink-muted">Fuel Quota:</span>
                <span className="font-semibold text-ink">39 L remaining</span>
              </div>
            </div>

            {stop.instructions && (
              <div className="p-3 bg-surface border border-line rounded-btn text-xs text-ink leading-relaxed">
                <span className="font-bold block text-ink-muted mb-1">Special Instructions:</span>
                {stop.instructions}
              </div>
            )}

            <Button
              variant="secondary"
              size="md"
              onClick={() => push("issue-wizard", { outletId: stop.outletId })}
            >
              ⚠️ Report Issue / Delay
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
