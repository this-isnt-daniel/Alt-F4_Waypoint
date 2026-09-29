import React from 'react';
import { Truck, CheckCircle, AlertTriangle, Play } from 'lucide-react';

export default function Screen01Login({ onStart }) {
  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-112px)] overflow-hidden">

      {/* ── Left: Forest hero (Centered, refined artwork, no overflow) ── */}
      <div
        className="w-full lg:w-1/2 flex flex-col justify-between p-8 lg:p-12 xl:p-16 relative overflow-hidden flex-shrink-0"
        style={{ background: '#0B3D33' }}
      >
        {/* Subtle decorative background glow circles */}
        <div
          className="absolute -top-20 -right-20 w-80 h-80 rounded-full opacity-10 pointer-events-none"
          style={{ background: '#0F9D6C' }}
        />
        <div
          className="absolute -bottom-20 -left-20 w-80 h-80 rounded-full opacity-10 pointer-events-none"
          style={{ background: '#14B8A6' }}
        />

        {/* Top Header info */}
        <div className="relative z-10">
          <p
            className="text-[11px] font-semibold tracking-[0.2em] uppercase mb-4"
            style={{ color: '#6EE7B7' }}
          >
            WAYPOINT GROUP PORTAL
          </p>
          <h1 className="text-4xl lg:text-5xl font-extrabold text-white leading-tight tracking-tight">
            Ayubowan,<br />Kasun Perera
          </h1>
          <p className="text-sm mt-3" style={{ color: '#A7D4C0' }}>
            Shift Start Scheduled:{' '}
            <span className="font-bold text-white tabular-nums">05:30 AM</span>
          </p>
        </div>

        {/* Centered Truck Illustration with clean geometry */}
        <div className="relative z-10 my-auto py-6 flex items-center justify-center">
          <svg
            className="w-full max-w-[340px] xl:max-w-[400px] h-auto drop-shadow-sm opacity-90 transition-opacity"
            viewBox="0 0 320 120"
            fill="none"
          >
            {/* Cargo Box (with subtle gradient styling) */}
            <rect x="10" y="16" width="200" height="74" rx="8" stroke="#10B981" strokeWidth="2.5" fill="#0D4B3F" />
            <line x1="20" y1="16" x2="20" y2="90" stroke="#10B981" strokeWidth="1" strokeDasharray="3 3" opacity="0.4" />
            <line x1="110" y1="16" x2="110" y2="90" stroke="#10B981" strokeWidth="1" strokeDasharray="3 3" opacity="0.4" />
            <line x1="10" y1="68" x2="210" y2="68" stroke="#10B981" strokeWidth="1.5" opacity="0.5" />
            
            {/* Waypoint subtle branding inside truck box */}
            <text x="75" y="48" fill="#A7D4C0" fontSize="13" fontWeight="bold" letterSpacing="2">WAYPOINT</text>
            <text x="88" y="60" fill="#6EE7B7" fontSize="8" letterSpacing="1">LOGISTICS</text>

            {/* Cab Front */}
            <path d="M210 32 H280 Q294 32 298 48 L304 68 Q306 74 306 82 V90 H210 V32 Z" stroke="#34D399" strokeWidth="2.5" fill="#0F5446" />
            
            {/* Cab Window */}
            <path d="M225 40 H275 Q282 40 286 52 L290 62 H225 V40 Z" stroke="#6EE7B7" strokeWidth="1.5" fill="#136353" />
            
            {/* Headlight */}
            <rect x="300" y="74" width="5" height="10" rx="2" fill="#FCD34D" />

            {/* Wheels */}
            <g>
              {/* Wheel 1 */}
              <circle cx="55" cy="94" r="16" fill="#06241E" stroke="#34D399" strokeWidth="2.5" />
              <circle cx="55" cy="94" r="6" fill="#10B981" />
              {/* Wheel 2 */}
              <circle cx="165" cy="94" r="16" fill="#06241E" stroke="#34D399" strokeWidth="2.5" />
              <circle cx="165" cy="94" r="6" fill="#10B981" />
              {/* Wheel 3 */}
              <circle cx="265" cy="94" r="16" fill="#06241E" stroke="#34D399" strokeWidth="2.5" />
              <circle cx="265" cy="94" r="6" fill="#10B981" />
            </g>

            {/* Road Base line & Dash markers */}
            <line x1="0" y1="110" x2="320" y2="110" stroke="#10B981" strokeWidth="1.5" opacity="0.3" />
            <line x1="30" y1="110" x2="60" y2="110" stroke="#34D399" strokeWidth="2.5" opacity="0.6" />
            <line x1="120" y1="110" x2="160" y2="110" stroke="#34D399" strokeWidth="2.5" opacity="0.6" />
            <line x1="220" y1="110" x2="250" y2="110" stroke="#34D399" strokeWidth="2.5" opacity="0.6" />
          </svg>
        </div>

        {/* Bottom meta caption */}
        <div className="relative z-10 pt-2 border-t border-white/10 flex items-center justify-between text-xs" style={{ color: '#A7D4C0' }}>
          <span>Peliyagoda Depot</span>
          <span className="font-mono">Mon, 29 Sep 2026</span>
        </div>
      </div>

      {/* ── Right: Clean Centered Cards Stack (No vertical page scroll) ── */}
      <div
        className="w-full lg:w-1/2 p-6 lg:p-8 xl:p-12 flex flex-col justify-center overflow-y-auto"
        style={{ background: '#F4F8F6' }}
      >
        <div className="w-full max-w-md mx-auto flex flex-col gap-4">

          {/* 1. Offline Readiness Card */}
          <div
            className="rounded-[20px] p-4 flex items-center gap-3.5"
            style={{
              background: '#E6F6EC',
              border: '1px solid #86efac',
              boxShadow: '0 4px 16px rgba(11,61,51,0.06)',
            }}
          >
            <div
              className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ background: '#16A34A' }}
            >
              <CheckCircle size={18} color="white" />
            </div>
            <div>
              <p className="text-sm font-bold leading-tight" style={{ color: '#14532D' }}>
                ✓ Offline Mode Ready
              </p>
              <p className="text-xs mt-0.5" style={{ color: '#166534' }}>
                Downloaded: 47 stops (3.2 MB)
              </p>
            </div>
          </div>

          {/* 2. Assigned Vehicle Card */}
          <div
            className="rounded-[20px] p-4"
            style={{
              background: '#FFFFFF',
              border: '1px solid #E2ECE7',
              boxShadow: '0 6px 20px rgba(11,61,51,0.06)',
            }}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2.5">
                <Truck size={20} style={{ color: '#0F9D6C' }} />
                <span className="text-xl font-bold tabular-nums" style={{ color: '#0B3D33' }}>
                  VEH-014
                </span>
              </div>
              <span
                className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide"
                style={{ background: '#E8F5EF', color: '#0F9D6C', border: '1px solid #C6E8D9' }}
              >
                PELIYAGODA DEPOT
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 pt-2.5" style={{ borderTop: '1px solid #E2ECE7' }}>
              <div>
                <p className="text-[10px] uppercase tracking-wide font-semibold mb-0.5" style={{ color: '#5B6B66' }}>
                  Total Runs
                </p>
                <p className="text-sm font-semibold" style={{ color: '#0E1A17' }}>2 Routes</p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wide font-semibold mb-0.5" style={{ color: '#5B6B66' }}>
                  Date
                </p>
                <p className="text-sm font-semibold" style={{ color: '#0E1A17' }}>Mon, 29 Sep 2026</p>
              </div>
            </div>
          </div>

          {/* 3. Safety Reminder */}
          <div
            className="rounded-[20px] p-3.5 flex items-start gap-3"
            style={{
              background: '#FFF4DB',
              border: '1px solid #FDE68A',
            }}
          >
            <AlertTriangle size={17} style={{ color: '#F59E0B', flexShrink: 0, marginTop: 1 }} />
            <p className="text-xs leading-relaxed font-medium" style={{ color: '#78350F' }}>
              Do not operate the mobile screen while the vehicle is in motion. Pull over to a safe area before logging inputs.
            </p>
          </div>

          {/* 4. Primary CTA Hero Button */}
          <button
            type="button"
            onClick={onStart}
            className="w-full flex items-center justify-center gap-2.5 rounded-2xl text-base font-bold text-white transition-all duration-150 active:scale-[0.98] cursor-pointer mt-1"
            style={{
              background: '#0F9D6C',
              height: 58,
              boxShadow: '0 4px 14px rgba(15,157,108,0.35)',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
            onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
          >
            <Play size={17} fill="white" />
            START SHIFT
          </button>
        </div>
      </div>
    </div>
  );
}
