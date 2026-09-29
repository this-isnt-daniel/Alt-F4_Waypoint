import React, { useState, useEffect, useRef } from 'react';
import { Check, Phone, Map } from 'lucide-react';
import { ACTIVE_ORDERS, DEFERRED_ORDERS, ORDER_STAGES, getStageIndex } from '../data/orders';
import DeliveryMap from './DeliveryMap';

export default function OrdersTab({ selectedOrderId }) {
  const [expandedMapId, setExpandedMapId] = useState(null);

  useEffect(() => {
    if (selectedOrderId) {
      setExpandedMapId(selectedOrderId);
    }
  }, [selectedOrderId]);

  const allOrders = [
    ...ACTIVE_ORDERS,
    ...DEFERRED_ORDERS.map((d) => ({ ...d, status: 'deferred', type: d.type || 'Dry' })),
  ];

  if (allOrders.length === 0) {
    return (
      <div className="flex items-center justify-center h-full py-24 text-center px-6">
        <div>
          <p className="text-[15px] font-medium text-slate-500 dark:text-slate-400">No active orders</p>
          <p className="text-[13px] text-slate-400 dark:text-slate-500 mt-1">You don't have any deliveries in progress.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto text-slate-900 dark:text-[#F8FAFC]">
      <div className="max-w-screen-md mx-auto px-4 md:px-6 py-5 space-y-4 pb-10">
        <h2 className="text-[19px] font-bold text-slate-900 dark:text-[#F8FAFC]">Orders in Progress</h2>

        {ACTIVE_ORDERS.map((order) => (
          <OrderCard 
            key={order.id} 
            order={order} 
            isMapExpanded={expandedMapId === order.id}
            onToggleMap={() => setExpandedMapId(prev => prev === order.id ? null : order.id)}
            isFocused={selectedOrderId === order.id}
          />
        ))}

        {DEFERRED_ORDERS.length > 0 && (
          <>
            <div className="flex items-center gap-3 pt-2">
              <div className="h-px flex-1 bg-slate-200 dark:bg-slate-800" />
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Deferred</span>
              <div className="h-px flex-1 bg-slate-200 dark:bg-slate-800" />
            </div>
            {DEFERRED_ORDERS.map((d) => (
              <DeferredCard key={d.id} order={d} />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function OrderCard({ order, isMapExpanded, onToggleMap, isFocused }) {
  const activeStage = getStageIndex(order.status);

  const statusConfig = {
    'out-for-delivery': { text: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-50 dark:bg-emerald-950/40', border: 'border-emerald-200 dark:border-emerald-800', dot: 'bg-emerald-500', animate: true },
    'loaded':           { text: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-50 dark:bg-emerald-950/40', border: 'border-emerald-200 dark:border-emerald-800', dot: 'bg-emerald-400', animate: false },
    'confirmed':        { text: 'text-slate-600 dark:text-slate-300',   bg: 'bg-slate-50 dark:bg-slate-800/50',     border: 'border-slate-200 dark:border-slate-700', dot: 'bg-slate-400', animate: false },
    'planned':          { text: 'text-slate-600 dark:text-slate-300',   bg: 'bg-slate-50 dark:bg-slate-800/50',     border: 'border-slate-200 dark:border-slate-700', dot: 'bg-slate-400', animate: false },
  };
  const cfg = statusConfig[order.status] || statusConfig.confirmed;

  const cardRef = useRef(null);

  useEffect(() => {
    if (isFocused && cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [isFocused]);

  return (
    <div ref={cardRef} className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="text-[15px] font-bold text-slate-900 dark:text-[#F8FAFC]">{order.id}</span>
          <span className="text-[11px] text-slate-400 dark:text-slate-500 font-medium">{order.type}</span>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold border flex items-center gap-1.5 ${cfg.bg} ${cfg.text} ${cfg.border}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${cfg.animate ? 'animate-pulse' : ''}`} />
          {ORDER_STAGES[activeStage]?.label}
        </span>
      </div>

      {/* ETA / Expected */}
      <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div>
          {order.eta ? (
            <p className="text-[13px] text-slate-700 dark:text-slate-300">
              ETA <span className="font-bold text-slate-900 dark:text-[#F8FAFC] text-[15px]">{order.eta}</span>
              <span className="text-slate-400 dark:text-slate-500 ml-2">· Expected {order.expectedArrival}</span>
            </p>
          ) : (
            <p className="text-[13px] text-slate-700 dark:text-slate-300">
              Expected <span className="font-bold text-slate-900 dark:text-[#F8FAFC]">{order.expectedArrival}</span>
            </p>
          )}
        </div>
        {order.status === 'out-for-delivery' && (
          <button
            type="button"
            onClick={onToggleMap}
            className="flex items-center gap-1.5 text-[12px] font-semibold text-slate-600 dark:text-slate-300 hover:text-emerald-600 dark:hover:text-emerald-400 bg-slate-50 dark:bg-slate-800/80 hover:bg-slate-100 dark:hover:bg-slate-800 px-3 py-1.5 rounded-md transition-colors cursor-pointer"
          >
            <Map size={14} />
            {isMapExpanded ? 'Hide map' : 'Track delivery'}
          </button>
        )}
      </div>

      {/* Map Section */}
      {isMapExpanded && order.status === 'out-for-delivery' && (
        <div className="border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-4">
          <DeliveryMap order={order} />
        </div>
      )}

      {/* Progress stepper */}
      <div className="px-4 py-4">
        <div className="flex items-center">
          {ORDER_STAGES.map((stage, idx) => {
            const isDone   = idx < activeStage;
            const isActive = idx === activeStage;
            return (
              <React.Fragment key={stage.key}>
                {/* Node */}
                <div className="flex flex-col items-center shrink-0">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center border-2 transition-all ${
                    isDone   ? 'bg-emerald-600 border-emerald-600 text-white' :
                    isActive ? 'bg-white dark:bg-[#111827] border-emerald-600 ring-2 ring-emerald-500/20' :
                               'bg-white dark:bg-[#111827] border-slate-300 dark:border-slate-700'
                  }`}>
                    {isDone ? (
                      <Check size={13} strokeWidth={3} />
                    ) : isActive ? (
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" />
                    ) : null}
                  </div>
                  <p className={`text-[10px] mt-1.5 font-medium text-center w-16 leading-tight ${
                    isActive ? 'text-emerald-700 dark:text-emerald-400 font-semibold' : isDone ? 'text-slate-600 dark:text-slate-300' : 'text-slate-400 dark:text-slate-500'
                  }`}>
                    {stage.label}
                  </p>
                </div>
                {/* Connector */}
                {idx < ORDER_STAGES.length - 1 && (
                  <div className="flex-1 h-0.5 mx-1.5 mb-5 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${idx < activeStage ? 'bg-emerald-600' : 'bg-slate-200 dark:bg-slate-800'}`} />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Driver & vehicle strip */}
      <div className="px-4 pb-3 flex items-center justify-between">
        <p className="text-[12px] text-slate-400 dark:text-slate-500">
          {order.vehicle || 'Vehicle Pending'} · {order.driver?.name || 'Driver Pending'}
        </p>
        {order.driver?.phone && (
          <a
            href={`tel:${order.driver.phone}`}
            className="w-7 h-7 rounded-full border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:border-emerald-300 dark:hover:border-emerald-500 transition-colors"
          >
            <Phone size={12} strokeWidth={2} />
          </a>
        )}
      </div>

      {/* Items preview */}
      <div className="px-4 pb-3 border-t border-slate-100 dark:border-slate-800 pt-3">
        <div className="space-y-1">
          {order.items.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between text-[12px]">
              <span className="text-slate-600 dark:text-slate-300">{item.name}</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200 tabular-nums">{item.qty} {item.unit}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function DeferredCard({ order }) {
  return (
    <div className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="text-[15px] font-bold text-slate-900 dark:text-[#F8FAFC]">{order.id}</span>
          <span className="text-[11px] text-slate-400 dark:text-slate-500 font-medium">{order.type}</span>
        </div>
        <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
          Deferred
        </span>
      </div>
      <div className="px-4 py-4 space-y-2.5">
        <div className="grid grid-cols-2 gap-3 text-[13px]">
          <div>
            <p className="text-slate-400 dark:text-slate-500 text-[11px] font-medium mb-0.5">Original</p>
            <p className="font-semibold text-slate-800 dark:text-slate-200">{order.originalDate}</p>
          </div>
          <div>
            <p className="text-slate-400 dark:text-slate-500 text-[11px] font-medium mb-0.5">New Delivery</p>
            <p className="font-bold text-slate-900 dark:text-[#F8FAFC]">{order.newDate}</p>
          </div>
        </div>
        <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 rounded-lg px-3 py-2.5 text-[12px] text-slate-700 dark:text-slate-300">
          <p className="font-semibold mb-0.5 text-slate-800 dark:text-slate-200">Reason</p>
          <p>{order.reasonDetail}</p>
        </div>
        {order.deferralCount > 1 && (
          <p className="text-[12px] text-slate-500 dark:text-slate-400 font-medium">
            ℹ This is deferral #{order.deferralCount} for this order
          </p>
        )}
      </div>
    </div>
  );
}
