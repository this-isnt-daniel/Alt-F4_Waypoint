import React, { useState } from 'react';
import { Clock, MapPin, AlertTriangle, Navigation, Package } from 'lucide-react';

const orderItems = [
  { item: 'Fresh Milk', qty: '240 u', weight: '180 kg', vol: '1.2 m³' },
  { item: 'Fresh Juice', qty: '120 u', weight: '85 kg', vol: '0.6 m³' },
  { item: 'Yogurt', qty: '60 u', weight: '45 kg', vol: '0.4 m³' },
];

export default function Screen05StopDetail({ onArrived, onProblem, darkMode = false }) {
  const [arrived, setArrived] = useState(false);
  const [unloadingStarted, setUnloadingStarted] = useState(false);

  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>

      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <p className={`text-sm font-semibold ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>STOP 1 OF 3 · OUT-014</p>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
              darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E6F6EC] text-[#16A34A] border-[#86efac]'
            }`}>
              ON TIME
            </span>
          </div>
          <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
            Keells Super — Gampaha
          </h1>
          <div className="flex items-center gap-1.5 mt-1">
            <MapPin size={13} className={darkMode ? 'text-gray-400' : 'text-[#5B6B66]'} />
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>23 Colombo Road, Gampaha</p>
          </div>
        </div>
      </div>

      {/* Countdown card — full width hero */}
      <div
        className={`rounded-[20px] p-6 mb-6 flex items-center justify-between border transition-all ${
          darkMode 
            ? 'bg-[#0E2721] border-[#1F4A3E] shadow-xl' 
            : 'bg-[#0B3D33] border-transparent shadow-lg'
        }`}
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
          className={`rounded-[20px] p-6 border transition-all ${
            darkMode 
              ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
              : 'bg-white border-[#E2ECE7] shadow-xs'
          }`}
        >
          <p className={`text-[11px] uppercase tracking-widest font-semibold mb-3 ${
            darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
          }`}>
            UNLOADING INSTRUCTIONS
          </p>
          <p className={`text-sm leading-relaxed ${darkMode ? 'text-gray-200' : 'text-[#0E1A17]'}`}>
            Use rear dock, report to goods receiving. Keep reefers running until delivery confirmation.
          </p>
        </div>

        {/* Right: Order content table */}
        <div
          className={`rounded-[20px] p-6 border transition-all ${
            darkMode 
              ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
              : 'bg-white border-[#E2ECE7] shadow-xs'
          }`}
        >
          <p className={`text-[11px] uppercase tracking-widest font-semibold mb-3 ${
            darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
          }`}>
            ORDER CONTENT DETAILS
          </p>
          <div className={`rounded-xl overflow-hidden border ${
            darkMode ? 'border-[#1F3D35]' : 'border-[#E2ECE7]'
          }`}>
            <table className="w-full text-xs">
              <thead>
                <tr className={darkMode ? 'bg-[#16332B]' : 'bg-[#F4F8F6]'}>
                  {['Item', 'Qty', 'Weight', 'Vol'].map(h => (
                    <th key={h} className={`text-left px-3 py-2.5 font-semibold uppercase tracking-wide ${
                      darkMode ? 'text-gray-300' : 'text-[#5B6B66]'
                    }`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className={darkMode ? 'divide-y divide-[#1F3D35]' : 'divide-y divide-[#E2ECE7]'}>
                {orderItems.map(row => (
                  <tr key={row.item} className={darkMode ? 'hover:bg-[#16332B]/50' : 'hover:bg-gray-50/50'}>
                    <td className={`px-3 py-2.5 font-medium ${darkMode ? 'text-white' : 'text-[#0E1A17]'}`}>{row.item}</td>
                    <td className={`px-3 py-2.5 font-mono tabular-nums ${darkMode ? 'text-gray-300' : 'text-[#5B6B66]'}`}>{row.qty}</td>
                    <td className={`px-3 py-2.5 font-mono tabular-nums ${darkMode ? 'text-gray-300' : 'text-[#5B6B66]'}`}>{row.weight}</td>
                    <td className={`px-3 py-2.5 font-mono tabular-nums ${darkMode ? 'text-gray-300' : 'text-[#5B6B66]'}`}>{row.vol}</td>
                  </tr>
                ))}
                {/* Total row */}
                <tr className={`border-t-2 ${
                  darkMode ? 'border-[#1F3D35] bg-[#16332B]' : 'border-[#E2ECE7] bg-[#F4F8F6]'
                }`}>
                  <td className={`px-3 py-2.5 font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>Total</td>
                  <td className={`px-3 py-2.5 font-bold tabular-nums font-mono ${darkMode ? 'text-emerald-300' : 'text-[#0B3D33]'}`}>420 u</td>
                  <td className={`px-3 py-2.5 font-bold tabular-nums font-mono ${darkMode ? 'text-emerald-300' : 'text-[#0B3D33]'}`}>310 kg</td>
                  <td className={`px-3 py-2.5 font-bold tabular-nums font-mono ${darkMode ? 'text-emerald-300' : 'text-[#0B3D33]'}`}>2.2 m³</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Action buttons row (Responsive across mobile, tablet, desktop) */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        {/* Report a problem (ghost red) */}
        <button
          onClick={onProblem}
          className={`w-full sm:w-auto px-5 flex items-center justify-center gap-2 rounded-2xl text-sm font-semibold transition-all active:scale-[0.98] cursor-pointer border ${
            darkMode
              ? 'border-red-900/80 text-red-400 hover:bg-red-950/40'
              : 'border-[#fca5a5] text-[#E5484D] hover:bg-[#FDECEC]'
          }`}
          style={{ minHeight: 52 }}
        >
          <AlertTriangle size={16} />
          <span>⚠ Report a Problem</span>
        </button>

        {/* Arrived CTA (primary) */}
        <button
          onClick={() => { setArrived(true); }}
          className="w-full sm:flex-1 px-4 flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white transition-all active:scale-[0.98] cursor-pointer shadow-md hover:shadow-lg"
          style={{
            minHeight: 56,
            background: arrived ? '#0B7F57' : '#0F9D6C',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
          onMouseLeave={e => (e.currentTarget.style.background = arrived ? '#0B7F57' : '#0F9D6C')}
        >
          <Navigation size={18} />
          <span className="text-center">{arrived ? '✓ Arrived — Begin Unloading' : '⊙ ARRIVED AT OUTLET (TAP TARGET)'}</span>
        </button>

        {/* Start unloading (disabled until arrived) */}
        <button
          disabled={!arrived}
          onClick={() => {
            setUnloadingStarted(true);
            onArrived();
          }}
          className={`w-full sm:w-auto px-5 flex items-center justify-center gap-2 rounded-2xl text-sm font-semibold transition-all cursor-pointer border ${
            arrived
              ? darkMode
                ? 'bg-[#10382E] text-[#34D399] border-[#185344] hover:bg-[#16483A]'
                : 'bg-[#E8F5EF] text-[#0F9D6C] border-[#C6E8D9] hover:bg-[#DCF2E7]'
              : darkMode
                ? 'bg-[#162923] text-gray-500 border-[#1F3D35] cursor-not-allowed'
                : 'bg-[#F1F5F9] text-[#94A3B8] border-[#E2E8F0] cursor-not-allowed'
          }`}
          style={{ minHeight: 52 }}
        >
          <Package size={16} />
          <span>Start Unloading</span>
        </button>
      </div>
    </div>
  );
}
