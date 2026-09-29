import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, ChevronDown, LogOut } from 'lucide-react';
import waypointLogo from './assets/icons/waypoint_logo.png';

export default function DriverHeader({ isOnline = true, driverUser, onLogout }) {
  const [time, setTime] = useState('');
  const [showMenu, setShowMenu] = useState(false);

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
      className="sticky top-0 z-40 w-full border-b"
      style={{ background: '#FFFFFF', borderColor: '#E2ECE7', boxShadow: '0 1px 4px rgba(11,61,51,0.06)' }}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Left: Logo + Portal badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5">
            <img src={waypointLogo} alt="Waypoint" className="w-7 h-7 object-contain rounded-lg shadow-2xs" />
            <span className="text-lg font-bold tracking-tight" style={{ color: '#0E1A17' }}>Waypoint</span>
          </div>
          <span
            className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase"
            style={{ background: '#E8F5EF', color: '#0F9D6C', border: '1px solid #C6E8D9' }}
          >
            Driver Portal
          </span>
        </div>

        {/* Center: Status chips + clock */}
        <div className="hidden md:flex items-center gap-3">
          {/* Connectivity pill */}
          <div
            className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
            style={
              isOnline
                ? { background: '#E6F6EC', color: '#16A34A', border: '1px solid #bbf7d0' }
                : { background: '#FDECEC', color: '#E5484D', border: '1px solid #fecaca' }
            }
          >
            {isOnline ? <Wifi size={12} /> : <WifiOff size={12} />}
            {isOnline ? '● Online' : '● Offline'}
          </div>

          {/* Vehicle chip */}
          <div
            className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
            style={{ background: '#F4F8F6', color: '#0B3D33', border: '1px solid #E2ECE7' }}
          >
            VEH014
          </div>

          {/* Clock */}
          <span className="text-sm font-mono font-medium tabular-nums" style={{ color: '#5B6B66' }}>
            {time || '05:30 AM'}
          </span>
        </div>

        {/* Right: Driver Avatar with Logout menu */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center gap-1.5 cursor-pointer p-1 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                style={{ background: '#E8F5EF', color: '#0F9D6C', border: '1px solid #C6E8D9' }}
              >
                {displayInitials}
              </div>
              <span className="hidden sm:block text-sm font-medium" style={{ color: '#0E1A17' }}>
                {displayName.split(' ')[0]}
              </span>
              <ChevronDown size={14} style={{ color: '#5B6B66' }} />
            </button>

            {/* Dropdown Menu */}
            {showMenu && (
              <div className="absolute right-0 mt-2 w-52 bg-white border border-gray-100 rounded-xl shadow-lg py-1.5 z-50">
                <div className="px-3 py-2 border-b border-gray-100">
                  <p className="text-xs font-semibold text-gray-900">{displayName}</p>
                  <p className="text-[11px] text-gray-500">Driver · VEH-014</p>
                  <p className="text-[10px] text-emerald-600 font-medium">{driverUser?.depot || 'Peliyagoda Depot'}</p>
                </div>
                {onLogout && (
                  <button
                    type="button"
                    onClick={() => {
                      setShowMenu(false);
                      onLogout();
                    }}
                    className="w-full text-left px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2 cursor-pointer"
                  >
                    <LogOut size={13} /> Sign out
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
