import React from 'react';
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

export default function Screen08Offline({ onContinue, onReviewRoute, darkMode = false }) {
  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>

      {/* Offline alert banner — full width, slate bg */}
      <div
        className={`w-full px-6 py-4 flex items-center gap-3 rounded-[20px] mb-6 border transition-all ${
          darkMode 
            ? 'bg-[#1E293B] border-red-500/50 shadow-lg' 
            : 'bg-[#334155] border-b-2 border-[#E5484D] shadow-sm'
        }`}
      >
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ background: '#E5484D' }}
        >
          <WifiOff size={16} color="white" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase" style={{ background: '#E5484D', color: 'white' }}>● Offline</span>
            <p className="text-sm font-semibold text-white">
              ⚡ Offline Mode Active — No signal near Kegalle. Delays expected.
            </p>
          </div>
        </div>
      </div>

      {/* Main 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">

        {/* Left: Explainer + queue (2/3) */}
        <div className="lg:col-span-2 flex flex-col gap-4">

          {/* Info card */}
          <div
            className={`rounded-[20px] p-5 border transition-all ${
              darkMode 
                ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
                : 'bg-white border-[#E2ECE7] shadow-xs'
            }`}
          >
            <div className="flex items-start gap-3">
              <Zap size={18} className="text-[#F59E0B] flex-shrink-0 mt-0.5" />
              <p className={`text-sm leading-relaxed ${darkMode ? 'text-gray-200' : 'text-[#0E1A17]'}`}>
                Waypoint auto-saves all transaction state locally on your device. Deliveries will process, sign, and sync automatically as soon as mobile networks return.
              </p>
            </div>
          </div>

          {/* Queue list */}
          <div
            className={`rounded-[20px] p-5 border transition-all ${
              darkMode 
                ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
                : 'bg-white border-[#E2ECE7] shadow-xs'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <p className={`text-[11px] uppercase tracking-widest font-semibold ${
                darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
              }`}>
                LOCAL DEVICE QUEUE
              </p>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                  darkMode ? 'bg-[#2A1E0E] text-amber-300 border-[#4A3416]' : 'bg-[#FFF4DB] text-[#B45309] border-[#FDE68A]'
                }`}
              >
                3 WAITING
              </span>
            </div>
            <div className="flex flex-col gap-2.5">
              {queueItems.map(item => (
                <div
                  key={item.id}
                  className={`rounded-xl px-4 py-3 flex items-center justify-between border transition-all ${
                    darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-[#E2ECE7]'
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
                        {item.id} {item.name}
                      </span>
                      <span className={`text-xs ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
                        — {item.outcome}
                      </span>
                      {item.time && (
                        <span className={`text-xs font-mono tabular-nums ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
                          • {item.time}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {item.status === 'saved' ? (
                      <span
                        className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                          darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E6F6EC] text-[#16A34A] border-[#86efac]'
                        }`}
                      >
                        <Check size={10} strokeWidth={3} /> {item.label}
                      </span>
                    ) : (
                      <span
                        className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                          darkMode ? 'bg-[#1E3A8A]/30 text-blue-300 border-[#3B82F6]/50' : 'bg-[#E8F0FF] text-[#3B82F6] border-[#BFDBFE]'
                        }`}
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
          <p className={`text-[11px] uppercase tracking-widest font-semibold ${
            darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
          }`}>
            ALTERNATE RECOVERY STATE PREVIEWS
          </p>

          {/* State 1: Syncing */}
          <div
            className={`rounded-[20px] p-4 border transition-all ${
              darkMode 
                ? 'bg-[#172554] border-[#1E40AF] text-blue-200' 
                : 'bg-[#E8F0FF] border-[#BFDBFE] text-[#1D4ED8]'
            }`}
          >
            <p className="text-xs font-semibold mb-2">State 1 — Syncing</p>
            <p className={`text-xs mb-2 ${darkMode ? 'text-blue-300' : 'text-[#1E40AF]'}`}>
              Syncing — 2 of 3 records uploaded
            </p>
            <div className={`w-full h-2 rounded-full ${darkMode ? 'bg-blue-900/60' : 'bg-[#BFDBFE]'}`}>
              <div className="h-full rounded-full bg-[#3B82F6]" style={{ width: '66%' }} />
            </div>
          </div>

          {/* State 2: Synced */}
          <div
            className={`rounded-[20px] p-4 border transition-all ${
              darkMode 
                ? 'bg-[#10382E] border-[#185344] text-emerald-200' 
                : 'bg-[#E6F6EC] border-[#86efac] text-[#16A34A]'
            }`}
          >
            <p className="text-xs font-semibold mb-2">State 2 — Synced</p>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full flex items-center justify-center bg-[#16A34A]">
                <Check size={14} color="white" strokeWidth={3} />
              </div>
              <p className={`text-xs font-semibold ${darkMode ? 'text-emerald-300' : 'text-[#166534]'}`}>
                ✓ All records synced successfully
              </p>
            </div>
          </div>

          {/* Route conflict card */}
          <div
            className={`rounded-[20px] p-4 border transition-all ${
              darkMode 
                ? 'bg-[#2A1E0E] border-[#4A3416] text-amber-200' 
                : 'bg-[#FFF4DB] border-[#FDE68A] text-[#78350F]'
            }`}
          >
            <div className="flex items-start gap-2 mb-3">
              <AlertTriangle size={14} className="text-[#F59E0B] flex-shrink-0 mt-0.5" />
              <p className={`text-xs font-bold ${darkMode ? 'text-amber-300' : 'text-[#92400E]'}`}>
                ROUTE CONFLICT DETECTED
              </p>
            </div>
            <p className={`text-xs leading-relaxed mb-3 ${darkMode ? 'text-amber-200/90' : 'text-[#78350F]'}`}>
              Stop order changed — Dispatcher moved OUT031 ahead of OUT027 while you were offline. Your records are safe.
            </p>
            <button
              onClick={onReviewRoute}
              className="w-full flex items-center justify-center gap-1.5 rounded-xl py-2 text-xs font-semibold cursor-pointer transition-all bg-[#F59E0B] hover:bg-[#D97706] text-white"
            >
              <ChevronRight size={13} />
              <span>⊙ Review Route Changes</span>
            </button>
          </div>
        </div>
      </div>

      {/* Footer note */}
      <div
        className={`rounded-xl p-4 mb-5 text-center border transition-all ${
          darkMode ? 'bg-[#0E2721] border-[#1F4A3E]' : 'bg-[#0B3D33] border-transparent'
        }`}
      >
        <p className="text-xs" style={{ color: '#A7D4C0' }}>
          No proof of delivery is ever lost. Delivery metrics and outcomes are preserved using unalterable local database queues.
        </p>
      </div>

      {/* CTA */}
      <button
        onClick={onContinue}
        className="w-full px-6 py-4 flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer shadow-md hover:shadow-lg"
        style={{ background: '#0F9D6C', minHeight: 56 }}
        onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
        onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
      >
        <Play size={18} fill="white" />
        <span>▶ CONTINUE SYSTEM OPERATIONS</span>
      </button>
    </div>
  );
}
