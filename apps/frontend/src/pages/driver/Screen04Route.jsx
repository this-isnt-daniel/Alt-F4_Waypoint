import React from 'react';
import {
  Check, Navigation, ChevronRight, AlertTriangle, ChevronDown, ChevronUp,
  MapPin, Clock, Package, DoorOpen, Truck, ShoppingBag
} from 'lucide-react';

const stops = [
  {
    id: 'OUT-014',
    name: 'Keells Super — Gampaha',
    address: '23 Colombo Road, Gampaha',
    window: '06:00 – 07:30',
    eta: '06:28 AM (On Time)',
    units: '420 units / 310 kg',
    dockType: 'Rear Dock',
    dockIcon: 'rear',
    status: 'next',
    warnings: [],
  },
  {
    id: 'OUT-027',
    name: 'Cargills Food City — Yakkala',
    window: '06:30 – 08:00',
    eta: '07:05 AM',
    units: null,
    dockType: 'Van Bay',
    dockIcon: 'van',
    status: 'upcoming',
    warnings: [{ type: 'amber', text: '⚠️ VAN-ONLY ACCESS' }],
  },
  {
    id: 'OUT-031',
    name: 'SPAR Express — Nittambuwa',
    window: '07:00 – 08:30',
    eta: '07:45 AM',
    units: null,
    dockType: 'Mall Bay',
    dockIcon: 'mall',
    status: 'upcoming',
    warnings: [{ type: 'red', text: '⚠️ MALL WINDOW 07:00-08:00 ONLY' }],
  },
];

function DockIcon({ type }) {
  if (type === 'rear') return <DoorOpen size={14} style={{ color: '#0F9D6C' }} />;
  if (type === 'van') return <Truck size={14} style={{ color: '#5B6B66' }} />;
  if (type === 'mall') return <ShoppingBag size={14} style={{ color: '#5B6B66' }} />;
  return null;
}

