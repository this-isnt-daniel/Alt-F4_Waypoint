import React from 'react';
import { ArrowRight } from 'lucide-react';

export default function LoaderQueue({ onOpenTrip }) {
  return (
    <div className="p-6 space-y-4 bg-[#f8fbf9] min-h-full">
      {/* Progress Card */}
      <div className="border border-slate-100 rounded-2xl p-5 bg-white shadow-sm mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[17px] font-bold text-slate-900">6 of 14 Vehicles Loaded & Approved</h2>
          <span className="text-sm font-bold text-brand-600">43% Complete</span>
        </div>
        <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
          <div className="h-full bg-brand-500 rounded-full" style={{ width: '43%' }}></div>
        </div>
      </div>

      {/* List */}
      <div className="space-y-3">
        {/* VEH011 */}
        <div className="border border-slate-200 rounded-xl p-5 flex items-center justify-between bg-white shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900 text-lg">VEH011</span>
              <span className="text-slate-400 text-sm">· Truck · Reefer</span>
            </div>
            <div className="text-[15px] text-slate-500 mb-3">
              Gampaha Fresh Run (Trip 2) · 3 Stops
            </div>
            <span className="px-3 py-1 bg-orange-50 text-orange-600 text-xs font-bold rounded-full border border-orange-100">Yet to Load</span>
          </div>
          <button onClick={onOpenTrip} className="h-10 px-4 bg-brand-500 hover:bg-brand-600 text-white font-semibold rounded-lg flex items-center gap-2 transition-colors shadow-sm">
            Open <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* VEH009 */}
        <div className="border border-slate-200 rounded-xl p-5 flex items-center justify-between bg-white shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900 text-lg">VEH009</span>
              <span className="text-slate-400 text-sm">· Truck · Reefer</span>
            </div>
            <div className="text-[15px] text-slate-500 mb-3">
              Gampaha Fresh Run (Trip 2) · 3 Stops
            </div>
            <span className="px-3 py-1 bg-orange-50 text-orange-600 text-xs font-bold rounded-full border border-orange-100">Yet to Load</span>
          </div>
          <button onClick={onOpenTrip} className="h-10 px-4 bg-brand-500 hover:bg-brand-600 text-white font-semibold rounded-lg flex items-center gap-2 transition-colors shadow-sm">
            Open <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* VEH019 */}
        <div className="border border-slate-200 rounded-xl p-5 flex items-center justify-between bg-white shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900 text-lg">VEH019</span>
              <span className="text-slate-400 text-sm">· Van · Ambient</span>
            </div>
            <div className="text-[15px] text-slate-500 mb-3">
              Colombo Central Style (Trip 2) · 4 Stops
            </div>
            <span className="px-3 py-1 bg-orange-50 text-orange-600 text-xs font-bold rounded-full border border-orange-100">Yet to Load</span>
          </div>
          <button onClick={onOpenTrip} className="h-10 px-4 bg-brand-500 hover:bg-brand-600 text-white font-semibold rounded-lg flex items-center gap-2 transition-colors shadow-sm">
            Open <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* VEH041 */}
        <div className="border border-slate-200 rounded-xl p-5 flex items-center justify-between bg-white shadow-sm opacity-60">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900 text-lg">VEH041</span>
              <span className="text-slate-400 text-sm">· Truck · Ambient</span>
            </div>
            <div className="text-[15px] text-slate-500 mb-3">
              Liberty Plaza Style (Trip 1)
            </div>
            <span className="px-3 py-1 bg-brand-50 text-brand-600 text-xs font-bold rounded-full border border-brand-100">Loaded</span>
          </div>
          <button className="text-slate-600 font-semibold text-sm underline decoration-slate-300 underline-offset-4">View</button>
        </div>

        {/* VEH014 */}
        <div className="border border-slate-200 rounded-xl p-5 flex items-center justify-between bg-white shadow-sm opacity-60">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900 text-lg">VEH014</span>
              <span className="text-slate-400 text-sm">· Truck · Reefer</span>
            </div>
            <div className="text-[15px] text-slate-500 mb-3">
              Kandy Fresh Run (Trip 1) · 5 Stops
            </div>
            <span className="px-3 py-1 bg-brand-50 text-brand-600 text-xs font-bold rounded-full border border-brand-100">Loaded</span>
          </div>
          <button className="text-slate-600 font-semibold text-sm underline decoration-slate-300 underline-offset-4">View</button>
        </div>

        {/* VEH022 */}
        <div className="border border-slate-200 rounded-xl p-5 flex items-center justify-between bg-white shadow-sm opacity-60">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-bold text-slate-900 text-lg">VEH022</span>
              <span className="text-slate-400 text-sm">· Van · Ambient</span>
            </div>
            <div className="text-[15px] text-slate-500 mb-3">
              Negombo Style (Trip 1)
            </div>
            <span className="px-3 py-1 bg-red-50 text-red-600 text-xs font-bold rounded-full border border-red-100">Unavailable</span>
          </div>
          <button className="text-slate-600 font-semibold text-sm underline decoration-slate-300 underline-offset-4">Details</button>
        </div>
      </div>
    </div>
  );
}
