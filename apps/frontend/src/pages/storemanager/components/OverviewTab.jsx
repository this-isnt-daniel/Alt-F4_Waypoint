import React, { useState } from 'react';
import { AlertCircle, Check, Truck, KeyRound, ArrowRight } from 'lucide-react';
import { ACTIVE_ORDERS, DEFERRED_ORDERS } from '../data/orders';

const STATUS_CONFIG = {
  'out-for-delivery': { label: 'Out for delivery', dot: 'bg-brand-500',  text: 'text-brand-700',  bg: 'bg-brand-50',  border: 'border-brand-200' },
  'loaded':           { label: 'Loaded',           dot: 'bg-amber-400',  text: 'text-amber-700',  bg: 'bg-amber-50',  border: 'border-amber-200' },
  'confirmed':        { label: 'Confirmed',        dot: 'bg-slate-400',  text: 'text-slate-600',  bg: 'bg-slate-50',  border: 'border-slate-200' },
  'planned':          { label: 'Planned',          dot: 'bg-slate-400',  text: 'text-slate-600',  bg: 'bg-slate-50',  border: 'border-slate-200' },
  'delivered':        { label: 'Delivered',        dot: 'bg-brand-500',  text: 'text-brand-700',  bg: 'bg-brand-50',  border: 'border-brand-200' },
};

