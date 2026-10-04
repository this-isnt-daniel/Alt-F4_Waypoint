import React, { useState } from 'react';
import { Check, AlertTriangle, ChevronDown, ChevronUp, X, ArrowRight } from 'lucide-react';
import { ORDER_HISTORY, DEFERRED_ORDERS } from '../data/orders';

const OUTCOME_STYLE = {
  confirmed: { label: 'Delivered',  bg: 'bg-brand-50',  text: 'text-brand-700',  border: 'border-brand-200' },
  partial:   { label: 'Partial',    bg: 'bg-amber-50',  text: 'text-amber-700',  border: 'border-amber-200' },
  deferred:  { label: 'Deferred',   bg: 'bg-rose-50',   text: 'text-rose-600',   border: 'border-rose-200'  },
};

const ISSUE_TYPES = [
  { id: 'short',   label: 'Short quantity' },
  { id: 'damaged', label: 'Damaged'        },
  { id: 'wrong',   label: 'Wrong item'     },
  { id: 'missing', label: 'Missing'        },
  { id: 'other',   label: 'Other'          },
];

export default function ReceiptsTab({ isConfirmed, onNavigate }) {
  const [expandedId, setExpandedId]       = useState(null);
  const [reportingId, setReportingId]     = useState(null);

  const toggle = (id) => setExpandedId((prev) => (prev === id ? null : id));

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-screen-md mx-auto px-4 md:px-6 py-5 space-y-5 pb-10">
        <div className="flex items-center justify-between">
          <h2 className="text-[19px] font-bold text-slate-900">Receipts &amp; Deferrals</h2>
          <button type="button" onClick={() => onNavigate && onNavigate('progress')} className="text-[11px] font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-100 hover:border-emerald-200 px-3 py-1.5 rounded-full transition-colors flex items-center gap-1.5 cursor-pointer">
            2 orders in progress today <ArrowRight size={12} strokeWidth={2.5} />
          </button>
        </div>

        <div className="pt-2 space-y-8">
          {/* RECEIVED ORDERS */}
          <section>
            <button onClick={() => onNavigate && onNavigate('history-received')} className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 hover:text-emerald-700 transition-colors cursor-pointer group">
              Received Orders <ArrowRight size={10} strokeWidth={3} className="opacity-0 group-hover:opacity-100 transition-opacity -ml-0.5" />
            </button>
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm divide-y divide-slate-50 overflow-hidden">
              
              {/* ORD-1029 */}
              <div>
                <button type="button" onClick={() => toggle('ORD-1029')} className="w-full px-5 py-4 flex items-center justify-between text-[14px] hover:bg-slate-50/50 transition-colors text-left">
                  <span className="text-slate-700">ORD-1029 · Thu, Oct 1</span>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <span className="font-semibold text-[#b45309]">Received with exceptions</span>
                    <ChevronDown size={16} className={`text-slate-400 transition-transform ${expandedId === 'ORD-1029' ? 'rotate-180' : ''}`} />
                  </div>
                </button>
                {expandedId === 'ORD-1029' && (
                  <div className="px-5 pb-4 pt-2 bg-slate-50/30 border-t border-slate-50">
                    <div className="space-y-3">
                      <div className="bg-white border border-slate-200 rounded-lg px-3 py-2.5 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <p className="text-[13px] font-semibold text-slate-900">Butter 200g Salted</p>
                          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                            Short quantity
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-[12px] text-slate-500">
                          <span>Ordered: <span className="font-semibold text-slate-800">12</span></span>
                          <span>Received: <span className="font-semibold text-amber-700">10</span></span>
                          <span className="font-semibold text-slate-600">Short by 2</span>
                        </div>
                        <p className="text-[11px] text-slate-400 pt-0.5">
                          Loader note: Damaged during loading
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* ORD-1011 */}
              <div>
                <button type="button" onClick={() => toggle('ORD-1011')} className="w-full px-5 py-4 flex items-center justify-between text-[14px] hover:bg-slate-50/50 transition-colors text-left">
                  <span className="text-slate-700">ORD-1011 · Thu, Oct 1</span>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <span className="font-semibold text-[#b45309]">Received with exceptions</span>
                    <ChevronDown size={16} className={`text-slate-400 transition-transform ${expandedId === 'ORD-1011' ? 'rotate-180' : ''}`} />
                  </div>
                </button>
                {expandedId === 'ORD-1011' && (
                  <div className="px-5 pb-4 pt-2 bg-slate-50/30 border-t border-slate-50">
                    <div className="space-y-3">
                      <div className="bg-white border border-slate-200 rounded-lg px-3 py-2.5 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <p className="text-[13px] font-semibold text-slate-900">Cream Cracker 500g Munchee</p>
                          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                            Short quantity
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-[12px] text-slate-500">
                          <span>Ordered: <span className="font-semibold text-slate-800">24</span></span>
                          <span>Received: <span className="font-semibold text-amber-700">23</span></span>
                          <span className="font-semibold text-slate-600">Short by 1</span>
                        </div>
                        <p className="text-[11px] text-slate-400 pt-0.5">
                          Loader note: Damaged during loading
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* ORD-1041 */}
              <div>
                <button type="button" onClick={() => toggle('ORD-1041')} className="w-full px-5 py-4 flex items-center justify-between text-[14px] hover:bg-slate-50/50 transition-colors text-left">
                  <span className="text-slate-700">ORD-1041 · Thu, Oct 1</span>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <span className="font-semibold text-[#059669]">Received in full</span>
                    <ChevronDown size={16} className={`text-slate-400 transition-transform ${expandedId === 'ORD-1041' ? 'rotate-180' : ''}`} />
                  </div>
                </button>
                {expandedId === 'ORD-1041' && (
                  <div className="px-5 pb-4 pt-2 bg-slate-50/30 border-t border-slate-50">
                    <div className="flex items-center gap-2 py-2 text-[13px] text-[#059669]">
                      <Check size={16} strokeWidth={2.5} />
                      <span>All units received in good condition.</span>
                    </div>
                  </div>
                )}
              </div>

            </div>
          </section>

          {/* MISSING & DAMAGED GOODS */}
          <section>
            <button onClick={() => onNavigate && onNavigate('history-missing-damaged')} className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 hover:text-emerald-700 transition-colors cursor-pointer group">
              Missing &amp; Damaged Goods <ArrowRight size={10} strokeWidth={3} className="opacity-0 group-hover:opacity-100 transition-opacity -ml-0.5" />
            </button>
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm divide-y divide-slate-50 overflow-hidden">
              <div className="px-5 py-4 flex items-start justify-between">
                <div>
                  <p className="text-[14px] font-bold text-slate-900">Butter 200g Salted · 2 short</p>
                  <p className="text-[12.5px] text-slate-400 mt-0.5">Damaged during loading — noted by loader</p>
                </div>
                <span className="text-[12.5px] text-slate-400">ORD-1029</span>
              </div>
              <div className="px-5 py-4 flex items-start justify-between">
                <div>
                  <p className="text-[14px] font-bold text-slate-900">Cream Cracker 500g Munchee · 1 short</p>
                  <p className="text-[12.5px] text-slate-400 mt-0.5">Damaged during loading — noted by loader</p>
                </div>
                <span className="text-[12.5px] text-slate-400">ORD-1011</span>
              </div>
            </div>
          </section>

          {/* DEFERRALS */}
          <section>
            <button onClick={() => onNavigate && onNavigate('history-deferrals')} className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 hover:text-emerald-700 transition-colors cursor-pointer group">
              Deferrals <ArrowRight size={10} strokeWidth={3} className="opacity-0 group-hover:opacity-100 transition-opacity -ml-0.5" />
            </button>
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
              <p className="text-[14px] font-bold text-slate-900">ORD-1038 · Chilled <span className="font-normal text-slate-800">— moved to</span> Fri, Oct 2</p>
              <p className="text-[12.5px] text-slate-400 mt-0.5">Fleet capacity was short; Fresh outlets prioritized by order age.</p>
            </div>
          </section>
        </div>
      </div>

      {/* ── Report Issue Modal ── */}
      {reportingId && (
        <ReportIssueModal
          orderId={reportingId}
          onClose={() => setReportingId(null)}
        />
      )}
    </div>
  );
}

function PendingIssueCard({ order, onReport }) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 sm:px-5 py-4 mb-2">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <AlertTriangle size={16} className="text-amber-500 shrink-0" />
          <div className="min-w-0">
            <p className="text-[13px] font-semibold text-slate-900 leading-snug">{order.id} — Partial delivery</p>
            <p className="text-[12px] text-slate-500 mt-0.5 leading-tight">
              {order.totalReceived}/{order.totalOrdered} received · {order.issues.length} item{order.issues.length !== 1 ? 's' : ''} affected
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onReport}
          className="shrink-0 h-8 px-3.5 flex items-center justify-center bg-amber-600 hover:bg-amber-700 text-white text-[12px] font-semibold rounded-lg transition-colors"
        >
          Report
        </button>
      </div>
      {order.issues.map((issue, i) => (
        <div key={i} className="mt-3 pt-3 border-t border-amber-200">
          <IssueDetail issue={issue} />
        </div>
      ))}
    </div>
  );
}

