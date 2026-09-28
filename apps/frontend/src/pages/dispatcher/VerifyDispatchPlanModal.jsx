import React from 'react';
import { X } from 'lucide-react';

export default function VerifyDispatchPlanModal({
  isOpen,
  onClose,
  onAdjustInWorkbench,
  onConfirmAndLock
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
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
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

          <p className="text-sm text-slate-800 leading-relaxed mt-4 font-normal">
            <strong className="font-bold text-slate-900">28 of 31</strong> orders are placed on 21 vehicles across 30 trips.{' '}
            <strong className="font-bold text-slate-900">3 chilled orders are deferred — every reefer is already deployed.</strong>
          </p>
        </div>

        {/* Scrollable Content Body */}
        <div className="px-7 py-2 overflow-y-auto flex-1 divide-y divide-slate-100 space-y-4">
          {/* Section 1: Deferred */}
          <div className="pt-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-bold text-slate-900">Deferred</span>
              <span className="text-xs text-slate-500 font-normal">3 orders · 820 kg · 3.5 m³</span>
            </div>

            <div className="divide-y divide-slate-100">
              {/* Row 1 */}
              <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-slate-900">ORD-30302</span>
                    <span className="text-xs font-semibold text-slate-800">Ja-Ela Central</span>
                    <span className="font-mono text-[11px] text-slate-400 font-medium">OUT091</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5 font-normal">
                    8 crates Pelwatte Fresh Milk · 120 kg · 0.9 m³
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="text-xs text-slate-600">Every reefer is full or out of Fresh time. </span>
                  <span className="text-xs font-semibold text-[#B45309]">Your call</span>
                </div>
              </div>

              {/* Row 2 */}
              <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-slate-900">ORD-30288</span>
                    <span className="text-xs font-semibold text-slate-800">Kandana</span>
                    <span className="font-mono text-[11px] text-slate-400 font-medium">OUT064</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5 font-normal">
                    12 cases Highland Butter 200g · 60 kg · 0.5 m³
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="text-xs text-slate-600">Every reefer is full or out of Fresh time. </span>
                  <span className="text-xs font-semibold text-[#B45309]">Your call</span>
                </div>
              </div>

              {/* Row 3 */}
              <div className="py-2.5 flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 sm:gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-slate-900">ORD-30244</span>
                    <span className="text-xs font-semibold text-slate-800">Colombo Hub</span>
                    <span className="font-mono text-[11px] text-slate-400 font-medium">OUT077</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5 font-normal">
                    10 crates dairy · 640 kg · 2.1 m³
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="text-xs text-slate-600">Van-only outlet needs a reefer van, and none is in today's pool. </span>
                  <span className="text-xs font-medium text-slate-500">Unavoidable</span>
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-500 mt-3 font-normal">
              Each outlet gets a deferral notice with its reason and moves to the front of tomorrow's queue.
            </p>
          </div>

          {/* Section 2: Priority Outlets */}
          <div className="pt-4 pb-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-bold text-slate-900">Priority outlets</span>
              <span className="text-xs text-slate-500 font-normal">skipped yesterday, placed first today</span>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-4 py-1 text-xs">
                <div className="flex items-center gap-3">
                  <span className="font-mono font-bold text-slate-900">OUT029</span>
                  <span className="font-semibold text-slate-800">Liberty Plaza Express</span>
                </div>
                <div className="text-slate-500">
                  ORD-30190 · 12 crates dairy
                </div>
                <div className="font-mono font-medium text-slate-800 text-right">
                  VEH014 · Trip 1
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-7 pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white">
          <p className="text-xs text-slate-500 leading-snug max-w-sm font-normal">
            Confirming sends loading lists to Loaders and deferral notices to the 3 outlets. The plan can’t be edited afterwards.
          </p>

          <div className="flex items-center gap-2.5 self-end sm:self-center">
            <button
              type="button"
              onClick={onAdjustInWorkbench}
              className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 text-xs font-bold transition shadow-2xs cursor-pointer whitespace-nowrap"
            >
              Adjust in workbench
            </button>
            <button
              type="button"
              onClick={onConfirmAndLock}
              className="px-5 py-2.5 rounded-xl bg-[#0F172A] hover:bg-[#1E293B] active:bg-[#020617] text-white text-xs font-bold transition shadow-sm cursor-pointer whitespace-nowrap"
            >
              Confirm & lock all trips
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
