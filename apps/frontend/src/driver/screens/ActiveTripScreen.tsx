import { useState } from "react";
import { Lock } from "lucide-react";
import { useNavigator } from "@/router/navigator";
import { DriverMap } from "@/driver/components/DriverMap";
import { BottomSheet } from "@/driver/components/BottomSheet";
import { AppIcon } from "@/driver/components/AppIcon";
import { useDriverState } from "@/driver/state/useDriverState";

export function ActiveTripScreen() {
  const { push } = useNavigator();
  const {
    currentTripSequence,
    currentTripStops,
    currentStopIndex,
    completedStopIds,
    flaggedStopIds,
    failedStopIds,
  } = useDriverState();

  const [viewMode, setViewMode] = useState<"map" | "list">("map");

  const currentOutletId =
    currentTripSequence[currentStopIndex] ?? currentTripSequence[0] ?? "OUT042";
  const stop =
    currentTripStops.find((s) => s.outletId === currentOutletId) ??
    currentTripStops[0];

  return (
    <div className="relative flex flex-col flex-1 h-[calc(100vh-84px)] max-w-[430px] mx-auto overflow-hidden bg-slate-50">
      {/* Surface: Map or Accessible Stop List */}
      {viewMode === "map" ? (
        <div className="relative flex-1 min-h-0">
          {/* Quick Floating Controls positioned strictly inside map canvas */}
          <div className="absolute top-3 left-3 z-[1000]">
            <button
              type="button"
              onClick={() => push("contact-dispatch")}
              className="bg-white/95 backdrop-blur-sm shadow-md border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 flex items-center gap-1.5 hover:bg-slate-50 transition-colors cursor-pointer"
              aria-label="Contact Dispatch"
            >
              <AppIcon name="phone" size={13} className="text-green" />
              <span>Contact Dispatch</span>
            </button>
          </div>

          <div className="absolute top-3 right-3 z-[1000]">
            <button
              type="button"
              onClick={() => setViewMode("list")}
              className="bg-white/95 backdrop-blur-sm shadow-md border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 flex items-center gap-1.5 hover:bg-slate-50 transition-colors cursor-pointer"
              aria-label="Switch to list view"
            >
              <AppIcon name="list" size={14} />
              <span>List view</span>
            </button>
          </div>

          <DriverMap
            stopIds={currentTripSequence}
            currentStopId={currentOutletId}
            completedStopIds={completedStopIds}
            flaggedStopIds={flaggedStopIds}
            failedStopIds={failedStopIds}
            onStopClick={(outletId) => {
              const stopIdx = currentTripSequence.indexOf(outletId);
              // Sequential rule: can only view current or review past stops
              if (stopIdx <= currentStopIndex) {
                const s = currentTripStops.find((x) => x.outletId === outletId);
                if (s) push("stop-detail", { seq: String(s.seq) });
              }
            }}
            className="absolute inset-0"
          />
        </div>
      ) : (
        <div className="flex-1 min-h-0 flex flex-col bg-slate-50">
          {/* List Subheader - positioned below TopBar and never covering it */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-white border-b border-slate-200 shrink-0 shadow-xs">
            <div>
              <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Route Stops ({currentTripSequence.length})
              </h2>
              <span className="text-[11px] text-slate-500">
                Stop {currentStopIndex + 1} is active · Sequential access
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => push("contact-dispatch")}
                className="bg-slate-100 hover:bg-slate-200 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-700 flex items-center gap-1 transition-colors cursor-pointer"
                aria-label="Contact dispatch"
              >
                <AppIcon name="phone" size={13} className="text-green" />
                <span>Dispatch</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode("map")}
                className="bg-white border border-slate-200 shadow-sm px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-700 flex items-center gap-1.5 hover:bg-slate-50 transition-colors cursor-pointer"
                aria-label="Switch to map view"
              >
                <AppIcon name="map" size={14} />
                <span>Map view</span>
              </button>
            </div>
          </div>

          {/* Sequential Stops Scrollable Area */}
          <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-2">
            {currentTripSequence.map((outletId, index) => {
              const stopItem = currentTripStops.find((s) => s.outletId === outletId);
              const isCurrent = index === currentStopIndex;
              const isPast = index < currentStopIndex;
              const isUpcoming = index > currentStopIndex;

              // Strict temporal logic: upcoming stops CANNOT be marked failed or delivered!
              const isCompleted = isPast && completedStopIds.includes(outletId);
              const isFlagged = isPast && flaggedStopIds.includes(outletId);
              const isFailed = isPast && failedStopIds.includes(outletId);

              return (
                <div
                  key={outletId}
                  className={`w-full p-3 rounded-xl border flex items-center justify-between transition-colors ${
                    isCurrent
                      ? "bg-white border-green shadow-sm ring-1 ring-green/30"
                      : isPast
                        ? "bg-white/80 border-slate-200"
                        : "bg-slate-100/70 border-slate-200/80 opacity-75"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span
                      className={`w-7 h-7 shrink-0 rounded-full flex items-center justify-center text-xs font-bold ${
                        isCurrent
                          ? "bg-green text-white ring-2 ring-green/30"
                          : isPast
                            ? isFailed
                              ? "bg-rose-100 text-rose-700"
                              : isFlagged
                                ? "bg-amber-100 text-amber-700"
                                : "bg-emerald-100 text-emerald-800"
                            : "bg-slate-200 text-slate-500"
                      }`}
                    >
                      {isCompleted ? "✓" : isFailed ? "✕" : index + 1}
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-slate-900 text-sm">
                          {outletId}
                        </span>
                        {isUpcoming && (
                          <span className="text-[10px] text-slate-400 font-medium bg-slate-200/60 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                            <Lock size={9} /> Locked
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-slate-500 block truncate max-w-[170px]">
                        {stopItem?.name ?? outletId}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 text-right text-xs shrink-0">
                    {isCurrent && (
                      <span className="text-green font-bold bg-green-fill px-2 py-0.5 rounded-full border border-green/20">
                        Current
                      </span>
                    )}
                    {isCompleted && (
                      <span className="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        Delivered
                      </span>
                    )}
                    {isFlagged && (
                      <span className="text-amber-700 font-medium bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        Partial
                      </span>
                    )}
                    {isFailed && (
                      <span className="text-rose-700 font-medium bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                        Failed
                      </span>
                    )}
                    {isUpcoming && (
                      <span className="text-slate-400 text-[11px] font-medium">
                        Upcoming
                      </span>
                    )}

                    {/* Action buttons - strictly sequential! */}
                    {isCurrent ? (
                      <button
                        type="button"
                        onClick={() => {
                          if (stopItem) push("stop-detail", { seq: String(stopItem.seq) });
                        }}
                        className="ml-1 text-xs font-semibold text-green bg-green-fill hover:bg-green/20 px-2.5 py-1 rounded-md border border-green/30 cursor-pointer"
                      >
                        Action
                      </button>
                    ) : isPast ? (
                      <button
                        type="button"
                        onClick={() => {
                          if (stopItem) push("stop-detail", { seq: String(stopItem.seq) });
                        }}
                        className="ml-1 text-xs font-medium text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 px-2 py-1 rounded-md cursor-pointer"
                      >
                        Review
                      </button>
                    ) : (
                      <button
                        type="button"
                        disabled
                        title="Complete preceding stops first. Route is sequential."
                        className="ml-1 text-xs font-medium text-slate-400 bg-slate-100/50 px-2 py-1 rounded-md cursor-not-allowed"
                      >
                        Locked
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Persistent Bottom Sheet docked at bottom for the current stop */}
      {stop && (
        <div className="shrink-0 z-30 w-full">
          <BottomSheet
            stop={stop}
            etaMin={12}
            windowClosingMin={43}
            onMarkArrived={() => push("mark-arrived", { seq: String(stop.seq) })}
            onChat={() => push("chat", { outletId: stop.outletId })}
            onCall={() => push("call-overlay", { outletId: stop.outletId })}
            onDetails={() => push("stop-detail", { seq: String(stop.seq) })}
            onFailed={() =>
              push("failed-reason", { outletId: stop.outletId, seq: String(stop.seq) })
            }
            onContactDispatch={() => push("contact-dispatch")}
          />
        </div>
      )}
    </div>
  );
}
