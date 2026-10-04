import React, { useState } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import { apiFetch } from '../../lib/api';
import { safeStorage } from '../../lib/security';

export default function DispatcherLogin({ onLogin }) {
  const [username, setUsername] = useState('dispatcher');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      });
      safeStorage.set('token', response.access_token);
      onLogin();
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen w-full bg-white flex flex-col items-center justify-center px-4 select-none">
      <form onSubmit={handleLogin} className="flex flex-col items-center max-w-sm w-full">
        {/* Logo and Brand Heading */}
        <div className="flex items-center justify-center gap-3.5 mb-5">
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
        <div className="mb-8">
          <span className="inline-flex items-center px-4 py-1.5 rounded-full text-[11px] font-semibold tracking-[0.16em] uppercase text-[#256149] bg-[#EBF6F0] border border-[#DCF0E5]">
            Dispatcher Portal
          </span>
        </div>

        {error && <div className="w-[250px] mb-4 text-center text-red-500 text-sm font-semibold">{error}</div>}

        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          className="w-[250px] h-11 px-4 mb-3 border border-slate-300 rounded-lg text-sm text-slate-900 bg-white placeholder:text-slate-400 font-medium focus:outline-none focus:border-[#059669] focus:ring-1 focus:ring-[#059669]"
          disabled={loading}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-[250px] h-11 px-4 mb-6 border border-slate-300 rounded-lg text-sm text-slate-900 bg-white placeholder:text-slate-400 font-medium focus:outline-none focus:border-[#059669] focus:ring-1 focus:ring-[#059669]"
          disabled={loading}
        />

        {/* Geist-style Action Button */}
        <button
          type="submit"
          disabled={loading}
          aria-label="Log in to Dispatcher Portal"
          className="w-[250px] h-11 bg-[#059669] hover:bg-[#047857] active:bg-[#065f46] text-white text-sm font-medium rounded-lg transition-all duration-150 ease-in-out shadow-sm hover:shadow flex items-center justify-center cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#059669] focus-visible:ring-offset-2 disabled:opacity-50"
        >
          {loading ? 'Logging in...' : 'Log in'}
        </button>

        <div className="w-[250px] mt-4 text-center">
          <p className="text-[12px] text-slate-400 font-medium">
            Demo account: <span className="font-bold text-slate-600">dispatcher</span> / <span className="font-bold text-slate-600">password123</span>
          </p>
        </div>
      </form>
    </main>
  );
}
