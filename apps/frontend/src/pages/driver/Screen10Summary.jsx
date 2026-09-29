import React from 'react';
import { Check, AlertTriangle, Play, Clock, Truck, Fuel, MapPin } from 'lucide-react';

const routeRecap = [
  { id: 'OUT014', name: 'Keells Super', status: 'delivered', time: '06:52', outcome: 'Delivered ✓' },
  { id: 'OUT027', name: 'Cargills Food City', status: 'delivered', time: '07:28', outcome: 'Delivered ✓' },
  { id: 'OUT031', name: 'SPAR Express', status: 'partial', time: '07:55', outcome: 'Partial ⚠ (8 damaged)' },
];

export default function Screen10Summary({ onStartTrip2, darkMode = false }) {
  const metrics = [
    {
      icon: <Clock size={20} className="text-[#0F9D6C]" />,
      label: '⏱ Total Trip Time',
      value: '3h 42m',
      badge: 'UNDER BUDGET',
      badgeColor: darkMode ? '#34D399' : '#16A34A',
      badgeBg: darkMode ? '#10382E' : '#E6F6EC',
    },
    {
      icon: <Truck size={20} className="text-[#0F9D6C]" />,
      label: '🚛 Total Distance',
      value: '47 km driven',
      badge: null,
    },
    {
      icon: <Fuel size={20} className="text-[#0F9D6C]" />,
      label: '⛽ Fuel Economy',
      value: '9.4 km/L ✓',
      badge: null,
    },
  ];

  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>

      {/* Hero header */}
      <div
        className={`rounded-[20px] p-6 mb-6 border transition-all ${
          darkMode 
            ? 'bg-[#0E2721] border-[#1F4A3E] shadow-xl' 
            : 'bg-[#0B3D33] border-transparent shadow-lg'
        }`}
      >
        <p className="text-xs font-semibold uppercase tracking-widest mb-1 text-[#6EE7B7]">
          TRIP COMPLETE
        </p>
        <h1 className="text-2xl font-bold text-white mb-4">Trip 1: Fresh Gampaha Summary</h1>

        {/* Summary pills */}
        <div className="flex flex-wrap gap-3">
          <div
            className={`flex items-center gap-2 px-4 py-2 rounded-full border ${
              darkMode ? 'bg-[#10382E] border-[#185344]' : 'bg-[#E6F6EC] border-[#86efac]'
            }`}
          >
            <Check size={14} className={darkMode ? 'text-[#34D399]' : 'text-[#16A34A]'} strokeWidth={3} />
            <span className={`text-sm font-bold ${darkMode ? 'text-[#34D399]' : 'text-[#14532D]'}`}>2 DELIVERED</span>
          </div>
          <div
            className={`flex items-center gap-2 px-4 py-2 rounded-full border ${
              darkMode ? 'bg-[#2A1E0E] border-[#4A3416]' : 'bg-[#FFF4DB] border-[#FDE68A]'
            }`}
          >
            <AlertTriangle size={14} className="text-[#F59E0B]" />
            <span className={`text-sm font-bold ${darkMode ? 'text-amber-300' : 'text-[#92400E]'}`}>1 PARTIAL</span>
          </div>
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20"
          >
            <span className="text-sm font-bold text-white">0 FAILED</span>
          </div>
        </div>
      </div>

      {/* Performance metrics grid */}
      <div className="mb-5">
        <p className={`text-[11px] uppercase tracking-widest font-semibold mb-3 ${
          darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
        }`}>
          PERFORMANCE METRICS
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {metrics.map(m => (
            <div
              key={m.label}
              className={`rounded-[20px] p-5 border transition-all ${
                darkMode 
                  ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
                  : 'bg-white border-[#E2ECE7] shadow-xs'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">{m.icon}</div>
              <p className={`text-xs mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>{m.label}</p>
              <p className={`text-2xl font-bold tabular-nums ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>{m.value}</p>
              {m.badge && (
                <span
                  className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wide border"
                  style={{ 
                    background: m.badgeBg, 
                    color: m.badgeColor,
                    borderColor: darkMode ? '#185344' : '#86efac'
                  }}
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
        className={`rounded-[20px] p-6 mb-5 border transition-all ${
          darkMode 
            ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
            : 'bg-white border-[#E2ECE7] shadow-xs'
        }`}
      >
        <p className={`text-[11px] uppercase tracking-widest font-semibold mb-4 ${
          darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
        }`}>
          ROUTE RECAP
        </p>
        <div className="flex flex-col gap-2.5">
          {routeRecap.map(stop => (
            <div
              key={stop.id}
              className={`flex items-center justify-between rounded-xl px-4 py-3 border transition-all ${
                stop.status === 'partial' 
                  ? darkMode ? 'bg-[#2A1E0E] border-[#4A3416]' : 'bg-[#FFF4DB] border-[#FDE68A]'
                  : darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-[#E2ECE7]'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center border ${
                    stop.status === 'delivered' 
                      ? darkMode ? 'bg-[#10382E] border-[#185344]' : 'bg-[#E6F6EC] border-[#86efac]'
                      : darkMode ? 'bg-[#3D280B] border-[#5E3F12]' : 'bg-[#FFF4DB] border-[#FDE68A]'
                  }`}
                >
                  {stop.status === 'delivered'
                    ? <Check size={14} className={darkMode ? 'text-[#34D399]' : 'text-[#16A34A]'} strokeWidth={3} />
                    : <AlertTriangle size={14} className="text-[#F59E0B]" />
                  }
                </div>
                <div>
                  <p className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-[#0E1A17]'}`}>
                    {stop.id} {stop.name}
                  </p>
                  <p className={`text-xs ${
                    stop.status === 'partial' 
                      ? darkMode ? 'text-amber-300' : 'text-[#B45309]' 
                      : darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
                  }`}>
                    → {stop.outcome}
                  </p>
                </div>
              </div>
              <span className={`text-sm font-mono font-bold tabular-nums ${darkMode ? 'text-emerald-300' : 'text-[#0B3D33]'}`}>
                {stop.time}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Next step card */}
      <div
        className={`rounded-[20px] p-5 mb-5 flex items-center gap-4 border transition-all ${
          darkMode 
            ? 'bg-[#10382E] border-[#185344] text-emerald-200' 
            : 'bg-[#E8F5EF] border-[#C6E8D9] text-[#0B3D33]'
        }`}
      >
        <MapPin size={20} className="text-[#0F9D6C] flex-shrink-0" />
        <div>
          <p className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
            Next Step: Please proceed back to Peliyagoda Depot.
          </p>
          <p className={`text-xs mt-0.5 ${darkMode ? 'text-emerald-300/80' : 'text-[#5B6B66]'}`}>
            Expected Return ETA: <span className="font-semibold font-mono tabular-nums">08:30 AM</span>
          </p>
        </div>
      </div>

      {/* CTA + footer */}
      <div className="flex flex-col gap-3">
        <button
          onClick={onStartTrip2}
          className="w-full px-6 py-4 flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer shadow-md hover:shadow-lg"
          style={{ background: '#0F9D6C', minHeight: 56 }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
          onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
        >
          <Play size={18} fill="white" />
          <span>▶ START TRIP 2 PREPARATION</span>
        </button>
        <p className={`text-xs text-center ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
          Next: Trip 2 — Colombo Depot, 4 stops
        </p>
      </div>
    </div>
  );
}
