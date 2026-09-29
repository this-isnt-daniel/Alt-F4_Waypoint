import React from 'react';
import { ArrowRight } from 'lucide-react';

const MOCK_QUEUE = [
  { id: 'VEH011', depot: 'peliyagoda', type: 'Truck · Reefer', route: 'Gampaha Fresh', trip: 'Trip 2', stops: 3, status: 'Yet to Load', state: 'ready' },
  { id: 'VEH009', depot: 'peliyagoda', type: 'Truck · Reefer', route: 'Gampaha Fresh', trip: 'Trip 2', stops: 3, status: 'Loading', state: 'loading' },
  { id: 'VEH019', depot: 'peliyagoda', type: 'Van · Ambient', route: 'Colombo Central Style', trip: 'Trip 2', stops: 4, status: 'Yet to Load', state: 'ready' },
  { id: 'VEH041', depot: 'peliyagoda', type: 'Truck · Ambient', route: 'Liberty Plaza Style', trip: 'Trip 1', stops: null, status: 'Loaded', state: 'loaded' },
  { id: 'VEH014', depot: 'peliyagoda', type: 'Truck · Reefer', route: 'Kandy Fresh Run', trip: 'Trip 1', stops: 5, status: 'Loaded', state: 'loaded' },
  { id: 'VEH022', depot: 'peliyagoda', type: 'Van · Ambient', route: 'Negombo Style', trip: 'Trip 1', stops: null, status: 'Unavailable', state: 'unavailable' },

  { id: 'VEH-K04', depot: 'kandy', type: 'Truck · Ambient', route: 'Kandy South Style', trip: 'Trip 1', stops: 5, status: 'Loading', state: 'loading' },
  { id: 'VEH-K08', depot: 'kandy', type: 'Van · Reefer', route: 'Peradeniya Fresh', trip: 'Trip 2', stops: 3, status: 'Yet to Load', state: 'ready' },
  { id: 'VEH-K01', depot: 'kandy', type: 'Truck · Ambient', route: 'Peradeniya Route', trip: 'Trip 1', stops: 4, status: 'Loaded', state: 'loaded' },
];

export default function LoaderQueue({ user, onOpenTrip }) {
  const currentDepot = user?.depot || 'peliyagoda';
  const localQueue = MOCK_QUEUE.filter(v => v.depot === currentDepot);

  const readyOrLoading = localQueue.filter(v => v.state === 'ready' || v.state === 'loading');
  const loaded = localQueue.filter(v => v.state === 'loaded');
  const unavailable = localQueue.filter(v => v.state === 'unavailable');

  // Calculate metrics based on local queue
  const loadedCount = loaded.length;
  const totalCount = readyOrLoading.length + loaded.length; // ignore unavailable in total progress
  const progressPercent = totalCount === 0 ? 0 : Math.round((loadedCount / totalCount) * 100);

  const renderVehicle = (veh) => {
    let badgeClass = '';
    let btnContent = null;
    let btnAction = null;
    let containerClass = 'border border-slate-200 rounded p-4 flex flex-col sm:flex-row sm:items-center justify-between bg-white shadow-sm gap-4';

    if (veh.state === 'ready' || veh.state === 'loading') {
      badgeClass = 'bg-brand-50 text-brand-700 border border-brand-100';
      btnAction = (
        <button onClick={() => onOpenTrip(veh.id, false)} className="h-10 px-4 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded flex items-center justify-center gap-2 transition-colors w-full sm:w-auto">
          {veh.state === 'loading' ? 'Resume' : 'Open'}
        </button>
      );
    } else if (veh.state === 'loaded') {
      containerClass += ' opacity-70 hover:opacity-100 transition-opacity';
      badgeClass = 'bg-slate-100 text-slate-600 border border-slate-200';
      btnAction = (
        <button onClick={() => onOpenTrip(veh.id, true)} className="h-10 px-4 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold rounded flex items-center justify-center transition-colors w-full sm:w-auto">
          View
        </button>
      );
    } else if (veh.state === 'unavailable') {
      containerClass += ' opacity-60';
      badgeClass = 'bg-slate-100 text-slate-500 border border-slate-200';
      btnAction = (
        <button className="h-10 px-4 bg-white border border-slate-300 hover:bg-slate-50 text-slate-600 font-semibold rounded flex items-center justify-center transition-colors w-full sm:w-auto">
          Details
        </button>
      );
    }

    return (
      <div key={veh.id} className={containerClass}>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-slate-900 text-[14px]">{veh.id}</span>
            <span className="text-slate-500 font-medium text-[12px]">· {veh.type}</span>
          </div>
          <div className="text-[13px] text-slate-600 mb-2.5">
            <span className="font-semibold text-slate-800">{veh.route}</span>
            <span className="mx-1.5 text-slate-300">·</span>
            {veh.trip}
            {veh.stops && <><span className="mx-1.5 text-slate-300">·</span>{veh.stops} stops</>}
          </div>
          <span className={`px-2.5 py-1 text-[11px] font-bold rounded ${badgeClass}`}>
            {veh.status}
          </span>
        </div>
        <div className="shrink-0 w-full sm:w-auto">
          {btnAction}
        </div>
      </div>
    );
  };

  return (
    <div className="p-4 md:p-6 space-y-8 bg-[#f8fbf9] min-h-full">
      {/* Progress */}
      <div className="border border-slate-200 rounded p-4 md:p-5 bg-white shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[14px] md:text-[15px] font-bold text-slate-900 uppercase tracking-wide">{loadedCount} of {totalCount} vehicles loaded</h2>
          <span className="text-[13px] font-bold text-brand-600">{progressPercent}% complete</span>
        </div>
        <div className="h-2 w-full bg-slate-100 rounded-sm overflow-hidden">
          <div className="h-full bg-brand-500 rounded-sm transition-all duration-500" style={{ width: `${progressPercent}%` }}></div>
        </div>
      </div>

      {/* Ready / Loading */}
      <div className="space-y-3">
        <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1">Ready to Load</h3>
        {readyOrLoading.length > 0 ? (
          readyOrLoading.map(renderVehicle)
        ) : (
          <div className="border border-slate-200 rounded p-5 bg-white shadow-sm flex items-center justify-center py-10">
            <span className="text-slate-500 text-[14px] font-medium">No vehicles waiting for loading.</span>
          </div>
        )}
      </div>

      {/* Loaded */}
      {loaded.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-[12px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1 mt-6">Loaded</h3>
          {loaded.map(renderVehicle)}
        </div>
      )}

      {/* Unavailable */}
      {unavailable.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-[12px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1 mt-6">Unavailable</h3>
          {unavailable.map(renderVehicle)}
        </div>
      )}
    </div>
  );
}
