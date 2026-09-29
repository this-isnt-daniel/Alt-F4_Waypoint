import React from 'react';
import { Check, AlertTriangle, Thermometer, Fuel, CheckCircle, FileText } from 'lucide-react';

const loaderItems = [
  { name: 'Fresh Milk', units: '240 units', status: 'ok', label: '✓ LOADED' },
  { name: 'Fresh Juice', units: '120 units', status: 'ok', label: '✓ LOADED' },
  { name: 'Yogurt', units: '60 units', status: 'warn', label: '⚠ SHORTFALL' },
];

const vehicleChecks = [
  { label: 'Reefer Temperature', value: '4°C ✓', ok: true },
  { label: 'Fuel Level', value: '¾ Tank ✓', ok: true },
  { label: 'Tyres & Pressure', value: 'OK ✓', ok: true },
  { label: 'Waybills & Documents', value: 'OK ✓', ok: true },
];

export default function Screen03Checklist({ onConfirm, darkMode = false }) {
  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>

      {/* Page header */}
      <div className="mb-6">
        <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
          PRE-DEPARTURE CHECK
        </h1>
        <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
          Trip 1: Fresh Gampaha
        </p>
      </div>

      {/* Main 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 mb-5">

        {/* Left: Loader verification (3/5) */}
        <div
          className={`lg:col-span-3 rounded-[20px] p-6 border transition-all ${
            darkMode 
              ? 'bg-[#122822] border-[#1F3D35] shadow-lg' 
              : 'bg-white border-[#E2ECE7] shadow-sm'
          }`}
        >
          {/* Loader header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className={`text-[11px] uppercase tracking-widest font-semibold mb-1 ${
                darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
              }`}>
                LOADER VERIFICATION
              </p>
              <p className={`text-base font-bold ${darkMode ? 'text-white' : 'text-[#0E1A17]'}`}>
                Amila (Loader)
              </p>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide border ${
                darkMode 
                  ? 'bg-[#10382E] text-[#34D399] border-[#185344]' 
                  : 'bg-[#E8F5EF] text-[#0F9D6C] border-[#C6E8D9]'
              }`}
            >
              AMILA (LOADER)
            </span>
          </div>

          {/* Items table */}
          <div className={`rounded-xl overflow-hidden border ${
            darkMode ? 'border-[#1F3D35]' : 'border-[#E2ECE7]'
          }`}>
            <table className="w-full text-sm">
              <thead>
                <tr className={darkMode ? 'bg-[#16332B]' : 'bg-[#F4F8F6]'}>
                  <th className={`text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide ${
                    darkMode ? 'text-gray-300' : 'text-[#5B6B66]'
                  }`}>Item</th>
                  <th className={`text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide ${
                    darkMode ? 'text-gray-300' : 'text-[#5B6B66]'
                  }`}>Units</th>
                  <th className={`text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide ${
                    darkMode ? 'text-gray-300' : 'text-[#5B6B66]'
                  }`}>Status</th>
                </tr>
              </thead>
              <tbody className={darkMode ? 'divide-y divide-[#1F3D35]' : 'divide-y divide-[#E2ECE7]'}>
                {loaderItems.map((item) => (
                  <tr
                    key={item.name}
                    className={`transition-colors ${
                      item.status === 'warn'
                        ? darkMode ? 'bg-[#2A1E0E]/40' : 'bg-[#FFF4DB]'
                        : darkMode ? 'hover:bg-[#16332B]/50' : 'hover:bg-gray-50/50'
                    }`}
                  >
                    <td className={`px-4 py-3 font-medium ${darkMode ? 'text-white' : 'text-[#0E1A17]'}`}>
                      {item.name}
                    </td>
                    <td className={`px-4 py-3 font-mono tabular-nums ${darkMode ? 'text-gray-300' : 'text-[#5B6B66]'}`}>
                      {item.units}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold"
                        style={
                          item.status === 'ok'
                            ? darkMode
                              ? { background: '#10382E', color: '#34D399', border: '1px solid #185344' }
                              : { background: '#E6F6EC', color: '#16A34A', border: '1px solid #bbf7d0' }
                            : darkMode
                              ? { background: '#2A1E0E', color: '#FCD34D', border: '1px solid #4A3416' }
                              : { background: '#FFF4DB', color: '#B45309', border: '1px solid #FDE68A' }
                        }
                      >
                        {item.status === 'ok' ? <Check size={11} /> : <AlertTriangle size={11} />}
                        {item.label}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Shortfall note */}
          <div
            className={`mt-4 rounded-xl p-4 flex items-start gap-3 border ${
              darkMode 
                ? 'bg-[#2A1E0E] border-[#4A3416] text-amber-200' 
                : 'bg-[#FFF4DB] border-[#FDE68A] text-[#78350F]'
            }`}
          >
            <AlertTriangle size={16} className="text-[#F59E0B] flex-shrink-0 mt-0.5" />
            <p className="text-xs">
              Loader flagged: <strong className={darkMode ? 'text-amber-100 font-bold' : ''}>8 units missing (damaged in warehouse).</strong>
            </p>
          </div>
        </div>

        {/* Right: Vehicle & temp checks (2/5) */}
        <div
          className={`lg:col-span-2 rounded-[20px] p-6 border transition-all ${
            darkMode 
              ? 'bg-[#122822] border-[#1F3D35] shadow-lg' 
              : 'bg-white border-[#E2ECE7] shadow-sm'
          }`}
        >
          <p className={`text-[11px] uppercase tracking-widest font-semibold mb-4 ${
            darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
          }`}>
            VEHICLE &amp; TEMP CHECKS
          </p>
          <div className="flex flex-col gap-3">
            {vehicleChecks.map(({ label, value, ok }) => (
              <div
                key={label}
                className={`flex items-center justify-between rounded-xl px-4 py-3 border ${
                  darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-[#E2ECE7]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center"
                    style={{ background: darkMode ? '#10382E' : '#E6F6EC' }}
                  >
                    <Check size={13} style={{ color: darkMode ? '#34D399' : '#16A34A' }} />
                  </div>
                  <span className={`text-xs font-medium ${darkMode ? 'text-gray-300' : 'text-[#5B6B66]'}`}>
                    {label}
                  </span>
                </div>
                <span className={`text-sm font-bold tabular-nums ${darkMode ? 'text-emerald-300' : 'text-[#0B3D33]'}`}>
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Summary banner */}
      <div
        className={`rounded-[20px] p-5 mb-5 border transition-all ${
          darkMode 
            ? 'bg-[#10382E] border-[#185344] text-emerald-200' 
            : 'bg-[#E8F5EF] border-[#C6E8D9] text-[#0B3D33]'
        }`}
      >
        <p className="text-sm font-semibold">
          412 of 420 units loaded — 8 units short (flagged by loader). Reefer temp stable at 4°C.
        </p>
      </div>

      {/* CTA + Footer note */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
        <button
          onClick={onConfirm}
          className="w-full sm:flex-1 px-6 py-4 flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white transition-all active:scale-[0.98] cursor-pointer shadow-md hover:shadow-lg"
          style={{ background: '#0F9D6C', minHeight: 56 }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
          onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
        >
          <CheckCircle size={18} />
          <span>✓ CONFIRM DEPARTURE</span>
        </button>
        <p className={`text-xs text-center sm:text-right ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`} style={{ maxWidth: 260 }}>
          Shortfall has been reported to dispatcher.
        </p>
      </div>
    </div>
  );
}
