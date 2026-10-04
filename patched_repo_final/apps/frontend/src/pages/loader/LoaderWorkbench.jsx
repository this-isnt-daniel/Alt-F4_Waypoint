import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Check, CheckCircle2, RefreshCcw, Truck } from 'lucide-react';
import {
  completeStop,
  fetchLoaderWorkbench,
  markVehicleUnavailable,
  saveLoadItem,
  startLoading,
  submitLoad,
} from './loaderApi';

function clientOp(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function normalizeStatus(loaded, expected, reason) {
  if (reason && loaded === expected) return 'damaged';
  if (loaded === expected) return 'verified';
  if (loaded === 0) return 'missing';
  if (loaded < expected) return 'short';
  return 'over';
}

function reasonFor(status, item) {
  if (status === 'verified') return undefined;
  if (item.discrepancy_reason) return item.discrepancy_reason;
  if (status === 'short') return 'Short at loading';
  if (status === 'missing') return 'Missing at loading';
  if (status === 'over') return 'Extra loaded';
  return 'Damaged at loading';
}

export default function LoaderWorkbench({ user, tripId, readOnly }) {
  const [workbench, setWorkbench] = useState(null);
  const [itemState, setItemState] = useState({});
  const [expandedStop, setExpandedStop] = useState(null);
  const [loading, setLoading] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const loadWorkbench = async () => {
    setLoading(true);
    setError('');
    setMessage('');
    try {
      if (!user?.token || !tripId) throw new Error("Missing auth token or tripId");
      const data = await fetchLoaderWorkbench(user.token, tripId);
      setWorkbench(data);
      const state = {};
      data.stops.forEach((stop) => {
        stop.items.forEach((item) => {
          state[item.line_item_id] = {
            loaded_qty: item.loaded_qty ?? item.assigned_qty,
            discrepancy_reason: item.discrepancy_reason || '',
            status: item.status || 'pending',
          };
        });
      });
      setItemState(state);
      const firstOpen = data.stops.find((stop) => !stop.complete) || data.stops[0];
      setExpandedStop(firstOpen?.stop_id || null);
    } catch (err) {
      setError(err.message);
      setWorkbench(null);
      setExpandedStop(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkbench();
  }, [tripId, user?.token]);

  const readOnlyTrip = readOnly || workbench?.read_only;
  const totals = useMemo(() => {
    if (!workbench) return { done: 0, total: 0, issues: 0 };
    let done = 0;
    let total = 0;
    let issues = 0;
    workbench.stops.forEach((stop) => {
      stop.items.forEach((item) => {
        const state = itemState[item.line_item_id];
        const status = state?.status || item.status;
        total += 1;
        if (status !== 'pending') done += 1;
        if (['short', 'over', 'damaged', 'missing', 'substituted'].includes(status)) issues += 1;
      });
    });
    return { done, total, issues };
  }, [workbench, itemState]);

  const updateItem = (lineItemId, patch) => {
    setItemState((prev) => ({
      ...prev,
      [lineItemId]: { ...prev[lineItemId], ...patch },
    }));
  };

  const saveItem = async (item) => {
    if (!workbench || readOnlyTrip) return;
    const state = itemState[item.line_item_id];
    const loaded = Number(state?.loaded_qty ?? item.assigned_qty);
    const status = normalizeStatus(loaded, item.assigned_qty, state?.discrepancy_reason);
    const discrepancyReason = reasonFor(status, { ...item, discrepancy_reason: state?.discrepancy_reason });
    setSavingId(item.line_item_id);
    setError('');
    try {
      const saved = await saveLoadItem(user.token, workbench.trip_id, item.line_item_id, {
        client_op_id: clientOp('save-load-item'),
        loaded_qty: loaded,
        status,
        ...(discrepancyReason ? { discrepancy_reason: discrepancyReason } : {}),
      });
      updateItem(item.line_item_id, {
        loaded_qty: saved.loaded_qty ?? loaded,
        status: saved.status,
        discrepancy_reason: saved.discrepancy_reason || '',
      });
      setMessage('Item saved');
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingId(null);
    }
  };

  const handleStart = async () => {
    if (!workbench || readOnlyTrip || !user?.token) return;
    setError('');
    try {
      await startLoading(user.token, workbench.trip_id);
      setMessage('Loading started');
      await loadWorkbench();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCompleteStop = async (stop) => {
    if (!workbench || readOnlyTrip || !user?.token) return;
    setError('');
    try {
      await completeStop(user.token, workbench.trip_id, stop.stop_id);
      setMessage('Stop completed');
      await loadWorkbench();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleFinalSubmit = async () => {
    if (!workbench || readOnlyTrip || !user?.token) return;
    const items = workbench.stops.flatMap((stop) => stop.items.map((item) => {
      const state = itemState[item.line_item_id] || {};
      const loaded = Number(state.loaded_qty ?? item.assigned_qty);
      const status = normalizeStatus(loaded, item.assigned_qty, state.discrepancy_reason);
      const discrepancyReason = reasonFor(status, { ...item, discrepancy_reason: state.discrepancy_reason });
      return {
        line_item_id: item.line_item_id,
        loaded_qty: loaded,
        status,
        ...(discrepancyReason ? { discrepancy_reason: discrepancyReason } : {}),
      };
    }));
    setError('');
    try {
      await submitLoad(user.token, workbench.trip_id, {
        client_op_id: clientOp('submit-load'),
        items,
      });
      setMessage('Trip loaded and ready for driver departure');
      await loadWorkbench();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleVehicleUnavailable = async () => {
    if (!workbench || readOnlyTrip || !user?.token) return;
    setError('');
    try {
      await markVehicleUnavailable(user.token, workbench.trip_id, {
        client_op_id: clientOp('vehicle-unavailable'),
        reason: 'Loader marked vehicle unavailable',
      });
      setMessage('Vehicle unavailable reported to dispatcher');
      await loadWorkbench();
    } catch (err) {
      setError(err.message);
    }
  };

  if (!workbench) {
    return (
      <div className="p-6 text-sm text-slate-500">
        {loading ? 'Loading workbench...' : 'Open a trip from the queue to start loading.'}
      </div>
    );
  }

  return (
    <div className="bg-[#F8FAF9] min-h-full pb-12">
      <div className="p-4 md:p-6 space-y-4">
        <div className="bg-white border border-slate-200 rounded p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Truck className="w-4 h-4 text-brand-700" />
              <h2 className="text-[16px] font-bold text-slate-900">{workbench.vehicle_id}</h2>
              <span className="text-[12px] text-slate-500">{workbench.vehicle_plate || 'No plate'}</span>
            </div>
            <p className="text-[13px] text-slate-600">
              {workbench.vehicle_type || 'Vehicle'} - {workbench.vehicle_temp || 'temp n/a'} - Trip {workbench.trip_no}
            </p>
            <p className="text-[12px] text-slate-500 mt-1 capitalize">
              Status: {workbench.status?.replaceAll('_', ' ')} - {totals.done}/{totals.total} items checked
              {totals.issues > 0 ? ` - ${totals.issues} discrepancy(s)` : ''}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={loadWorkbench} className="px-3 py-2 border border-slate-200 rounded text-[13px] font-semibold text-slate-700 flex items-center gap-1">
              <RefreshCcw className="w-3.5 h-3.5" /> Refresh
            </button>
            {!readOnlyTrip && workbench.status === 'planned' && (
              <button onClick={handleStart} className="px-3 py-2 bg-brand-600 text-white rounded text-[13px] font-semibold">
                Start loading
              </button>
            )}
            {!readOnlyTrip && (
              <button onClick={handleVehicleUnavailable} className="px-3 py-2 border border-red-200 text-red-700 rounded text-[13px] font-semibold bg-red-50">
                Vehicle unavailable
              </button>
            )}
          </div>
        </div>

        {error && <div className="border border-red-200 bg-red-50 text-red-700 rounded px-4 py-3 text-[13px]">{error}</div>}
        {message && <div className="border border-brand-100 bg-brand-50 text-brand-800 rounded px-4 py-3 text-[13px]">{message}</div>}

        <div className="space-y-3">
          {workbench.stops.map((stop) => {
            const open = expandedStop === stop.stop_id;
            const checked = stop.items.filter((item) => (itemState[item.line_item_id]?.status || item.status) !== 'pending').length;
            const canComplete = checked === stop.items.length;
            return (
              <div key={stop.stop_id} className="bg-white border border-slate-200 rounded overflow-hidden">
                <button
                  onClick={() => setExpandedStop(open ? null : stop.stop_id)}
                  className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-50"
                >
                  <div>
                    <div className="text-[14px] font-bold text-slate-900">
                      {stop.stop_seq}. {stop.outlet_name || stop.outlet_id}
                    </div>
                    <div className="text-[12px] text-slate-500">
                      {stop.order_id} - {stop.items.length} items - {checked}/{stop.items.length} checked
                    </div>
                  </div>
                  <span className={`text-[11px] font-bold px-2 py-1 rounded ${stop.complete ? 'bg-brand-50 text-brand-700' : 'bg-slate-100 text-slate-600'}`}>
                    {stop.complete ? 'Complete' : open ? 'Open' : 'Waiting'}
                  </span>
                </button>

                {open && (
                  <div className="border-t border-slate-100">
                    <div className="hidden md:grid grid-cols-[1fr_110px_170px_160px_90px] gap-2 px-4 py-2 bg-slate-50 text-[10px] font-bold uppercase text-slate-400">
                      <div>Product</div>
                      <div className="text-right">Assigned</div>
                      <div>Loaded</div>
                      <div>Reason</div>
                      <div className="text-right">Action</div>
                    </div>
                    {stop.items.map((item) => {
                      const state = itemState[item.line_item_id] || {};
                      const loaded = Number(state.loaded_qty ?? item.assigned_qty);
                      const status = state.status || item.status || 'pending';
                      const mismatch = status !== 'pending' && status !== 'verified';
                      return (
                        <div key={item.line_item_id} className={`px-4 py-3 border-t border-slate-100 grid md:grid-cols-[1fr_110px_170px_160px_90px] gap-2 md:items-center ${mismatch ? 'bg-amber-50' : ''}`}>
                          <div>
                            <div className="text-[13px] font-semibold text-slate-900">{item.product_name || item.product_id}</div>
                            <div className="text-[10px] text-slate-400">{item.product_id} - {item.line_item_id}</div>
                          </div>
                          <div className="md:text-right text-[13px] text-slate-700 font-medium">
                            {item.assigned_qty} {item.unit || 'units'}
                          </div>
                          <div className="flex items-center gap-2">
                            <input
                              type="number"
                              min={0}
                              value={loaded}
                              disabled={readOnlyTrip}
                              onChange={(event) => updateItem(item.line_item_id, { loaded_qty: Number(event.target.value), status: 'pending' })}
                              className="w-20 border border-slate-200 rounded px-2 py-1 text-[13px] font-semibold"
                            />
                            <span className="text-[11px] text-slate-500">{item.unit || 'units'}</span>
                            {status === 'verified' && <CheckCircle2 className="w-4 h-4 text-brand-600" />}
                            {mismatch && <AlertTriangle className="w-4 h-4 text-amber-600" />}
                          </div>
                          <input
                            type="text"
                            value={state.discrepancy_reason || ''}
                            disabled={readOnlyTrip}
                            onChange={(event) => updateItem(item.line_item_id, { discrepancy_reason: event.target.value, status: 'pending' })}
                            placeholder="Reason if mismatch"
                            className="border border-slate-200 rounded px-2 py-1 text-[12px]"
                          />
                          <div className="md:text-right">
                            <button
                              type="button"
                              disabled={readOnlyTrip || savingId === item.line_item_id}
                              onClick={() => saveItem(item)}
                              className="px-3 py-1.5 bg-brand-600 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded text-[12px] font-semibold"
                            >
                              {savingId === item.line_item_id ? 'Saving' : 'Save'}
                            </button>
                          </div>
                        </div>
                      );
                    })}
                    {!readOnlyTrip && (
                      <div className="px-4 py-3 bg-slate-50 border-t border-slate-100 flex justify-end">
                        <button
                          onClick={() => handleCompleteStop(stop)}
                          disabled={!canComplete}
                          className="px-4 py-2 bg-brand-600 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded text-[13px] font-semibold"
                        >
                          Complete stop
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {!readOnlyTrip && (
          <div className="bg-white border border-slate-200 rounded p-4 text-center">
            <button
              onClick={handleFinalSubmit}
              disabled={totals.done !== totals.total}
              className="w-full py-2.5 bg-brand-600 disabled:bg-slate-200 disabled:text-slate-400 text-white text-[14px] font-semibold rounded flex items-center justify-center gap-2"
            >
              <Check className="w-4 h-4" />
              Final submit load check
            </button>
            {totals.done !== totals.total && (
              <p className="mt-2 text-[12px] text-slate-500">Save every item before final submit.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
