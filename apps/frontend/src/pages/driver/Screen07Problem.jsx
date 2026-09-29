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

export default function Screen07Problem({ onSubmit, darkMode = false }) {
  const [selectedReason, setSelectedReason] = useState('flood');
  const [photoAdded, setPhotoAdded] = useState(false);

  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>

      {/* Page header */}
      <div className="mb-6">
        <p className={`text-xs font-semibold uppercase tracking-widest mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
          REPORT A PROBLEM
        </p>
        <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
          OUT027 Cargills Food City
        </h1>
      </div>

      {/* 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 mb-5">

        {/* Left: Reason grid (3/5) */}
        <div
          className={`lg:col-span-3 rounded-[20px] p-6 border transition-all ${
            darkMode 
              ? 'bg-[#122822] border-[#1F3D35] shadow-lg' 
              : 'bg-white border-[#E2ECE7] shadow-sm'
          }`}
        >
          <p className={`text-[11px] uppercase tracking-widest font-semibold mb-4 ${
            darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
          }`}>
            SELECT EXCLUSION REASON
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {reasons.map(r => {
              const isSel = selectedReason === r.id;
              return (
                <button
                  key={r.id}
                  onClick={() => setSelectedReason(r.id)}
                  className={`flex flex-col items-center justify-center gap-2 rounded-2xl p-4 transition-all cursor-pointer relative border-2 ${
                    isSel 
                      ? darkMode ? 'bg-[#10382E] border-[#0F9D6C]' : 'bg-[#E8F5EF] border-[#0F9D6C]'
                      : darkMode ? 'bg-[#16332B] border-[#1F3D35] hover:bg-[#1A3D34]' : 'bg-[#F4F8F6] border-[#E2ECE7] hover:bg-gray-100'
                  }`}
                  style={{ minHeight: 100 }}
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
                    className={`text-xs font-semibold text-center leading-tight ${
                      isSel 
                        ? darkMode ? 'text-white font-bold' : 'text-[#0B3D33] font-bold'
                        : darkMode ? 'text-gray-300' : 'text-[#5B6B66]'
                    }`}
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
            className={`rounded-[20px] p-5 border transition-all ${
              darkMode 
                ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
                : 'bg-white border-[#E2ECE7] shadow-xs'
            }`}
          >
            <p className={`text-[11px] uppercase tracking-widest font-semibold mb-3 ${
              darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
            }`}>
              EVIDENCE PHOTOS
            </p>
            <button
              onClick={() => setPhotoAdded(true)}
              className={`w-full rounded-xl flex items-center justify-center gap-3 transition-all cursor-pointer border-2 ${
                photoAdded 
                  ? darkMode ? 'bg-[#1E3A8A]/30 border-[#3B82F6]' : 'bg-[#E8F0FF] border-[#3B82F6]'
                  : darkMode ? 'bg-[#16332B] border-dashed border-[#1F3D35] hover:border-[#0F9D6C]' : 'bg-[#F4F8F6] border-dashed border-[#CBD5E1] hover:border-[#0F9D6C]'
              }`}
              style={{ height: 90 }}
            >
              <Camera size={20} style={{ color: photoAdded ? '#3B82F6' : darkMode ? '#94A3B8' : '#CBD5E1' }} />
              <span className={`text-sm font-medium ${
                photoAdded ? 'text-[#3B82F6]' : darkMode ? 'text-gray-300' : 'text-[#5B6B66]'
              }`}>
                {photoAdded ? '✓ Photo added' : '📷 Add Photo Evidence'}
              </span>
            </button>
          </div>

          {/* Explanation note */}
          <div
            className={`rounded-[20px] p-5 flex-1 border transition-all ${
              darkMode 
                ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
                : 'bg-white border-[#E2ECE7] shadow-xs'
            }`}
          >
            <p className={`text-[11px] uppercase tracking-widest font-semibold mb-2 ${
              darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
            }`}>
              EXPLANATION NOTE
            </p>
            <textarea
              defaultValue="Road block due to morning flooding. Authorities redirecting heavy traffic."
              rows={4}
              className={`w-full rounded-xl p-3 text-sm resize-none outline-none border transition-colors ${
                darkMode 
                  ? 'bg-[#16332B] border-[#1F3D35] text-white focus:border-[#0F9D6C]' 
                  : 'bg-[#F4F8F6] border-[#E2ECE7] text-[#0E1A17] focus:border-[#0F9D6C]'
              }`}
              style={{ lineHeight: '1.6' }}
            />
          </div>
        </div>
      </div>

      {/* CTA + footer */}
      <div className="flex flex-col gap-3">
        <button
          onClick={onSubmit}
          className="w-full px-6 py-4 flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer shadow-md hover:shadow-lg"
          style={{ background: '#E5484D', minHeight: 56 }}
          onMouseEnter={e => (e.currentTarget.style.background = '#C0393E')}
          onMouseLeave={e => (e.currentTarget.style.background = '#E5484D')}
        >
          <Clock3 size={18} />
          <span>⏱ SUBMIT PROBLEM REPORT</span>
        </button>
        <p className={`text-xs text-center ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
          OUT027 manager &amp; dispatcher will be alerted immediately.
        </p>
      </div>
    </div>
  );
}
