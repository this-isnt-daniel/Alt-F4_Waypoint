import React from 'react';
import { X, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function RecoveryPlanModal({
  isOpen,
  onClose,
  onConfirmRecovery
}) {
  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 backdrop-blur-[2px] flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-3xl shadow-2xl border border-slate-200/90 w-full max-w-[720px] overflow-hidden flex flex-col max-h-[92vh] animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-7 pb-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
                <h2 className="text-xl font-bold text-slate-900 tracking-tight">
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

          <p className="text-sm text-slate-800 leading-relaxed mt-4 font-normal">
            <strong className="font-bold text-slate-900">3 of 5</strong> orphaned orders are placed on 2 vehicles in open slots.{' '}
            <strong className="font-bold text-slate-900">2 orders are deferred — 1 fresh window closed, 1 en-route cold-chain breach.</strong>
          </p>
        </div>

        {/* Scrollable Content Body */}
        <div className="px-7 py-2 overflow-y-auto flex-1 divide-y divide-slate-100 space-y-4">
          {/* Section 1: Deferred */}
          <div className="pt-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-bold text-slate-900">Deferred</span>
              <span className="text-xs text-slate-500 font-normal">2 orders · 830 kg · 3.2 m³</span>
            </div>

            <div className="divide-y divide-slate-100">
              {/* Row 1 */}
              <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-slate-900">ORD-30088</span>
                    <span className="text-xs font-semibold text-slate-800">Maharagama Central</span>
                    <span className="font-mono text-[11px] text-slate-400 font-medium">OUT-3012</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5 font-normal">
                    16 crates fresh chilled whole chicken · 390 kg · 1.5 m³
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="text-xs text-slate-600">Fresh window closed before available departure slot. </span>
                  <span className="text-xs font-semibold text-[#B45309]">Unavoidable</span>
                </div>
              </div>

              {/* Row 2 */}
              <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-slate-900">ORD-30095</span>
                    <span className="text-xs font-semibold text-slate-800">Mount Lavinia Hub</span>
                    <span className="font-mono text-[11px] text-slate-400 font-medium">OUT-5021</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5 font-normal">
                    18 crates cold-chain dairy packs · 440 kg · 1.7 m³
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="text-xs text-slate-600">En-route cold-chain breach on A1 Highway; quarantined. </span>
                  <span className="text-xs font-semibold text-[#B45309]">Unavoidable</span>
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-500 mt-3 font-normal">
              Each outlet receives an automated deferral notice with its logged reason.
            </p>
          </div>

          {/* Section 2: Re-slotted Recovery Trips */}
          <div className="pt-4 pb-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-bold text-slate-900">Recovery trips</span>
              <span className="text-xs text-slate-500 font-normal">filling empty vehicle slots without altering existing manifests</span>
            </div>

            <div className="space-y-2.5">
              {/* Recovery Trip 1: VEH014 Trip 2 */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs">
                <div className="flex items-center gap-2.5">
                  <div className="flex items-center gap-1.5 font-mono font-bold text-slate-900">
                    <span>VEH014</span>
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                      Recovery
                    </span>
                  </div>
                  <span className="text-slate-400">•</span>
                  <span className="text-slate-700 font-semibold">Trip 2 of 2 (Reefer Van)</span>
                </div>
                <div className="text-slate-600 text-xs">
                  OUT-1029 Liberty Plaza & OUT-4089 Nugegoda (1,100 kg)
                </div>
                <div className="font-mono font-bold text-emerald-700 text-right">
                  09:30 AM – 11:45 AM
                </div>
              </div>

              {/* Recovery Trip 2: VEH016 Trip 1 */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs">
                <div className="flex items-center gap-2.5">
                  <div className="flex items-center gap-1.5 font-mono font-bold text-slate-900">
                    <span>VEH016</span>
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                      Recovery
                    </span>
                  </div>
                  <span className="text-slate-400">•</span>
                  <span className="text-slate-700 font-semibold">Trip 1 of 2 (Reefer Truck)</span>
                </div>
                <div className="text-slate-600 text-xs">
                  OUT-1044 Kollupitiya Central (840 kg)
                </div>
                <div className="font-mono font-bold text-emerald-700 text-right">
                  09:00 AM – 10:30 AM
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-7 pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white">
          <p className="text-xs text-slate-500 leading-snug max-w-sm font-normal">
            Confirming updates driver manifests in the mobile app, sends new Bay loading lists to Loaders, and sends deferral notices to affected outlets.
          </p>

          <div className="flex items-center gap-2.5 self-end sm:self-center">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 text-xs font-bold transition shadow-2xs cursor-pointer whitespace-nowrap"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => {
                onClose();
                if (onConfirmRecovery) onConfirmRecovery();
              }}
              className="px-5 py-2.5 rounded-xl bg-[#0F172A] hover:bg-[#1E293B] active:bg-[#020617] text-white text-xs font-bold transition shadow-sm cursor-pointer whitespace-nowrap"
            >
              Confirm & lock recovery plan
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
