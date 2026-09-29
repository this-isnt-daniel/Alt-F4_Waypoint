import { useNavigator } from "@/router/navigator";
import { MockMap } from "@/driver/components/MockMap";
import { BottomSheet } from "@/driver/components/BottomSheet";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function ActiveTripScreen() {
  const { push } = useNavigator();
  const { currentStopSeq } = useDriverState();

  const stop = TRIP_1_STOPS.find((s) => s.seq === currentStopSeq) ?? TRIP_1_STOPS[1]!;

  return (
    <div className="relative min-h-[calc(100vh-60px)] pb-72 max-w-[430px] mx-auto">
      {/* Map Surface */}
      <div className="p-3">
        <MockMap
          currentStopSeq={currentStopSeq}
          onPinClick={(seq) => push("stop-detail", { seq: String(seq) })}
        />
      </div>

      {/* Map Command Surface Banner */}
      <div className="px-4 py-2">
        <div className="p-3 bg-surface border border-line rounded-card shadow-1 flex items-center justify-between text-xs">
          <div>
            <span className="font-bold text-ink block">Active Route · Trip 1</span>
            <span className="text-ink-muted">6 stops remaining · ETA Return 09:30</span>
          </div>
          <button
            type="button"
            onClick={() => push("route-changed")}
            className="text-2xs font-bold text-green border border-green/30 px-2 py-1 rounded-pill bg-green-fill"
          >
            Resequenced
          </button>
        </div>
      </div>

      {/* Persistent Bottom Sheet */}
      <BottomSheet
        stop={stop}
        etaMin={12}
        windowClosingMin={43}
        onMarkArrived={() => push("mark-arrived", { seq: String(stop.seq) })}
      />
    </div>
  );
}
