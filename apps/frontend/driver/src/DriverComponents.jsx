import React from 'react';
import {
  Wifi,
  WifiOff,
  Truck,
  CheckCircle,
  AlertTriangle,
  Play,
  Lock,
  Snowflake,
  LifeBuoy,
  Check,
  DoorOpen,
  ShoppingBag,
  Navigation,
  Clock,
  MapPin,
  Package,
  Camera,
  Smartphone,
  FileText,
  Clock3,
  RefreshCw,
  Zap,
  Bell,
  ArrowUpDown,
  Fuel,
  ChevronRight,
  ChevronDown
} from 'lucide-react';

export default function DriverComponents({ darkMode = false }) {
  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
      {/* Title */}
      <div className="mb-8">
        <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${
          darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E8F5EF] text-[#0F9D6C] border-[#C6E8D9]'
        }`}>
          Design System & Component Library
        </span>
        <h1 className={`text-3xl font-bold mt-2 ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
          Driver Portal Components & States
        </h1>
        <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
          Interactive states (default, pressed/active, disabled, loading, offline, error) and atomic building blocks.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Buttons & Actions */}
        <div className={`rounded-[20px] p-6 border shadow-sm flex flex-col gap-4 transition-all ${
          darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
        }`}>
          <h2 className={`text-sm font-bold tracking-wide uppercase ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
            Buttons & CTAs
          </h2>
          
          <div className="flex flex-col gap-3">
            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Primary Hero CTA (Default, 64px)</p>
              <button className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white shadow-sm cursor-pointer" style={{ background: '#0F9D6C', height: 64 }}>
                <Play size={18} fill="white" /> ▶ START SHIFT
              </button>
            </div>

            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Primary Hover / Pressed State</p>
              <button className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white cursor-pointer" style={{ background: '#0B7F57', height: 64 }}>
                <Play size={18} fill="white" /> Pressed #0B7F57
              </button>
            </div>

            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Danger CTA (64px)</p>
              <button className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white cursor-pointer" style={{ background: '#E5484D', height: 64 }}>
                <Clock3 size={18} /> ⏱ SUBMIT PROBLEM REPORT
              </button>
            </div>

            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Secondary / Ghost Button (56px)</p>
              <button className={`w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-semibold border cursor-pointer ${
                darkMode ? 'border-red-900 text-red-400 hover:bg-red-950/40' : 'border-[#fca5a5] text-[#E5484D] hover:bg-[#FDECEC]'
              }`} style={{ height: 56 }}>
                <AlertTriangle size={16} /> ⚠ Report a Problem
              </button>
            </div>

            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Locked / Disabled State (52px)</p>
              <button disabled className={`w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold border border-dashed cursor-not-allowed ${
                darkMode ? 'border-[#1F3D35] bg-[#162923] text-gray-500' : 'border-[#CBD5E1] bg-[#F1F5F9] text-[#64748B]'
              }`} style={{ height: 52 }}>
                <Lock size={14} /> 🔒 LOCKED UNTIL TRIP 1 DONE
              </button>
            </div>
          </div>
        </div>

        {/* Connectivity, Chips & Warning Indicators */}
        <div className={`rounded-[20px] p-6 border shadow-sm flex flex-col gap-4 transition-all ${
          darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
        }`}>
          <h2 className={`text-sm font-bold tracking-wide uppercase ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
            Pills, Badges & Chips
          </h2>

          <div className="flex flex-col gap-3">
            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Connectivity Pills</p>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
                  darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E6F6EC] text-[#16A34A] border-[#bbf7d0]'
                }`}>
                  <Wifi size={12} /> ● Online
                </span>
                <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
                  darkMode ? 'bg-[#331417] text-red-300 border-[#5C1D24]' : 'bg-[#FDECEC] text-[#E5484D] border-[#fecaca]'
                }`}>
                  <WifiOff size={12} /> ● Offline
                </span>
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#334155] text-white">
                  ● Offline (Slate Strip)
                </span>
              </div>
            </div>

            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Vehicle & Depot Chips</p>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                  darkMode ? 'bg-[#16332B] text-gray-200 border-[#1F3D35]' : 'bg-[#F4F8F6] text-[#0B3D33] border-[#E2ECE7]'
                }`}>
                  VEH014
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase border ${
                  darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E8F5EF] text-[#0F9D6C] border-[#C6E8D9]'
                }`}>
                  PELIYAGODA DEPOT
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase border ${
                  darkMode ? 'bg-[#0F3832] text-teal-300 border-[#17544B]' : 'bg-[#E0FFFE] text-[#0F766E] border-[#99F6E4]'
                }`}>
                  <Snowflake size={11} className="inline mr-1" /> CHILLED REEFER
                </span>
              </div>
            </div>

            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Warning & Critical Chips</p>
              <div className="flex flex-col gap-2">
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border flex items-center gap-1 ${
                  darkMode ? 'bg-[#2A1E0E] text-amber-300 border-[#4A3416]' : 'bg-[#FFF4DB] text-[#B45309] border-[#FDE68A]'
                }`}>
                  <AlertTriangle size={12} /> ⚠️ VAN-ONLY ACCESS
                </span>
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border flex items-center gap-1 ${
                  darkMode ? 'bg-[#331417] text-rose-300 border-[#5C1D24]' : 'bg-[#FDECEC] text-[#E5484D] border-[#fecaca]'
                }`}>
                  <AlertTriangle size={12} /> ⚠️ MALL WINDOW 07:00-08:00 ONLY
                </span>
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border flex items-center gap-1 ${
                  darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E6F6EC] text-[#16A34A] border-[#86efac]'
                }`}>
                  <CheckCircle size={12} /> ON TIME
                </span>
              </div>
            </div>

            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Dock-Type Icon Set</p>
              <div className="grid grid-cols-2 gap-2">
                <div className={`flex items-center gap-1.5 p-2 rounded-xl border text-xs font-medium ${
                  darkMode ? 'bg-[#16332B] border-[#1F3D35] text-gray-200' : 'bg-[#F4F8F6] border-transparent text-gray-700'
                }`}>
                  <DoorOpen size={14} className="text-[#0F9D6C]" /> Rear Dock
                </div>
                <div className={`flex items-center gap-1.5 p-2 rounded-xl border text-xs font-medium ${
                  darkMode ? 'bg-[#16332B] border-[#1F3D35] text-gray-200' : 'bg-[#F4F8F6] border-transparent text-gray-700'
                }`}>
                  <Truck size={14} className={darkMode ? 'text-gray-400' : 'text-[#5B6B66]'} /> Van Bay
                </div>
                <div className={`flex items-center gap-1.5 p-2 rounded-xl border text-xs font-medium ${
                  darkMode ? 'bg-[#16332B] border-[#1F3D35] text-gray-200' : 'bg-[#F4F8F6] border-transparent text-gray-700'
                }`}>
                  <ShoppingBag size={14} className={darkMode ? 'text-gray-400' : 'text-[#5B6B66]'} /> Mall Bay
                </div>
                <div className={`flex items-center gap-1.5 p-2 rounded-xl border text-xs font-medium ${
                  darkMode ? 'bg-[#16332B] border-[#1F3D35] text-gray-200' : 'bg-[#F4F8F6] border-transparent text-gray-700'
                }`}>
                  <MapPin size={14} className={darkMode ? 'text-gray-400' : 'text-[#5B6B66]'} /> Street / Curb
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sync Queue, Loading & Segmented Controls */}
        <div className={`rounded-[20px] p-6 border shadow-sm flex flex-col gap-4 transition-all ${
          darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
        }`}>
          <h2 className={`text-sm font-bold tracking-wide uppercase ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
            Queue & Controls
          </h2>

          <div className="flex flex-col gap-3">
            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Segmented Control (Delivery Outcome)</p>
              <div className={`flex rounded-xl p-1 border ${
                darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-[#E2ECE7]'
              }`}>
                <span className="flex-1 py-1.5 text-center text-xs font-semibold rounded-lg bg-[#0F9D6C] text-white">
                  ✓ Full Delivery
                </span>
                <span className={`flex-1 py-1.5 text-center text-xs font-semibold ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
                  Partial
                </span>
                <span className={`flex-1 py-1.5 text-center text-xs font-semibold ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
                  Rejected
                </span>
              </div>
            </div>

            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>Queue Row States (Saved / Saving / Synced)</p>
              <div className="flex flex-col gap-2">
                <div className={`flex items-center justify-between p-2.5 rounded-xl border text-xs ${
                  darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-transparent'
                }`}>
                  <span className={`font-semibold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>OUT-014 Keells</span>
                  <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold border ${
                    darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E6F6EC] text-[#16A34A] border-[#86efac]'
                  }`}>
                    <Check size={10} strokeWidth={3} /> Saved ✓
                  </span>
                </div>

                <div className={`flex items-center justify-between p-2.5 rounded-xl border text-xs ${
                  darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-transparent'
                }`}>
                  <span className={`font-semibold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>OUT-031 SPAR</span>
                  <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold border ${
                    darkMode ? 'bg-[#1E3A8A]/40 text-blue-300 border-[#3B82F6]/50' : 'bg-[#E8F0FF] text-[#3B82F6] border-[#BFDBFE]'
                  }`}>
                    <RefreshCw size={10} className="animate-spin" /> Saving...
                  </span>
                </div>

                <div className={`flex items-center justify-between p-2.5 rounded-xl border text-xs ${
                  darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-transparent'
                }`}>
                  <span className={`font-semibold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>All 3 Records</span>
                  <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold border ${
                    darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E6F6EC] text-[#166534] border-[#86efac]'
                  }`}>
                    <CheckCircle size={11} /> Synced
                  </span>
                </div>
              </div>
            </div>

            <div>
              <p className={`text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>KPI Summary Pills</p>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                  darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E6F6EC] text-[#14532D] border-[#86efac]'
                }`}>
                  2 DELIVERED
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                  darkMode ? 'bg-[#2A1E0E] text-amber-300 border-[#4A3416]' : 'bg-[#FFF4DB] text-[#92400E] border-[#FDE68A]'
                }`}>
                  1 PARTIAL
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                  darkMode ? 'bg-[#16332B] text-gray-300 border-[#1F3D35]' : 'bg-white text-[#5B6B66] border-[#E2ECE7]'
                }`}>
                  0 FAILED
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
