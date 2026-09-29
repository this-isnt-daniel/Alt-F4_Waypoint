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

export default function DriverComponents() {
  return (
    <div className="max-w-7xl mx-auto px-6 py-8" style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>
      {/* Title */}
      <div className="mb-8">
        <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider" style={{ background: '#E8F5EF', color: '#0F9D6C', border: '1px solid #C6E8D9' }}>
          Design System & Component Library
        </span>
        <h1 className="text-3xl font-bold mt-2" style={{ color: '#0B3D33' }}>
          Driver Portal Components & States
        </h1>
        <p className="text-sm mt-1" style={{ color: '#5B6B66' }}>
          Interactive states (default, pressed/active, disabled, loading, offline, error) and atomic building blocks.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Buttons & Actions */}
        <div className="rounded-[20px] p-6 bg-white border border-[#E2ECE7] shadow-sm flex flex-col gap-4">
          <h2 className="text-sm font-bold tracking-wide uppercase" style={{ color: '#0B3D33' }}>Buttons & CTAs</h2>
          
          <div className="flex flex-col gap-3">
            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Primary Hero CTA (Default, 64px)</p>
              <button className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white shadow-sm cursor-pointer" style={{ background: '#0F9D6C', height: 64 }}>
                <Play size={18} fill="white" /> ▶ START SHIFT
              </button>
            </div>

            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Primary Hover / Pressed State</p>
              <button className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white cursor-pointer" style={{ background: '#0B7F57', height: 64 }}>
                <Play size={18} fill="white" /> Pressed #0B7F57
              </button>
            </div>

            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Danger CTA (64px)</p>
              <button className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold text-white cursor-pointer" style={{ background: '#E5484D', height: 64 }}>
                <Clock3 size={18} /> ⏱ SUBMIT PROBLEM REPORT
              </button>
            </div>

            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Secondary / Ghost Button (56px)</p>
              <button className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-semibold border border-[#fca5a5] text-[#E5484D] cursor-pointer" style={{ height: 56 }}>
                <AlertTriangle size={16} /> ⚠ Report a Problem
              </button>
            </div>

            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Locked / Disabled State (52px)</p>
              <button disabled className="w-full flex items-center justify-center gap-2 rounded-2xl text-sm font-bold border border-dashed border-[#CBD5E1] bg-[#F1F5F9] text-[#64748B] cursor-not-allowed" style={{ height: 52 }}>
                <Lock size={14} /> 🔒 LOCKED UNTIL TRIP 1 DONE
              </button>
            </div>
          </div>
        </div>

        {/* Connectivity, Chips & Warning Indicators */}
        <div className="rounded-[20px] p-6 bg-white border border-[#E2ECE7] shadow-sm flex flex-col gap-4">
          <h2 className="text-sm font-bold tracking-wide uppercase" style={{ color: '#0B3D33' }}>Pills, Badges & Chips</h2>

          <div className="flex flex-col gap-3">
            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Connectivity Pills</p>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#E6F6EC] text-[#16A34A] border border-[#bbf7d0]">
                  <Wifi size={12} /> ● Online
                </span>
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#FDECEC] text-[#E5484D] border border-[#fecaca]">
                  <WifiOff size={12} /> ● Offline
                </span>
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#334155] text-white">
                  ● Offline (Slate Strip)
                </span>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Vehicle & Depot Chips</p>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-[#F4F8F6] text-[#0B3D33] border border-[#E2ECE7]">
                  VEH014
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase bg-[#E8F5EF] text-[#0F9D6C] border border-[#C6E8D9]">
                  PELIYAGODA DEPOT
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase bg-[#E0FFFE] text-[#0F766E] border border-[#99F6E4]">
                  <Snowflake size={11} className="inline mr-1" /> CHILLED REEFER
                </span>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Warning & Critical Chips</p>
              <div className="flex flex-col gap-2">
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-[#FFF4DB] text-[#B45309] border border-[#FDE68A] flex items-center gap-1">
                  <AlertTriangle size={12} /> ⚠️ VAN-ONLY ACCESS
                </span>
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-[#FDECEC] text-[#E5484D] border border-[#fecaca] flex items-center gap-1">
                  <AlertTriangle size={12} /> ⚠️ MALL WINDOW 07:00-08:00 ONLY
                </span>
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-[#E6F6EC] text-[#16A34A] border border-[#86efac] flex items-center gap-1">
                  <CheckCircle size={12} /> ON TIME
                </span>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Dock-Type Icon Set</p>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-1.5 p-2 rounded-xl bg-[#F4F8F6] text-xs font-medium">
                  <DoorOpen size={14} className="text-[#0F9D6C]" /> Rear Dock
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded-xl bg-[#F4F8F6] text-xs font-medium">
                  <Truck size={14} className="text-[#5B6B66]" /> Van Bay
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded-xl bg-[#F4F8F6] text-xs font-medium">
                  <ShoppingBag size={14} className="text-[#5B6B66]" /> Mall Bay
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded-xl bg-[#F4F8F6] text-xs font-medium">
                  <MapPin size={14} className="text-[#5B6B66]" /> Street / Curb
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sync Queue, Loading & Segmented Controls */}
        <div className="rounded-[20px] p-6 bg-white border border-[#E2ECE7] shadow-sm flex flex-col gap-4">
          <h2 className="text-sm font-bold tracking-wide uppercase" style={{ color: '#0B3D33' }}>Queue & Controls</h2>

          <div className="flex flex-col gap-3">
            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Segmented Control (Delivery Outcome)</p>
              <div className="flex rounded-xl p-1 bg-[#F4F8F6] border border-[#E2ECE7]">
                <span className="flex-1 py-1.5 text-center text-xs font-semibold rounded-lg bg-[#0F9D6C] text-white">
                  ✓ Full Delivery
                </span>
                <span className="flex-1 py-1.5 text-center text-xs font-semibold text-[#5B6B66]">
                  Partial
                </span>
                <span className="flex-1 py-1.5 text-center text-xs font-semibold text-[#5B6B66]">
                  Rejected
                </span>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>Queue Row States (Saved / Saving / Synced)</p>
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between p-2 rounded-xl bg-[#F4F8F6] text-xs">
                  <span className="font-semibold text-[#0B3D33]">OUT-014 Keells</span>
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold bg-[#E6F6EC] text-[#16A34A]">
                    <Check size={10} strokeWidth={3} /> Saved ✓
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-xl bg-[#F4F8F6] text-xs">
                  <span className="font-semibold text-[#0B3D33]">OUT-031 SPAR</span>
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold bg-[#E8F0FF] text-[#3B82F6]">
                    <RefreshCw size={10} className="animate-spin" /> Saving...
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-xl bg-[#F4F8F6] text-xs">
                  <span className="font-semibold text-[#0B3D33]">All 3 Records</span>
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold bg-[#E6F6EC] text-[#166534]">
                    <CheckCircle size={11} /> Synced
                  </span>
                </div>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold mb-1" style={{ color: '#5B6B66' }}>KPI Summary Pills</p>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#E6F6EC] text-[#14532D] border border-[#86efac]">
                  2 DELIVERED
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FFF4DB] text-[#92400E] border border-[#FDE68A]">
                  1 PARTIAL
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-white text-[#5B6B66] border border-[#E2ECE7]">
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
