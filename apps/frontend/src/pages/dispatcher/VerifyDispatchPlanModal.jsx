import React, { useState, useEffect } from 'react';
import { X, Lock, ArrowDown, ChevronDown, ChevronUp } from 'lucide-react';

/**
 * Authentic Vercel Geist Spinner component.
 * Radiates 12 bar segments with staggered linear opacity animation.
 */
function GeistSpinner({ size = 20, color = '#059669' }) {
  const bars = Array.from({ length: 12 });
  return (
    <div
      className="relative inline-block"
      style={{ width: `${size}px`, height: `${size}px` }}
      aria-label="Loading"
      role="status"
    >
      {bars.map((_, i) => (
        <span
          key={i}
          className="absolute rounded-full"
          style={{
            top: '0%',
            left: '46%',
            width: '8%',
            height: '28%',
            backgroundColor: color,
            transformOrigin: '50% 178%',
            transform: `rotate(${i * 30}deg)`,
            animation: 'geistSpinnerFade 1.2s linear infinite',
            animationDelay: `${-1.2 + (i * 0.1)}s`,
          }}
        />
      ))}
      <style>{`
        @keyframes geistSpinnerFade {
          0% { opacity: 1; }
          100% { opacity: 0.15; }
        }
      `}</style>
    </div>
  );
}

