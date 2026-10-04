import React, { useState } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import { apiFetch } from '../../lib/api';
import { safeStorage } from '../../lib/security';

const USERS = {
  peliyagoda: { id: 'USR-LOAD', name: 'Loader Demo', depot: 'peliyagoda', bay: 'Bay Lead A', username: 'loader@waypoint.local', password: 'password123' },
};

export default function LoaderLogin({ onLogin }) {
  const [username, setUsername] = useState(USERS.peliyagoda.username);
  const [password, setPassword] = useState(USERS.peliyagoda.password);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      });
      safeStorage.set('token', token.access_token);

      const profile = await apiFetch('/auth/me');
      onLogin({
        id: profile.user_id,
        name: profile.name || username,
        depot: profile.depot_id || 'peliyagoda',
        bay: 'Bay Lead A',
        token: token.access_token,
        username: profile.username,
        role: profile.role
      });
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen w-full bg-slate-50 flex flex-col items-center justify-center px-4 font-sans select-none">
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-8 max-w-sm w-full">
        {/* Logo and Brand Heading */}
        <div className="flex flex-col items-center justify-center mb-6">
          <div className="flex items-center gap-3 mb-3">
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
          <span className="inline-flex items-center px-3.5 py-1 rounded-full text-[11px] font-bold tracking-wider uppercase text-emerald-800 bg-emerald-50 border border-emerald-200">
            Loader Portal
          </span>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 text-sm font-semibold rounded">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-[13px] font-bold text-slate-700 mb-1.5">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full h-10 px-3 border border-slate-300 rounded text-[14px] text-slate-900 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-[13px] font-bold text-slate-700 mb-1.5">Password</label>
            {/* Using type="text" to keep it visible for judges so they know what is typed as requested */}
            <input
              type="text"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full h-10 px-3 border border-slate-300 rounded text-[14px] text-slate-900 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
            />
          </div>
          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white text-[14px] font-bold rounded shadow-sm hover:shadow transition-all flex items-center justify-center disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? 'Signing in...' : 'Log In'}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
