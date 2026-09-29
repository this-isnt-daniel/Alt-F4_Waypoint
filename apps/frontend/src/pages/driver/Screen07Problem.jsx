import React, { useState } from 'react';
import { Store, Lock, AlertTriangle, Cloud, Clock, MoreHorizontal, Camera, Clock3, Send } from 'lucide-react';

const reasons = [
  { id: 'closed', icon: '🏪', label: 'Outlet Closed' },
  { id: 'blocked', icon: '🔒', label: 'Access Blocked' },
  { id: 'breakdown', icon: '⚠️', label: 'Vehicle Breakdown' },
  { id: 'flood', icon: '🌊', label: 'Road Disruption / Flooding', selected: true },
  { id: 'late', icon: '⏱', label: 'Running Late' },
  { id: 'other', icon: '•••', label: 'Other Issues' },
];

export default function Screen07Problem({ onSubmit }) {
  const [selectedReason, setSelectedReason] = useState('flood');
  const [photoAdded, setPhotoAdded] = useState(false);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8" style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>

      {/* Page header */}
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: '#5B6B66' }}>
          REPORT A PROBLEM
        </p>
        <h1 className="text-2xl font-bold" style={{ color: '#0B3D33' }}>
          OUT027 Cargills Food City
        </h1>
      </div>

      {/* 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 mb-5">

        {/* Left: Reason grid (3/5) */}
        <div
          className="lg:col-span-3 rounded-[20px] p-6"
          style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
        >
          <p className="text-[11px] uppercase tracking-widest font-semibold mb-4" style={{ color: '#5B6B66' }}>
            SELECT EXCLUSION REASON
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {reasons.map(r => {
              const isSel = selectedReason === r.id;
              return (
                <button
                  key={r.id}
                  onClick={() => setSelectedReason(r.id)}
                  className="flex flex-col items-center justify-center gap-2 rounded-2xl p-4 transition-all cursor-pointer relative"
                  style={{
                    background: isSel ? '#E8F5EF' : '#F4F8F6',
                    border: isSel ? '2px solid #0F9D6C' : '1px solid #E2ECE7',
                    minHeight: 100,
                  }}
                >
                  {isSel && (
                    <div
                      className="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center"
                      style={{ background: '#0F9D6C' }}
                    >
                      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                        <path d="M2 5l2 2 4-4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                  )}
                  <span className="text-2xl">{r.icon}</span>
                  <span
                    className="text-xs font-semibold text-center leading-tight"
                    style={{ color: isSel ? '#0B3D33' : '#5B6B66' }}
                  >
                    {r.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Photo + explanation (2/5) */}
        <div className="lg:col-span-2 flex flex-col gap-4">

          {/* Photo evidence */}
          <div
            className="rounded-[20px] p-5"
            style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
          >
            <p className="text-[11px] uppercase tracking-widest font-semibold mb-3" style={{ color: '#5B6B66' }}>
              EVIDENCE PHOTOS
            </p>
            <button
              onClick={() => setPhotoAdded(true)}
              className="w-full rounded-xl flex items-center justify-center gap-3 transition-all cursor-pointer"
              style={{
                height: 90,
                background: photoAdded ? '#E8F0FF' : '#F4F8F6',
                border: photoAdded ? '2px solid #3B82F6' : '2px dashed #CBD5E1',
              }}
            >
              <Camera size={20} style={{ color: photoAdded ? '#3B82F6' : '#CBD5E1' }} />
              <span className="text-sm font-medium" style={{ color: photoAdded ? '#3B82F6' : '#5B6B66' }}>
                {photoAdded ? '✓ Photo added' : '📷 Add Photo Evidence'}
              </span>
            </button>
          </div>

          {/* Explanation note */}
          <div
            className="rounded-[20px] p-5 flex-1"
            style={{ background: '#FFFFFF', border: '1px solid #E2ECE7', boxShadow: '0 8px 24px rgba(11,61,51,0.08)' }}
          >
            <p className="text-[11px] uppercase tracking-widest font-semibold mb-2" style={{ color: '#5B6B66' }}>
              EXPLANATION NOTE
            </p>
            <textarea
              defaultValue="Road block due to morning flooding. Authorities redirecting heavy traffic."
              rows={4}
              className="w-full rounded-xl p-3 text-sm resize-none outline-none"
              style={{
                background: '#F4F8F6',
                border: '1px solid #E2ECE7',
                color: '#0E1A17',
                lineHeight: '1.6',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = '#0F9D6C')}
              onBlur={e => (e.currentTarget.style.borderColor = '#E2ECE7')}
            />
          </div>
        </div>
      </div>

      {/* CTA + footer */}
      <div className="flex flex-col gap-3">
        <button
          onClick={onSubmit}
          className="w-full flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer"
          style={{ background: '#E5484D', height: 64, boxShadow: '0 4px 14px rgba(229,72,77,0.3)' }}
          onMouseEnter={e => (e.currentTarget.style.background = '#C0393E')}
          onMouseLeave={e => (e.currentTarget.style.background = '#E5484D')}
        >
          <Clock3 size={18} />
          ⏱ SUBMIT PROBLEM REPORT
        </button>
        <p className="text-xs text-center" style={{ color: '#5B6B66' }}>
          OUT027 manager &amp; dispatcher will be alerted immediately.
        </p>
      </div>
    </div>
  );
}
