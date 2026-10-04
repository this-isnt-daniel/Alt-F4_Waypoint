import React, { useEffect, useMemo, useState } from 'react';
import { ArrowRight, RefreshCcw } from 'lucide-react';
import { fetchLoaderQueue } from './loaderApi';

function normalizeTrip(trip) {
  const status = trip.status || 'planned';
  const state = status === 'planned' ? 'ready' : status;
  return {
    ...trip,
    state,
    displayStatus: status.replaceAll('_', ' '),
    vehicleType: [trip.vehicle_type, trip.vehicle_temp].filter(Boolean).join(' - ') || 'Vehicle',
    routeLabel: trip.route_label || `${trip.vehicle_id} Trip ${trip.trip_no}`,
  };
}

export default function LoaderQueue({ user, onOpenTrip }) {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadQueue = async () => {
    setLoading(true);
    setError('');
    try {
      if (!user?.token) throw new Error("Missing auth token");
      const rows = await fetchLoaderQueue(user.token);
      setQueue(rows.map(normalizeTrip));
    } catch (err) {
      setError(err.message);
      setQueue([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [user?.token]);

  const readyOrLoading = queue.filter((trip) => ['ready', 'loading', 'planned'].includes(trip.state));
  const loaded = queue.filter((trip) => trip.state === 'loaded' || trip.state === 'out_for_delivery');
  const unavailable = queue.filter((trip) => trip.state === 'vehicle_unavailable');

  const metrics = useMemo(() => {
    const totalCount = readyOrLoading.length + loaded.length;
    const loadedCount = loaded.length;
    return {
      loadedCount,
      totalCount,
      progressPercent: totalCount === 0 ? 0 : Math.round((loadedCount / totalCount) * 100),
    };
  }, [readyOrLoading.length, loaded.length]);

  const renderTrip = (trip) => {
    const isEditable = trip.state === 'ready' || trip.state === 'planned' || trip.state === 'loading';
    const isLoaded = trip.state === 'loaded' || trip.state === 'out_for_delivery';
    let badgeClass = 'bg-brand-50 text-brand-700 border border-brand-100';
    let containerClass = 'border border-slate-200 rounded p-4 flex flex-col sm:flex-row sm:items-center justify-between bg-white shadow-sm gap-4';

    if (isLoaded) {
      badgeClass = 'bg-slate-100 text-slate-600 border border-slate-200';
      containerClass += ' opacity-80 hover:opacity-100 transition-opacity';
    }
    if (trip.state === 'vehicle_unavailable') {
      badgeClass = 'bg-red-50 text-red-700 border border-red-100';
      containerClass += ' opacity-75';
    }

    return (
      <div key={trip.trip_id} className={containerClass}>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-slate-900 text-[14px]">{trip.vehicle_id}</span>
            <span className="text-slate-500 font-medium text-[12px]">{trip.vehicleType}</span>
          </div>
          <div className="text-[13px] text-slate-600 mb-2.5">
            <span className="font-semibold text-slate-800">{trip.routeLabel}</span>
            <span className="mx-1.5 text-slate-300">-</span>
            Trip {trip.trip_no}
            <span className="mx-1.5 text-slate-300">-</span>
            {trip.stop_count} stops
            <span className="mx-1.5 text-slate-300">-</span>
            {trip.verified_items}/{trip.total_items} items
            {trip.discrepancy_count > 0 && (
              <span className="ml-2 text-amber-700 font-semibold">{trip.discrepancy_count} issue(s)</span>
            )}
          </div>
          <span className={`px-2.5 py-1 text-[11px] font-bold rounded capitalize ${badgeClass}`}>
            {trip.displayStatus}
          </span>
        </div>
        <div className="shrink-0 w-full sm:w-auto">
          <button
            onClick={() => onOpenTrip(trip.trip_id, trip.read_only || !isEditable)}
            className={`h-10 px-4 font-semibold rounded flex items-center justify-center gap-2 transition-colors w-full sm:w-auto ${
              isEditable
                ? 'bg-brand-600 hover:bg-brand-700 text-white'
                : 'bg-white border border-slate-300 hover:bg-slate-50 text-slate-700'
            }`}
          >
            {isEditable ? (trip.state === 'loading' ? 'Resume' : 'Open') : 'View'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="p-4 md:p-6 space-y-8 bg-[#f8fbf9] min-h-full">
      <div className="border border-slate-200 rounded p-4 md:p-5 bg-white shadow-sm">
        <div className="flex items-center justify-between mb-3 gap-3">
          <h2 className="text-[14px] md:text-[15px] font-bold text-slate-900 uppercase tracking-wide">
            {metrics.loadedCount} of {metrics.totalCount} trips loaded
          </h2>
          <button
            type="button"
            onClick={loadQueue}
            disabled={loading}
            className="text-[12px] font-bold text-brand-700 flex items-center gap-1 disabled:opacity-50"
          >
            <RefreshCcw className="w-3.5 h-3.5" />
            {loading ? 'Refreshing' : 'Refresh'}
          </button>
        </div>
        <div className="h-2 w-full bg-slate-100 rounded-sm overflow-hidden">
          <div className="h-full bg-brand-500 rounded-sm transition-all duration-500" style={{ width: `${metrics.progressPercent}%` }} />
        </div>
        {error && <p className="mt-3 text-[12px] text-amber-700">{error}</p>}
      </div>

      <div className="space-y-3">
        <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1">Ready to Load</h3>
        {readyOrLoading.length > 0 ? readyOrLoading.map(renderTrip) : (
          <div className="border border-slate-200 rounded p-5 bg-white shadow-sm flex items-center justify-center py-10">
            <span className="text-slate-500 text-[14px] font-medium">No trips waiting for loading.</span>
          </div>
        )}
      </div>

      {loaded.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-[12px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1 mt-6">Loaded</h3>
          {loaded.map(renderTrip)}
        </div>
      )}

      {unavailable.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-[12px] font-bold text-slate-500 uppercase tracking-wider mb-2 ml-1 mt-6">Unavailable</h3>
          {unavailable.map(renderTrip)}
        </div>
      )}
    </div>
  );
}
