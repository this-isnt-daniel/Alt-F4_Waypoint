import React, { useState } from 'react';
import { AlertCircle, Check } from 'lucide-react';
import { ACTIVE_ORDERS, DEFERRED_ORDERS } from '../data/orders';

const STATUS_CONFIG = {
  'out-for-delivery': { label: 'Out for delivery', dot: 'bg-emerald-500', text: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-50 dark:bg-emerald-950/40', border: 'border-emerald-200 dark:border-emerald-800' },
  'loaded':           { label: 'Loaded',           dot: 'bg-emerald-400', text: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-50 dark:bg-emerald-950/40', border: 'border-emerald-200 dark:border-emerald-800' },
  'confirmed':        { label: 'Confirmed',        dot: 'bg-slate-400',   text: 'text-slate-600 dark:text-slate-300',   bg: 'bg-slate-50 dark:bg-slate-800/50',     border: 'border-slate-200 dark:border-slate-700' },
  'planned':          { label: 'Planned',          dot: 'bg-slate-400',   text: 'text-slate-600 dark:text-slate-300',   bg: 'bg-slate-50 dark:bg-slate-800/50',     border: 'border-slate-200 dark:border-slate-700' },
  'delivered':        { label: 'Delivered',        dot: 'bg-emerald-500', text: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-50 dark:bg-emerald-950/40', border: 'border-emerald-200 dark:border-emerald-800' },
};

export default function OverviewTab({ onNavigate, isConfirmed, setIsConfirmed }) {
  const todayOrders = ACTIVE_ORDERS.filter(o => o.deliveryDate === 'today');
  const upcomingOrders = ACTIVE_ORDERS.filter(o => o.deliveryDate !== 'today');
  
  // Sort upcoming chronologically (mock string matching for now)
  const sortedUpcoming = upcomingOrders.sort((a, b) => {
    if (a.deliveryDate.includes('Tomorrow')) return -1;
    if (b.deliveryDate.includes('Tomorrow')) return 1;
    return a.deliveryDate.localeCompare(b.deliveryDate);
  });

  return (
    <div className="h-full overflow-y-auto text-slate-900 dark:text-[#F8FAFC]">
      <div className="max-w-screen-md mx-auto px-4 md:px-6 py-8 space-y-12 pb-24 md:pb-16">

        {/* ── SECTION 1: TODAY ── */}
        <section>
          <p className="text-[12px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-[0.15em] mb-4">TODAY</p>
          
          {todayOrders.length > 0 ? (
            <div className="space-y-4">
              {todayOrders.map((order, idx) => {
                const isPrimary = idx === 0;
                
                if (isPrimary) {
                  return (
                    <div key={order.id} className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
                      <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                        <p className="text-[13px] font-semibold text-slate-800 dark:text-slate-200">Today's Delivery</p>
                        <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">{order.type}</span>
                      </div>
                      <div className="px-5 py-5">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div>
                            <p className="text-[18px] font-bold text-slate-900 dark:text-[#F8FAFC] mb-1">{order.id}</p>
                            <div className="flex items-center gap-2">
                              {order.status === 'out-for-delivery' && <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />}
                              <p className="text-[14px] font-semibold text-emerald-700 dark:text-emerald-400">
                                {STATUS_CONFIG[order.status]?.label || order.status}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="text-[13px] text-slate-500 dark:text-slate-400 mb-5">
                          <p>Expected <span className="font-semibold text-slate-800 dark:text-slate-200">{order.expectedArrival}</span></p>
                          {order.eta && <p>Current ETA <span className="font-semibold text-emerald-700 dark:text-emerald-400">{order.eta}</span></p>}
                        </div>
                        
                        {/* Primary Action */}
                        <div className="flex items-center gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                          {order.status === 'out-for-delivery' ? (
                            isConfirmed ? (
                              <div className="flex items-center gap-1.5 text-[13px] font-semibold text-emerald-700 dark:text-emerald-400">
                                <Check size={16} /> Receipt confirmed
                              </div>
                            ) : (
                              <>
                                <button
                                  type="button"
                                  onClick={() => setIsConfirmed(true)}
                                  className="h-9 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-600 dark:hover:bg-emerald-500 text-white text-[13px] font-semibold transition-colors shadow-sm cursor-pointer"
                                >
                                  Confirm receipt
                                </button>
                                <button
                                  type="button"
                                  onClick={() => onNavigate('progress', order.id)}
                                  className="h-9 px-4 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-[13px] font-semibold transition-colors cursor-pointer"
                                >
                                  Track delivery
                                </button>
                              </>
                            )
                          ) : (
                            <button
                              type="button"
                              onClick={() => onNavigate('progress', order.id)}
                              className="h-9 px-4 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-[13px] font-semibold transition-colors cursor-pointer"
                            >
                              View delivery
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                }

                // Compact secondary orders
                return (
                  <div key={order.id} className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl px-5 py-4 flex items-center justify-between hover:border-slate-300 dark:hover:border-slate-700 transition-colors cursor-pointer" onClick={() => onNavigate('progress', order.id)}>
                    <div className="flex items-center gap-4">
                      <p className="text-[14px] font-bold text-slate-900 dark:text-[#F8FAFC] w-20">{order.id}</p>
                      <p className="text-[13px] font-medium text-slate-500 dark:text-slate-400 w-20">{order.type}</p>
                      <p className="text-[13px] font-semibold text-slate-700 dark:text-slate-300">{STATUS_CONFIG[order.status]?.label || order.status}</p>
                    </div>
                    <p className="text-[13px] font-semibold text-slate-800 dark:text-slate-200">{order.expectedArrival}</p>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-[14px] text-slate-500 dark:text-slate-400">No deliveries today.</p>
          )}
        </section>

        {/* ── SECTION 2: UPCOMING ── */}
        <section>
          <p className="text-[12px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-[0.15em] mb-4">UPCOMING</p>
          
          {sortedUpcoming.length > 0 ? (
            <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {sortedUpcoming.map((order) => {
                  const cfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.confirmed;
                  return (
                    <div key={order.id} className="px-5 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-6">
                        <p className="text-[14px] font-semibold text-slate-900 dark:text-[#F8FAFC] w-32">{order.deliveryDate}</p>
                        <div>
                          <p className="text-[14px] font-bold text-slate-900 dark:text-[#F8FAFC]">{order.id}</p>
                          <p className="text-[12px] text-slate-500 dark:text-slate-400">{order.totalProducts} products</p>
                        </div>
                        <div className="hidden md:block">
                          <span className={`px-2 py-1 rounded-md text-[11px] font-semibold border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
                            {cfg.label}
                          </span>
                        </div>
                        <div className="hidden md:block">
                          <p className="text-[13px] text-slate-700 dark:text-slate-300">Expected {order.expectedArrival}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 justify-between md:justify-end">
                        <div className="md:hidden">
                          <span className={`px-2 py-1 rounded-md text-[11px] font-semibold border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
                            {cfg.label}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => onNavigate('order')}
                          className="h-8 px-3 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-[12px] font-semibold transition-colors cursor-pointer"
                        >
                          View order
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <p className="text-[14px] text-slate-500 dark:text-slate-400">No upcoming orders.</p>
          )}
        </section>

        {/* ── SECTION 3: DEFERRED ── */}
        <section>
          <p className="text-[12px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-[0.15em] mb-4">DEFERRED</p>
          
          {DEFERRED_ORDERS.length > 0 ? (
            <div className="space-y-4">
              {DEFERRED_ORDERS.map((d) => (
                <div key={d.id} className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl px-5 py-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
                  <div className="flex items-start gap-4">
                    <AlertCircle size={18} className="text-emerald-500 dark:text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-[15px] font-bold text-slate-900 dark:text-[#F8FAFC] mb-2">{d.id}</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1 text-[13px]">
                        <p className="text-slate-500 dark:text-slate-400">Original delivery: <span className="font-medium text-slate-700 dark:text-slate-200">{d.originalDate}</span></p>
                        <p className="text-slate-500 dark:text-slate-400">New delivery: <span className="font-semibold text-slate-900 dark:text-[#F8FAFC]">{d.newDate}</span></p>
                        <p className="text-slate-500 dark:text-slate-400 md:col-span-2">Reason: <span className="font-medium text-slate-700 dark:text-slate-200">{d.reason}</span></p>
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => onNavigate('receipts')}
                    className="shrink-0 h-9 px-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300 text-[13px] font-semibold transition-colors cursor-pointer"
                  >
                    View details
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[14px] text-slate-500 dark:text-slate-400">No deferred orders.</p>
          )}
        </section>

      </div>
    </div>
  );
}
