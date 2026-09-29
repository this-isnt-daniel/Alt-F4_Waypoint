import React, { useState } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';

const USERS = {
  peliyagoda: { id: 1, name: 'J. Silva', depot: 'peliyagoda', bay: 'Bay Lead A', username: 'peliyagoda_loader', password: 'password123' },
  kandy: { id: 2, name: 'S. Bandara', depot: 'kandy', bay: null, username: 'kandy_loader', password: 'password123' }
};

export default function LoaderLogin({ onLogin }) {
  const [username, setUsername] = useState(USERS.peliyagoda.username);
  const [password, setPassword] = useState(USERS.peliyagoda.password);

  const handleLogin = (e) => {
    e.preventDefault();
    if (username === USERS.kandy.username) {
      onLogin(USERS.kandy);
    } else {
      onLogin(USERS.peliyagoda);
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
              onClick={() => { setUsername(USERS.peliyagoda.username); setPassword(USERS.peliyagoda.password); }}
              className={`flex-1 py-2 px-2 text-[12px] font-bold border rounded transition-colors ${
                username === USERS.peliyagoda.username 
                  ? 'border-brand-500 bg-brand-50 text-brand-700' 
                  : 'border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              Peliyagoda
            </button>
            <button
              type="button"
              onClick={() => { setUsername(USERS.kandy.username); setPassword(USERS.kandy.password); }}
              className={`flex-1 py-2 px-2 text-[12px] font-bold border rounded transition-colors ${
                username === USERS.kandy.username 
                  ? 'border-brand-500 bg-brand-50 text-brand-700' 
                  : 'border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              Kandy
            </button>
          </div>
        </div>

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
              className="w-full h-11 bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white text-[14px] font-bold rounded shadow-sm hover:shadow transition-all flex items-center justify-center"
            >
              Log In
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