export default function Screen04Route({ onNavigate, onProblem }) {
  return (
    <div className="max-w-7xl mx-auto px-6 py-8" style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>

      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: '#0B3D33' }}>Fresh — Gampaha Trip</h1>
        <div className="flex items-center gap-3 mt-1.5">
          <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: '#E2ECE7', maxWidth: 200 }}>
            <div className="h-full rounded-full" style={{ background: '#0F9D6C', width: '0%' }} />
          </div>
          <p className="text-sm font-medium" style={{ color: '#5B6B66' }}>Route progress: 0 / 3 stops completed</p>
        </div>
      </div>

      {/* 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Left: Timeline rail (1/3) */}
        <div
          className="rounded-[20px] p-5"
          style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
        >
          <p className="text-[11px] uppercase tracking-widest font-semibold mb-4" style={{ color: '#5B6B66' }}>
            ROUTE TIMELINE
          </p>
          <div className="relative pl-6">
            {/* Vertical connector */}
            <div
              className="absolute left-[10px] top-4 bottom-4 w-0.5"
              style={{ background: '#E2ECE7' }}
            />

            {/* Stop 0 — Depot (completed) */}
            <div className="relative mb-6">
              <div
                className="absolute -left-6 w-5 h-5 rounded-full flex items-center justify-center"
                style={{ background: '#0F9D6C' }}
              >
                <Check size={11} color="white" strokeWidth={3} />
              </div>
              <div>
                <p className="text-xs font-bold" style={{ color: '#0F9D6C' }}>✓ Peliyagoda Depot</p>
                <p className="text-[11px] tabular-nums" style={{ color: '#5B6B66' }}>Departed at 05:45 AM</p>
              </div>
            </div>

            {/* Stop 1 — NEXT (active pulse) */}
            <div className="relative mb-6">
              <span className="absolute -left-6 flex h-5 w-5 items-center justify-center">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-50" style={{ background: '#0F9D6C' }} />
                <span className="relative inline-flex h-4 w-4 rounded-full" style={{ background: '#0F9D6C' }} />
              </span>
              <div className="rounded-xl p-3" style={{ background: '#E8F5EF', border: '1px solid #C6E8D9' }}>
                <span className="text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full inline-block mb-1.5" style={{ background: '#0F9D6C', color: 'white' }}>NEXT STOP</span>
                <p className="text-xs font-bold" style={{ color: '#0B3D33' }}>OUT-014 · Keells Super</p>
                <p className="text-[11px] tabular-nums mt-0.5" style={{ color: '#5B6B66' }}>ETA: 06:28 AM</p>
              </div>
            </div>

            {/* Stop 2 */}
            <div className="relative mb-6">
              <div
                className="absolute -left-6 w-5 h-5 rounded-full border-2"
                style={{ background: 'white', borderColor: '#CBD5E1' }}
              />
              <div>
                <p className="text-xs font-medium" style={{ color: '#0E1A17' }}>OUT-027 · Cargills Yakkala</p>
                <p className="text-[11px] tabular-nums" style={{ color: '#5B6B66' }}>ETA: 07:05 AM</p>
                <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-semibold" style={{ background: '#FFF4DB', color: '#B45309' }}>⚠️ VAN-ONLY</span>
              </div>
            </div>

            {/* Stop 3 */}
            <div className="relative">
              <div
                className="absolute -left-6 w-5 h-5 rounded-full border-2"
                style={{ background: 'white', borderColor: '#CBD5E1' }}
              />
              <div>
                <p className="text-xs font-medium" style={{ color: '#0E1A17' }}>OUT-031 · SPAR Nittambuwa</p>
                <p className="text-[11px] tabular-nums" style={{ color: '#5B6B66' }}>ETA: 07:45 AM</p>
                <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-semibold" style={{ background: '#FDECEC', color: '#E5484D' }}>⚠️ MALL WINDOW ONLY</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Stop detail cards (2/3) */}
        <div className="lg:col-span-2 flex flex-col gap-4">

          {/* Stop 1 — NEXT (expanded + elevated) */}
          <div
            className="rounded-[20px] p-6"
            style={{
              background: '#FFFFFF',
              border: '2px solid #0F9D6C',
              boxShadow: '0 12px 32px rgba(15,157,108,0.15)',
            }}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-widest" style={{ background: '#0F9D6C', color: 'white' }}>NEXT STOP</span>
                  <span className="text-xs font-semibold" style={{ color: '#5B6B66' }}>OUT-014</span>
                  <div className="flex items-center gap-1 px-2 py-0.5 rounded-full" style={{ background: '#E8F5EF' }}>
                    <DoorOpen size={11} style={{ color: '#0F9D6C' }} />
                    <span className="text-[11px] font-semibold" style={{ color: '#0B3D33' }}>Rear Dock</span>
                  </div>
                </div>
                <h2 className="text-lg font-bold" style={{ color: '#0B3D33' }}>Keells Super — Gampaha</h2>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full font-semibold" style={{ background: '#E6F6EC', color: '#16A34A' }}>On Time</span>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl p-3" style={{ background: '#F4F8F6' }}>
                <p className="text-[11px] uppercase tracking-wide font-semibold mb-0.5" style={{ color: '#5B6B66' }}>Window</p>
                <p className="text-sm font-bold tabular-nums" style={{ color: '#0E1A17' }}>06:00 – 07:30</p>
              </div>
              <div className="rounded-xl p-3" style={{ background: '#F4F8F6' }}>
                <p className="text-[11px] uppercase tracking-wide font-semibold mb-0.5" style={{ color: '#5B6B66' }}>ETA</p>
                <p className="text-sm font-bold tabular-nums" style={{ color: '#0F9D6C' }}>06:28 AM (On Time)</p>
              </div>
              <div className="rounded-xl p-3" style={{ background: '#F4F8F6' }}>
                <p className="text-[11px] uppercase tracking-wide font-semibold mb-0.5" style={{ color: '#5B6B66' }}>Load</p>
                <p className="text-sm font-bold" style={{ color: '#0E1A17' }}>420 units / 310 kg</p>
              </div>
            </div>
          </div>

          {/* Stop 2 */}
          <div
            className="rounded-[20px] p-5"
            style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 4px 12px rgba(11,61,51,0.06)' }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full" style={{ background: '#F4F8F6', border: '1px solid #E2ECE7' }}>
                  <Truck size={12} style={{ color: '#5B6B66' }} />
                  <span className="text-[11px] font-semibold" style={{ color: '#5B6B66' }}>Van Bay</span>
                </div>
                <div>
                  <p className="text-xs font-semibold" style={{ color: '#5B6B66' }}>OUT-027</p>
                  <p className="text-sm font-bold" style={{ color: '#0E1A17' }}>Cargills Food City — Yakkala</p>
                  <p className="text-xs tabular-nums mt-0.5" style={{ color: '#5B6B66' }}>Window: 06:30 – 08:00 | ETA: 07:05 AM</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold" style={{ background: '#FFF4DB', color: '#B45309', border: '1px solid #FDE68A' }}>
                ⚠️ VAN-ONLY ACCESS
              </span>
            </div>
          </div>

          {/* Stop 3 */}
          <div
            className="rounded-[20px] p-5"
            style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 4px 12px rgba(11,61,51,0.06)' }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full" style={{ background: '#F4F8F6', border: '1px solid #E2ECE7' }}>
                  <ShoppingBag size={12} style={{ color: '#5B6B66' }} />
                  <span className="text-[11px] font-semibold" style={{ color: '#5B6B66' }}>Mall Bay</span>
                </div>
                <div>
                  <p className="text-xs font-semibold" style={{ color: '#5B6B66' }}>OUT-031</p>
                  <p className="text-sm font-bold" style={{ color: '#0E1A17' }}>SPAR Express — Nittambuwa</p>
                  <p className="text-xs tabular-nums mt-0.5" style={{ color: '#5B6B66' }}>Window: 07:00 – 08:30 | ETA: 07:45 AM</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold" style={{ background: '#FDECEC', color: '#E5484D', border: '1px solid #fecaca' }}>
                ⚠️ MALL WINDOW 07:00-08:00 ONLY
              </span>
            </div>
          </div>

          {/* CTA */}
          <button
            onClick={onNavigate}
            className="w-full flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer"
            style={{ background: '#0F9D6C', height: 64, boxShadow: '0 4px 14px rgba(15,157,108,0.35)' }}
            onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
            onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
          >
            <Navigation size={18} />
            ⊙ NAVIGATE TO STOP 1
          </button>
        </div>
      </div>
    </div>
  );
}
