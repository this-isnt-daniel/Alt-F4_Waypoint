import React, { useState } from 'react';
import { Check, Camera, MapPin, Clock, Smartphone, FileText, ChevronRight } from 'lucide-react';

const outcomes = ['✓ Full Delivery', 'Partial', 'Rejected'];

export default function Screen06POD({ onConfirm, darkMode = false }) {
  const [selected, setSelected] = useState('✓ Full Delivery');
  const [photoTaken, setPhotoTaken] = useState(false);

  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>

      {/* Step breadcrumb */}
      <div className="flex items-center gap-2 mb-2">
        {['Arrived', 'Unloading', 'Proof of Delivery'].map((step, i) => (
          <React.Fragment key={step}>
            <span
              className={`text-xs font-semibold ${
                i === 2 
                  ? 'text-[#0F9D6C] font-bold' 
                  : darkMode ? 'text-gray-400 font-medium' : 'text-[#5B6B66] font-medium'
              }`}
            >
              {step}
            </span>
            {i < 2 && <ChevronRight size={12} className={darkMode ? 'text-gray-600' : 'text-[#CBD5E1]'} />}
          </React.Fragment>
        ))}
      </div>

      {/* Page header */}
      <div className="mb-6">
        <p className={`text-xs font-semibold uppercase tracking-widest mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
          PROOF OF DELIVERY
        </p>
        <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
          OUT-014 Keells Super Gampaha
        </h1>
      </div>

      {/* 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">

        {/* Left: Delivery outcome + receiver */}
        <div className="flex flex-col gap-4">

          {/* Outcome segmented control */}
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
              DELIVERY OUTCOME VERIFICATION
            </p>
            <div
              className={`flex rounded-xl p-1 border ${
                darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-[#E2ECE7]'
              }`}
            >
              {outcomes.map(outcome => (
                <button
                  key={outcome}
                  onClick={() => setSelected(outcome)}
                  className={`flex-1 rounded-lg py-2.5 text-xs font-semibold transition-all cursor-pointer ${
                    selected === outcome
                      ? 'bg-[#0F9D6C] text-white shadow-xs'
                      : darkMode ? 'text-gray-300 hover:text-white' : 'text-[#5B6B66] hover:text-[#0E1A17]'
                  }`}
                >
                  {outcome}
                </button>
              ))}
            </div>
          </div>

          {/* Receiver name */}
          <div
            className={`rounded-[20px] p-5 border transition-all ${
              darkMode 
                ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
                : 'bg-white border-[#E2ECE7] shadow-xs'
            }`}
          >
            <label className={`block text-[11px] uppercase tracking-widest font-semibold mb-2 ${
              darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
            }`}>
              Receiver Full Name
            </label>
            <input
              type="text"
              defaultValue="Goods Receiving"
              className={`w-full rounded-xl px-4 py-3 text-sm font-medium outline-none border transition-colors ${
                darkMode 
                  ? 'bg-[#16332B] border-[#1F3D35] text-white focus:border-[#0F9D6C]' 
                  : 'bg-[#F4F8F6] border-[#E2ECE7] text-[#0E1A17] focus:border-[#0F9D6C]'
              }`}
            />
          </div>
        </div>

        {/* Right: Photo evidence + Secure metadata */}
        <div className="flex flex-col gap-4">

          {/* Photo capture */}
          <div
            className={`rounded-[20px] p-5 flex-1 flex flex-col justify-between border transition-all ${
              darkMode 
                ? 'bg-[#122822] border-[#1F3D35] shadow-sm' 
                : 'bg-white border-[#E2ECE7] shadow-xs'
            }`}
          >
            <div>
              <p className={`text-[11px] uppercase tracking-widest font-semibold mb-1 ${
                darkMode ? 'text-gray-400' : 'text-[#5B6B66]'
              }`}>
                Take Delivery Photo
              </p>
              <p className={`text-xs mb-3 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
                Capture rear dock door or goods with invoices
              </p>
            </div>
            <button
              onClick={() => setPhotoTaken(true)}
              className={`w-full rounded-xl flex flex-col items-center justify-center gap-2 transition-all cursor-pointer py-8 border-2 ${
                photoTaken 
                  ? darkMode ? 'bg-[#1E3A8A]/30 border-[#3B82F6]' : 'bg-[#E8F0FF] border-[#3B82F6]'
                  : darkMode ? 'bg-[#16332B] border-dashed border-[#1F3D35] hover:border-[#0F9D6C]' : 'bg-[#F4F8F6] border-dashed border-[#CBD5E1] hover:border-[#0F9D6C]'
              }`}
            >
              {photoTaken ? (
                <>
                  <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: '#3B82F6' }}>
                    <Check size={20} color="white" strokeWidth={3} />
                  </div>
                  <p className="text-sm font-semibold text-[#3B82F6]">Photo captured</p>
                </>
              ) : (
                <>
                  <Camera size={28} className={darkMode ? 'text-gray-400' : 'text-[#CBD5E1]'} />
                  <p className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-[#5B6B66]'}`}>
                    📷 Add Delivery Photo
                  </p>
                </>
              )}
            </button>
          </div>

          {/* Secure metadata */}
          <div
            className={`rounded-[20px] p-5 border transition-all ${
              darkMode 
                ? 'bg-[#0E2721] border-[#1F4A3E] shadow-md' 
                : 'bg-[#0B3D33] border-transparent shadow-sm'
            }`}
          >
            <p className="text-[11px] uppercase tracking-widest font-semibold mb-2" style={{ color: '#6EE7B7' }}>
              SECURE METADATA (AUTO-ATTACHED)
            </p>
            {[
              { icon: <MapPin size={13} />, label: 'GPS', value: '7.0873° N, 80.0144° E' },
              { icon: <Clock size={13} />, label: 'Time', value: '06:52 AM' },
              { icon: <Smartphone size={13} />, label: 'Device', value: "Kasun's Phone" },
            ].map(({ icon, label, value }) => (
              <div key={label} className="flex items-center justify-between py-1.5 border-b border-white/10 last:border-b-0">
                <div className="flex items-center gap-2">
                  <span style={{ color: '#6EE7B7' }}>{icon}</span>
                  <span className="text-xs" style={{ color: '#A7D4C0' }}>{label}</span>
                </div>
                <span className="text-xs font-mono font-semibold tabular-nums text-white">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={onConfirm}
        className="w-full px-6 py-4 flex items-center justify-center gap-3 rounded-2xl text-base font-bold text-white transition-all active:scale-[0.98] cursor-pointer shadow-md hover:shadow-lg"
        style={{ background: '#0F9D6C', minHeight: 56 }}
        onMouseEnter={e => (e.currentTarget.style.background = '#0B7F57')}
        onMouseLeave={e => (e.currentTarget.style.background = '#0F9D6C')}
      >
        <FileText size={18} />
        <span>📋 CONFIRM DELIVERY &amp; SYNC</span>
      </button>
    </div>
  );
}
