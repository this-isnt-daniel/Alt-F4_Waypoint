import React, { useState } from 'react';
import { LogIn, UserPlus, CheckCircle2, ShieldCheck, KeyRound, Truck } from 'lucide-react';
import waypointLogo from './assets/icons/waypoint_logo.png';

export default function DriverAuth({ onAuthSuccess }) {
  const [authMode, setAuthMode] = useState('signin'); // 'signin' | 'signup'
  const [driverId, setDriverId] = useState('Nimal Perera');
  const [pin, setPin] = useState('••••');
  const [depot, setDepot] = useState('Peliyagoda Depot');
  const [phone, setPhone] = useState('+94 77 123 4567');

  const handleSubmit = (e) => {
    e.preventDefault();
    onAuthSuccess({
      name: driverId,
      depot: depot,
      phone: phone,
    });
  };

  return (
    <div className="flex flex-col lg:flex-row min-h-screen w-full" style={{ background: '#081C17' }}>

      {/* ── Left Side: Brand & Hero Artwork ────────────────────────── */}
      <div
        className="w-full lg:w-1/2 p-8 lg:p-14 flex flex-col justify-between relative overflow-hidden"
        style={{
          background: 'radial-gradient(circle at 20% 30%, #0F3E33 0%, #081C17 100%)',
          borderRight: '1px solid rgba(16, 185, 129, 0.15)',
        }}
      >
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-6">
            <img src={waypointLogo} alt="Waypoint" className="w-10 h-10 object-contain rounded-xl shadow-md" />
            <div>
              <span className="text-xl font-extrabold text-white tracking-tight">Waypoint</span>
              <span className="ml-2 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#10B981]/20 text-[#34D399] border border-[#10B981]/30">
                Driver Portal
              </span>
            </div>
          </div>

          <p className="text-[11px] font-bold tracking-[0.2em] uppercase text-[#34D399] mb-2">
            WAYPOINT GROUP
          </p>
          <h1 className="text-4xl lg:text-5xl font-black text-white leading-tight tracking-tight">
            {authMode === 'signin' ? 'Driver sign-in' : 'Driver registration'}
          </h1>
          <p className="text-sm mt-3 text-[#94A3B8] max-w-md">
            {authMode === 'signin'
              ? 'Secure access for today’s assigned route and real-time dispatch synchronization.'
              : 'Register as an authorized fleet driver for Waypoint distribution network.'}
          </p>
        </div>

        {/* Center Graphic */}
        <div className="relative z-10 my-8 py-4 flex items-center justify-center">
          <div className="w-24 h-24 rounded-3xl bg-[#0F9D6C]/20 border border-[#0F9D6C]/40 flex items-center justify-center shadow-2xl relative">
            <Truck size={48} className="text-[#34D399]" />
            <div className="absolute -bottom-2 -right-2 w-8 h-8 rounded-full bg-[#10B981] flex items-center justify-center text-white shadow-lg">
              <ShieldCheck size={16} />
            </div>
          </div>
        </div>

        {/* Left Footer Trust Badges */}
        <div className="relative z-10 pt-4 border-t border-white/10 flex flex-wrap items-center justify-between gap-3 text-xs text-[#94A3B8]">
          <span className="flex items-center gap-1.5 text-[#34D399]">
            <CheckCircle2 size={14} /> Device verified · Peliyagoda depot
          </span>
          <span className="text-white/60">Mon, 29 Sep 2026</span>
        </div>
      </div>

      {/* ── Right Side: Sign-in / Sign-up Card Form ────────────────── */}
      <div
        className="w-full lg:w-1/2 p-6 lg:p-14 flex flex-col justify-center items-center"
        style={{ background: '#081C17' }}
      >
        <div className="w-full max-w-md my-auto">

          {/* Mode Switcher Tabs */}
          <div className="flex rounded-2xl p-1 bg-[#0F2D25] border border-[#10B981]/20 mb-8">
            <button
              type="button"
              onClick={() => setAuthMode('signin')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                authMode === 'signin'
                  ? 'bg-[#0F9D6C] text-white shadow-md'
                  : 'text-[#94A3B8] hover:text-white'
              }`}
            >
              <LogIn size={14} />
              Driver Sign-in
            </button>
            <button
              type="button"
              onClick={() => setAuthMode('signup')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                authMode === 'signup'
                  ? 'bg-[#0F9D6C] text-white shadow-md'
                  : 'text-[#94A3B8] hover:text-white'
              }`}
            >
              <UserPlus size={14} />
              New Driver Registration
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">

            {/* Driver ID / Name */}
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-[#94A3B8] mb-1.5">
                DRIVER ID / FULL NAME
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={driverId}
                  onChange={(e) => setDriverId(e.target.value)}
                  placeholder="e.g. Nimal Perera"
                  className="w-full rounded-2xl px-4 py-3.5 text-sm font-semibold text-white bg-[#0F2D25] border border-[#10B981]/30 focus:border-[#34D399] outline-none transition-all placeholder:text-gray-500"
                />
              </div>
            </div>

            {/* Signup extra fields */}
            {authMode === 'signup' && (
              <>
                <div>
                  <label className="block text-[11px] font-bold uppercase tracking-wider text-[#94A3B8] mb-1.5">
                    CONTACT NUMBER
                  </label>
                  <input
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+94 77 123 4567"
                    className="w-full rounded-2xl px-4 py-3.5 text-sm font-semibold text-white bg-[#0F2D25] border border-[#10B981]/30 focus:border-[#34D399] outline-none transition-all"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold uppercase tracking-wider text-[#94A3B8] mb-1.5">
                    ASSIGNED DEPOT
                  </label>
                  <select
                    value={depot}
                    onChange={(e) => setDepot(e.target.value)}
                    className="w-full rounded-2xl px-4 py-3.5 text-sm font-semibold text-white bg-[#0F2D25] border border-[#10B981]/30 focus:border-[#34D399] outline-none transition-all"
                  >
                    <option value="Peliyagoda Depot" className="bg-[#0F2D25] text-white">Peliyagoda Depot</option>
                    <option value="Colombo Depot" className="bg-[#0F2D25] text-white">Colombo Depot</option>
                    <option value="Gampaha Hub" className="bg-[#0F2D25] text-white">Gampaha Hub</option>
                  </select>
                </div>
              </>
            )}

            {/* Secure PIN */}
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-[#94A3B8] mb-1.5">
                SECURE PIN
              </label>
              <div className="relative">
                <input
                  type="password"
                  required
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  placeholder="Enter 4-digit PIN"
                  className="w-full rounded-2xl px-4 py-3.5 text-sm font-mono tracking-widest text-white bg-[#0F2D25] border border-[#10B981]/30 focus:border-[#34D399] outline-none transition-all placeholder:text-gray-500"
                />
                <KeyRound size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-[#34D399]" />
              </div>
            </div>

            {/* Device Verified Pill */}
            <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0F2D25]/70 border border-[#10B981]/20 text-xs text-[#34D399]">
              <CheckCircle2 size={15} />
              <span>Device verified · Peliyagoda depot</span>
            </div>

            {/* Primary Action Button */}
            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 rounded-2xl text-base font-bold text-[#06241E] bg-[#34D399] hover:bg-[#10B981] hover:text-white transition-all duration-150 active:scale-[0.98] cursor-pointer mt-3 shadow-lg shadow-[#10B981]/20"
              style={{ height: 58 }}
            >
              <LogIn size={18} />
              {authMode === 'signin' ? 'Sign in' : 'Complete Registration & Start'}
            </button>

            {/* Help link */}
            <p className="text-center text-xs text-[#94A3B8] mt-3">
              Need help? <a href="tel:+94112345678" className="text-[#34D399] hover:underline">Call depot support</a>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
