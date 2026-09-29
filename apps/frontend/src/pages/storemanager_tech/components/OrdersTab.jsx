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
          <p className="text-[15px] font-medium text-slate-500">No active orders</p>
          <p className="text-[13px] text-slate-400 mt-1">You don't have any deliveries in progress.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-screen-md mx-auto px-4 md:px-6 py-5 space-y-4 pb-10">
        <h2 className="text-[19px] font-bold text-slate-900">Orders in Progress</h2>

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
              <div className="h-px flex-1 bg-slate-200" />
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Deferred</span>
              <div className="h-px flex-1 bg-slate-200" />
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
    'out-for-delivery': { text: 'text-brand-700', bg: 'bg-brand-50', border: 'border-brand-200', dot: 'bg-brand-500', animate: true },
    'loaded':           { text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', dot: 'bg-amber-400', animate: false },
    'confirmed':        { text: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-200', dot: 'bg-slate-400', animate: false },
    'planned':          { text: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-200', dot: 'bg-slate-400', animate: false },
  };
  const cfg = statusConfig[order.status] || statusConfig.confirmed;

  const cardRef = useRef(null);

  useEffect(() => {
    if (isFocused && cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [isFocused]);

  return (
    <div ref={cardRef} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[15px] font-bold text-slate-900 shrink-0">{order.id}</span>
          <span className="text-[11px] text-slate-400 font-medium truncate">{order.type}</span>
        </div>
        <span className={`shrink-0 px-2.5 py-1 rounded-full text-[11px] font-bold border flex items-center gap-1.5 ${cfg.bg} ${cfg.text} ${cfg.border}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${cfg.animate ? 'animate-pulse' : ''}`} />
          {ORDER_STAGES[activeStage]?.label}
        </span>
      </div>

      {/* ETA / Expected */}
      <div className="px-4 py-3 border-b border-slate-100 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          {order.eta ? (
            <p className="text-[13px] text-slate-700">
              ETA <span className="font-bold text-slate-900 text-[15px]">{order.eta}</span>
              <span className="text-slate-400 ml-2">· Expected {order.expectedArrival}</span>
            </p>
          ) : (
            <p className="text-[13px] text-slate-700">
              Expected <span className="font-bold text-slate-900">{order.expectedArrival}</span>
            </p>
          )}
        </div>
        {order.status === 'out-for-delivery' && (
          <button
            type="button"
            onClick={onToggleMap}
            className="self-start sm:self-auto flex items-center gap-1.5 text-[12px] font-semibold text-slate-600 hover:text-brand-600 bg-slate-50 hover:bg-slate-100 px-3 py-1.5 rounded-md transition-colors"
          >
            <Map size={14} />
            {isMapExpanded ? 'Hide map' : 'Track delivery'}
          </button>
        )}
      </div>

      {/* Map Section */}
      {isMapExpanded && order.status === 'out-for-delivery' && (
        <div className="border-b border-slate-100 bg-slate-50 p-4">
          <DeliveryMap order={order} />
        </div>
      )}

      {/* Progress stepper */}
      <div className="px-4 py-4">
        <div className="flex items-center">
          {ORDER_STAGES.map((stage, idx) => {
            const isDone   = idx < activeStage;
            const isActive = idx === activeStage;
            const isPending = idx > activeStage;
            return (
              <React.Fragment key={stage.key}>
                {/* Node */}
                <div className="flex flex-col items-center shrink-0">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center border-2 transition-all ${
                    isDone   ? 'bg-brand-600 border-brand-600 text-white' :
                    isActive ? 'bg-white border-brand-600 ring-2 ring-brand-200' :
                               'bg-white border-slate-300'
                  }`}>
                    {isDone ? (
                      <Check size={13} strokeWidth={3} />
                    ) : isActive ? (
                      <span className="w-2.5 h-2.5 rounded-full bg-brand-600" />
                    ) : null}
                  </div>
                  <p className={`text-[10px] mt-1.5 font-medium text-center w-16 leading-tight ${
                    isActive ? 'text-brand-700 font-semibold' : isDone ? 'text-slate-600' : 'text-slate-400'
                  }`}>
                    {stage.label}
                  </p>
                </div>
                {/* Connector */}
                {idx < ORDER_STAGES.length - 1 && (
                  <div className="flex-1 h-0.5 mx-1.5 mb-5 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${idx < activeStage ? 'bg-brand-600' : 'bg-slate-200'}`} />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Driver & vehicle strip */}
      <div className="px-4 pb-3 flex items-center justify-between">
        <p className="text-[12px] text-slate-400">
          {order.vehicle || 'Vehicle Pending'} · {order.driver?.name || 'Driver Pending'}
        </p>
        {order.driver?.phone && (
          <a
            href={`tel:${order.driver.phone}`}
            className="w-7 h-7 rounded-full border border-slate-200 flex items-center justify-center text-slate-500 hover:text-brand-600 hover:border-brand-300 transition-colors"
          >
            <Phone size={12} strokeWidth={2} />
          </a>
        )}
      </div>

      {/* Items preview */}
      <div className="px-4 pb-3 border-t border-slate-100 pt-3">
        <div className="space-y-1">
          {order.items.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between text-[12px]">
              <span className="text-slate-600">{item.name}</span>
              <span className="font-semibold text-slate-800 tabular-nums">{item.qty} {item.unit}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function DeferredCard({ order }) {
  return (
    <div className="bg-white border border-amber-200 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-amber-100 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="text-[15px] font-bold text-slate-900">{order.id}</span>
          <span className="text-[11px] text-slate-400">{order.type}</span>
        </div>
        <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
          Deferred
        </span>
      </div>
      <div className="px-4 py-4 space-y-2.5">
        <div className="grid grid-cols-2 gap-3 text-[13px]">
          <div>
            <p className="text-slate-400 text-[11px] font-medium mb-0.5">Original</p>
            <p className="font-semibold text-slate-800">{order.originalDate}</p>
          </div>
          <div>
            <p className="text-slate-400 text-[11px] font-medium mb-0.5">New Delivery</p>
            <p className="font-bold text-slate-900">{order.newDate}</p>
          </div>
        </div>
        <div className="bg-amber-50 border border-amber-100 rounded-lg px-3 py-2.5 text-[12px] text-amber-800">
          <p className="font-semibold mb-0.5">Reason</p>
          <p>{order.reasonDetail}</p>
        </div>
        {order.deferralCount > 1 && (
          <p className="text-[12px] text-amber-600 font-semibold">
            ⚠ This is deferral #{order.deferralCount} for this order
          </p>
        )}
      </div>
    </div>
  );
}
