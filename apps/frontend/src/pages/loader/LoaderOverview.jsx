import React, { useState } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import { Moon, Bell } from 'lucide-react';
import LoaderHome from './LoaderHome';
import LoaderQueue from './LoaderQueue';
import LoaderWorkbench from './LoaderWorkbench';

export default function LoaderOverview({ onLogout }) {
  const [activeTab, setActiveTab] = useState('Workbench');

  return (
    <div className="min-h-screen bg-[#f0f9f6] flex justify-center py-0 sm:py-8 font-sans">
      <div className="w-full max-w-[768px] bg-white sm:rounded-[24px] shadow-sm overflow-hidden flex flex-col relative h-screen sm:h-[90vh]">
        
        {/* Header */}
        <header className="px-6 pt-8 pb-4 flex items-center justify-between bg-white z-10 shrink-0">
          <div className="flex items-center gap-3">
            <img src={waypointLogo} alt="Logo" className="w-10 h-10 object-contain rounded-full bg-black p-1" />
            <div>
              <h1 className="text-[19px] font-bold text-slate-900 leading-tight">Peliyagoda Central Depot</h1>
              <p className="text-[13px] text-slate-500">Peliyagoda Central Hub · Bay Lead A</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="text-slate-600 hover:text-slate-900"><Moon className="w-5 h-5" /></button>
            <button className="text-slate-600 hover:text-slate-900 relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-0 right-0.5 w-2 h-2 bg-[#E53E3E] rounded-full border-2 border-white"></span>
            </button>
            <span className="px-3 py-1 bg-brand-50 text-brand-700 text-xs font-bold rounded-full border border-brand-100">Bay A</span>
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
        <main className="flex-1 bg-white overflow-y-auto relative">
          {activeTab === 'Home' && <LoaderHome />}
          {activeTab === 'Queue' && <LoaderQueue onOpenTrip={() => setActiveTab('Workbench')} />}
          {activeTab === 'Workbench' && <LoaderWorkbench />}
          {activeTab === 'Deferrals' && <div className="p-6 text-center text-slate-500 font-medium">Deferrals Log (To be implemented)</div>}
        </main>
      </div>
    </div>
  );
}
