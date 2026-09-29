import React from 'react';
import { Bell, Check, ArrowRight, ArrowUpDown } from 'lucide-react';

const newTimeline = [
  {
    id: 'OUT014',
    name: 'Keells Super',
    status: 'delivered',
    time: '06:12 AM',
    note: 'Delivered',
    note2: null,
  },
  {
    id: 'OUT031',
    name: 'SPAR Express',
    status: 'next',
    time: 'ETA 07:05 AM',
    note: 'Was Stop 3',
  },
  {
    id: 'OUT027',
    name: 'Cargills Food City',
    status: 'then',
    time: 'ETA 07:40 AM',
    note: 'Was Stop 2',
  },
];

export default function Screen09RouteChange({ onAcknowledge, darkMode = false }) {
  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>

      {/* Amber alert banner */}
      <div
        className={`rounded-[20px] p-5 mb-6 flex items-start gap-4 border transition-all ${
          darkMode 
            ? 'bg-[#2A1E0E] border-[#4A3416] text-amber-200 shadow-lg' 
            : 'bg-[#FFF4DB] border-[#FDE68A] text-[#78350F] shadow-xs'
        }`}
      >
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 bg-[#F59E0B]"
        >
          <Bell size={18} color="white" />
        </div>
        <div>
          <p className={`text-sm font-bold ${darkMode ? 'text-amber-300' : 'text-[#92400E]'}`}>
            🔔 Route Update from Dispatcher
          </p>
          <p className={`text-xs mt-0.5 ${darkMode ? 'text-amber-200/90' : 'text-[#78350F]'}`}>
            Urgent adjustment based on receiver window.
          </p>
        </div>
        <span className={`ml-auto text-xs font-mono tabular-nums font-semibold ${darkMode ? 'text-amber-300' : 'text-[#92400E]'}`}>
          06:35 AM
        </span>
      </div>

      {/* 2-column: Before/After comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">

        {/* Left: Rearranged trip sequence detail */}
        <div
          className={`rounded-[20px] p-6 border transition-all ${
            darkMode 
              ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
              : 'bg-white border-[#E2ECE7] shadow-xs'
          }`}
        >
          <p className={`text-[11px] uppercase tracking-widest font-semibold mb-4 ${
            darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
          }`}>
            REARRANGED TRIP SEQUENCE
          </p>

          <div
            className={`rounded-xl p-4 mb-4 flex items-start gap-3 border ${
              darkMode ? 'bg-[#2A1E0E] border-[#4A3416]' : 'bg-[#FFF4DB] border-[#FDE68A]'
            }`}
          >
            <ArrowUpDown size={16} className="text-[#F59E0B] flex-shrink-0 mt-0.5" />
            <div>
              <p className={`text-sm font-bold ${darkMode ? 'text-amber-300' : 'text-[#92400E]'}`}>
                Stop order changed
              </p>
              <p className={`text-xs mt-1 leading-relaxed ${darkMode ? 'text-amber-200/90' : 'text-[#78350F]'}`}>
                OUT031 SPAR Express moved <strong>BEFORE</strong> OUT027 Cargills Food City.
              </p>
              <p className={`text-xs mt-1.5 font-semibold ${darkMode ? 'text-amber-300' : 'text-[#B45309]'}`}>
                Reason: SPAR mall receiving window closes strictly at 07:00.
              </p>
            </div>
          </div>

          <p className={`text-xs leading-relaxed ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
            This update was queued while you were offline and delivered immediately when your mobile signal returned.
          </p>
        </div>

        {/* Right: New route timeline */}
        <div
          className={`rounded-[20px] p-6 border transition-all ${
            darkMode 
              ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
              : 'bg-white border-[#E2ECE7] shadow-xs'
          }`}
        >
          <p className={`text-[11px] uppercase tracking-widest font-semibold mb-4 ${
            darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
          }`}>
            NEW ESTIMATED ROUTE TIMELINE
          </p>

          <div className="relative pl-6">
            {/* Connector */}
            <div
              className={`absolute left-[10px] top-3 bottom-3 w-0.5 ${
                darkMode ? 'bg-[#1F3D35]' : 'bg-[#E2ECE7]'
              }`}
            />

            {newTimeline.map((stop, idx) => {
              const isDelivered = stop.status === 'delivered';
              const isNext = stop.status === 'next';
              return (
                <div key={stop.id} className={`relative ${idx < newTimeline.length - 1 ? 'mb-5' : ''}`}>
                  {/* Node */}
                  <div
                    className="absolute -left-6 w-5 h-5 rounded-full flex items-center justify-center"
                    style={{
                      background: isDelivered ? '#0F9D6C' : isNext ? '#0F9D6C' : darkMode ? '#16332B' : 'white',
                      border: isDelivered || isNext ? 'none' : darkMode ? '2px solid #2E5A4E' : '2px solid #CBD5E1',
                    }}
                  >
                    {isDelivered && <Check size={11} color="white" strokeWidth={3} />}
                    {isNext && (
                      <span className="w-2.5 h-2.5 rounded-full block bg-white" />
                    )}
                  </div>

                  <div
                    className={`rounded-xl p-3 border transition-all ${
                      isNext 
                        ? darkMode ? 'bg-[#10382E] border-[#185344]' : 'bg-[#E8F5EF] border-[#C6E8D9]'
                        : isDelivered 
                          ? 'bg-transparent border-transparent' 
                          : darkMode ? 'bg-[#16332B] border-[#1F3D35] opacity-75' : 'bg-[#F8FAFC] border-transparent opacity-75'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          {isDelivered && <span className="text-[11px] font-bold text-[#0F9D6C]">✓ Stop 1:</span>}
                          {isNext && <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#0F9D6C] text-white">NEXT →</span>}
                          {stop.status === 'then' && <span className={`text-[11px] font-semibold ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>THEN →</span>}
                          <span className={`text-xs font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>{stop.id} {stop.name}</span>
                        </div>
                        <p className={`text-[11px] tabular-nums mt-0.5 font-mono ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
                          {stop.time}
                          {stop.note && <span className="ml-2">• {stop.note}</span>}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* CTA + footer */}
      <div className="flex flex-col gap-3">
        <button
          onClick={onAcknowledge}
          className="w-full px-6 py-4 flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer shadow-md hover:shadow-lg"
          style={{ background: '#0F9D6C', minHeight: 56 }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
          onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
        >
          <Check size={18} />
          <span>✓ ACKNOWLEDGE &amp; UPDATE ROUTE</span>
        </button>
        <p className={`text-xs text-center ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
          Dispatcher: Nalini · Updated 06:35 AM
        </p>
      </div>
    </div>
  );
}
