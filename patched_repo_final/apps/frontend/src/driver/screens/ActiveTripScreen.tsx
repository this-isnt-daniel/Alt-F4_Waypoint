import { useState, useEffect, useRef } from "react";
import { useNavigator } from "@/router/navigator";
import { DriverMap } from "@/driver/components/DriverMap";
import { useDriverState } from "@/driver/state/useDriverState";
import { Check, X, LocateFixed } from "lucide-react";

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

  const currentOutletId =
    currentTripSequence[currentStopIndex] ?? currentTripSequence[0] ?? "OUT042";

  const [selectedOutletId, setSelectedOutletId] = useState<string | null>(currentOutletId);
  const [recenterTrigger, setRecenterTrigger] = useState(0);

  const displayOutletId = selectedOutletId;
  const stop = displayOutletId
    ? currentTripStops.find((s) => s.outletId === displayOutletId)
    : null;

  const isNextStop = displayOutletId === currentOutletId;
  const isTripComplete = currentStopIndex >= currentTripSequence.length;

  const windowCloses = stop?.window?.split("–")[1]?.trim() ?? "06:30";

  // For horizontal scroll auto-scroll to selected item (simplified approach)
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-slate-100 relative">
      {/* ── MAP ── */}
      <div className="flex-1 min-h-0 relative">
        <DriverMap
          stopIds={currentTripSequence}
          currentStopId={currentOutletId}
          selectedStopId={selectedOutletId || undefined}
          recenterTrigger={recenterTrigger}
          completedStopIds={completedStopIds}
          flaggedStopIds={flaggedStopIds}
          failedStopIds={failedStopIds}
          onStopClick={(outletId) => setSelectedOutletId(outletId)}
          className="absolute inset-0"
        />
      </div>

      {isTripComplete ? (
        <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-slate-200 shadow-[0_-4px_24px_rgba(0,0,0,0.06)] z-[1000] pb-[env(safe-area-inset-bottom)]">
          {/* ── TRIP COMPLETE SHEET ── */}
          <div className="px-5 pb-8 pt-6">
            <p className="text-[12px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
              TRIP COMPLETE
            </p>
            <p className="text-[22px] font-bold text-slate-900 leading-tight mb-4">
              {currentTripSequence.length} / {currentTripSequence.length} stops
            </p>
            
            <div className="flex gap-4 mb-6">
              <div>
                <span className="block text-[18px] font-bold text-slate-900">{completedStopIds.length}</span>
                <span className="text-[13px] font-medium text-slate-500">delivered</span>
              </div>
              <div>
                <span className="block text-[18px] font-bold text-slate-900">{flaggedStopIds.length}</span>
                <span className="text-[13px] font-medium text-slate-500">partial</span>
              </div>
              <div>
                <span className="block text-[18px] font-bold text-slate-900">{failedStopIds.length}</span>
                <span className="text-[13px] font-medium text-slate-500">not completed</span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => push("return-depot")}
              className="w-full bg-[#059669] text-white font-bold text-[15px] py-3.5 rounded-lg transition-colors active:scale-[0.98] cursor-pointer hover:bg-emerald-700"
            >
              RETURN TO DEPOT
            </button>
          </div>
        </div>
      ) : (
        <div className="absolute bottom-0 left-0 right-0 flex flex-col z-[1000] pointer-events-none">
          {/* ── EXPANDED PREVIEW (Slides up above strip) ── */}
          {stop && (
            <div className="bg-white px-5 pt-5 pb-5 rounded-t-xl shadow-[0_-8px_24px_rgba(0,0,0,0.08)] border-t border-slate-200 animate-in slide-in-from-bottom-4 duration-200 pointer-events-auto">
              <div className="flex justify-between items-start mb-1">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                    {isNextStop ? "Next Stop" : `Stop ${stop.seq}`}
                  </p>
                  <h2 className="text-[20px] font-bold text-slate-900 leading-tight">
                    {stop.outletId}
                  </h2>
                </div>
                <button 
                  onClick={() => setSelectedOutletId(null)}
                  className="p-1.5 -mr-2 -mt-1 text-slate-400 hover:text-slate-600 bg-slate-50 rounded-full"
                >
                  <X size={20} strokeWidth={2.5} />
                </button>
              </div>
              
              <p className="text-[15px] font-semibold text-slate-600 mb-3">{stop.name}</p>

              <div className="flex flex-col gap-1 mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-[15px] font-bold text-slate-900">12 min</span>
                  <span className="text-slate-300">·</span>
                  <span className="text-[15px] font-semibold text-slate-600">5.4 km</span>
                </div>
                <p className="text-[13px] font-medium text-slate-500">
                  Window {stop.window}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2 mb-5">
                {stop.temp && <span className="text-[12px] font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded">{stop.temp}</span>}
                {stop.dock && <span className="text-[12px] font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded">{stop.dock}</span>}
                {stop.parking !== "Normal" && <span className="text-[12px] font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded">{stop.parking}</span>}
              </div>

              <button
                type="button"
                onClick={() => push("stop-detail", { seq: String(stop.seq) })}
                className="w-full bg-white border-2 border-slate-200 text-slate-900 font-bold text-[14px] py-3.5 rounded-lg transition-colors active:scale-[0.98] cursor-pointer hover:bg-slate-50 hover:border-slate-300"
              >
                VIEW MORE DETAILS
              </button>
            </div>
          )}

          {/* ── MAP CONTROLS ── */}
          <div className="absolute right-4 bottom-[84px] pointer-events-auto flex flex-col gap-2 transition-transform">
            <button
              onClick={() => {
                setSelectedOutletId(null);
                setRecenterTrigger(c => c + 1);
              }}
              className="w-10 h-10 rounded-full bg-white shadow-[0_2px_12px_rgba(0,0,0,0.12)] border border-slate-100 flex items-center justify-center text-slate-700 hover:bg-slate-50 active:scale-95 transition-all"
            >
              <LocateFixed size={20} strokeWidth={2.5} className="text-[#059669]" />
            </button>
          </div>

          {/* ── HORIZONTAL STRIP ── */}
          <div className="pb-[env(safe-area-inset-bottom)] pointer-events-none">
            <div 
              ref={scrollContainerRef}
              className="flex overflow-x-auto snap-x snap-mandatory hide-scrollbar gap-2.5 px-4 py-3.5 items-center pointer-events-auto"
              style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
            >
              {currentTripSequence.map((outletId, idx) => {
                const isCompleted = completedStopIds.includes(outletId);
                const isCurrentOrNext = outletId === currentOutletId;
                const isSelected = outletId === selectedOutletId;
                const stopData = currentTripStops.find((s) => s.outletId === outletId);
                
                let cardClasses = "flex items-center gap-2 px-3.5 py-2.5 rounded-xl border-2 transition-all whitespace-nowrap snap-center shrink-0 cursor-pointer ";
                
                if (isCompleted) {
                  cardClasses += "bg-slate-50 border-slate-200 text-slate-500 opacity-60";
                } else if (isCurrentOrNext) {
                  cardClasses += "bg-emerald-50 border-[#059669] text-[#059669]";
                } else {
                  cardClasses += "bg-white border-slate-200 text-slate-700 shadow-[0_2px_8px_rgba(0,0,0,0.08)]";
                }
                
                if (isSelected && !isCompleted && !isCurrentOrNext) {
                   // Add a subtle highlight if selected and not already accented
                   cardClasses += " ring-2 ring-slate-400 ring-offset-1";
                }

                return (
                  <button
                    key={outletId}
                    onClick={() => {
                      setSelectedOutletId(outletId);
                      // Center the card in the scroll view
                      const btn = document.getElementById(`strip-card-${outletId}`);
                      if (btn && scrollContainerRef.current) {
                        const container = scrollContainerRef.current;
                        const scrollLeft = btn.offsetLeft - container.offsetWidth / 2 + btn.offsetWidth / 2;
                        container.scrollTo({ left: scrollLeft, behavior: 'smooth' });
                      }
                    }}
                    id={`strip-card-${outletId}`}
                    className={cardClasses}
                  >
                    {isCompleted ? (
                      <Check size={16} strokeWidth={3} className="text-slate-400" />
                    ) : (
                      <span className="font-bold text-[14px]">{idx + 1}</span>
                    )}
                    <span className="font-semibold text-[14px] tracking-tight truncate max-w-[180px]">
                      {stopData ? `${stopData.outletId} · ${stopData.name}` : outletId}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