export default function VerifyDispatchPlanModal({
  isOpen,
  onClose,
  onAdjustInWorkbench,
  onManualAllocation,
  onConfirmAndLock
}) {
  const [isLoading, setIsLoading] = useState(true);
  const [showPriorityDetails, setShowPriorityDetails] = useState(false);

  // Trigger 3-second Vercel Geist loading state whenever the modal opens
  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      setShowPriorityDetails(false);
      const timer = setTimeout(() => {
        setIsLoading(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 backdrop-blur-[2px] flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-3xl shadow-2xl border border-slate-200/90 w-full max-w-[700px] overflow-hidden flex flex-col max-h-[92vh] animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-7 pb-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                Verify the dispatch plan
              </h2>
              <p className="text-xs text-slate-500 font-medium mt-1">
                Peliyagoda Hub · deliveries for Fri, Oct 2 · 31 orders closed at 4:00 PM
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 rounded-full p-1 transition cursor-pointer"
              title="Close"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Loading State with Green-Themed Geist Spinner */}
        {isLoading ? (
          <div className="px-7 py-20 flex flex-col items-center justify-center flex-1 space-y-4 min-h-[360px] animate-in fade-in duration-150">
            <div className="w-14 h-14 rounded-2xl bg-[#EBF6F0] border border-[#DCF0E5] flex items-center justify-center shadow-2xs">
              <GeistSpinner size={30} color="#059669" />
            </div>

            <div className="text-center">
              <p className="text-sm font-bold text-[#0B2019] tracking-tight">
                Calculating routes...
              </p>
            </div>
          </div>
        ) : (
          /* Loaded Plan Body (Matched Pixel-for-Pixel with Target Design) */
          <>
            <div className="px-7 pb-4 overflow-y-auto flex-1 space-y-5 animate-in fade-in duration-200">
              {/* Top Two Summary Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {/* Placed Card */}
                <div className="bg-[#EDF7F1] border border-[#D1F2DD] rounded-2xl p-4 flex flex-col justify-between">
                  <span className="text-xs font-semibold text-[#059669]">Placed</span>
                  <div className="mt-1">
                    <p className="text-2xl font-bold text-[#0B2019] tracking-tight">28 of 31 orders</p>
                    <p className="text-xs text-[#065F46] font-medium mt-0.5">21 vehicles · 30 trips</p>
                  </div>
                </div>

                {/* Deferred Card */}
                <div className="bg-[#FEF5EE] border border-[#FDE4D0] rounded-2xl p-4 flex flex-col justify-between">
                  <span className="text-xs font-semibold text-[#9A4B1A]">Deferred</span>
                  <div className="mt-1">
                    <p className="text-2xl font-bold text-[#7A3611] tracking-tight">3 chilled orders</p>
                    <p className="text-xs text-[#9A4B1A] font-medium mt-0.5">Every reefer is deployed</p>
                  </div>
                </div>
              </div>

              {/* Deferred Breakdown Section */}
              <div className="pt-1">
                <h3 className="text-xs font-bold text-slate-900 mb-3 tracking-normal">
                  Deferred · 3 orders · 820kg · 3.5 m³
                </h3>

                <div className="divide-y divide-slate-100">
                  {/* Order 1: ORD-30302 */}
                  <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-mono font-bold text-xs text-slate-300">ORD-30302</span>
                        <span className="text-xs font-bold text-slate-800">Ja-Ela Central</span>
                        <span className="font-mono text-xs font-bold text-slate-600">OUT091</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 font-normal">
                        8 crates Pelwatte fresh milk · 120kg · 0.9 m³
                      </p>
                    </div>
                    <div className="text-left sm:text-right flex-shrink-0">
                      <span className="text-xs text-slate-500 block">Fresh window closes in 42 min</span>
                      <div className="flex items-center sm:justify-end gap-1.5 mt-0.5">
                        <span className="text-xs font-bold text-[#9A4B1A]">Your call</span>
                        <button
                          type="button"
                          onClick={onManualAllocation}
                          className="text-xs font-bold text-[#059669] hover:underline cursor-pointer transition-colors"
                        >
                          Assign manually →
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Order 2: ORD-30288 */}
                  <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-mono font-bold text-xs text-slate-300">ORD-30288</span>
                        <span className="text-xs font-bold text-slate-800">Kandana</span>
                        <span className="font-mono text-xs font-bold text-slate-600">OUT064</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 font-normal">
                        12 cases Highland butter 200g · 60kg · 0.5 m³
                      </p>
                    </div>
                    <div className="text-left sm:text-right flex-shrink-0">
                      <span className="text-xs text-slate-500 block">Fresh window closes in 55 min</span>
                      <div className="flex items-center sm:justify-end gap-1.5 mt-0.5">
                        <span className="text-xs font-bold text-[#9A4B1A]">Your call</span>
                        <button
                          type="button"
                          onClick={onManualAllocation}
                          className="text-xs font-bold text-[#059669] hover:underline cursor-pointer transition-colors"
                        >
                          Assign manually →
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Order 3: ORD-30244 */}
                  <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-mono font-bold text-xs text-slate-300">ORD-30244</span>
                        <span className="text-xs font-bold text-slate-800">Colombo Hub</span>
                        <span className="font-mono text-xs font-bold text-slate-600">OUT077</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 font-normal">
                        10 crates dairy · 640kg · 2.1 m³
                      </p>
                    </div>
                    <div className="text-left sm:text-right flex-shrink-0">
                      <span className="text-xs text-slate-500 block">Van-only outlet, no reefer van in pool</span>
                      <div className="sm:text-right mt-0.5">
                        <span className="text-xs font-bold text-slate-700">Unavoidable</span>
                      </div>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-slate-500 mt-3 font-normal">
                  Each deferred outlet gets a notice with its reason and moves to the front of tomorrow's queue.
                </p>
              </div>

              {/* Priority Outlets Strip */}
              <div className="rounded-2xl bg-[#EDF7F1] border border-[#D1F2DD] p-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#065F46]">
                    Priority outlets (3) · skipped yesterday, placed first today
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowPriorityDetails(!showPriorityDetails)}
                    className="font-bold text-[#059669] hover:underline cursor-pointer"
                  >
                    {showPriorityDetails ? 'Hide' : 'View all'}
                  </button>
                </div>

                {showPriorityDetails && (
                  <div className="mt-3 pt-2.5 border-t border-[#D1F2DD] space-y-2 animate-in fade-in">
                    <div className="flex items-center justify-between text-xs text-slate-700">
                      <span className="font-mono font-bold">OUT029 · Liberty Plaza Express</span>
                      <span className="text-slate-500">ORD-30190 · 12 crates dairy</span>
                      <span className="font-mono font-semibold text-slate-800">VEH014 · Trip 1</span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-700">
                      <span className="font-mono font-bold">OUT042 · Nugegoda Super</span>
                      <span className="text-slate-500">ORD-30182 · 18 crates produce</span>
                      <span className="font-mono font-semibold text-slate-800">VEH009 · Trip 1</span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-700">
                      <span className="font-mono font-bold">OUT015 · Kollupitiya Mart</span>
                      <span className="text-slate-500">ORD-30175 · 14 crates bakery</span>
                      <span className="font-mono font-semibold text-slate-800">VEH002 · Trip 1</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Warning Notice Box with Lock */}
              <div className="rounded-2xl bg-[#FEF5EE] border border-[#FDE4D0] p-3.5 flex items-start gap-2.5 text-xs text-[#7A3611] leading-relaxed">
                <Lock size={15} className="text-[#9A4B1A] flex-shrink-0 mt-0.5" />
                <p className="font-medium">
                  <strong>This locks all 30 trips and sends loading lists and deferral notices. It can't be edited afterward.</strong>
                </p>
              </div>
            </div>

            {/* Footer with Actions matching screenshot */}
            <div className="p-6 pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white">
              <div className="flex items-center gap-4 text-xs font-semibold text-slate-700">
                <button
                  type="button"
                  onClick={onAdjustInWorkbench}
                  className="hover:text-slate-900 underline cursor-pointer transition-colors"
                >
                  Adjust in workbench
                </button>
              </div>

              <button
                type="button"
                onClick={onConfirmAndLock}
                className="px-6 py-2.5 rounded-xl bg-[#059669] hover:bg-[#047857] active:bg-[#065F46] text-white text-xs font-bold transition shadow-xs cursor-pointer whitespace-nowrap self-end sm:self-center"
              >
                Confirm & lock all trips
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
