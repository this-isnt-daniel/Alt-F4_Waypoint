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

export default function Screen03Checklist({ onConfirm }) {
  return (
    <div className="max-w-7xl mx-auto px-6 py-8" style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>

      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: '#0B3D33' }}>PRE-DEPARTURE CHECK</h1>
        <p className="text-sm mt-1" style={{ color: '#5B6B66' }}>Trip 1: Fresh Gampaha</p>
      </div>

      {/* Main 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 mb-5">

        {/* Left: Loader verification (3/5) */}
        <div
          className="lg:col-span-3 rounded-[20px] p-6"
          style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
        >
          {/* Loader header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-[11px] uppercase tracking-widest font-semibold mb-1" style={{ color: '#5B6B66' }}>
                LOADER VERIFICATION
              </p>
              <p className="text-base font-bold" style={{ color: '#0E1A17' }}>Amila (Loader)</p>
            </div>
            <span
              className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide"
              style={{ background: '#E8F5EF', color: '#0F9D6C', border: '1px solid #C6E8D9' }}
            >
              AMILA (LOADER)
            </span>
          </div>

          {/* Items table */}
          <div className="rounded-xl overflow-hidden" style={{ border: '1px solid #E2ECE7' }}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: '#F4F8F6' }}>
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: '#5B6B66' }}>Item</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: '#5B6B66' }}>Units</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: '#5B6B66' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {loaderItems.map((item) => (
                  <tr
                    key={item.name}
                    style={{
                      background: item.status === 'warn' ? '#FFF4DB' : 'transparent',
                      borderTop: '1px solid #E2ECE7',
                    }}
                  >
                    <td className="px-4 py-3 font-medium" style={{ color: '#0E1A17' }}>{item.name}</td>
                    <td className="px-4 py-3 font-mono tabular-nums" style={{ color: '#5B6B66' }}>{item.units}</td>
                    <td className="px-4 py-3">
                      <span
                        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold"
                        style={
                          item.status === 'ok'
                            ? { background: '#E6F6EC', color: '#16A34A' }
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
            className="mt-4 rounded-xl p-4 flex items-start gap-3"
            style={{ background: '#FFF4DB', border: '1px solid #FDE68A' }}
          >
            <AlertTriangle size={16} style={{ color: '#F59E0B', flexShrink: 0, marginTop: 1 }} />
            <p className="text-xs" style={{ color: '#78350F' }}>
              Loader flagged: <strong>8 units missing (damaged in warehouse).</strong>
            </p>
          </div>
        </div>

        {/* Right: Vehicle & temp checks (2/5) */}
        <div
          className="lg:col-span-2 rounded-[20px] p-6"
          style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
        >
          <p className="text-[11px] uppercase tracking-widest font-semibold mb-4" style={{ color: '#5B6B66' }}>
            VEHICLE &amp; TEMP CHECKS
          </p>
          <div className="flex flex-col gap-3">
            {vehicleChecks.map(({ label, value, ok }) => (
              <div
                key={label}
                className="flex items-center justify-between rounded-xl px-4 py-3"
                style={{ background: '#F4F8F6', border: '1px solid #E2ECE7' }}
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center"
                    style={{ background: '#E6F6EC' }}
                  >
                    <Check size={13} style={{ color: '#16A34A' }} />
                  </div>
                  <span className="text-xs font-medium" style={{ color: '#5B6B66' }}>{label}</span>
                </div>
                <span className="text-sm font-bold tabular-nums" style={{ color: '#0B3D33' }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Summary banner */}
      <div
        className="rounded-[20px] p-5 mb-5"
        style={{ background: '#E8F5EF', border: '1px solid #C6E8D9' }}
      >
        <p className="text-sm font-semibold" style={{ color: '#0B3D33' }}>
          412 of 420 units loaded — 8 units short (flagged by loader). Reefer temp stable at 4°C.
        </p>
      </div>

      {/* CTA + Footer note */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <button
          onClick={onConfirm}
          className="flex-1 flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white transition-all active:scale-[0.98] cursor-pointer"
          style={{ background: '#0F9D6C', height: 64, boxShadow: '0 4px 14px rgba(15,157,108,0.35)' }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
          onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
        >
          <CheckCircle size={18} />
          ✓ CONFIRM DEPARTURE
        </button>
        <p className="text-xs text-center sm:text-right" style={{ color: '#5B6B66', maxWidth: 260 }}>
          Shortfall has been reported to dispatcher.
        </p>
      </div>

      {/* UX Rationale */}
      <div className="rounded-xl p-4 mt-6" style={{ background: '#E8F5EF', border: '1px solid #C6E8D9' }}>
        <p className="text-[11px] uppercase tracking-widest font-semibold mb-1.5" style={{ color: '#0F9D6C' }}>
          UX Rationale · Screen 03
        </p>
        <p className="text-xs leading-relaxed" style={{ color: '#374151' }}>
          Bridges the Loader and Driver roles. Surfacing loader shortfall flags here lets the driver catch discrepancies before leaving the depot — not at the outlet. The 8-unit yogurt shortfall flows through to the store manager as an expected partial delivery, preventing disputes.
        </p>
      </div>
    </div>
  );
}
