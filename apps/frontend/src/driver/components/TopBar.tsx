import { useEffect, useState } from "react";
import { WifiOff } from "lucide-react";
import { ConnectionIndicator, type ConnectionTone } from "./ConnectionIndicator";
import { VEHICLE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";
import waypointLogo from "@/assets/icons/waypoint_logo.png";
import { cn } from "@/lib/cn";

// ── COMPACT PRE-TRIP HEADER ──────────────────────────────────────
// Shown before the driver starts a trip: signin, start-day, today-trips, etc.
// Shows Waypoint identity + vehicle ID + connection dot.
export function PreTripBar() {
  const { connection, setConnection, syncRecords } = useDriverState();
  const tone: ConnectionTone = connection === "offline" ? "offline" : "online";

  return (
    <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200 shrink-0">
      {/* Waypoint wordmark */}
      <div className="flex items-center gap-2">
        <img src={waypointLogo} alt="Waypoint" className="w-6 h-6 object-contain rounded-sm" />
        <span className="text-[16px] font-bold text-[#0B2019] tracking-tight">Waypoint</span>
      </div>

      {/* Connection + vehicle tag */}
      <div className="flex items-center gap-2">
        <span className="text-[12px] font-medium text-slate-400">{VEHICLE.id}</span>
        <button
          type="button"
          onClick={() => setConnection(connection === "offline" ? "online" : "offline")}
          title={connection === "offline" ? "Offline – tap to go online" : "Online – tap to simulate offline"}
          className="rounded-full cursor-pointer focus:outline-none focus:ring-2 focus:ring-green/40"
        >
          <ConnectionIndicator tone={tone} count={syncRecords.length} />
        </button>
      </div>
    </header>
  );
}

import { Info, User } from "lucide-react";

// ── COMPACT ACTIVE-TRIP HEADER ───────────────────────────────────
// Shown during active delivery: floating overlay on top of the map.
// Shows: Waypoint · Info/Account · Connectivity · Trip Progress
export function ActiveTripBar({
  tripLabel = "Trip 1 · Fresh",
  stopLabel = "Stop 2 of 8",
  syncTone,
  onOpenVehicle,
  onOpenAccount,
}: {
  tripLabel?: string;
  stopLabel?: string;
  syncTone?: ConnectionTone;
  onOpenVehicle?: () => void;
  onOpenAccount?: () => void;
}) {
  const { connection, setConnection, syncRecords } = useDriverState();

  const resolvedTone: ConnectionTone =
    connection === "offline" ? "offline" : syncTone ?? "online";

  return (
    <div className="absolute top-0 left-0 right-0 z-50 pointer-events-none flex flex-col px-4 pt-safe-top mt-3 gap-2">
      {/* Top Row: Logo/Wordmark (left) and Icons (right) */}
      <div className="flex justify-between items-start">
        {/* Left: Branding */}
        <div className="flex items-center gap-2 bg-white/90 backdrop-blur-md px-3 py-2 rounded-full shadow-sm pointer-events-auto border border-slate-100">
          <img src={waypointLogo} alt="Waypoint" className="w-4 h-4 object-contain rounded-sm" />
          <span className="text-[13px] font-bold text-[#0B2019] tracking-tight">Waypoint</span>
        </div>
        
        {/* Right: Actions */}
        <div className="flex items-center gap-2 pointer-events-auto">
          {/* Connection Toggle */}
          <button
            type="button"
            onClick={() => setConnection(connection === "offline" ? "online" : "offline")}
            className={cn(
              "flex items-center justify-center rounded-full bg-white/90 backdrop-blur-md shadow-sm border border-slate-100 cursor-pointer hover:bg-slate-50 transition-all",
              resolvedTone === "offline" ? "h-9 px-1.5" : "w-9 h-9"
            )}
          >
            <ConnectionIndicator tone={resolvedTone} count={syncRecords.length} />
          </button>
          
          {/* Info Icon (Vehicle) */}
          <button 
            type="button"
            onClick={onOpenVehicle}
            className="flex items-center justify-center w-9 h-9 rounded-full bg-white/90 backdrop-blur-md shadow-sm border border-slate-100 text-slate-700 cursor-pointer hover:bg-slate-50 transition-colors"
          >
            <Info size={18} strokeWidth={2.5} />
          </button>

          {/* Account Icon */}
          <button 
            type="button"
            onClick={onOpenAccount}
            className="flex items-center justify-center w-9 h-9 rounded-full bg-white/90 backdrop-blur-md shadow-sm border border-slate-100 text-slate-700 cursor-pointer hover:bg-slate-50 transition-colors"
          >
            <User size={18} strokeWidth={2.5} />
          </button>
        </div>
      </div>

      {/* Second Row: Trip Progress Overlay */}
      <div className="pointer-events-auto self-start bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-lg shadow-sm border border-slate-100 flex flex-col">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{tripLabel}</span>
        <span className="text-[14px] font-bold text-slate-900 leading-tight">{stopLabel}</span>
      </div>
    </div>
  );
}
