import React, { useState } from 'react';
import { Check, AlertTriangle, ChevronDown, ChevronUp, X } from 'lucide-react';
import { ORDER_HISTORY, DEFERRED_ORDERS } from '../data/orders';

const OUTCOME_STYLE = {
  confirmed: { label: 'Delivered',  bg: 'bg-emerald-50 dark:bg-emerald-950/40',  text: 'text-emerald-700 dark:text-emerald-300',  border: 'border-emerald-200 dark:border-emerald-800' },
  partial:   { label: 'Partial',    bg: 'bg-emerald-50 dark:bg-emerald-950/40',  text: 'text-emerald-700 dark:text-emerald-300',  border: 'border-emerald-200 dark:border-emerald-800' },
  deferred:  { label: 'Deferred',   bg: 'bg-rose-50 dark:bg-rose-950/40',   text: 'text-rose-600 dark:text-rose-400',   border: 'border-rose-200 dark:border-rose-800'  },
};

const ISSUE_TYPES = [
  { id: 'short',   label: 'Short quantity' },
  { id: 'damaged', label: 'Damaged'        },
  { id: 'wrong',   label: 'Wrong item'     },
  { id: 'missing', label: 'Missing'        },
  { id: 'other',   label: 'Other'          },
];

export default function ReceiptsTab() {
  const [expandedId, setExpandedId]       = useState(null);
  const [reportingId, setReportingId]     = useState(null);

  const toggle = (id) => setExpandedId((prev) => (prev === id ? null : id));

  return (
    <div className="h-full overflow-y-auto text-slate-900 dark:text-[#F8FAFC]">
      <div className="max-w-screen-md mx-auto px-4 md:px-6 py-5 space-y-5 pb-10">
        <h2 className="text-[19px] font-bold text-slate-900 dark:text-[#F8FAFC]">Receipts &amp; Deferrals</h2>

        {/* ── Pending receipt confirmation ── */}
        {ORDER_HISTORY.filter((o) => o.receipt === 'partial').length > 0 && (
          <section>
            <p className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2.5">Open Issues</p>
            {ORDER_HISTORY.filter((o) => o.receipt === 'partial').map((order) => (
              <PendingIssueCard
                key={order.id}
                order={order}
                onReport={() => setReportingId(order.id)}
              />
            ))}
          </section>
        )}

        {/* ── Active deferrals ── */}
        {DEFERRED_ORDERS.length > 0 && (
          <section>
            <p className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2.5">Deferrals</p>
            {DEFERRED_ORDERS.map((d) => (
              <div key={d.id} className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden mb-2 shadow-sm">
                <div className="px-4 py-3.5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[14px] font-bold text-slate-900 dark:text-[#F8FAFC]">{d.id}</span>
                        <span className="text-[11px] text-slate-400 dark:text-slate-500">{d.type}</span>
                      </div>
                      <p className="text-[12px] text-slate-500 dark:text-slate-400 space-y-0.5">
                        <span className="block">Original: <span className="font-semibold text-slate-700 dark:text-slate-200">{d.originalDate}</span></span>
                        <span className="block">New delivery: <span className="font-bold text-slate-900 dark:text-[#F8FAFC]">{d.newDate}</span></span>
                      </p>
                    </div>
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 shrink-0">
                      Deferred
                    </span>
                  </div>
                  <p className="mt-2.5 text-[12px] text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 rounded-lg px-3 py-2 leading-relaxed">
                    {d.reasonDetail}
                  </p>
                  {d.deferralCount > 1 && (
                    <p className="mt-2 text-[12px] font-medium text-slate-500 dark:text-slate-400">ℹ Deferral #{d.deferralCount} this month</p>
                  )}
                </div>
              </div>
            ))}
          </section>
        )}

        {/* ── Order History ── */}
        <section>
          <p className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2.5">Order History</p>
          <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
            {ORDER_HISTORY.map((order, idx) => {
              const isExpanded = expandedId === order.id;
              const outcome = OUTCOME_STYLE[order.receipt] || OUTCOME_STYLE.confirmed;
              const isLast = idx === ORDER_HISTORY.length - 1;

              return (
                <div key={order.id} className={isLast ? '' : 'border-b border-slate-100 dark:border-slate-800'}>
                  {/* Row header */}
                  <button
                    type="button"
                    onClick={() => toggle(order.id)}
                    className="w-full px-4 py-3.5 flex items-center justify-between text-left hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-[12px] text-slate-400 dark:text-slate-500 font-medium w-14 shrink-0">{order.date}</span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-[14px] font-semibold text-slate-900 dark:text-[#F8FAFC]">{order.id}</span>
                          <span className="text-[11px] text-slate-400 dark:text-slate-500">{order.type}</span>
                        </div>
                        <p className="text-[12px] text-slate-500 dark:text-slate-400 mt-0.5">
                          {order.totalReceived}/{order.totalOrdered} received
                          {order.issues.length > 0 && (
                            <span className="ml-1.5 text-emerald-600 dark:text-emerald-400 font-semibold">· {order.issues.length} issue{order.issues.length !== 1 ? 's' : ''}</span>
                          )}
                          {order.note && (
                            <span className="ml-1.5 text-slate-400 dark:text-slate-500">· {order.note}</span>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold border ${outcome.bg} ${outcome.text} ${outcome.border}`}>
                        {outcome.label}
                      </span>
                      {isExpanded ? <ChevronUp size={15} className="text-slate-400 dark:text-slate-500" /> : <ChevronDown size={15} className="text-slate-400 dark:text-slate-500" />}
                    </div>
                  </button>

                  {/* Expanded detail */}
                  {isExpanded && (
                    <div className="px-4 pb-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/30 dark:bg-slate-900/40">
                      {order.issues.length === 0 ? (
                        <div className="flex items-center gap-2 py-3 text-[13px] text-emerald-700 dark:text-emerald-400 font-medium">
                          <Check size={15} className="text-emerald-600 dark:text-emerald-400" />
                          <span>All {order.totalOrdered} units received in good condition.</span>
                        </div>
                      ) : (
                        <div className="py-3 space-y-3">
                          {order.issues.map((issue, iIdx) => (
                            <IssueDetail key={iIdx} issue={issue} />
                          ))}
                        </div>
                      )}

                      {/* Report issue button */}
                      {order.receipt !== 'deferred' && (
                        <button
                          type="button"
                          onClick={() => setReportingId(order.id)}
                          className="mt-1 text-[12px] font-semibold text-emerald-600 dark:text-emerald-400 hover:underline cursor-pointer"
                        >
                          + Report an issue with this delivery
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* Empty history */}
        {ORDER_HISTORY.length === 0 && (
          <div className="py-12 text-center text-slate-400 dark:text-slate-500">
            <p className="text-[14px] font-medium">No delivery history yet.</p>
            <p className="text-[13px] mt-1">Completed deliveries will appear here.</p>
          </div>
        )}
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
    <div className="bg-emerald-500/10 dark:bg-emerald-950/30 border border-emerald-500/20 dark:border-emerald-800/30 rounded-xl px-4 py-4 mb-2 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <AlertTriangle size={15} className="text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-[13px] font-semibold text-slate-900 dark:text-[#F8FAFC]">{order.id} — Partial delivery</p>
            <p className="text-[12px] text-slate-500 dark:text-slate-400 mt-0.5">
              {order.totalReceived}/{order.totalOrdered} received · {order.issues.length} item{order.issues.length !== 1 ? 's' : ''} affected
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onReport}
          className="shrink-0 h-8 px-3 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-600 dark:hover:bg-emerald-500 text-white text-[12px] font-semibold rounded-lg transition-colors cursor-pointer"
        >
          Report
        </button>
      </div>
      {order.issues.map((issue, i) => (
        <div key={i} className="mt-3 pt-3 border-t border-emerald-500/20 dark:border-emerald-800/30">
          <IssueDetail issue={issue} />
        </div>
      ))}
    </div>
  );
}

function IssueDetail({ issue }) {
  return (
    <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2.5 space-y-1.5">
      <div className="flex items-center justify-between">
        <p className="text-[13px] font-semibold text-slate-900 dark:text-[#F8FAFC]">{issue.item}</p>
        <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60 capitalize">
          {issue.type}
        </span>
      </div>
      <div className="flex items-center gap-4 text-[12px] text-slate-500 dark:text-slate-400">
        <span>Ordered: <span className="font-semibold text-slate-800 dark:text-slate-200">{issue.ordered}</span></span>
        <span>Received: <span className="font-semibold text-emerald-700 dark:text-emerald-400">{issue.received}</span></span>
        <span className="font-semibold text-slate-600 dark:text-slate-300">Short by {issue.ordered - issue.received}</span>
      </div>
      {issue.loaderNote && (
        <p className="text-[11px] text-slate-400 dark:text-slate-500 pt-0.5">
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

  const submit = () => setStep('done');

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-end md:items-center justify-center p-0 md:p-4">
      <div className="bg-white dark:bg-[#111827] w-full md:max-w-md md:rounded-2xl rounded-t-2xl overflow-hidden shadow-2xl border border-slate-200 dark:border-slate-800">
        {/* Header */}
        <div className="px-5 pt-5 pb-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-[16px] font-bold text-slate-900 dark:text-[#F8FAFC]">Report an issue</h2>
            <p className="text-[12px] text-slate-400 dark:text-slate-500 mt-0.5">{orderId}</p>
          </div>
          <button type="button" onClick={onClose} className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer">
            <X size={18} />
          </button>
        </div>

        {step === 'done' ? (
          <div className="px-5 py-8 text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-950/60 flex items-center justify-center mx-auto mb-3">
              <Check size={22} className="text-emerald-600 dark:text-emerald-400" strokeWidth={2.5} />
            </div>
            <p className="text-[15px] font-bold text-slate-900 dark:text-[#F8FAFC]">Issue reported</p>
            <p className="text-[13px] text-slate-500 dark:text-slate-400 mt-1">Your report has been submitted.</p>
            <button
              type="button"
              onClick={onClose}
              className="mt-5 w-full h-10 border border-slate-200 dark:border-slate-700 rounded-xl text-[13px] font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer"
            >
              Close
            </button>
          </div>
        ) : step === 'type' ? (
          <div className="px-5 py-4 space-y-3">
            <p className="text-[13px] font-semibold text-slate-700 dark:text-slate-300">What's the issue?</p>
            <div className="grid grid-cols-2 gap-2">
              {ISSUE_TYPES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => { setIssueType(t.id); setStep('detail'); }}
                  className="h-10 border border-slate-200 dark:border-slate-700 rounded-xl text-[13px] font-semibold text-slate-700 dark:text-slate-300 hover:border-emerald-500 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50/30 dark:hover:bg-emerald-950/20 transition-colors cursor-pointer"
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* detail step */
          <div className="px-5 py-4 space-y-3">
            <p className="text-[13px] font-semibold text-slate-700 dark:text-slate-300 capitalize">{ISSUE_TYPES.find((t) => t.id === issueType)?.label}</p>

            <div>
              <label className="block text-[12px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Item name</label>
              <input
                type="text"
                value={item}
                onChange={(e) => setItem(e.target.value)}
                placeholder="e.g. Linen Shirt"
                className="w-full h-10 px-3 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-xl text-[13px] text-slate-900 dark:text-[#F8FAFC] focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {(issueType === 'short' || issueType === 'damaged') && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[12px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Ordered</label>
                  <input
                    type="number"
                    value={ordered}
                    onChange={(e) => setOrdered(e.target.value)}
                    className="w-full h-10 px-3 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-xl text-[13px] text-center font-bold text-slate-900 dark:text-[#F8FAFC] focus:outline-none focus:ring-2 focus:ring-emerald-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                </div>
                <div>
                  <label className="block text-[12px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Received</label>
                  <input
                    type="number"
                    value={received}
                    onChange={(e) => setReceived(e.target.value)}
                    className="w-full h-10 px-3 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-xl text-[13px] text-center font-bold text-slate-900 dark:text-[#F8FAFC] focus:outline-none focus:ring-2 focus:ring-emerald-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-1">
              <button
                type="button"
                onClick={() => setStep('type')}
                className="flex-1 h-10 border border-slate-200 dark:border-slate-700 rounded-xl text-[13px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer"
              >
                Back
              </button>
              <button
                type="button"
                onClick={submit}
                disabled={!item.trim()}
                className="flex-[2] h-10 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-600 dark:hover:bg-emerald-500 text-white rounded-xl text-[13px] font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
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
