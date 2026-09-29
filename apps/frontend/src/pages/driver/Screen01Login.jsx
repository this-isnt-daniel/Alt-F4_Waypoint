import React from 'react';
import { Truck, CheckCircle, AlertTriangle, Play } from 'lucide-react';

export default function Screen01Login({ onStart, darkMode = false }) {
  return (
    <div className="w-full flex justify-center py-6 sm:py-8 lg:py-10">
      <div 
        className={`w-full rounded-[24px] overflow-hidden border shadow-sm flex flex-col lg:flex-row transition-all ${
          darkMode 
            ? 'bg-[#0E201B] border-[#1D3B33] text-gray-100 shadow-xl' 
            : 'bg-white border-[#E2ECE7] text-gray-900 shadow-xs'
        }`}
      >
        {/* ── Left Hero Side (Forest Artwork & Greeting) ── */}
        <div
          className="w-full lg:w-1/2 p-6 sm:p-8 lg:p-10 xl:p-12 flex flex-col justify-between relative overflow-hidden flex-shrink-0"
          style={{ background: '#0B3D33' }}
        >
          {/* Subtle decorative glow */}
          <div
            className="absolute -top-20 -right-20 w-72 h-72 rounded-full opacity-10 pointer-events-none"
            style={{ background: '#0F9D6C' }}
          />
          <div
            className="absolute -bottom-20 -left-20 w-72 h-72 rounded-full opacity-10 pointer-events-none"
            style={{ background: '#14B8A6' }}
          />

          {/* Heading */}
          <div className="relative z-10">
            <p
              className="text-[11px] font-semibold tracking-[0.2em] uppercase mb-3"
              style={{ color: '#6EE7B7' }}
            >
              WAYPOINT GROUP PORTAL
            </p>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white leading-tight tracking-tight">
              Ayubowan,<br />Kasun Perera
            </h1>
            <p className="text-sm mt-3" style={{ color: '#A7D4C0' }}>
              Shift Start Scheduled:{' '}
              <span className="font-bold text-white tabular-nums">05:30 AM</span>
            </p>
          </div>

          {/* Center Graphic */}
          <div className="relative z-10 my-6 sm:my-8 py-2 flex items-center justify-center">
            <svg
              className="w-full max-w-[280px] sm:max-w-[320px] lg:max-w-[360px] h-auto drop-shadow-sm opacity-95 transition-opacity"
              viewBox="0 0 320 120"
              fill="none"
            >
              <rect x="10" y="16" width="200" height="74" rx="8" stroke="#10B981" strokeWidth="2.5" fill="#0D4B3F" />
              <line x1="20" y1="16" x2="20" y2="90" stroke="#10B981" strokeWidth="1" strokeDasharray="3 3" opacity="0.4" />
              <line x1="110" y1="16" x2="110" y2="90" stroke="#10B981" strokeWidth="1" strokeDasharray="3 3" opacity="0.4" />
              <line x1="10" y1="68" x2="210" y2="68" stroke="#10B981" strokeWidth="1.5" opacity="0.5" />
              <text x="75" y="48" fill="#A7D4C0" fontSize="13" fontWeight="bold" letterSpacing="2">WAYPOINT</text>
              <text x="88" y="60" fill="#6EE7B7" fontSize="8" letterSpacing="1">LOGISTICS</text>
              <path d="M210 32 H280 Q294 32 298 48 L304 68 Q306 74 306 82 V90 H210 V32 Z" stroke="#34D399" strokeWidth="2.5" fill="#0F5446" />
              <path d="M225 40 H275 Q282 40 286 52 L290 62 H225 V40 Z" stroke="#6EE7B7" strokeWidth="1.5" fill="#136353" />
              <rect x="300" y="74" width="5" height="10" rx="2" fill="#FCD34D" />
              <g>
                <circle cx="55" cy="94" r="16" fill="#06241E" stroke="#34D399" strokeWidth="2.5" />
                <circle cx="55" cy="94" r="6" fill="#10B981" />
                <circle cx="165" cy="94" r="16" fill="#06241E" stroke="#34D399" strokeWidth="2.5" />
                <circle cx="165" cy="94" r="6" fill="#10B981" />
                <circle cx="265" cy="94" r="16" fill="#06241E" stroke="#34D399" strokeWidth="2.5" />
                <circle cx="265" cy="94" r="6" fill="#10B981" />
              </g>
              <line x1="0" y1="110" x2="320" y2="110" stroke="#10B981" strokeWidth="1.5" opacity="0.3" />
              <line x1="30" y1="110" x2="60" y2="110" stroke="#34D399" strokeWidth="2.5" opacity="0.6" />
              <line x1="120" y1="110" x2="160" y2="110" stroke="#34D399" strokeWidth="2.5" opacity="0.6" />
              <line x1="220" y1="110" x2="250" y2="110" stroke="#34D399" strokeWidth="2.5" opacity="0.6" />
            </svg>
          </div>

          {/* Footer note */}
          <div className="relative z-10 pt-3 border-t border-white/10 flex items-center justify-between text-xs" style={{ color: '#A7D4C0' }}>
            <span>Peliyagoda Depot</span>
            <span className="font-mono">Mon, 29 Sep 2026</span>
          </div>
        </div>

        {/* ── Right Cards Stack (Auto Height, responsive on resize) ── */}
        <div 
          className={`w-full lg:w-1/2 p-6 sm:p-8 lg:p-10 flex flex-col justify-center transition-colors ${
            darkMode ? 'bg-[#0E201B]' : 'bg-[#F4F8F6]'
          }`}
        >
          <div className="w-full max-w-lg mx-auto flex flex-col gap-4">

            {/* Offline Readiness Card */}
            <div
              className={`rounded-[20px] p-4 flex items-center gap-3.5 border transition-all ${
                darkMode
                  ? 'bg-[#133026] border-[#1D4A3C]'
                  : 'bg-[#E6F6EC] border-[#86efac]'
              }`}
            >
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ background: '#16A34A' }}
              >
                <CheckCircle size={18} color="white" />
              </div>
              <div>
                <p className={`text-sm font-bold leading-tight ${darkMode ? 'text-emerald-300' : 'text-[#14532D]'}`}>
                  ✓ Offline Mode Ready
                </p>
                <p className={`text-xs mt-0.5 ${darkMode ? 'text-emerald-400/80' : 'text-[#166534]'}`}>
                  Downloaded: 47 stops (3.2 MB)
                </p>
              </div>
            </div>

            {/* Assigned Vehicle Card */}
            <div
              className={`rounded-[20px] p-5 border transition-all ${
                darkMode
                  ? 'bg-[#152B24] border-[#1E3E34]'
                  : 'bg-white border-[#E2ECE7] shadow-xs'
              }`}
            >
              <div className="flex items-center justify-between mb-3 gap-2">
                <div className="flex items-center gap-2.5">
                  <Truck size={20} style={{ color: '#0F9D6C' }} />
                  <span className={`text-xl font-bold tracking-tight tabular-nums ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
                    VEH-014
                  </span>
                </div>
                <span
                  className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-[10px] sm:text-[11px] font-bold uppercase tracking-wider border leading-tight shrink-0 ${
                    darkMode
                      ? 'bg-[#10382E] text-[#34D399] border-[#185344]'
                      : 'bg-[#E8F5EF] text-[#0F9D6C] border-[#C6E8D9]'
                  }`}
                >
                  PELIYAGODA DEPOT
                </span>
              </div>
              <div 
                className={`grid grid-cols-2 gap-4 pt-3.5 border-t ${
                  darkMode ? 'border-[#1E3E34]' : 'border-[#E2ECE7]'
                }`}
              >
                <div>
                  <p className={`text-[10px] uppercase tracking-wider font-semibold mb-1 ${
                    darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
                  }`}>
                    Total Runs
                  </p>
                  <p className={`text-sm font-semibold ${darkMode ? 'text-gray-200' : 'text-[#0E1A17]'}`}>
                    2 Routes
                  </p>
                </div>
                <div>
                  <p className={`text-[10px] uppercase tracking-wider font-semibold mb-1 ${
                    darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
                  }`}>
                    Date
                  </p>
                  <p className={`text-sm font-semibold ${darkMode ? 'text-gray-200' : 'text-[#0E1A17]'}`}>
                    Mon, 29 Sep 2026
                  </p>
                </div>
              </div>
            </div>

            {/* Safety Reminder */}
            <div
              className={`rounded-[20px] p-4 flex items-start gap-3 border ${
                darkMode
                  ? 'bg-[#2A1E0E] border-[#4A3416]'
                  : 'bg-[#FFF4DB] border-[#FDE68A]'
              }`}
            >
              <AlertTriangle size={17} className="text-[#F59E0B] flex-shrink-0 mt-0.5" />
              <p className={`text-xs leading-relaxed font-medium ${darkMode ? 'text-amber-200' : 'text-[#78350F]'}`}>
                Do not operate the mobile screen while the vehicle is in motion. Pull over to a safe area before logging inputs.
              </p>
            </div>

            {/* Primary CTA Hero Button */}
            <button
              type="button"
              onClick={onStart}
              className="w-full inline-flex items-center justify-center gap-2.5 rounded-2xl text-base font-bold text-white transition-all duration-150 active:scale-[0.98] cursor-pointer mt-1 shadow-md hover:shadow-lg"
              style={{
                background: '#0F9D6C',
                minHeight: 56,
              }}
              onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
              onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
            >
              <Play size={17} fill="white" className="shrink-0" />
              <span>START SHIFT</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
