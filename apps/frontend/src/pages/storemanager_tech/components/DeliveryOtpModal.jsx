import React, { useState } from 'react';
import { X, Truck, KeyRound, Check, Copy, ArrowRight, ShieldCheck } from 'lucide-react';

export default function DeliveryOtpModal({
  isOpen,
  onClose,
  otp = '482 910',
  orderId = 'ORD-2026-0929',
  driverName = 'Kamal Perera',
  vehicleNo = 'WP-CAD-8921',
  outletName = 'Nugegoda Outlet',
  onConfirmHandover
}) {
  const [copied, setCopied] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  if (!isOpen) return null;

  const rawOtp = otp.replace(/\s+/g, '');
  const digits = rawOtp.split('');

  const handleCopy = () => {
    navigator.clipboard?.writeText(rawOtp);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleConfirm = () => {
    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      onConfirmHandover?.();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div 
        className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-100 animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-slate-900">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <Truck size={18} />
            </div>
            <div>
              <h3 className="text-[15px] font-bold">Delivery Handover</h3>
              <p className="text-[11px] text-slate-500 font-medium">{outletName}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {/* Status info box */}
          <div className="bg-emerald-50/70 border border-emerald-100 rounded-xl p-3.5 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1.5 mb-0.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[12px] font-bold text-emerald-900 uppercase tracking-wide">Vehicle at Loading Bay</span>
              </div>
              <p className="text-[13px] font-semibold text-slate-800">{orderId} · {vehicleNo}</p>
              <p className="text-[12px] text-slate-500">Driver: {driverName}</p>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-bold text-emerald-700 bg-white px-2.5 py-1 rounded-full border border-emerald-200 shadow-xs">
                Awaiting OTP
              </span>
            </div>
          </div>

          {/* OTP Instruction & Display */}
          <div className="text-center space-y-3">
            <p className="text-[13px] text-slate-600">
              Provide this confirmation OTP to the driver to enter on their mobile app:
            </p>

            <div className="flex items-center justify-center gap-2 sm:gap-2.5 my-2">
              {digits.map((digit, i) => (
                <div
                  key={i}
                  className="w-11 h-13 sm:w-12 sm:h-14 bg-slate-50 border-2 border-emerald-500/80 rounded-xl flex items-center justify-center text-[24px] sm:text-[26px] font-black font-mono text-slate-900 shadow-sm"
                >
                  {digit}
                </div>
              ))}
            </div>

            <div className="flex items-center justify-center">
              <button
                type="button"
                onClick={handleCopy}
                className="text-[12px] font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1.5 px-3 py-1 rounded-md hover:bg-slate-100 transition-colors"
              >
                {copied ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
                <span>{copied ? 'OTP Copied' : 'Copy OTP'}</span>
              </button>
            </div>
          </div>

          <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 text-[12px] text-slate-500 leading-relaxed flex items-start gap-2">
            <ShieldCheck size={16} className="text-brand-600 shrink-0 mt-0.5" />
            <span>
              Once the driver enters this OTP on the Waypoint Driver mobile app, physical receipt is recorded and the order transitions directly to your Receipts &amp; Deferrals log.
            </span>
          </div>
        </div>

        {/* Footer actions */}
        <div className="px-6 py-4 bg-slate-50/70 border-t border-slate-100 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-[13px] font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-200/50 rounded-lg transition-colors"
          >
            Close
          </button>
          <button
            type="button"
            disabled={isVerifying}
            onClick={handleConfirm}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[13px] rounded-lg shadow-sm transition-all flex items-center gap-2 active:scale-95 disabled:opacity-60 cursor-pointer"
          >
            {isVerifying ? (
              <span>Verifying Handover...</span>
            ) : (
              <>
                <span>Confirm Handover &amp; View Receipts</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
