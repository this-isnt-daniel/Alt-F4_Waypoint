import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { DriverMap } from "@/driver/components/DriverMap";
import { BottomSheet } from "@/driver/components/BottomSheet";
import { AppIcon } from "@/driver/components/AppIcon";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function ActiveTripScreen() {
  const { push } = useNavigator();
  const {
    trip1Sequence,
    currentStopIndex,
    completedStopIds,
    flaggedStopIds,
    failedStopIds,
  } = useDriverState();

  const [viewMode, setViewMode] = useState<"map" | "list">("map");

  const currentOutletId = trip1Sequence[currentStopIndex] ?? "OUT047";
  const stop =
    TRIP_1_STOPS.find((s) => s.outletId === currentOutletId) ?? TRIP_1_STOPS[1]!;

  return (
    <div className="relative flex flex-col h-[calc(100vh-52px)] max-w-[430px] mx-auto pb-44">
      {/* Map / List toggle floating header */}
      <div className="absolute top-3 right-3 z-30">
        <button
          type="button"
          onClick={() => setViewMode(viewMode === "map" ? "list" : "map")}
          className="bg-white/95 backdrop-blur-sm shadow-md border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 flex items-center gap-1.5 hover:bg-slate-50 transition-colors"
          aria-label={viewMode === "map" ? "Switch to list view" : "Switch to map view"}
        >
          <AppIcon name={viewMode === "map" ? "list" : "map"} size={14} />
          <span>{viewMode === "map" ? "List view" : "Map view"}</span>
        </button>
      </div>

      {/* Surface: Map or Accessible Stop List */}
      {viewMode === "map" ? (
        <div className="flex-1 relative min-h-[360px]">
          <DriverMap
            stopIds={trip1Sequence}
            currentStopId={currentOutletId}
            completedStopIds={completedStopIds}
            flaggedStopIds={flaggedStopIds}
            failedStopIds={failedStopIds}
            onStopClick={(outletId) => {
              const s = TRIP_1_STOPS.find((x) => x.outletId === outletId);
              if (s) push("stop-detail", { seq: String(s.seq) });
            }}
            className="absolute inset-0"
          />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-slate-50">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
            Route Stops ({trip1Sequence.length})
          </h2>
          {trip1Sequence.map((outletId, index) => {
            const stopItem = TRIP_1_STOPS.find((s) => s.outletId === outletId);
            const isCurrent = outletId === currentOutletId;
            const isCompleted = completedStopIds.includes(outletId);
            const isFlagged = flaggedStopIds.includes(outletId);
            const isFailed = failedStopIds.includes(outletId);

            return (
              <button
                key={outletId}
                type="button"
                onClick={() => {
                  if (stopItem) push("stop-detail", { seq: String(stopItem.seq) });
                }}
                className={`w-full text-left p-3 rounded-xl border flex items-center justify-between transition-colors ${
                  isCurrent
                    ? "bg-white border-green shadow-sm ring-1 ring-green/30"
                    : isCompleted
                      ? "bg-white/60 border-slate-200 opacity-75"
                      : "bg-white border-slate-200"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                      isCurrent
                        ? "bg-green text-white"
                        : isCompleted
                          ? "bg-slate-200 text-slate-600"
                          : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    {index + 1}
                  </span>
                  <div>
                    <span className="font-semibold text-slate-900 text-sm block">
                      {outletId}
                    </span>
                    <span className="text-xs text-slate-500 block truncate max-w-[200px]">
                      {stopItem?.name ?? outletId}
                    </span>
                  </div>
                </div>

                <div className="text-right text-xs">
                  {isCurrent && (
                    <span className="text-green font-bold bg-green-fill px-2 py-0.5 rounded-full border border-green/20">
                      Current
                    </span>
                  )}
                  {isCompleted && (
                    <span className="text-slate-500 font-medium">Delivered</span>
                  )}
                  {isFlagged && (
                    <span className="text-amber-600 font-medium">Partial</span>
                  )}
                  {isFailed && (
                    <span className="text-red-600 font-medium">Failed</span>
                  )}
                  {!isCurrent && !isCompleted && !isFlagged && !isFailed && (
                    <span className="text-slate-400">Upcoming</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Persistent Bottom Sheet */}
      <BottomSheet
        stop={stop}
        etaMin={12}
        windowClosingMin={43}
        onMarkArrived={() => push("mark-arrived", { seq: String(stop.seq) })}
        onChat={() => push("chat", { outletId: stop.outletId })}
        onCall={() => push("call-overlay", { outletId: stop.outletId })}
        onDetails={() => push("stop-detail", { seq: String(stop.seq) })}
      />
    </div>
  );
}
