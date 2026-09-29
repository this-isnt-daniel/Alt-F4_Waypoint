import React, { useState } from 'react';
import { X, CheckCircle2, AlertTriangle, AlertCircle, Snowflake, Truck, ShieldCheck, FileCheck } from 'lucide-react';

export default function InspectDeliveryModal({
  isOpen,
  onClose,
  vehicle,
  outlet,
  onConfirmReceipt,
}) {
  if (!isOpen || !vehicle) return null;

  // Initialize line items state with condition flags
  const [itemsStatus, setItemsStatus] = useState(() => {
    const initial = {};
    vehicle.products.forEach((p, idx) => {
      initial[idx] = { condition: 'accepted', damagedQty: 0, reason: '' };
    });
    return initial;
  });

  const [generalNotes, setGeneralNotes] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [receiptNumber, setReceiptNumber] = useState('');

  const handleConditionChange = (idx, condition) => {
    setItemsStatus((prev) => ({
      ...prev,
      [idx]: { ...prev[idx], condition },
    }));
  };

  const hasDiscrepancy = Object.values(itemsStatus).some(
    (item) => item.condition !== 'accepted'
  );

  const handleSignReceipt = () => {
    const recId = `REC-${Math.floor(10000 + Math.random() * 90000)}`;
    setReceiptNumber(recId);
    setIsSubmitted(true);
    if (onConfirmReceipt) {
      onConfirmReceipt({
        receiptId: recId,
        vehicleId: vehicle.id,
        driverName: vehicle.driver.name,
        hasDiscrepancy,
        itemsStatus,
        notes: generalNotes,
        timestamp: new Date().toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: true,
        }),
      });
    }
  };

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
        <div className="p-6 pb-4 border-b border-slate-100 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                {isSubmitted ? 'Delivery Receipt Confirmed' : 'Inspect & Accept Delivery'}
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {outlet?.name} · Driver: <strong className="text-slate-800">{vehicle.driver.name}</strong> ({vehicle.id} · {vehicle.vehicleType})
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

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-5">
          {isSubmitted ? (
            /* Confirmation State */
            <div className="py-6 flex flex-col items-center text-center space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 shadow-sm">
                <FileCheck size={32} />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Receipt Signed & Logged
              </h3>
              <p className="text-xs text-slate-500 max-w-sm">
                Digital Proof of Delivery verified with receiving PIN <strong className="font-mono text-slate-800">{outlet?.receivingPin}</strong>. Handshake completed with driver {vehicle.driver.name}.
              </p>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 w-full max-w-sm text-left text-xs font-mono">
                <div className="flex justify-between py-0.5">
                  <span className="text-slate-500">Receipt Ref:</span>
                  <span className="font-bold text-slate-800">{receiptNumber}</span>
                </div>
                <div className="flex justify-between py-0.5">
                  <span className="text-slate-500">Timestamp:</span>
                  <span className="text-slate-800">Today · {new Date().toLocaleTimeString()}</span>
                </div>
                <div className="flex justify-between py-0.5">
                  <span className="text-slate-500">Condition Status:</span>
                  <span className={hasDiscrepancy ? 'font-bold text-amber-600' : 'font-bold text-emerald-600'}>
                    {hasDiscrepancy ? 'Discrepancy Flagged' : 'All Items Verified Clean'}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-sm transition cursor-pointer"
              >
                Done
              </button>
            </div>
          ) : (
            /* Inspection Form */
            <>
              {/* Receiving PIN Handshake Card */}
              <div className="bg-slate-900 text-white rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0 border border-emerald-500/30">
                    <ShieldCheck size={22} />
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400">
                      Digital PoD Handshake
                    </span>
                    <p className="text-xs text-slate-300">
                      Give this 4-digit PIN to Driver <strong>{vehicle.driver.name}</strong> for terminal entry:
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <span className="font-mono text-xl font-extrabold tracking-widest bg-slate-800 border border-slate-700 px-3.5 py-1 rounded-xl text-emerald-300 shadow-inner">
                    {outlet?.receivingPin || '4829'}
                  </span>
                </div>
              </div>

              {/* Line Items Inspection Checklist */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                    Cargo Manifest Inspection
                  </span>
                  <span className="text-[11px] text-slate-500 font-medium">
                    {vehicle.products.length} line items
                  </span>
                </div>

                <div className="space-y-2.5">
                  {vehicle.products.map((item, idx) => {
                    const status = itemsStatus[idx] || { condition: 'accepted' };

                    return (
                      <div
                        key={idx}
                        className={`rounded-2xl border p-3.5 transition-all text-xs ${
                          status.condition === 'accepted'
                            ? 'bg-slate-50/50 border-slate-200'
                            : 'bg-amber-50/60 border-amber-300'
                        }`}
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-slate-900">{item.name}</span>
                              <span className="font-mono text-[10px] text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                                {item.orderNo}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-500 mt-0.5">
                              Quantity: <strong className="text-slate-800">{item.quantity}</strong> · Category: {item.category}
                            </p>
                          </div>

                          {/* Condition Selector */}
                          <div className="flex flex-wrap items-center gap-1.5">
                            {[
                              { id: 'accepted', label: 'Accepted', icon: CheckCircle2, color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
                              { id: 'damaged', label: 'Damaged', icon: AlertTriangle, color: 'text-amber-800 bg-amber-100 border-amber-300' },
                              { id: 'missing', label: 'Shortfall', icon: AlertCircle, color: 'text-rose-700 bg-rose-50 border-rose-200' },
                              { id: 'temperature', label: 'Temp Breach', icon: Snowflake, color: 'text-sky-700 bg-sky-50 border-sky-200' },
                            ].map((opt) => {
                              const isSelected = status.condition === opt.id;
                              const Icon = opt.icon;
                              return (
                                <button
                                  key={opt.id}
                                  type="button"
                                  onClick={() => handleConditionChange(idx, opt.id)}
                                  className={`px-2 py-1 rounded-lg text-[11px] font-semibold border flex items-center gap-1 transition cursor-pointer ${
                                    isSelected
                                      ? opt.color + ' ring-1 ring-current'
                                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                                  }`}
                                >
                                  <Icon size={12} />
                                  <span>{opt.label}</span>
                                </button>
                              );
                            })}
                          </div>
                        </div>

                        {status.condition !== 'accepted' && (
                          <div className="mt-2.5 pt-2 border-t border-amber-200/80">
                            <input
                              type="text"
                              placeholder="Specify discrepancy details (e.g. 2 crates crushed at curb / seal warm)..."
                              value={status.reason || ''}
                              onChange={(e) =>
                                setItemsStatus((prev) => ({
                                  ...prev,
                                  [idx]: { ...prev[idx], reason: e.target.value },
                                }))
                              }
                              className="w-full text-xs p-2 rounded-lg bg-white border border-amber-300 focus:outline-none focus:ring-1 focus:ring-amber-500 text-slate-800"
                            />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* General Delivery Notes */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  General Receiving Notes (Optional):
                </label>
                <textarea
                  rows={2}
                  value={generalNotes}
                  onChange={(e) => setGeneralNotes(e.target.value)}
                  placeholder="Note dock conditions, driver handover observations, or curb remarks..."
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-600 text-slate-800 resize-none"
                />
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        {!isSubmitted && (
          <div className="p-4 px-6 border-t border-slate-100 bg-slate-50/60 flex items-center justify-between gap-3">
            <span className="text-xs text-slate-500">
              {hasDiscrepancy ? (
                <span className="text-amber-700 font-semibold flex items-center gap-1">
                  <AlertTriangle size={13} />
                  Shortfall / damage will be filed with Dispatch
                </span>
              ) : (
                'Clean receipt verified against manifest'
              )}
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-xl transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSignReceipt}
                className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 rounded-xl shadow-sm transition flex items-center gap-1.5 cursor-pointer"
              >
                <CheckCircle2 size={14} />
                <span>Confirm & Sign Receipt</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
