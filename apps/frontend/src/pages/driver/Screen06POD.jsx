import React, { useState } from 'react';
import { Check, Camera, MapPin, Clock, Smartphone, FileText, ChevronRight } from 'lucide-react';

const outcomes = ['✓ Full Delivery', 'Partial', 'Rejected'];

export default function Screen06POD({ onConfirm }) {
  const [selected, setSelected] = useState('✓ Full Delivery');
  const [photoTaken, setPhotoTaken] = useState(false);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8" style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>

      {/* Step breadcrumb */}
      <div className="flex items-center gap-2 mb-2">
        {['Arrived', 'Unloading', 'Proof of Delivery'].map((step, i) => (
          <React.Fragment key={step}>
            <span
              className="text-xs font-semibold"
              style={{ color: i === 2 ? '#0F9D6C' : '#5B6B66', fontWeight: i === 2 ? 700 : 500 }}
            >
              {step}
            </span>
            {i < 2 && <ChevronRight size={12} style={{ color: '#CBD5E1' }} />}
          </React.Fragment>
        ))}
      </div>

      {/* Page header */}
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: '#5B6B66' }}>
          STEP 3: PROOF OF DELIVERY
        </p>
        <h1 className="text-2xl font-bold" style={{ color: '#0B3D33' }}>
          OUT-014 Keells Super Gampaha
        </h1>
      </div>

      {/* 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">

        {/* Left: Delivery outcome + receiver */}
        <div className="flex flex-col gap-4">

          {/* Outcome segmented control */}
          <div
            className="rounded-[20px] p-5"
            style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
          >
            <p className="text-[11px] uppercase tracking-widest font-semibold mb-3" style={{ color: '#5B6B66' }}>
              DELIVERY OUTCOME VERIFICATION
            </p>
            <div
              className="flex rounded-xl p-1"
              style={{ background: '#F4F8F6', border: '1px solid #E2ECE7' }}
            >
              {outcomes.map(outcome => (
                <button
                  key={outcome}
                  onClick={() => setSelected(outcome)}
                  className="flex-1 rounded-lg py-2.5 text-xs font-semibold transition-all cursor-pointer"
                  style={{
                    background: selected === outcome ? '#0F9D6C' : 'transparent',
                    color: selected === outcome ? 'white' : '#5B6B66',
                  }}
                >
                  {outcome}
                </button>
              ))}
            </div>
          </div>

          {/* Receiver name */}
          <div
            className="rounded-[20px] p-5"
            style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
          >
            <label className="block text-[11px] uppercase tracking-widest font-semibold mb-2" style={{ color: '#5B6B66' }}>
              Receiver Full Name
            </label>
            <input
              type="text"
              defaultValue="Goods Receiving"
              className="w-full rounded-xl px-4 py-3 text-sm font-medium outline-none"
              style={{
                background: '#F4F8F6',
                border: '1px solid #E2ECE7',
                color: '#0E1A17',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = '#0F9D6C')}
              onBlur={e => (e.currentTarget.style.borderColor = '#E2ECE7')}
            />
          </div>
        </div>

        {/* Right: Photo evidence + Secure metadata */}
        <div className="flex flex-col gap-4">

          {/* Photo capture */}
          <div
            className="rounded-[20px] p-5 flex-1 flex flex-col justify-between"
            style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
          >
            <div>
              <p className="text-[11px] uppercase tracking-widest font-semibold mb-1" style={{ color: '#5B6B66' }}>
                Take Delivery Photo
              </p>
              <p className="text-xs mb-3" style={{ color: '#5B6B66' }}>
                Capture rear dock door or goods with invoices
              </p>
            </div>
            <button
              onClick={() => setPhotoTaken(true)}
              className="w-full rounded-xl flex flex-col items-center justify-center gap-2 transition-all cursor-pointer py-8"
              style={{
                background: photoTaken ? '#E8F0FF' : '#F4F8F6',
                border: photoTaken ? '2px solid #3B82F6' : '2px dashed #CBD5E1',
              }}
            >
              {photoTaken ? (
                <>
                  <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: '#3B82F6' }}>
                    <Check size={20} color="white" strokeWidth={3} />
                  </div>
                  <p className="text-sm font-semibold" style={{ color: '#3B82F6' }}>Photo captured</p>
                </>
              ) : (
                <>
                  <Camera size={28} style={{ color: '#CBD5E1' }} />
                  <p className="text-sm font-medium" style={{ color: '#5B6B66' }}>📷 Add Delivery Photo</p>
                </>
              )}
            </button>
          </div>

          {/* Secure metadata */}
          <div
            className="rounded-[20px] p-5"
            style={{ background: '#0B3D33', boxShadow: '0 8px 24px rgba(11,61,51,0.15)' }}
          >
            <p className="text-[11px] uppercase tracking-widest font-semibold mb-2" style={{ color: '#6EE7B7' }}>
              SECURE METADATA (AUTO-ATTACHED)
            </p>
            {[
              { icon: <MapPin size={13} />, label: 'GPS', value: '7.0873° N, 80.0144° E' },
              { icon: <Clock size={13} />, label: 'Time', value: '06:52 AM' },
              { icon: <Smartphone size={13} />, label: 'Device', value: "Kasun's Phone" },
            ].map(({ icon, label, value }) => (
              <div key={label} className="flex items-center justify-between py-1.5" style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                <div className="flex items-center gap-2">
                  <span style={{ color: '#6EE7B7' }}>{icon}</span>
                  <span className="text-xs" style={{ color: '#A7D4C0' }}>{label}</span>
                </div>
                <span className="text-xs font-mono font-semibold tabular-nums" style={{ color: 'white' }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={onConfirm}
        className="w-full flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer"
        style={{ background: '#0F9D6C', height: 64, boxShadow: '0 4px 14px rgba(15,157,108,0.35)' }}
        onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
        onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
      >
        <FileText size={18} />
        📋 CONFIRM DELIVERY &amp; SYNC
      </button>
    </div>
  );
}
