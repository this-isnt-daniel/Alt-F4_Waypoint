import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, ChevronDown } from 'lucide-react';
import waypointLogo from './assets/icons/waypoint_logo.png';

export default function DriverHeader({ isOnline = true, onBackToPortals }) {
  const [time, setTime] = useState('');

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

        {/* Left: Logo + Portal name */}
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToPortals}
            className="flex items-center gap-2.5 hover:opacity-80 transition-opacity cursor-pointer"
          >
            <img src={waypointLogo} alt="Waypoint" className="w-7 h-7 object-contain rounded-lg" />
            <span className="text-lg font-bold tracking-tight" style={{ color: '#0E1A17' }}>Waypoint</span>
          </button>
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

        {/* Right: Driver avatar */}
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
            style={{ background: '#E8F5EF', color: '#0F9D6C', border: '1px solid #C6E8D9' }}
          >
            KP
          </div>
          <span className="hidden sm:block text-sm font-medium" style={{ color: '#0E1A17' }}>
            Kasun Perera
          </span>
          <ChevronDown size={14} style={{ color: '#5B6B66' }} />
        </div>
      </div>
    </header>
  );
}
