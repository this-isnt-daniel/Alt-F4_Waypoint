import React, { useState } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import { apiFetch } from '../../lib/api';
import { safeStorage } from '../../lib/security';

const USERS = {
  dep1: { id: 1, name: 'Loader One', depot: 'peliyagoda', bay: 'Bay Lead A', username: 'loader', password: 'password123' },
  dep2: { id: 2, name: 'Loader Two', depot: 'peliyagoda', bay: null, username: 'loader1', password: 'password123' }
};

export default function LoaderLogin({ onLogin }) {
  const [username, setUsername] = useState(USERS.dep1.username);
  const [password, setPassword] = useState(USERS.dep1.password);
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
        depot: profile.depot_id,
        bay: profile.depot_id === 'DEP1' ? 'Bay Lead A' : null,
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
    <main className="min-h-screen w-full bg-[#f8fbf9] flex flex-col items-center justify-center px-4 font-sans select-none">
      <div className="bg-white border border-slate-200 rounded-md shadow-sm p-6 sm:p-8 max-w-sm w-full">
        {/* Logo and Brand Heading */}
        <div className="flex flex-col items-center justify-center mb-8">
          <div className="flex items-center gap-3.5 mb-4">
            <img
              src={waypointLogo}
              alt="Waypoint Logo"
              className="w-10 h-10 object-contain rounded-md"
            />
            <h1 className="text-[32px] font-extrabold text-[#0B2019] tracking-tight leading-none">
              Waypoint
            </h1>
          </div>
          <span className="inline-flex items-center px-3 py-1 rounded text-[11px] font-bold tracking-widest uppercase text-brand-700 bg-brand-50 border border-brand-100">
            Loader Portal
          </span>
        </div>

        {/* Quick Fill Buttons for Judges */}
        <div className="mb-6 border-b border-slate-100 pb-6">
          <p className="text-[12px] font-bold text-slate-500 uppercase text-center tracking-wider mb-3">
            Quick Fill For Judges
          </p>
          <div className="flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={() => { setUsername(USERS.dep1.username); setPassword(USERS.dep1.password); }}
              className={`flex-1 py-2 px-2 text-[12px] font-bold border rounded transition-colors ${
                username === USERS.dep1.username
                  ? 'border-brand-500 bg-brand-50 text-brand-700'
                  : 'border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              DEP1
            </button>
            <button
              type="button"
              onClick={() => { setUsername(USERS.dep2.username); setPassword(USERS.dep2.password); }}
              className={`flex-1 py-2 px-2 text-[12px] font-bold border rounded transition-colors ${
                username === USERS.dep2.username
                  ? 'border-brand-500 bg-brand-50 text-brand-700'
                  : 'border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              DEP2
            </button>
          </div>
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
              className="w-full h-10 px-3 bg-white border border-slate-300 rounded text-[14px] font-medium text-slate-900 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-[13px] font-bold text-slate-700 mb-1.5">Password</label>
            {/* Using type="text" to keep it visible for judges so they know what is typed as requested */}
            <input
              type="text"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full h-10 px-3 bg-white border border-slate-300 rounded text-[14px] font-medium text-slate-900 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
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
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-[12px] text-emerald-900 text-center font-medium">
            Demo credentials: <span className="font-mono font-bold">loader</span> / <span className="font-mono font-bold">password123</span>
          </div>
        </form>
      </div>
    </main>
  );
}
