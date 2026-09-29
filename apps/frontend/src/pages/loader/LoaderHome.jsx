import React from 'react';

export default function LoaderHome() {
  return (
    <div className="p-6 space-y-6">
      {/* Shift Card */}
      <div className="border border-slate-100 rounded-2xl p-5 shadow-sm">
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-900">Morning Dispatch & Turnaround</h2>
          <span className="px-3 py-1 bg-brand-50 text-brand-700 text-xs font-bold rounded-full">
            Shift Active · 03:00 AM – 11:30 AM
          </span>
        </div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-slate-500">Dispatch Progress</span>
          <span className="text-sm font-bold text-brand-600">8 of 14 Vehicles (57%)</span>
        </div>
        <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
          <div className="h-full bg-brand-500 rounded-full" style={{ width: '57%' }}></div>
        </div>
      </div>

      {/* Active Vehicles Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-900">Active Vehicles</h3>
        <span className="text-sm font-bold text-brand-500">5 Live</span>
      </div>

      {/* Vehicle List */}
      <div className="space-y-3">
        {/* VEH011 */}
        <div className="border border-slate-100 rounded-xl p-4 flex items-start justify-between shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900">VEH011</span>
              <span className="text-slate-400 text-sm">· Truck · Reefer</span>
            </div>
            <div className="text-sm text-slate-600 mb-1">
              Route: <span className="font-semibold text-slate-800">Gampaha Fresh</span> (3 stops)
            </div>
            <div className="text-xs text-slate-500">Expected Depot Return: 08:22 AM</div>
          </div>
          <span className="px-3 py-1 bg-blue-50 text-blue-600 text-xs font-bold rounded-full">En Route</span>
        </div>

        {/* VEH009 */}
        <div className="border border-slate-100 rounded-xl p-4 flex items-start justify-between shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900">VEH009</span>
              <span className="text-slate-400 text-sm">· Truck · Reefer</span>
            </div>
            <div className="text-sm text-slate-600 mb-1">
              Route: <span className="font-semibold text-slate-800">Gampaha Fresh</span> (3 stops)
            </div>
            <div className="text-xs font-semibold text-orange-500 mb-1">ETA: 08:45 AM (In 15 mins)</div>
            <div className="text-xs font-semibold text-brand-600">Pre-stage next trip cargo</div>
          </div>
          <span className="px-3 py-1 bg-orange-50 text-orange-600 text-xs font-bold rounded-full">Returning</span>
        </div>

        {/* VEH019 */}
        <div className="border border-slate-100 rounded-xl p-4 flex items-start justify-between shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900">VEH019</span>
              <span className="text-slate-400 text-sm">· Van · Ambient</span>
            </div>
            <div className="text-sm text-slate-600 mb-1">
              Route: <span className="font-semibold text-slate-800">Colombo Central Style</span> (4 stops)
            </div>
            <div className="text-xs font-semibold text-red-500">Adjusted return: 10:42 AM (+22m late)</div>
          </div>
          <span className="px-3 py-1 bg-red-50 text-red-600 text-xs font-bold rounded-full">Delayed</span>
        </div>

        {/* VEH041 */}
        <div className="border border-slate-100 rounded-xl p-4 flex items-start justify-between shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900">VEH041</span>
              <span className="text-slate-400 text-sm">· Truck · Ambient</span>
            </div>
            <div className="text-sm text-slate-600 mb-1">
              Route: <span className="font-semibold text-slate-800">Liberty Plaza Style</span>
            </div>
            <div className="text-xs text-slate-500">Released 03:28 AM · Driver: S. Perera</div>
          </div>
          <span className="px-3 py-1 bg-brand-50 text-brand-600 text-xs font-bold rounded-full">Dispatched</span>
        </div>

        {/* VEH014 */}
        <div className="border border-slate-100 rounded-xl p-4 flex items-start justify-between shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900">VEH014</span>
              <span className="text-slate-400 text-sm">· Truck · Reefer</span>
            </div>
            <div className="text-sm text-slate-600 mb-1">
              Route: <span className="font-semibold text-slate-800">Kandy Fresh</span> (5 stops)
            </div>
            <div className="text-xs text-slate-500">Expected Depot Return: 09:15 AM</div>
          </div>
          <span className="px-3 py-1 bg-blue-50 text-blue-600 text-xs font-bold rounded-full">En Route</span>
        </div>
      </div>
    </div>
  );
}
