import React, { useState } from 'react';
import { Clock, MapPin, AlertTriangle, Navigation, Package } from 'lucide-react';

const orderItems = [
  { item: 'Fresh Milk', qty: '240 u', weight: '180 kg', vol: '1.2 m³' },
  { item: 'Fresh Juice', qty: '120 u', weight: '85 kg', vol: '0.6 m³' },
  { item: 'Yogurt', qty: '60 u', weight: '45 kg', vol: '0.4 m³' },
];

export default function Screen05StopDetail({ onArrived, onProblem }) {
  const [arrived, setArrived] = useState(false);
  const [unloadingStarted, setUnloadingStarted] = useState(false);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8" style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>

      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-semibold" style={{ color: '#5B6B66' }}>STOP 1 OF 3 · OUT-014</p>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold" style={{ background: '#E6F6EC', color: '#16A34A', border: '1px solid #86efac' }}>
              ON TIME
            </span>
          </div>
          <h1 className="text-2xl font-bold" style={{ color: '#0B3D33' }}>Keells Super — Gampaha</h1>
          <div className="flex items-center gap-1.5 mt-1">
            <MapPin size={13} style={{ color: '#5B6B66' }} />
            <p className="text-sm" style={{ color: '#5B6B66' }}>23 Colombo Road, Gampaha</p>
          </div>
        </div>
      </div>

      {/* Countdown card — full width hero */}
      <div
        className="rounded-[20px] p-6 mb-6 flex items-center justify-between"
        style={{
          background: '#0B3D33',
          boxShadow: '0 12px 32px rgba(11,61,51,0.20)',
        }}
      >
        <div className="flex items-center gap-4">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center"
            style={{ background: 'rgba(15,157,108,0.3)' }}
          >
            <Clock size={24} color="#6EE7B7" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: '#6EE7B7' }}>
              ⏱ Window closes
            </p>
            <p className="text-4xl font-bold tabular-nums text-white">07:30</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs font-semibold mb-1" style={{ color: '#A7D4C0' }}>ETA Arrival</p>
          <p className="text-2xl font-bold tabular-nums" style={{ color: '#6EE7B7' }}>07:12</p>
          <p className="text-xs mt-1" style={{ color: '#6EE7B7' }}>18 min remaining</p>
        </div>
      </div>

      {/* 2-column: Instructions + Order Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">

        {/* Left: Unloading instructions */}
        <div
          className="rounded-[20px] p-6"
          style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
        >
          <p className="text-[11px] uppercase tracking-widest font-semibold mb-3" style={{ color: '#5B6B66' }}>
            UNLOADING INSTRUCTIONS
          </p>
          <p className="text-sm leading-relaxed" style={{ color: '#0E1A17' }}>
            Use rear dock, report to goods receiving. Keep reefers running until delivery confirmation.
          </p>
        </div>

        {/* Right: Order content table */}
        <div
          className="rounded-[20px] p-6"
          style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
        >
          <p className="text-[11px] uppercase tracking-widest font-semibold mb-3" style={{ color: '#5B6B66' }}>
            ORDER CONTENT DETAILS
          </p>
          <div className="rounded-xl overflow-hidden" style={{ border: '1px solid #E2ECE7' }}>
            <table className="w-full text-xs">
              <thead>
                <tr style={{ background: '#F4F8F6' }}>
                  {['Item', 'Qty', 'Weight', 'Vol'].map(h => (
                    <th key={h} className="text-left px-3 py-2.5 font-semibold uppercase tracking-wide" style={{ color: '#5B6B66' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {orderItems.map(row => (
                  <tr key={row.item} style={{ borderTop: '1px solid #E2ECE7' }}>
                    <td className="px-3 py-2.5 font-medium" style={{ color: '#0E1A17' }}>{row.item}</td>
                    <td className="px-3 py-2.5 font-mono tabular-nums" style={{ color: '#5B6B66' }}>{row.qty}</td>
                    <td className="px-3 py-2.5 font-mono tabular-nums" style={{ color: '#5B6B66' }}>{row.weight}</td>
                    <td className="px-3 py-2.5 font-mono tabular-nums" style={{ color: '#5B6B66' }}>{row.vol}</td>
                  </tr>
                ))}
                {/* Total row */}
                <tr style={{ borderTop: '2px solid #E2ECE7', background: '#F4F8F6' }}>
                  <td className="px-3 py-2.5 font-bold" style={{ color: '#0B3D33' }}>Total</td>
                  <td className="px-3 py-2.5 font-bold tabular-nums font-mono" style={{ color: '#0B3D33' }}>420 u</td>
                  <td className="px-3 py-2.5 font-bold tabular-nums font-mono" style={{ color: '#0B3D33' }}>310 kg</td>
                  <td className="px-3 py-2.5 font-bold tabular-nums font-mono" style={{ color: '#0B3D33' }}>2.2 m³</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Action buttons row */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        {/* Report a problem (ghost red) */}
        <button
          onClick={onProblem}
          className="sm:w-48 flex items-center justify-center gap-2 rounded-2xl text-sm font-semibold transition-all active:scale-[0.98] cursor-pointer"
          style={{
            height: 56,
            background: 'transparent',
            border: '1px solid #fca5a5',
            color: '#E5484D',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = '#FDECEC')}
          onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
        >
          <AlertTriangle size={16} />
          ⚠ Report a Problem
        </button>

        {/* Arrived CTA (primary) */}
        <button
          onClick={() => { setArrived(true); }}
          className="flex-1 flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white transition-all active:scale-[0.98] cursor-pointer"
          style={{
            height: 64,
            background: arrived ? '#0B7F57' : '#0F9D6C',
            boxShadow: '0 4px 14px rgba(15,157,108,0.35)',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
          onMouseLeave={e => (e.currentTarget.style.background = arrived ? '#0B7F57' : '#0F9D6C')}
        >
          <Navigation size={18} />
          {arrived ? '✓ Arrived — Begin Unloading' : '⊙ ARRIVED AT OUTLET (TAP TARGET)'}
        </button>

        {/* Start unloading (disabled until arrived) */}
        <button
          disabled={!arrived}
          onClick={() => setUnloadingStarted(true)}
          className="sm:w-48 flex items-center justify-center gap-2 rounded-2xl text-sm font-semibold transition-all cursor-pointer"
          style={{
            height: 56,
            background: arrived ? '#E8F5EF' : '#F1F5F9',
            color: arrived ? '#0F9D6C' : '#94A3B8',
            border: arrived ? '1px solid #C6E8D9' : '1px solid #E2E8F0',
            cursor: arrived ? 'pointer' : 'not-allowed',
          }}
        >
          <Package size={16} />
          Start Unloading
        </button>
      </div>

      {/* UX Rationale */}
      <div className="rounded-xl p-4 mt-6" style={{ background: '#E8F5EF', border: '1px solid #C6E8D9' }}>
        <p className="text-[11px] uppercase tracking-widest font-semibold mb-1.5" style={{ color: '#0F9D6C' }}>
          UX Rationale · Screen 05
        </p>
        <p className="text-xs leading-relaxed" style={{ color: '#374151' }}>
          The window countdown is the single most important info — tells the driver if they'll make it. Sequential action flow (Arrived → Start Unloading → Complete) creates a verifiable timestamp chain feeding into delivery analytics and dispute resolution.
        </p>
      </div>
    </div>
  );
}
