import React, { useState } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import { Moon, Sun, Bell } from 'lucide-react';
import { useTheme } from '../../theme/useTheme';
import LoaderHome from './LoaderHome';
import LoaderQueue from './LoaderQueue';
import LoaderWorkbench from './LoaderWorkbench';

export default function LoaderOverview({ onLogout }) {
  const [activeTab, setActiveTab] = useState('Workbench');
  const { isDark, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-[#f0f9f6] dark:bg-[#0B0F17] flex justify-center py-0 sm:py-8 font-sans transition-colors duration-200">
      <div className="w-full max-w-[768px] bg-white dark:bg-[#111827] sm:rounded-[24px] shadow-sm dark:border dark:border-slate-800 overflow-hidden flex flex-col relative h-screen sm:h-[90vh]">
        
        {/* Header */}
        <header className="px-6 pt-8 pb-4 flex items-center justify-between bg-white dark:bg-[#111827] border-b border-transparent dark:border-slate-800 z-10 shrink-0">
          <div className="flex items-center gap-3">
            <img src={waypointLogo} alt="Logo" className="w-10 h-10 object-contain rounded-full bg-black p-1 shadow-sm" />
            <div>
              <h1 className="text-[19px] font-bold text-slate-900 dark:text-[#F8FAFC] leading-tight">Peliyagoda Central Depot</h1>
              <p className="text-[13px] text-slate-500 dark:text-[#94A3B8]">Peliyagoda Central Hub · Bay Lead A</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button 
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-emerald-400 hover:text-slate-900 dark:hover:text-emerald-300 transition-colors cursor-pointer"
              title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <button className="text-slate-600 dark:text-slate-300 hover:text-slate-900 relative p-2">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-[#E53E3E] rounded-full border-2 border-white dark:border-slate-900"></span>
            </button>
            <span className="px-3 py-1 bg-brand-50 dark:bg-emerald-950/50 text-brand-700 dark:text-emerald-400 text-xs font-bold rounded-full border border-brand-100 dark:border-emerald-800/40">Bay A</span>
          </div>
        </header>

        {/* Tabs */}
        <nav className="flex items-center px-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111827] z-10 shrink-0">
          {['Home', 'Queue', 'Workbench', 'Deferrals'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-4 text-[14px] font-bold text-center border-b-[3px] transition-colors cursor-pointer ${
                activeTab === tab
                  ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
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
