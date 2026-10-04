import React, { useState } from 'react';
import { User, Lock, Eye, EyeOff, ArrowLeft } from 'lucide-react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';

export default function StoreManagerLogin({ onLogin }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [username, setUsername] = useState('tech@waypoint.local');
  const [password, setPassword] = useState('password123');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!username.trim()) {
      setError('Please enter your username');
      return;
    }
    if (!password.trim()) {
      setError('Please enter your password');
      return;
    }

    // Authenticated user & outlet for Waypoint Tech
    const manager = {
      id: 'SM-TCH-01',
      name: 'K. Wickrema',
      username: username.trim(),
      role: 'Store Manager',
      pin: '123456'
    };
    const outlet = {
      id: 'TCH-001',
      name: 'Waypoint Tech Hub — Colombo 03'
    };

    onLogin(manager, outlet);
  };

  return (
    <main className="min-h-screen w-full bg-white flex flex-col items-center justify-center px-4 select-none">
      <div className="flex flex-col items-center max-w-sm w-full">
        {/* Logo and Brand Heading */}
        <div className="flex items-center justify-center gap-3.5 mb-4">
          <img
            src={waypointLogo}
            alt="Waypoint Logo"
            className="w-12 h-12 object-contain rounded-xl shadow-sm"
          />
          <h1
            className="text-[48px] font-extrabold text-[#0B2019] tracking-tight leading-none"
            style={{ fontFamily: "'Inter', sans-serif" }}
          >
            Waypoint
          </h1>
        </div>

        {/* Portal Pill Badge */}
        <div className="mb-6">
          <span className="inline-flex items-center px-4 py-1.5 rounded-full text-[11px] font-semibold tracking-[0.16em] uppercase text-[#256149] bg-[#EBF6F0] border border-[#DCF0E5]">
            Waypoint Tech
          </span>
        </div>

        {!isExpanded ? (
          /* Initial Screen: Clean "Log in" button */
          <button
            type="button"
            onClick={() => setIsExpanded(true)}
            aria-label="Log in to Waypoint Tech"
            className="mt-2 w-[230px] h-11 bg-[#059669] hover:bg-[#047857] active:bg-[#065f46] text-white text-sm font-medium rounded-lg transition-all duration-150 ease-in-out shadow-sm hover:shadow flex items-center justify-center cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#059669] focus-visible:ring-offset-2"
          >
            Log in
          </button>
        ) : (
          /* Expanded: Username & Password boxes appear */
          <form
            onSubmit={handleSubmit}
            className="w-full flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-200"
          >
            {/* Username Input */}
            <div className="w-full">
              <label className="block text-[13px] font-semibold text-slate-700 mb-1.5">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <User size={16} />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => { setUsername(e.target.value); setError(null); }}
                  placeholder="e.g. tech_manager"
                  className="w-full h-11 pl-9 pr-3 border border-slate-300 rounded-lg text-[14px] text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#059669] focus:border-transparent transition-all"
                  autoFocus
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="w-full">
              <label className="block text-[13px] font-semibold text-slate-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock size={16} />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(null); }}
                  placeholder="Enter password"
                  className="w-full h-11 pl-9 pr-10 border border-slate-300 rounded-lg text-[14px] text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#059669] focus:border-transparent transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 cursor-pointer"
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <p className="text-[12px] text-red-600 font-medium">{error}</p>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 mt-2">
              <button
                type="button"
                onClick={() => { setIsExpanded(false); setError(null); }}
                className="w-11 h-11 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg flex items-center justify-center transition-colors cursor-pointer shrink-0"
                title="Back"
              >
                <ArrowLeft size={16} />
              </button>
              <button
                type="submit"
                className="flex-1 h-11 bg-[#059669] hover:bg-[#047857] active:bg-[#065f46] text-white text-sm font-semibold rounded-lg transition-all shadow-sm hover:shadow flex items-center justify-center cursor-pointer"
              >
                Sign in to Waypoint Tech
              </button>
            </div>
          </form>
        )}
      </div>
    </main>
  );
}
