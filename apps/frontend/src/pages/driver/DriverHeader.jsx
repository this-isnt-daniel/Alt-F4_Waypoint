import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  ChevronDown, 
  Sun, 
  Moon, 
  Wifi, 
  WifiOff, 
  LogOut, 
  Check
} from 'lucide-react';
import waypointLogo from './assets/icons/waypoint_logo.png';

export default function DriverHeader({ 
  navTabs = [], 
  activeTab = '', 
  onSelectTab, 
  driverUser, 
  onLogout,
  isOnline = true,
  onToggleSignal,
  darkMode = false,
  onToggleDarkMode,
  hasUnreadNotifications = true,
  onToggleNotifications,
  depots = ['Peliyagoda Depot', 'Colombo Depot', 'Gampaha Hub'],
  currentDepot = 'Peliyagoda Depot',
  onSelectDepot
}) {
  const [time, setTime] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showDepotMenu, setShowDepotMenu] = useState(false);
  const [showNotificationsModal, setShowNotificationsModal] = useState(false);

  const displayName = driverUser?.name || 'Kasun Perera';
  const displayInitials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header 
      className={`w-full border-b sticky top-0 z-40 transition-colors duration-200 ${
        darkMode 
          ? 'bg-[#0E1A17] border-[#1C2E29] text-gray-100 shadow-sm' 
          : 'bg-white border-gray-100 text-gray-900 shadow-xs'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">

        {/* ── Left: Brand Logo & Navigation Pills (identical to StoreManager layout) ── */}
        <div className="flex items-center gap-6 xl:gap-8 flex-shrink-0">
          {/* Logo & Brand title */}
          <div 
            onClick={() => onSelectTab && onSelectTab(navTabs[0]?.id || 'overview')}
            className="flex items-center gap-2.5 cursor-pointer flex-shrink-0"
          >
            <img
              src={waypointLogo}
              alt="Waypoint"
              className="w-7 h-7 object-contain rounded-lg shadow-xs"
            />
            <span
              className={`text-xl font-bold tracking-tight ${darkMode ? 'text-white' : 'text-[#0B2019]'}`}
              style={{ fontFamily: "'Inter', sans-serif" }}
            >
              Waypoint
            </span>
            <span
              className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wider uppercase"
              style={{ 
                background: darkMode ? '#103328' : '#E8F7F0', 
                color: '#059669', 
                border: darkMode ? '1px solid #174D3D' : '1px solid #C6E8D9' 
              }}
            >
              Driver
            </span>
          </div>

          {/* Navigation Pills (identical to StoreManager pills) */}
          {navTabs.length > 0 && (
            <nav className="hidden md:flex items-center gap-1.5" aria-label="Portal Navigation">
              {navTabs.map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => onSelectTab && onSelectTab(tab.id)}
                    className={`px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors cursor-pointer whitespace-nowrap ${
                      isActive
                        ? darkMode 
                          ? 'bg-[#124235] text-[#34D399] font-semibold' 
                          : 'bg-[#E8F7F0] text-[#059669] font-semibold'
                        : darkMode 
                          ? 'text-gray-300 hover:text-white hover:bg-[#18332B]' 
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          )}
        </div>

        {/* ── Right: Depot Selector, Signal Toggle, Vehicle, Clock, Dark/Light Mode, Notifications, Avatar ── */}
        <div className="flex items-center gap-2 sm:gap-2.5 flex-shrink-0">

          {/* Depot / Outlet Selector Pill */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowDepotMenu(!showDepotMenu)}
              className={`inline-flex items-center gap-1.5 px-3 py-1 text-sm font-normal rounded-full transition-colors cursor-pointer border whitespace-nowrap ${
                darkMode
                  ? 'bg-[#152923] border-[#203D34] text-gray-200 hover:border-[#2D5448]'
                  : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{currentDepot}</span>
              <ChevronDown size={14} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
            </button>

            {/* Depot Menu */}
            {showDepotMenu && (
              <div 
                className={`absolute right-0 mt-2 w-48 rounded-xl shadow-lg py-1.5 z-50 border ${
                  darkMode ? 'bg-[#152923] border-[#224037]' : 'bg-white border-gray-100'
                }`}
              >
                <div className="px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                  Select Depot Hub
                </div>
                {depots.map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => {
                      if (onSelectDepot) onSelectDepot(d);
                      setShowDepotMenu(false);
                    }}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between transition-colors ${
                      d === currentDepot 
                        ? 'text-[#059669] font-bold bg-[#E8F7F0]/40' 
                        : darkMode 
                          ? 'text-gray-200 hover:bg-[#1E3B32]' 
                          : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <span>{d}</span>
                    {d === currentDepot && <Check size={13} />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Connectivity / Signal Pill */}
          <button
            type="button"
            onClick={onToggleSignal}
            title="Click to toggle Online/Offline signal state"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-all cursor-pointer whitespace-nowrap"
            style={
              isOnline
                ? darkMode
                  ? { background: '#123D2E', color: '#34D399', borderColor: '#1F5A44' }
                  : { background: '#E6F6EC', color: '#16A34A', borderColor: '#bbf7d0' }
                : darkMode
                  ? { background: '#3F1E20', color: '#F87171', borderColor: '#65292D' }
                  : { background: '#FDECEC', color: '#E5484D', borderColor: '#fecaca' }
            }
          >
            {isOnline ? <Wifi size={12} /> : <WifiOff size={12} />}
            <span className="hidden sm:inline">{isOnline ? 'Online' : 'Offline'}</span>
          </button>

          {/* Vehicle Chip (Clean typography, no strikethrough or cut off) */}
          <div
            className={`hidden md:inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold font-mono tracking-wider border whitespace-nowrap select-none ${
              darkMode 
                ? 'bg-[#152923] text-[#34D399] border-[#224037]' 
                : 'bg-[#F4F8F6] text-[#0B3D33] border-[#E2ECE7]'
            }`}
          >
            VEH014
          </div>

          {/* Real-time Clock */}
          <span 
            className={`hidden xl:inline-block text-xs font-mono font-medium tabular-nums whitespace-nowrap select-none ${
              darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}
          >
            {time || '05:30 AM'}
          </span>

          {/* ☀️ / 🌙 Dark & Light Mode Toggle */}
          <button
            type="button"
            onClick={onToggleDarkMode}
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            className={`relative w-8 h-8 rounded-full border flex items-center justify-center transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#059669] flex-shrink-0 ${
              darkMode
                ? 'border-[#224037] bg-[#152923] text-amber-400 hover:border-amber-400/50 hover:bg-[#1B352E]'
                : 'border-gray-200 bg-white text-gray-600 hover:text-gray-900 hover:border-gray-300'
            }`}
          >
            {darkMode ? <Sun size={15} strokeWidth={2} /> : <Moon size={15} strokeWidth={2} />}
          </button>

          {/* 🔔 Notifications Button (identical to StoreManager bell) */}
          <div className="relative flex-shrink-0">
            <button
              type="button"
              onClick={() => {
                if (onToggleNotifications) onToggleNotifications();
                setShowNotificationsModal(!showNotificationsModal);
              }}
              title="Notifications"
              className={`relative w-8 h-8 rounded-full border flex items-center justify-center transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#059669] ${
                darkMode
                  ? 'border-[#224037] bg-[#152923] text-gray-300 hover:text-white hover:border-[#2D5448]'
                  : 'border-gray-200 bg-white text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              <Bell size={15} strokeWidth={2} />
              {hasUnreadNotifications && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-[#059669] rounded-full ring-2 ring-white" />
              )}
            </button>

            {/* Notifications Popover */}
            {showNotificationsModal && (
              <div 
                className={`absolute right-0 mt-2 w-72 rounded-2xl shadow-xl p-3 z-50 border ${
                  darkMode ? 'bg-[#152923] border-[#224037] text-gray-200' : 'bg-white border-gray-100 text-gray-900'
                }`}
              >
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-gray-100/50">
                  <p className="text-xs font-bold">Driver Notifications</p>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#E8F7F0] text-[#059669] font-bold">
                    3 New
                  </span>
                </div>
                <div className="flex flex-col gap-2 text-xs">
                  <div className={`p-2 rounded-xl border ${darkMode ? 'bg-[#0E1A17] border-[#1F3D33]' : 'bg-amber-50/60 border-amber-200/60'}`}>
                    <p className="font-semibold text-amber-800 text-[11px]">🔔 Route Sequence Updated</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">OUT031 SPAR Express moved ahead of OUT027.</p>
                  </div>
                  <div className={`p-2 rounded-xl border ${darkMode ? 'bg-[#0E1A17] border-[#1F3D33]' : 'bg-emerald-50/60 border-emerald-200/60'}`}>
                    <p className="font-semibold text-emerald-800 text-[11px]">✓ Offline Run Sheet Cached</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">47 stops available for offline delivery.</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Profile Avatar (identical to StoreManager layout) */}
          <div className="relative flex-shrink-0">
            <button
              type="button"
              onClick={() => setShowUserMenu(!showUserMenu)}
              title="Driver Account"
              className="w-8 h-8 rounded-full bg-[#E0F2E9] border border-[#C6E7D5] text-[#059669] text-xs font-semibold flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity"
            >
              {displayInitials}
            </button>

            {/* Profile Dropdown */}
            {showUserMenu && (
              <div 
                className={`absolute right-0 mt-2 w-52 rounded-xl shadow-lg py-1 z-50 border ${
                  darkMode ? 'bg-[#152923] border-[#224037]' : 'bg-white border-gray-100'
                }`}
              >
                <div className="px-3 py-2 border-b border-gray-100/50">
                  <p className={`text-xs font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{displayName}</p>
                  <p className="text-[11px] text-gray-400">driver/VEH-014 · {currentDepot}</p>
                </div>
                {onLogout && (
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      onLogout();
                    }}
                    className="w-full text-left px-3 py-2 text-xs text-red-600 hover:bg-red-50/50 transition-colors cursor-pointer flex items-center gap-1.5"
                  >
                    <LogOut size={13} />
                    <span>Sign out</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
