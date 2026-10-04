import React, { useState } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import { apiFetch } from '../../lib/api';
import { safeStorage } from '../../lib/security';

export default function DispatcherLogin({ onLogin }) {
  const [username, setUsername] = useState('dispatcher@waypoint.local');
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
    <main className="min-h-screen w-full bg-slate-50 flex flex-col items-center justify-center px-4 select-none">
      <div className="w-full max-w-sm bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
        {/* Logo and Brand Heading */}
        <div className="flex items-center justify-center gap-3 mb-3">
          <img
            src={waypointLogo}
            alt="Waypoint Logo"
            className="w-10 h-10 object-contain rounded-xl shadow-sm"
          />
          <h1
            className="text-3xl font-extrabold text-slate-900 tracking-tight"
            style={{ fontFamily: "'Inter', sans-serif" }}
          >
            Waypoint
          </h1>
        </div>

        {/* Portal Pill Badge */}
        <div className="flex justify-center mb-6">
          <span className="inline-flex items-center px-3.5 py-1 rounded-full text-[11px] font-bold tracking-wider uppercase text-emerald-800 bg-emerald-50 border border-emerald-200">
            Dispatcher Portal
          </span>
        </div>

        {error && (
          <div className="w-full mb-4 p-3 bg-red-50 border border-red-200 text-center text-red-600 text-xs font-semibold rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Username / Email
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="dispatcher@waypoint.local"
              className="w-full h-11 px-3.5 border border-slate-300 rounded-lg text-sm text-slate-900 bg-white placeholder-slate-400 font-medium focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:border-transparent transition-all"
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full h-11 px-3.5 border border-slate-300 rounded-lg text-sm text-slate-900 bg-white placeholder-slate-400 font-medium focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:border-transparent transition-all"
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            aria-label="Log in to Dispatcher Portal"
            className="w-full h-11 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white text-sm font-semibold rounded-lg transition-all shadow-sm flex items-center justify-center cursor-pointer disabled:opacity-50 mt-1"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </main>
  );
}
