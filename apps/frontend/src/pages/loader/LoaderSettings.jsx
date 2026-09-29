import React, { useState } from 'react';

export default function LoaderSettings({ user }) {
  const [name, setName] = useState(user?.name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const handleSave = (e) => {
    e.preventDefault();
    alert('Settings saved successfully.');
  };

  return (
    <div className="p-4 sm:p-6 bg-white min-h-full font-sans">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-900">Settings</h2>
        <p className="text-[13px] text-slate-500 mt-1">Manage your profile and security settings.</p>
      </div>

      <div className="max-w-md">
        <form onSubmit={handleSave} className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-[12px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">Profile</h3>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-1.5">Full Name</label>
              <input 
                type="text" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full h-10 px-3 border border-slate-300 rounded text-[14px] text-slate-900 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                required
              />
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-[12px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">Security</h3>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-1.5">Current Password</label>
              <input 
                type="password" 
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full h-10 px-3 border border-slate-300 rounded text-[14px] text-slate-900 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                required
              />
            </div>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-1.5">New Password</label>
              <input 
                type="password" 
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full h-10 px-3 border border-slate-300 rounded text-[14px] text-slate-900 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                required
              />
            </div>
          </div>

          <div className="pt-4">
            <button 
              type="submit"
              className="h-10 px-6 bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white text-[14px] font-bold rounded transition-colors"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
