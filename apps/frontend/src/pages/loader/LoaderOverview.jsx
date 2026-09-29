import React, { useState } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import { Moon, Bell, LogOut, Settings } from 'lucide-react';
import LoaderHome from './LoaderHome';
import LoaderQueue from './LoaderQueue';
import LoaderWorkbench from './LoaderWorkbench';
import LoaderDeferrals from './LoaderDeferrals';
import LoaderSettings from './LoaderSettings';

export default function LoaderOverview({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('Workbench');
  const [activeVehicleId, setActiveVehicleId] = useState(null);
  const [isReadOnly, setIsReadOnly] = useState(false);

  const handleOpenTrip = (vehicleId, readOnly = false) => {
    setActiveVehicleId(vehicleId);
    setIsReadOnly(readOnly);
    setActiveTab('Workbench');
  };

  // Derive location context from user depot
  const isPeliyagoda = user?.depot === 'peliyagoda';
  const depotName = isPeliyagoda ? 'Peliyagoda Central Depot' : 'Kandy Regional Hub';

  return (
    <div className="w-full h-dvh bg-white flex flex-col overflow-hidden font-sans">
        
        {/* Header */}
        <header className="px-4 sm:px-6 h-14 flex items-center justify-between bg-white z-10 shrink-0 border-b border-slate-100">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="flex items-center gap-2.5 shrink-0">
              <img src={waypointLogo} alt="Waypoint" className="w-5 h-5 object-contain rounded-sm" />
              <span className="text-[15px] font-bold text-[#0B2019] tracking-tight">Waypoint</span>
            </div>
            <div className="w-[1px] h-4 bg-slate-200" />
            <span className="text-[14px] font-bold text-slate-900 tracking-tight">{depotName}</span>
          </div>
          <div className="flex items-center gap-4">
            <button className="text-slate-600 hover:text-slate-900"><Moon className="w-5 h-5" /></button>
            <button className="text-slate-600 hover:text-slate-900 relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-0 right-0.5 w-2 h-2 bg-[#E53E3E] rounded-full border-2 border-white"></span>
            </button>
            <button onClick={onLogout} className="text-slate-400 hover:text-slate-600 ml-1">
              <LogOut className="w-5 h-5" />
            </button>
            <button onClick={() => setActiveTab('Settings')} className={`ml-1 transition-colors ${activeTab === 'Settings' ? 'text-brand-600' : 'text-slate-400 hover:text-slate-600'}`}>
              <Settings className="w-5 h-5" />
            </button>
            {user?.bay && (
              <span className="px-2.5 py-1 bg-brand-50 text-brand-700 text-[11px] font-bold rounded border border-brand-100 whitespace-nowrap">
                {user.bay.replace('Lead ', '')}
              </span>
            )}
          </div>
        </header>

        {/* Tabs */}
        <nav className="flex items-center px-4 border-b border-slate-200 bg-white z-10 shrink-0">
          {['Home', 'Queue', 'Workbench', 'Deferrals'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-4 text-[14px] font-bold text-center border-b-[3px] transition-colors ${
                activeTab === tab
                  ? 'border-slate-800 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>

        {/* Content Area */}
        <main className="flex-1 bg-white overflow-y-auto relative flex flex-col min-h-0">
          {activeTab === 'Home' && <LoaderHome user={user} />}
          {activeTab === 'Queue' && <LoaderQueue user={user} onOpenTrip={handleOpenTrip} />}
          {activeTab === 'Workbench' && <LoaderWorkbench user={user} vehicleId={activeVehicleId} readOnly={isReadOnly} />}
          {activeTab === 'Deferrals' && <LoaderDeferrals user={user} />}
          {activeTab === 'Settings' && <LoaderSettings user={user} />}
        </main>
    </div>
  );
}
