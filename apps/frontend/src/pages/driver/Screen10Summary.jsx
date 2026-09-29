import React from 'react';
import { Check, AlertTriangle, Play, Clock, Truck, Fuel, MapPin } from 'lucide-react';

const routeRecap = [
  { id: 'OUT014', name: 'Keells Super', status: 'delivered', time: '06:52', outcome: 'Delivered ✓' },
  { id: 'OUT027', name: 'Cargills Food City', status: 'delivered', time: '07:28', outcome: 'Delivered ✓' },
  { id: 'OUT031', name: 'SPAR Express', status: 'partial', time: '07:55', outcome: 'Partial ⚠ (8 damaged)' },
];

const metrics = [
  {
    icon: <Clock size={20} style={{ color: '#0F9D6C' }} />,
    label: '⏱ Total Trip Time',
    value: '3h 42m',
    badge: 'UNDER BUDGET',
    badgeColor: '#16A34A',
    badgeBg: '#E6F6EC',
  },
  {
    icon: <Truck size={20} style={{ color: '#0F9D6C' }} />,
    label: '🚛 Total Distance',
    value: '47 km driven',
    badge: null,
  },
  {
    icon: <Fuel size={20} style={{ color: '#0F9D6C' }} />,
    label: '⛽ Fuel Economy',
    value: '9.4 km/L ✓',
    badge: null,
  },
];

export default function Screen10Summary({ onStartTrip2 }) {
  return (
    <div className="max-w-7xl mx-auto px-6 py-8" style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>

      {/* Hero header */}
      <div
        className="rounded-[20px] p-6 mb-6"
        style={{ background: '#0B3D33', boxShadow: '0 12px 32px rgba(11,61,51,0.20)' }}
      >
        <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: '#6EE7B7' }}>
          TRIP COMPLETE
        </p>
        <h1 className="text-2xl font-bold text-white mb-4">Trip 1: Fresh Gampaha Summary</h1>

        {/* Summary pills */}
        <div className="flex flex-wrap gap-3">
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-full"
            style={{ background: '#E6F6EC', border: '1px solid #86efac' }}
          >
            <Check size={14} style={{ color: '#16A34A' }} strokeWidth={3} />
            <span className="text-sm font-bold" style={{ color: '#14532D' }}>2 DELIVERED</span>
          </div>
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-full"
            style={{ background: '#FFF4DB', border: '1px solid #FDE68A' }}
          >
            <AlertTriangle size={14} style={{ color: '#F59E0B' }} />
            <span className="text-sm font-bold" style={{ color: '#92400E' }}>1 PARTIAL</span>
          </div>
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-full"
            style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)' }}
          >
            <span className="text-sm font-bold text-white">0 FAILED</span>
          </div>
        </div>
      </div>

      {/* Performance metrics grid */}
      <div className="mb-5">
        <p className="text-[11px] uppercase tracking-widest font-semibold mb-3" style={{ color: '#5B6B66' }}>
          PERFORMANCE METRICS
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {metrics.map(m => (
            <div
              key={m.label}
              className="rounded-[20px] p-5"
              style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
            >
              <div className="flex items-center gap-2 mb-2">{m.icon}</div>
              <p className="text-xs mb-1" style={{ color: '#5B6B66' }}>{m.label}</p>
              <p className="text-2xl font-bold tabular-nums" style={{ color: '#0B3D33' }}>{m.value}</p>
              {m.badge && (
                <span
                  className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wide"
                  style={{ background: m.badgeBg, color: m.badgeColor }}
                >
                  {m.badge}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Route recap */}
      <div
        className="rounded-[20px] p-6 mb-5"
        style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
      >
        <p className="text-[11px] uppercase tracking-widest font-semibold mb-4" style={{ color: '#5B6B66' }}>
          ROUTE RECAP
        </p>
        <div className="flex flex-col gap-2.5">
          {routeRecap.map(stop => (
            <div
              key={stop.id}
              className="flex items-center justify-between rounded-xl px-4 py-3"
              style={{
                background: stop.status === 'partial' ? '#FFF4DB' : '#F4F8F6',
                border: stop.status === 'partial' ? '1px solid #FDE68A' : '1px solid #E2ECE7',
              }}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center"
                  style={{ background: stop.status === 'delivered' ? '#E6F6EC' : '#FFF4DB' }}
                >
                  {stop.status === 'delivered'
                    ? <Check size={14} style={{ color: '#16A34A' }} strokeWidth={3} />
                    : <AlertTriangle size={14} style={{ color: '#F59E0B' }} />
                  }
                </div>
                <div>
                  <p className="text-sm font-bold" style={{ color: '#0E1A17' }}>
                    {stop.id} {stop.name}
                  </p>
                  <p className="text-xs" style={{ color: stop.status === 'partial' ? '#B45309' : '#5B6B66' }}>
                    → {stop.outcome}
                  </p>
                </div>
              </div>
              <span className="text-sm font-mono font-bold tabular-nums" style={{ color: '#0B3D33' }}>
                {stop.time}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Next step card */}
      <div
        className="rounded-[20px] p-5 mb-5 flex items-center gap-4"
        style={{ background: '#E8F5EF', border: '1px solid #C6E8D9' }}
      >
        <MapPin size={20} style={{ color: '#0F9D6C', flexShrink: 0 }} />
        <div>
          <p className="text-sm font-bold" style={{ color: '#0B3D33' }}>
            Next Step: Please proceed back to Peliyagoda Depot.
          </p>
          <p className="text-xs mt-0.5" style={{ color: '#5B6B66' }}>
            Expected Return ETA: <span className="font-semibold font-mono tabular-nums">08:30 AM</span>
          </p>
        </div>
      </div>

      {/* CTA + footer */}
      <div className="flex flex-col gap-3">
        <button
          onClick={onStartTrip2}
          className="w-full flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer"
          style={{ background: '#0F9D6C', height: 64, boxShadow: '0 4px 14px rgba(15,157,108,0.35)' }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
          onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
        >
          <Play size={18} fill="white" />
          ▶ START TRIP 2 PREPARATION
        </button>
        <p className="text-xs text-center" style={{ color: '#5B6B66' }}>
          Next: Trip 2 — Colombo Depot, 4 stops
        </p>
      </div>
    </div>
  );
}
