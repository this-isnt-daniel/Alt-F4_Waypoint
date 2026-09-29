import React from 'react';
import { X, CheckCircle2, AlertTriangle, Truck, Clock, PackageCheck, Layers } from 'lucide-react';

export default function OrderConfirmationModal({
  isOpen,
  onClose,
  outlet,
  orderLines,
  totals,
  isPastCutoff,
  onFinalSubmit,
}) {
  if (!isOpen) return null;

  const { totalUnits, estWeightKg, estVolumeM3, dryItems, chilledItems, dispatchesCount } = totals;
  const isFresh = outlet?.brand === 'Waypoint Fresh';

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 backdrop-blur-[2px] flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-3xl shadow-2xl border border-slate-200/90 w-full max-w-[620px] overflow-hidden flex flex-col max-h-[92vh] animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 pb-4 border-b border-slate-100 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                Review & Confirm Order
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {outlet?.name} · {outlet?.brand}
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

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {/* Scheduling Notice / Cutoff Banner */}
          <div
            className={`p-3.5 rounded-2xl border flex items-start gap-3 text-xs ${
              isPastCutoff
                ? 'bg-amber-50/80 border-amber-200 text-amber-900'
                : 'bg-emerald-50/80 border-emerald-200 text-emerald-900'
            }`}
          >
            <Clock size={16} className={`shrink-0 mt-0.5 ${isPastCutoff ? 'text-amber-600' : 'text-emerald-600'}`} />
            <div>
              <p className="font-bold">
                {isPastCutoff
                  ? 'Past 4:00 PM Order Cutoff · Scheduled for Day +2'
                  : 'Submitted Before 4:00 PM Cutoff · Next Morning Delivery'}
              </p>
              <p className="mt-0.5 leading-relaxed text-[11px] opacity-90">
                {isPastCutoff
                  ? 'Orders placed after 4:00 PM close enter the subsequent planning run. Scheduled delivery: Saturday before store opening.'
                  : `Your confirmed order will enter the 4 PM Dispatcher Queue. Expected arrival: Tomorrow morning before ${outlet?.mustArriveBefore || '08:00 AM'}.`}
              </p>
            </div>
          </div>

          {/* Dual Dispatch Allocation Plan for Fresh */}
          {isFresh && dispatchesCount > 1 && (
            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800 flex items-center gap-1.5 uppercase text-[11px] tracking-wide">
                  <Layers size={13} className="text-[#059669]" />
                  Dual-Vehicle Dispatch Allocation
                </span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                  2 Separate Trucks
                </span>
              </div>
              <p className="text-slate-600 text-[11px]">
                Waypoint logistics automatically splits ambient groceries and cold-chain cargo to protect climate integrity:
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-white border border-slate-200 rounded-xl p-2.5">
                  <div className="flex items-center gap-1.5 font-bold text-slate-900 mb-1">
                    <Truck size={12} className="text-slate-600" />
                    <span>Dry Box Vehicle</span>
                  </div>
                  <p className="text-[11px] text-slate-500">{dryItems.length} lines (Groceries/Staples)</p>
                </div>
                <div className="bg-white border border-sky-200 rounded-xl p-2.5">
                  <div className="flex items-center gap-1.5 font-bold text-sky-900 mb-1">
                    <Truck size={12} className="text-sky-600" />
                    <span>Reefer Vehicle</span>
                  </div>
                  <p className="text-[11px] text-sky-600">{chilledItems.length} lines (Dairy/Poultry/Frozen)</p>
                </div>
              </div>
            </div>
          )}

          {/* Metric Totals Grid */}
          <div className="grid grid-cols-3 gap-2.5 text-center">
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-2.5">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Total Units</span>
              <span className="text-base font-bold text-slate-900 font-mono">{totalUnits}</span>
            </div>
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-2.5">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Gross Weight</span>
              <span className="text-base font-bold text-slate-900 font-mono">~{estWeightKg} kg</span>
            </div>
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-2.5">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Volume</span>
              <span className="text-base font-bold text-slate-900 font-mono">{estVolumeM3} m³</span>
            </div>
          </div>

          {/* Itemized Lines */}
          <div className="space-y-1.5">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide block pb-1">
              Order Items ({orderLines.length})
            </span>
            <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 border border-slate-200/70 rounded-xl bg-white text-xs">
              {orderLines.map((line) => (
                <div key={line.id} className="p-2.5 flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-slate-900">{line.name}</span>
                    <span className="text-[10px] text-slate-400 font-mono ml-2">{line.id}</span>
                    <p className="text-[11px] text-slate-500">{line.format}</p>
                  </div>
                  <div className="text-right font-mono font-bold text-slate-800">
                    {line.qty} {line.category === 'Hanging' ? 'racks' : 'cases'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 px-6 border-t border-slate-100 bg-slate-50/60 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-xl transition cursor-pointer"
          >
            Edit Order
          </button>
          <button
            type="button"
            onClick={() => {
              onFinalSubmit();
              onClose();
            }}
            className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 rounded-xl shadow-sm transition flex items-center gap-1.5 cursor-pointer"
          >
            <PackageCheck size={15} />
            <span>Confirm & Place Order</span>
          </button>
        </div>
      </div>
    </div>
  );
}
