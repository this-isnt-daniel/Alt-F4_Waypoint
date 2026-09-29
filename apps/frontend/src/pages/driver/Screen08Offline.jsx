import React, { useState } from 'react';
import { WifiOff, Zap, Check, RefreshCw, AlertTriangle, Play, ChevronRight } from 'lucide-react';

const queueItems = [
  {
    id: 'OUT-014',
    name: 'Keells Super',
    outcome: 'Full Delivery',
    time: '06:52 AM',
    status: 'saved',
    label: 'Saved ✓',
  },
  {
    id: 'OUT-027',
    name: 'Cargills Food City',
    outcome: 'Partial (2 damaged)',
    time: '07:28 AM',
    status: 'saved',
    label: 'Saved ✓',
  },
  {
    id: 'OUT-031',
    name: 'SPAR Express',
    outcome: 'In Progress',
    time: null,
    status: 'saving',
    label: 'Saving...',
  },
];

export default function Screen08Offline({ onContinue, onReviewRoute }) {
  return (
    <div style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>

      {/* Offline alert banner — full width, slate bg */}
      <div
        className="w-full px-6 py-4 flex items-center gap-3"
        style={{ background: '#334155', borderBottom: '2px solid #E5484D' }}
      >
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ background: '#E5484D' }}
        >
          <WifiOff size={16} color="white" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase" style={{ background: '#E5484D', color: 'white' }}>● Offline</span>
            <p className="text-sm font-semibold text-white">
              ⚡ Offline Mode Active — No signal near Kegalle. Delays expected.
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">

        {/* Main 2-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">

          {/* Left: Explainer + queue (2/3) */}
          <div className="lg:col-span-2 flex flex-col gap-4">

            {/* Info card */}
            <div
              className="rounded-[20px] p-5"
              style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
            >
              <div className="flex items-start gap-3">
                <Zap size={18} style={{ color: '#F59E0B', flexShrink: 0, marginTop: 2 }} />
                <p className="text-sm leading-relaxed" style={{ color: '#0E1A17' }}>
                  Waypoint auto-saves all transaction state locally on your device. Deliveries will process, sign, and sync automatically as soon as mobile networks return.
                </p>
              </div>
            </div>

            {/* Queue list */}
            <div
              className="rounded-[20px] p-5"
              style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
            >
              <div className="flex items-center justify-between mb-4">
                <p className="text-[11px] uppercase tracking-widest font-semibold" style={{ color: '#5B6B66' }}>
                  LOCAL DEVICE QUEUE
                </p>
                <span
                  className="px-2.5 py-0.5 rounded-full text-xs font-bold"
                  style={{ background: '#FFF4DB', color: '#B45309', border: '1px solid #FDE68A' }}
                >
                  3 WAITING
                </span>
              </div>
              <div className="flex flex-col gap-2.5">
                {queueItems.map(item => (
                  <div
                    key={item.id}
                    className="rounded-xl px-4 py-3 flex items-center justify-between"
                    style={{ background: '#F4F8F6', border: '1px solid #E2ECE7' }}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold" style={{ color: '#0B3D33' }}>{item.id} {item.name}</span>
                        <span className="text-xs" style={{ color: '#5B6B66' }}>— {item.outcome}</span>
                        {item.time && <span className="text-xs font-mono tabular-nums" style={{ color: '#5B6B66' }}>• {item.time}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {item.status === 'saved' ? (
                        <span
                          className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold"
                          style={{ background: '#E6F6EC', color: '#16A34A' }}
                        >
                          <Check size={10} strokeWidth={3} /> {item.label}
                        </span>
                      ) : (
                        <span
                          className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold"
                          style={{ background: '#E8F0FF', color: '#3B82F6' }}
                        >
                          <RefreshCw size={10} className="animate-spin" /> {item.label}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Recovery state previews (1/3) */}
          <div className="flex flex-col gap-4">
            <p className="text-[11px] uppercase tracking-widest font-semibold" style={{ color: '#5B6B66' }}>
              ALTERNATE RECOVERY STATE PREVIEWS
            </p>

            {/* State 1: Syncing */}
            <div
              className="rounded-[20px] p-4"
              style={{ background: '#E8F0FF', border: '1px solid #BFDBFE', boxShadow: '0 4px 12px rgba(59,130,246,0.1)' }}
            >
              <p className="text-xs font-semibold mb-2" style={{ color: '#1D4ED8' }}>State 1 — Syncing</p>
              <p className="text-xs mb-2" style={{ color: '#1E40AF' }}>Syncing — 2 of 3 records uploaded</p>
              <div className="w-full h-2 rounded-full" style={{ background: '#BFDBFE' }}>
                <div className="h-full rounded-full" style={{ background: '#3B82F6', width: '66%' }} />
              </div>
            </div>

            {/* State 2: Synced */}
            <div
              className="rounded-[20px] p-4"
              style={{ background: '#E6F6EC', border: '1px solid #86efac' }}
            >
              <p className="text-xs font-semibold mb-2" style={{ color: '#16A34A' }}>State 2 — Synced</p>
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: '#16A34A' }}>
                  <Check size={14} color="white" strokeWidth={3} />
                </div>
                <p className="text-xs font-semibold" style={{ color: '#166534' }}>✓ All records synced successfully</p>
              </div>
            </div>

            {/* Route conflict card */}
            <div
              className="rounded-[20px] p-4"
              style={{ background: '#FFF4DB', border: '1px solid #FDE68A' }}
            >
              <div className="flex items-start gap-2 mb-3">
                <AlertTriangle size={14} style={{ color: '#F59E0B', flexShrink: 0, marginTop: 1 }} />
                <p className="text-xs font-bold" style={{ color: '#92400E' }}>ROUTE CONFLICT DETECTED</p>
              </div>
              <p className="text-xs leading-relaxed mb-3" style={{ color: '#78350F' }}>
                Stop order changed — Dispatcher moved OUT031 ahead of OUT027 while you were offline. Your records are safe.
              </p>
              <button
                onClick={onReviewRoute}
                className="w-full flex items-center justify-center gap-1.5 rounded-xl py-2 text-xs font-semibold cursor-pointer transition-all"
                style={{ background: '#F59E0B', color: 'white' }}
                onMouseEnter={e => (e.currentTarget.style.background = '#D97706')}
                onMouseLeave={e => (e.currentTarget.style.background = '#F59E0B')}
              >
                <ChevronRight size={13} />
                ⊙ Review Route Changes
              </button>
            </div>
          </div>
        </div>

        {/* Footer note */}
        <div
          className="rounded-xl p-4 mb-5 text-center"
          style={{ background: '#0B3D33' }}
        >
          <p className="text-xs" style={{ color: '#A7D4C0' }}>
            No proof of delivery is ever lost. Delivery metrics and outcomes are preserved using unalterable local database queues.
          </p>
        </div>

        {/* CTA */}
        <button
          onClick={onContinue}
          className="w-full flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer"
          style={{ background: '#0F9D6C', height: 64, boxShadow: '0 4px 14px rgba(15,157,108,0.35)' }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
          onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
        >
          <Play size={18} />
          ▶ CONTINUE SYSTEM OPERATIONS
        </button>
      </div>
    </div>
  );
}