export default function OverviewTab({ onNavigate, isConfirmed, setIsConfirmed, deliveryArrived = true, onOpenOtpModal }) {
  const todayOrders = ACTIVE_ORDERS.filter(o => o.deliveryDate === 'today');
  const upcomingOrders = ACTIVE_ORDERS.filter(o => o.deliveryDate !== 'today');
  
  // Sort upcoming chronologically (mock string matching for now)
  // Our mock string starts with either "Tomorrow" or "Oct X"
  const sortedUpcoming = upcomingOrders.sort((a, b) => {
    if (a.deliveryDate.includes('Tomorrow')) return -1;
    if (b.deliveryDate.includes('Tomorrow')) return 1;
    return a.deliveryDate.localeCompare(b.deliveryDate);
  });

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-screen-md mx-auto px-4 md:px-6 py-8 space-y-8 pb-24 md:pb-16">

        {/* ── Order Arrived Alert Banner ── */}
        {deliveryArrived && (
          <div className="bg-white rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-md border border-slate-100 flex items-center justify-between p-4 relative overflow-hidden border-l-[4px] border-l-[#059669] transition-all duration-200 hover:-translate-y-1 cursor-pointer">
            <div className="pl-1">
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-[15px] font-bold text-slate-900">Order ORD-10492</span>
                <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-[#E8F7F0] text-[#059669]">Arrived</span>
                <span className="text-[12px] font-medium text-slate-400 ml-1">· 2 min ago</span>
              </div>
              <p className="text-[13px] text-slate-500 font-medium">
                VEH402 is at the loading dock — share this code with the driver
              </p>
            </div>
            
            <div className="flex gap-2">
              {['1', '6', '4', '4'].map((digit, i) => (
                <div key={i} className="w-8 h-10 rounded-md bg-[#065F46] text-white flex items-center justify-center font-bold text-[16px]">
                  {digit}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── SECTION 1: TODAY ── */}
        <section>
          <p className="text-[12px] font-bold text-slate-400 uppercase tracking-[0.15em] mb-4">TODAY</p>
          
          {todayOrders.length > 0 ? (
            <div className="space-y-4">
              {todayOrders.map((order, idx) => {
                const isPrimary = idx === 0;
                
                if (isPrimary) {
                  return (
                    <div key={order.id} className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                        <p className="text-[13px] font-semibold text-slate-800">Today's Delivery</p>
                        <span className="text-[11px] font-semibold text-slate-500 uppercase">{order.type}</span>
                      </div>
                      <div className="px-5 py-5">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div>
                            <p className="text-[18px] font-bold text-slate-900 mb-1">{order.id}</p>
                            <div className="flex items-center gap-2">
                              {deliveryArrived ? (
                                <>
                                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                                  <p className="text-[14px] font-bold text-emerald-700">
                                    Arrived at Bay · Awaiting OTP
                                  </p>
                                </>
                              ) : (
                                <>
                                  {order.status === 'out-for-delivery' && <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />}
                                  <p className="text-[14px] font-semibold text-brand-700">
                                    {STATUS_CONFIG[order.status]?.label || order.status}
                                  </p>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-[13px] text-slate-500 mb-5">
                          <p>Expected <span className="font-semibold text-slate-800">{order.expectedArrival}</span></p>
                          {order.eta && <p>Current ETA <span className="font-semibold text-brand-700">{order.eta}</span></p>}
                        </div>
                        
                        {/* Primary Action */}
                        <div className="flex items-center gap-3 pt-4 border-t border-slate-100">
                          {isConfirmed ? (
                            <div className="flex items-center justify-between w-full">
                              <div className="flex items-center gap-1.5 text-[13px] font-semibold text-emerald-700">
                                <Check size={16} strokeWidth={2.5} /> Receipt confirmed via Driver OTP
                              </div>
                              <button
                                type="button"
                                onClick={() => onNavigate('receipts')}
                                className="text-[12px] font-bold text-brand-600 hover:text-brand-800 flex items-center gap-1"
                              >
                                View in Receipts <ArrowRight size={13} />
                              </button>
                            </div>
                          ) : deliveryArrived ? (
                            <>
                              <button
                                type="button"
                                onClick={onOpenOtpModal}
                                className="flex-1 min-w-0 h-10 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[13px] font-bold transition-colors shadow-sm flex items-center justify-center gap-1.5 cursor-pointer"
                              >
                                <KeyRound size={15} className="shrink-0" />
                                <span className="leading-tight text-center">Provide OTP to Driver</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => onNavigate('progress', order.id)}
                                className="flex-1 min-w-0 h-10 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[13px] font-semibold transition-colors flex items-center justify-center"
                              >
                                Track delivery
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                type="button"
                                onClick={() => setIsConfirmed(true)}
                                className="h-9 px-4 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-[13px] font-semibold transition-colors shadow-sm"
                              >
                                Confirm receipt
                              </button>
                              <button
                                type="button"
                                onClick={() => onNavigate('progress', order.id)}
                                className="h-9 px-4 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[13px] font-semibold transition-colors"
                              >
                                Track delivery
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                }

                // Compact secondary orders
                return (
                  <div key={order.id} className="bg-white border border-slate-200 rounded-xl px-5 py-4 flex items-center justify-between hover:border-slate-300 transition-colors cursor-pointer" onClick={() => onNavigate('progress', order.id)}>
                    <div className="flex items-center gap-4">
                      <p className="text-[14px] font-bold text-slate-900 w-20">{order.id}</p>
                      <p className="text-[13px] font-medium text-slate-500 w-20">{order.type}</p>
                      <p className="text-[13px] font-semibold text-slate-700">{STATUS_CONFIG[order.status]?.label || order.status}</p>
                    </div>
                    <p className="text-[13px] font-semibold text-slate-800">{order.expectedArrival}</p>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-[14px] text-slate-500">No deliveries today.</p>
          )}
        </section>

        {/* ── SECTION 2: UPCOMING ── */}
        <section>
          <p className="text-[12px] font-bold text-slate-400 uppercase tracking-[0.15em] mb-4">UPCOMING</p>
          
          {sortedUpcoming.length > 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <div className="divide-y divide-slate-100">
                {sortedUpcoming.map((order) => {
                  const cfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.confirmed;
                  return (
                    <div key={order.id} className="px-5 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-6">
                        <p className="text-[14px] font-semibold text-slate-900 w-32">{order.deliveryDate}</p>
                        <div>
                          <p className="text-[14px] font-bold text-slate-900">{order.id}</p>
                          <p className="text-[12px] text-slate-500">{order.totalProducts} products</p>
                        </div>
                        <div className="hidden md:block">
                          <span className={`px-2 py-1 rounded-md text-[11px] font-semibold border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
                            {cfg.label}
                          </span>
                        </div>
                        <div className="hidden md:block">
                          <p className="text-[13px] text-slate-700">Expected {order.expectedArrival}</p>
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
                          className="h-8 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[12px] font-semibold transition-colors"
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
            <p className="text-[14px] text-slate-500">No upcoming orders.</p>
          )}
        </section>

        {/* ── SECTION 3: DEFERRED ── */}
        <section>
          <p className="text-[12px] font-bold text-slate-400 uppercase tracking-[0.15em] mb-4">DEFERRED</p>
          
          {DEFERRED_ORDERS.length > 0 ? (
            <div className="space-y-4">
              {DEFERRED_ORDERS.map((d) => (
                <div key={d.id} className="bg-white border border-amber-200 rounded-xl px-5 py-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <AlertCircle size={18} className="text-amber-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-[15px] font-bold text-slate-900 mb-2">{d.id}</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1 text-[13px]">
                        <p className="text-slate-500">Original delivery: <span className="font-medium text-slate-700">{d.originalDate}</span></p>
                        <p className="text-slate-500">New delivery: <span className="font-semibold text-slate-900">{d.newDate}</span></p>
                        <p className="text-slate-500 md:col-span-2">Reason: <span className="font-medium text-slate-700">{d.reason}</span></p>
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => onNavigate('receipts')}
                    className="shrink-0 h-9 px-4 rounded-lg bg-amber-50 border border-amber-200 hover:bg-amber-100 text-amber-700 text-[13px] font-semibold transition-colors"
                  >
                    View details
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[14px] text-slate-500">No deferred orders.</p>
          )}
        </section>

      </div>
    </div>
  );
}
