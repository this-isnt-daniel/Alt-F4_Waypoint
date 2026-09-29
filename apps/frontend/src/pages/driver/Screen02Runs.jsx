import React from 'react';
import { Lock, Snowflake, Play, LifeBuoy, Package, Weight } from 'lucide-react';

export default function Screen02Runs({ onStartTrip }) {
  return (
    <div className="max-w-7xl mx-auto px-6 py-8" style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>

      {/* Page header + KPI strip */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1" style={{ color: '#0B3D33' }}>TODAY'S RUN TARGETS</h1>
        <div className="flex items-center gap-4">
          <span
            className="px-3 py-1 rounded-full text-sm font-semibold"
            style={{ background: '#0F9D6C', color: 'white' }}
          >
            7 Stops
          </span>
          <span
            className="px-3 py-1 rounded-full text-sm font-semibold"
            style={{ background: '#0B3D33', color: 'white' }}
          >
            2,100 Units
          </span>
        </div>
      </div>

      {/* Section label */}
      <p
        className="text-xs font-semibold uppercase tracking-[0.18em] mb-4"
        style={{ color: '#5B6B66' }}
      >
        ASSIGNED TRIPS (2)
      </p>

      {/* Trip Cards – 2-column grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5 mb-8">

        {/* Trip 1 — Active */}
        <div
          className="rounded-[20px] overflow-hidden relative"
          style={{
            background: '#FFFFFF',
            border: '1px solid #E2ECE7',
            boxShadow: '0 8px 24px rgba(11,61,51,0.10)',
          }}
        >
          {/* Emerald left rail */}
          <div
            className="absolute inset-y-0 left-0 w-1.5 rounded-l-[20px]"
            style={{ background: '#0F9D6C' }}
          />
          <div className="pl-7 pr-6 py-5">
            {/* Card header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span
                  className="w-2 h-2 rounded-full inline-block"
                  style={{ background: '#0F9D6C' }}
                />
                <span className="text-lg font-bold" style={{ color: '#0E1A17' }}>
                  Fresh — Gampaha
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Snowflake size={13} style={{ color: '#14B8A6' }} />
                <span
                  className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase tracking-wide"
                  style={{ background: '#E0FFFE', color: '#0F766E', border: '1px solid #99F6E4' }}
                >
                  CHILLED REEFER
                </span>
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              {[
                { label: 'Stops', value: '3 Deliveries' },
                { label: 'Weight', value: '890 kg' },
                { label: 'Volume', value: '4.2 m³' },
                { label: 'Load', value: '1,240 Units' },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-xl p-3" style={{ background: '#F4F8F6' }}>
                  <p className="text-[11px] uppercase tracking-wide font-semibold mb-0.5" style={{ color: '#5B6B66' }}>
                    {label}
                  </p>
                  <p className="text-sm font-bold tabular-nums" style={{ color: '#0E1A17' }}>{value}</p>
                </div>
              ))}
            </div>

            {/* Times */}
            <div
              className="flex items-center justify-between rounded-xl px-4 py-2.5 mb-4"
              style={{ background: '#E8F5EF', border: '1px solid #C6E8D9' }}
            >
              <div>
                <p className="text-[11px] uppercase tracking-wide font-semibold" style={{ color: '#5B6B66' }}>Depart</p>
                <p className="text-sm font-bold tabular-nums" style={{ color: '#0B3D33' }}>05:45 AM</p>
              </div>
              <div className="h-8 w-px" style={{ background: '#C6E8D9' }} />
              <div className="text-right">
                <p className="text-[11px] uppercase tracking-wide font-semibold" style={{ color: '#5B6B66' }}>ETA Return</p>
                <p className="text-sm font-bold tabular-nums" style={{ color: '#0B3D33' }}>09:30 AM</p>
              </div>
            </div>

            {/* CTA */}
            <button
              onClick={onStartTrip}
              className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white transition-all active:scale-[0.98] cursor-pointer"
              style={{ background: '#0F9D6C', height: 52 }}
              onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
              onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
            >
              <Play size={15} fill="white" />
              START TRIP 1
            </button>
          </div>
        </div>

        {/* Trip 2 — Locked */}
        <div
          className="rounded-[20px] overflow-hidden relative opacity-60"
          style={{
            background: '#FFFFFF',
            border: '1px solid #E2ECE7',
            boxShadow: '0 4px 12px rgba(11,61,51,0.04)',
          }}
        >
          {/* Grey left rail */}
          <div
            className="absolute inset-y-0 left-0 w-1.5 rounded-l-[20px]"
            style={{ background: '#CBD5E1' }}
          />
          <div className="pl-7 pr-6 py-5">
            {/* Card header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span
                  className="w-2 h-2 rounded-full inline-block"
                  style={{ background: '#CBD5E1' }}
                />
                <span className="text-lg font-bold" style={{ color: '#94A3B8' }}>
                  Style — Colombo
                </span>
              </div>
              <span
                className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase tracking-wide"
                style={{ background: '#F1F5F9', color: '#64748B', border: '1px solid #CBD5E1' }}
              >
                <Lock size={10} />
                LOCKED
              </span>
            </div>

            {/* Stats grid – muted */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              {[
                { label: 'Stops', value: '4 Deliveries' },
                { label: 'Weight', value: '540 kg' },
                { label: 'Volume', value: '2.8 m³' },
                { label: 'Load', value: '860 Units' },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-xl p-3" style={{ background: '#F8FAFC' }}>
                  <p className="text-[11px] uppercase tracking-wide font-semibold mb-0.5" style={{ color: '#94A3B8' }}>
                    {label}
                  </p>
                  <p className="text-sm font-bold tabular-nums" style={{ color: '#94A3B8' }}>{value}</p>
                </div>
              ))}
            </div>

            {/* Locked CTA */}
            <div
              className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold"
              style={{
                background: '#F1F5F9',
                color: '#64748B',
                height: 52,
                border: '1px dashed #CBD5E1',
              }}
            >
              <Lock size={14} />
              LOCKED UNTIL TRIP 1 DONE
            </div>
          </div>
        </div>
      </div>

      {/* Footer link */}
      <div className="flex justify-center">
        <button
          className="text-sm font-medium underline cursor-pointer transition-opacity hover:opacity-70"
          style={{ color: '#0F9D6C' }}
        >
          Need Dispatch Assistance? Tap here
        </button>
      </div>
    </div>
  );
}
