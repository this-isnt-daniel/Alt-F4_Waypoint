import React from 'react';
import { Truck, CheckCircle, AlertTriangle, Play, ShieldCheck } from 'lucide-react';

export default function Screen01Login({ onStart }) {
  return (
    <div className="flex min-h-[calc(100vh-64px)]">

      {/* ── Left: Forest hero ──────────────────────────────────── */}
      <div
        className="hidden lg:flex w-[58%] flex-col justify-between p-12 relative overflow-hidden"
        style={{ background: '#0B3D33' }}
      >
        {/* Background pattern circles */}
        <div
          className="absolute -top-24 -right-24 w-96 h-96 rounded-full opacity-10"
          style={{ background: '#0F9D6C' }}
        />
        <div
          className="absolute -bottom-16 -left-16 w-64 h-64 rounded-full opacity-10"
          style={{ background: '#14B8A6' }}
        />

        {/* Top overline */}
        <div>
          <p
            className="text-xs font-semibold tracking-[0.2em] uppercase mb-8"
            style={{ color: '#6EE7B7' }}
          >
            WAYPOINT GROUP PORTAL
          </p>
          <h1 className="text-5xl font-bold text-white leading-tight mb-3">
            Ayubowan,<br />Kasun Perera
          </h1>
          <p className="text-base" style={{ color: '#A7D4C0' }}>
            Shift Start Scheduled:{' '}
            <span className="font-bold text-white tabular-nums">05:30 AM</span>
          </p>
        </div>

        {/* Truck line-art illustration */}
        <div className="mt-12 opacity-25">
          <svg width="280" height="110" viewBox="0 0 280 110" fill="none">
            <rect x="0" y="20" width="195" height="68" rx="8" stroke="white" strokeWidth="2.5" />
            <rect x="195" y="32" width="78" height="56" rx="6" stroke="white" strokeWidth="2.5" />
            <rect x="207" y="42" width="26" height="20" rx="3" stroke="white" strokeWidth="1.5" />
            <circle cx="42" cy="96" r="15" stroke="white" strokeWidth="2.5" />
            <circle cx="42" cy="96" r="6" stroke="white" strokeWidth="1.5" />
            <circle cx="140" cy="96" r="15" stroke="white" strokeWidth="2.5" />
            <circle cx="140" cy="96" r="6" stroke="white" strokeWidth="1.5" />
            <circle cx="248" cy="96" r="15" stroke="white" strokeWidth="2.5" />
            <circle cx="248" cy="96" r="6" stroke="white" strokeWidth="1.5" />
            <line x1="20" y1="68" x2="190" y2="68" stroke="white" strokeWidth="1.5" opacity="0.6" />
            <line x1="80" y1="20" x2="80" y2="68" stroke="white" strokeWidth="1.5" opacity="0.4" />
            <line x1="140" y1="20" x2="140" y2="68" stroke="white" strokeWidth="1.5" opacity="0.4" />
            {/* Road lines */}
            <line x1="0" y1="108" x2="280" y2="108" stroke="white" strokeWidth="1" opacity="0.3" />
            <line x1="60" y1="104" x2="90" y2="104" stroke="white" strokeWidth="2" opacity="0.4" />
            <line x1="120" y1="104" x2="150" y2="104" stroke="white" strokeWidth="2" opacity="0.4" />
            <line x1="180" y1="104" x2="210" y2="104" stroke="white" strokeWidth="2" opacity="0.4" />
          </svg>
        </div>

        {/* Bottom persona note */}
        <p className="text-xs mt-4" style={{ color: '#6B9E87' }}>
          Mon, 29 Sep 2026 · Peliyagoda Depot
        </p>
      </div>

      {/* ── Right: Cards panel ─────────────────────────────────── */}
      <div
        className="flex-1 lg:w-[42%] p-6 lg:p-10 overflow-y-auto flex flex-col gap-5"
        style={{ background: '#F4F8F6' }}
      >

        {/* Offline Readiness */}
        <div
          className="rounded-[20px] p-5 flex items-start gap-4"
          style={{
            background: '#E6F6EC',
            border: '1px solid #86efac',
            boxShadow: '0 8px 24px rgba(11,61,51,0.08)',
          }}
        >
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ background: '#16A34A' }}
          >
            <CheckCircle size={20} color="white" />
          </div>
          <div>
            <p className="text-sm font-bold" style={{ color: '#14532D' }}>
              ✓ Offline Mode Ready
            </p>
            <p className="text-xs mt-1" style={{ color: '#166534' }}>
              Downloaded: 47 stops (3.2 MB)
            </p>
          </div>
        </div>

        {/* Assigned Vehicle card */}
        <div
          className="rounded-[20px] p-5"
          style={{
            background: '#FFFFFF',
            border: '1px solid #E2ECE7',
            boxShadow: '0 8px 24px rgba(11,61,51,0.08)',
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <Truck size={22} style={{ color: '#0F9D6C' }} />
              <span className="text-2xl font-bold tabular-nums" style={{ color: '#0B3D33' }}>
                VEH-014
              </span>
            </div>
            <span
              className="px-2.5 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wide"
              style={{ background: '#E8F5EF', color: '#0F9D6C', border: '1px solid #C6E8D9' }}
            >
              PELIYAGODA DEPOT
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3 pt-3" style={{ borderTop: '1px solid #E2ECE7' }}>
            <div>
              <p className="text-[11px] uppercase tracking-wide font-semibold mb-0.5" style={{ color: '#5B6B66' }}>
                Total Runs
              </p>
              <p className="text-sm font-semibold" style={{ color: '#0E1A17' }}>2 Routes</p>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wide font-semibold mb-0.5" style={{ color: '#5B6B66' }}>
                Date
              </p>
              <p className="text-sm font-semibold" style={{ color: '#0E1A17' }}>Mon, 29 Sep 2026</p>
            </div>
          </div>
        </div>

        {/* Safety Reminder */}
        <div
          className="rounded-[20px] p-5 flex items-start gap-3"
          style={{
            background: '#FFF4DB',
            border: '1px solid #FDE68A',
            boxShadow: '0 8px 24px rgba(11,61,51,0.06)',
          }}
        >
          <AlertTriangle size={20} style={{ color: '#F59E0B', flexShrink: 0, marginTop: 1 }} />
          <p className="text-xs leading-relaxed font-medium" style={{ color: '#78350F' }}>
            Do not operate the mobile screen while the vehicle is in motion. Pull over to a safe area before logging inputs.
          </p>
        </div>

        {/* CTA */}
        <button
          onClick={onStart}
          className="w-full flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all duration-150 active:scale-[0.98] cursor-pointer mt-2"
          style={{
            background: '#0F9D6C',
            height: 64,
            boxShadow: '0 4px 14px rgba(15,157,108,0.35)',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
          onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
        >
          <Play size={18} fill="white" />
          START SHIFT
        </button>

        {/* UX Rationale */}
        <div
          className="rounded-xl p-4 mt-2"
          style={{ background: '#E8F5EF', border: '1px solid #C6E8D9' }}
        >
          <p className="text-[11px] uppercase tracking-widest font-semibold mb-1.5" style={{ color: '#0F9D6C' }}>
            UX Rationale · Screen 01
          </p>
          <p className="text-xs leading-relaxed" style={{ color: '#374151' }}>
            Confirms identity and assignment before leaving depot Wi-Fi. "Data downloaded for offline use" gives confidence for signal-dead zones. Vehicle ID becomes persistent identifier across all screens.
          </p>
        </div>
      </div>
    </div>
  );
}
