import React, { useState, useEffect } from 'react';
import { X, Lock, AlertTriangle, CheckCircle2 } from 'lucide-react';

/**
 * Authentic Vercel Geist Spinner component in primary green theme.
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

export default function RecoveryPlanModal({
  isOpen,
  onClose,
  onAdjustInWorkbench,
  onConfirmRecovery
}) {
  const [isLoading, setIsLoading] = useState(true);

  // Trigger 2.5s Geist loading state when recovery modal opens
  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      const timer = setTimeout(() => {
        setIsLoading(false);
      }, 2500);
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
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                  Verify the recovery plan
                </h2>
              </div>
              <p className="text-xs text-slate-500 font-medium mt-1">
                Peliyagoda Hub · mid-shift disruption recovery · 2 vehicles lost (VEH011, VEH006)
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
                Calculating recovery routes...
              </p>
            </div>
          </div>
        ) : (
          /* Loaded Recovery Plan Body */
          <>
            <div className="px-7 pb-4 overflow-y-auto flex-1 space-y-5 animate-in fade-in duration-200">
              {/* Top Two Summary Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {/* Recovered Card */}
                <div className="bg-[#EDF7F1] border border-[#D1F2DD] rounded-2xl p-4 flex flex-col justify-between">
                  <span className="text-xs font-semibold text-[#059669]">Re-slotted onto Fleet</span>
                  <div className="mt-1">
                    <p className="text-2xl font-bold text-[#0B2019] tracking-tight">3 of 5 orders</p>
                    <p className="text-xs text-[#065F46] font-medium mt-0.5">Assigned to VEH014, VEH009 & VEH041</p>
                  </div>
                </div>

                {/* Deferred Card */}
                <div className="bg-[#FEF5EE] border border-[#FDE4D0] rounded-2xl p-4 flex flex-col justify-between">
                  <span className="text-xs font-semibold text-[#9A4B1A]">Deferred to Next Wave</span>
                  <div className="mt-1">
                    <p className="text-2xl font-bold text-[#7A3611] tracking-tight">2 orders deferred</p>
                    <p className="text-xs text-[#9A4B1A] font-medium mt-0.5">1 window closed · 1 POD quarantine</p>
                  </div>
                </div>
              </div>

              {/* Deferred Breakdown Section */}
              <div className="pt-1">
                <h3 className="text-xs font-bold text-slate-900 mb-3 tracking-normal">
                  Deferred · 2 orders · 830kg · 3.2 m³
                </h3>

                <div className="divide-y divide-slate-100">
                  {/* Deferred Order 1 */}
                  <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-mono font-bold text-xs text-slate-300">ORD-30088</span>
                        <span className="text-xs font-bold text-slate-800">Maharagama Central</span>
                        <span className="font-mono text-xs font-bold text-slate-600">OUT-3012</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 font-normal">
                        16 crates fresh chilled chicken · 390 kg · 1.5 m³
                      </p>
                    </div>
                    <div className="text-left sm:text-right flex-shrink-0">
                      <span className="text-xs text-slate-500 block">Fresh window closed before departure</span>
                      <div className="sm:text-right mt-0.5">
                        <span className="text-xs font-bold text-[#B45309]">Unavoidable</span>
                      </div>
                    </div>
                  </div>

                  {/* Deferred Order 2 */}
                  <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-mono font-bold text-xs text-slate-300">ORD-30095</span>
                        <span className="text-xs font-bold text-slate-800">Mount Lavinia Hub</span>
                        <span className="font-mono text-xs font-bold text-slate-600">OUT-5021</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 font-normal">
                        18 crates cold-chain dairy packs · 440 kg · 1.7 m³
                      </p>
                    </div>
                    <div className="text-left sm:text-right flex-shrink-0">
                      <span className="text-xs text-slate-500 block">Cold-chain breach en-route; quarantined</span>
                      <div className="sm:text-right mt-0.5">
                        <span className="text-xs font-bold text-slate-700">Quarantined</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Re-slotted Recovery Trips Strip */}
              <div className="rounded-2xl bg-[#EDF7F1] border border-[#D1F2DD] p-3.5 space-y-2 text-xs">
                <span className="font-bold text-[#065F46] block">
                  Active Recovery Trips (Filling open vehicle capacity without altering loaded stops)
                </span>
                <div className="space-y-1.5 text-slate-700">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold">VEH014 · Van Reefer</span>
                    <span className="text-slate-500">Trip 1 of 2 → OUT-4089 Nugegoda</span>
                    <span className="font-mono font-bold text-emerald-700">07:45 AM - 11:15 AM</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold">VEH009 · Truck Reefer</span>
                    <span className="text-slate-500">Trip 2 of 2 → OUT-2041 Wattala</span>
                    <span className="font-mono font-bold text-emerald-700">07:15 AM - 11:00 AM</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold">VEH041 · Truck Ambient</span>
                    <span className="text-slate-500">Trip 1 of 2 → OUT-1029 Liberty Plaza</span>
                    <span className="font-mono font-bold text-emerald-700">08:00 AM - 11:45 AM</span>
                  </div>
                </div>
              </div>

              {/* Warning Notice Box with Lock */}
              <div className="rounded-2xl bg-[#FEF5EE] border border-[#FDE4D0] p-3.5 flex items-start gap-2.5 text-xs text-[#7A3611] leading-relaxed">
                <Lock size={15} className="text-[#9A4B1A] flex-shrink-0 mt-0.5" />
                <p className="font-medium">
                  <strong>This locks Recovery Plan v2, updates manifests in Driver app, and notifies loaders. It can't be edited afterward.</strong>
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white">
              <div className="flex items-center gap-4 text-xs font-semibold text-slate-700">
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    if (onAdjustInWorkbench) onAdjustInWorkbench();
                  }}
                  className="hover:text-slate-900 underline cursor-pointer transition-colors"
                >
                  Adjust in workbench
                </button>
              </div>

              <button
                type="button"
                onClick={() => {
                  onClose();
                  if (onConfirmRecovery) onConfirmRecovery();
                }}
                className="px-6 py-2.5 rounded-xl bg-[#059669] hover:bg-[#047857] active:bg-[#065F46] text-white text-xs font-bold transition shadow-xs cursor-pointer whitespace-nowrap self-end sm:self-center"
              >
                Confirm & lock recovery plan
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