function IssueDetail({ issue }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg px-3 py-2.5 space-y-1.5">
      <div className="flex items-center justify-between">
        <p className="text-[13px] font-semibold text-slate-900">{issue.item}</p>
        <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 capitalize">
          {issue.type}
        </span>
      </div>
      <div className="flex items-center gap-4 text-[12px] text-slate-500">
        <span>Ordered: <span className="font-semibold text-slate-800">{issue.ordered}</span></span>
        <span>Received: <span className="font-semibold text-amber-700">{issue.received}</span></span>
        <span className="font-semibold text-slate-600">Short by {issue.ordered - issue.received}</span>
      </div>
      {issue.loaderNote && (
        <p className="text-[11px] text-slate-400 pt-0.5">
          Loader note: {issue.loaderNote}
        </p>
      )}
    </div>
  );
}

function ReportIssueModal({ orderId, onClose }) {
  const [step, setStep]     = useState('type');    // 'type' | 'detail' | 'done'
  const [issueType, setIssueType] = useState(null);
  const [item, setItem]     = useState('');
  const [ordered, setOrdered] = useState('');
  const [received, setReceived] = useState('');

  const submit = async () => {
    try {
      const { safeStorage } = await import('@/lib/security');
      const token = safeStorage.get('token');
      if (token) {
        const { apiFetch } = await import('@/lib/api');
        await apiFetch(`/store-manager/orders/${orderId}/receipt`, {
          method: 'POST',
          body: JSON.stringify({
            client_op_id: `receipt-${Date.now()}`,
            pod_id: `POD-${orderId}`,
            items_ok: false,
            discrepancies: [
              {
                product_id: item || 'PROD-F01',
                expected_qty: ordered ? parseInt(ordered, 10) : undefined,
                actual_qty: received ? parseInt(received, 10) : undefined,
                reason_code: issueType || 'missing',
                note: `Reported issue: ${issueType}`
              }
            ]
          })
        });
      }
    } catch (err) {
      console.warn('Backend receipt report notification:', err);
    }
    setStep('done');
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-end md:items-center justify-center p-0 md:p-4">
      <div className="bg-white w-full md:max-w-md md:rounded-2xl rounded-t-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-5 pt-5 pb-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-[16px] font-bold text-slate-900">Report an issue</h2>
            <p className="text-[12px] text-slate-400 mt-0.5">{orderId}</p>
          </div>
          <button type="button" onClick={onClose} className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        {step === 'done' ? (
          <div className="px-5 py-8 text-center">
            <div className="w-12 h-12 rounded-full bg-brand-100 flex items-center justify-center mx-auto mb-3">
              <Check size={22} className="text-brand-600" strokeWidth={2.5} />
            </div>
            <p className="text-[15px] font-bold text-slate-900">Issue reported</p>
            <p className="text-[13px] text-slate-500 mt-1">Your report has been submitted.</p>
            <button
              type="button"
              onClick={onClose}
              className="mt-5 w-full h-10 border border-slate-200 rounded-xl text-[13px] font-semibold text-slate-700 hover:bg-slate-50"
            >
              Close
            </button>
          </div>
        ) : step === 'type' ? (
          <div className="px-5 py-4 space-y-3">
            <p className="text-[13px] font-semibold text-slate-700">What's the issue?</p>
            <div className="grid grid-cols-2 gap-2">
              {ISSUE_TYPES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => { setIssueType(t.id); setStep('detail'); }}
                  className="h-10 border border-slate-200 rounded-xl text-[13px] font-semibold text-slate-700 hover:border-brand-400 hover:text-brand-700 hover:bg-brand-50/30 transition-colors"
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* detail step */
          <div className="px-5 py-4 space-y-3">
            <p className="text-[13px] font-semibold text-slate-700 capitalize">{ISSUE_TYPES.find((t) => t.id === issueType)?.label}</p>

            <div>
              <label className="block text-[12px] font-semibold text-slate-500 mb-1">Item name</label>
              <input
                type="text"
                value={item}
                onChange={(e) => setItem(e.target.value)}
                placeholder="e.g. Butter 200g Salted"
                className="w-full h-10 px-3 border border-slate-200 rounded-xl text-[13px] focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            {(issueType === 'short' || issueType === 'damaged') && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[12px] font-semibold text-slate-500 mb-1">Ordered</label>
                  <input
                    type="number"
                    value={ordered}
                    onChange={(e) => setOrdered(e.target.value)}
                    className="w-full h-10 px-3 border border-slate-200 rounded-xl text-[13px] text-center font-bold focus:outline-none focus:ring-2 focus:ring-brand-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                </div>
                <div>
                  <label className="block text-[12px] font-semibold text-slate-500 mb-1">Received</label>
                  <input
                    type="number"
                    value={received}
                    onChange={(e) => setReceived(e.target.value)}
                    className="w-full h-10 px-3 border border-slate-200 rounded-xl text-[13px] text-center font-bold focus:outline-none focus:ring-2 focus:ring-brand-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-1">
              <button
                type="button"
                onClick={() => setStep('type')}
                className="flex-1 h-10 border border-slate-200 rounded-xl text-[13px] font-semibold text-slate-600 hover:bg-slate-50"
              >
                Back
              </button>
              <button
                type="button"
                onClick={submit}
                disabled={!item.trim()}
                className="flex-[2] h-10 bg-slate-900 text-white rounded-xl text-[13px] font-semibold hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Submit report
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
