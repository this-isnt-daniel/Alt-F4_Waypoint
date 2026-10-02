import React, { useState } from 'react';
import { Phone, Flag, X, AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, Check } from 'lucide-react';

// ─── Test Data ─────────────────────────────────────────────────────────────────

const WORKBENCH_DATA_PELIYAGODA = {
  vehicle: { id: 'VEH011', type: 'Truck', refrigeration: 'Reefer', plate: 'WP-KA-4521' },
  driver: { name: 'K. Rathnayake', initials: 'KR', license: 'CDL · 8 years', gatePass: 'GP-0411 (Active)', phone: '+94 77 345 6789' },
  stops: [
    {
      id: 'stop-1',
      number: 1,
      outlet: 'Kandana Express',
      outletId: 'OUT-0122',
      deliveryOrder: 'Delivers last · Stop 3',
      weightKg: 530,
      volumeM3: 3.5,
      tempRequirement: 'Chilled',
      items: [
        { id: 'i1', name: 'Fresh Whole Milk 1L', sku: 'FRS-001', assigned: 20, loaded: 20, unit: 'crates' },
        { id: 'i2', name: 'Chilled Chicken Drumsticks', sku: 'FRS-014', assigned: 15, loaded: 15, unit: 'cartons' },
      ]
    },
    {
      id: 'stop-2',
      number: 2,
      outlet: 'Ja-Ela Central',
      outletId: 'OUT-0091',
      deliveryOrder: 'Delivers 2nd · Stop 2',
      weightKg: 1100,
      volumeM3: 4.5,
      tempRequirement: 'Chilled',
      items: [
        { id: 'i3', name: 'Fresh Pasteurised Milk 1L', sku: 'FRS-003', assigned: 40, loaded: 40, unit: 'crates' },
        { id: 'i4', name: 'Dairy Butter 200g', sku: 'FRS-022', assigned: 25, loaded: 25, unit: 'blocks' },
        { id: 'i5', name: "Women's Tops — Assorted", sku: 'STY-101', assigned: 6, loaded: 6, unit: 'cartons' },
        { id: 'i6', name: 'Casual Dresses — Mixed Sizes', sku: 'STY-108', assigned: 8, loaded: 8, unit: 'cartons' },
      ]
    },
    {
      id: 'stop-3',
      number: 3,
      outlet: 'Ragama Tech Mart',
      outletId: 'OUT-2041',
      deliveryOrder: 'Delivers 1st · Stop 1',
      weightKg: 820,
      volumeM3: 5.2,
      tempRequirement: 'Ambient',
      items: [
        { id: 'i7', name: 'Samsung Microwave 23L', sku: 'TEC-009', assigned: 4, loaded: 4, unit: 'units', handling: 'Fragile' },
        { id: 'i8', name: 'Refrigerator X300', sku: 'TEC-012', assigned: 2, loaded: 2, unit: 'units', handling: 'Fragile' },
        { id: 'i9', name: 'Laptop Accessories Kit', sku: 'TEC-031', assigned: 10, loaded: 10, unit: 'boxes' },
        { id: 'i10', name: 'Carrot (Fresh)', sku: 'FRS-044', assigned: 15, loaded: 15, unit: 'kg' },
      ]
    },
  ]
};

const WORKBENCH_DATA_KANDY = {
  vehicle: { id: 'VEH-K04', type: 'Truck', refrigeration: 'Ambient', plate: 'WP-KA-9912' },
  driver: { name: 'S. Bandara', initials: 'SB', license: 'CDL · 5 years', gatePass: 'GP-K882 (Active)', phone: '+94 77 999 8888' },
  stops: [
    {
      id: 'stop-k1',
      number: 1,
      outlet: 'Peradeniya Central',
      outletId: 'OUT-K011',
      deliveryOrder: 'Delivers last · Stop 2',
      weightKg: 420,
      volumeM3: 2.1,
      tempRequirement: 'Ambient',
      items: [
        { id: 'ki1', name: 'Premium Rice 5kg', sku: 'GRO-101', assigned: 50, loaded: 50, unit: 'bags' },
        { id: 'ki2', name: 'Lentils 1kg', sku: 'GRO-102', assigned: 100, loaded: 100, unit: 'packs' },
      ]
    },
    {
      id: 'stop-k2',
      number: 2,
      outlet: 'Kandy City Mart',
      outletId: 'OUT-K099',
      deliveryOrder: 'Delivers 1st · Stop 1',
      weightKg: 650,
      volumeM3: 3.2,
      tempRequirement: 'Ambient',
      items: [
        { id: 'ki3', name: 'Cooking Oil 1L', sku: 'GRO-105', assigned: 30, loaded: 30, unit: 'bottles' },
        { id: 'ki4', name: 'Tea Powder 500g', sku: 'GRO-108', assigned: 40, loaded: 40, unit: 'packs' },
      ]
    }
  ]
};

// ─── Main Component ─────────────────────────────────────────────────────────────

export default function LoaderWorkbench({ user, vehicleId, readOnly }) {
  const currentDepot = user?.depot || 'peliyagoda';
  const baseData = currentDepot === 'kandy' ? WORKBENCH_DATA_KANDY : WORKBENCH_DATA_PELIYAGODA;
  const WORKBENCH_DATA = { ...baseData, vehicle: { ...baseData.vehicle } };
  if (vehicleId) {
    WORKBENCH_DATA.vehicle.id = vehicleId;
  }

  const [vehicleAvailable, setVehicleAvailable] = useState(true);
  const [showDriverDetails, setShowDriverDetails] = useState(false);

  // Stop state: track which stop is expanded and each stop's completion status
  const allStops = new Set(WORKBENCH_DATA.stops.map(s => s.id));
  const initialExpanded = readOnly ? null : (currentDepot === 'kandy' ? 'stop-k2' : 'stop-2');
  const initialCompleted = readOnly ? allStops : (currentDepot === 'kandy' ? new Set(['stop-k1']) : new Set(['stop-1']));
  
  const [expandedStop, setExpandedStop] = useState(initialExpanded);
  const [completedStops, setCompletedStops] = useState(initialCompleted);

  // Item state per item: { loaded, discrepancy }
  const [itemState, setItemState] = useState(() => {
    const state = {};
    WORKBENCH_DATA.stops.forEach(stop => {
      stop.items.forEach(item => {
        state[item.id] = { loaded: readOnly ? item.assigned : item.loaded, discrepancy: null };
      });
    });
    // Pre-seed stop 1 as complete with a discrepancy (Peliyagoda only) if not read-only
    if (!readOnly) {
      if (currentDepot === 'peliyagoda') {
        state['i2'] = { loaded: 13, discrepancy: { type: 'Missing at dock', short: 2, description: '' } };
      } else {
        state['ki2'] = { loaded: 98, discrepancy: { type: 'Quantity error', short: 2, description: '' } };
      }
    }
    return state;
  });

  const [discrepancyModal, setDiscrepancyModal] = useState(null); // { itemId, stopId }
  const [attentionFilter, setAttentionFilter] = useState('all'); // per stop: 'all' | 'attention'

  // ── Derived helpers ──

  const getItemStatus = (item) => {
    const s = itemState[item.id];
    if (!s) return 'pending';
    if (s.discrepancy) return 'mismatch';
    if (s.loaded === item.assigned) return 'verified';
    if (s.loaded !== item.assigned && s.loaded !== item.assigned) return 'pending';
    return 'pending';
  };

  const getStopProgress = (stop) => {
    const total = stop.items.length;
    const done = stop.items.filter(item => {
      const st = getItemStatus(item);
      return st === 'verified' || st === 'mismatch';
    }).length;
    return { done, total };
  };

  const totalStops = WORKBENCH_DATA.stops.length;
  const completedCount = completedStops.size;
  const allDone = completedCount === totalStops;

  const handleCompleteStop = (stop) => {
    const nextCompletedStops = new Set(completedStops);
    nextCompletedStops.add(stop.id);
    setCompletedStops(nextCompletedStops);

    // Find next stop and expand it
    const idx = WORKBENCH_DATA.stops.findIndex(s => s.id === stop.id);
    const nextStop = WORKBENCH_DATA.stops[idx + 1];
    if (nextStop) {
      setExpandedStop(nextStop.id);
    } else {
      setExpandedStop(null);
    }
  };

  const handleSetLoaded = (itemId, val) => {
    setItemState(prev => ({ ...prev, [itemId]: { ...prev[itemId], loaded: val } }));
  };

  const handleSaveDiscrepancy = (itemId, discrepancy) => {
    setItemState(prev => ({ ...prev, [itemId]: { ...prev[itemId], discrepancy } }));
    setDiscrepancyModal(null);
  };

  if (!vehicleAvailable) {
    return <WorkbenchUnavailable onToggle={() => setVehicleAvailable(true)} />;
  }

  return (
    <div className="bg-[#F8FAF9] min-h-full pb-12 relative">
      <div className="p-4 md:p-6 space-y-4">

        {/* ── Vehicle / Driver Context ── */}
        <div className="bg-white border border-slate-200 rounded overflow-hidden">
          {/* Vehicle row */}
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div>
                <span className="text-[15px] font-bold text-slate-900">{WORKBENCH_DATA.vehicle.id}</span>
                <span className="ml-2 text-[13px] text-slate-500">{WORKBENCH_DATA.vehicle.type} · {WORKBENCH_DATA.vehicle.refrigeration}</span>
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 bg-slate-100 text-slate-500 rounded border border-slate-200 uppercase tracking-wide">
                {WORKBENCH_DATA.vehicle.plate}
              </span>
            </div>
            {/* Truck Available Toggle */}
            {!readOnly && (
              <div className="flex items-center gap-2">
                <span className="text-[12px] font-semibold text-slate-600 hidden sm:block">Available</span>
                <button
                  onClick={() => setVehicleAvailable(false)}
                  className="w-12 h-6 bg-brand-600 rounded-full relative transition-colors"
                  aria-label="Toggle vehicle availability"
                >
                  <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-all" />
                </button>
              </div>
            )}
          </div>

          {/* Driver row */}
          <button
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors text-left"
            onClick={() => setShowDriverDetails(true)}
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-brand-50 border border-brand-100 flex items-center justify-center text-[13px] font-bold text-brand-700 shrink-0">
                {WORKBENCH_DATA.driver.initials}
              </div>
              <div>
                <div className="text-[14px] font-bold text-slate-900">{WORKBENCH_DATA.driver.name}</div>
                <div className="text-[12px] text-slate-500">Driver · {WORKBENCH_DATA.driver.license}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Phone className="w-4 h-4 text-slate-400" />
              <ChevronRight className="w-4 h-4 text-slate-300" />
            </div>
          </button>
        </div>

        {/* ── Overall Progress ── */}
        <div className="flex items-center justify-between px-1">
          <span className="text-[12px] font-bold text-slate-500 uppercase tracking-wider">
            Packing Sequence
          </span>
          <span className="text-[12px] font-semibold text-slate-600">
            {completedCount} of {totalStops} stops complete
          </span>
        </div>
        <p className="text-[12px] text-slate-400 -mt-3 px-1">Pack from the back first, doors last</p>

        {/* ── Stops ── */}
        <div className="space-y-3">
          {WORKBENCH_DATA.stops.map((stop) => {
            const isComplete = completedStops.has(stop.id);
            const isActive = expandedStop === stop.id;
            const progress = getStopProgress(stop);

            if (isComplete && !isActive) {
              return (
                <CompletedStop
                  key={stop.id}
                  stop={stop}
                  progress={progress}
                  onClick={() => setExpandedStop(isActive ? null : stop.id)}
                />
              );
            }

            if (isActive) {
              return (
                <ActiveStop
                  key={stop.id}
                  stop={stop}
                  progress={progress}
                  itemState={itemState}
                  attentionFilter={attentionFilter}
                  setAttentionFilter={setAttentionFilter}
                  getItemStatus={getItemStatus}
                  onSetLoaded={handleSetLoaded}
                  onOpenDiscrepancy={(itemId) => setDiscrepancyModal({ itemId, stopId: stop.id })}
                  onComplete={() => handleCompleteStop(stop)}
                  readOnly={readOnly}
                  isComplete={isComplete}
                  onCollapse={() => setExpandedStop(null)}
                />
              );
            }

            // Waiting / future stop
            return (
              <FutureStop
                key={stop.id}
                stop={stop}
                onClick={() => setExpandedStop(stop.id)}
              />
            );
          })}
        </div>

        {/* ── All Complete ── */}
        {allDone && (
          <div className="bg-white border border-slate-200 rounded p-5 text-center space-y-3">
            <div className="w-10 h-10 rounded-full bg-brand-100 text-brand-600 flex items-center justify-center mx-auto">
              <Check className="w-6 h-6" strokeWidth={2.5} />
            </div>
            <div>
              <h3 className="text-[16px] font-bold text-slate-900">Loading Complete</h3>
              <p className="text-[13px] text-slate-500 mt-0.5">
                {totalStops} of {totalStops} stops · All items verified
              </p>
              {Object.values(itemState).some(s => s.discrepancy) && (
                <p className="text-[12px] font-semibold text-amber-600 mt-1">
                  {Object.values(itemState).filter(s => s.discrepancy).length} discrepancy recorded
                </p>
              )}
            </div>
            {readOnly ? (
              <button disabled className="w-full py-2.5 bg-slate-100 text-slate-500 text-[14px] font-semibold rounded cursor-not-allowed border border-slate-200">
                Vehicle Deployed
              </button>
            ) : (
              <button className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-[14px] font-semibold rounded transition-colors">
                Ready for Deployment
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── Discrepancy Modal ── */}
      {discrepancyModal && (() => {
        const stop = WORKBENCH_DATA.stops.find(s => s.id === discrepancyModal.stopId);
        const item = stop?.items.find(i => i.id === discrepancyModal.itemId);
        if (!item) return null;
        return (
          <DiscrepancyModal
            item={item}
            itemState={itemState[item.id]}
            onClose={() => setDiscrepancyModal(null)}
            onSave={(disc) => handleSaveDiscrepancy(item.id, disc)}
          />
        );
      })()}

      {/* ── Driver Details Sheet ── */}
      {showDriverDetails && (
        <DriverDetailsSheet
          driver={WORKBENCH_DATA.driver}
          vehicle={WORKBENCH_DATA.vehicle}
          onClose={() => setShowDriverDetails(false)}
        />
      )}
    </div>
  );
}

// ─── Completed Stop ─────────────────────────────────────────────────────────────

function CompletedStop({ stop, progress, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full bg-[#F4FAF6] border border-[#DCF0E5] rounded px-4 py-3 flex items-center justify-between text-left hover:bg-[#EBF6F0] transition-colors"
    >
      <div className="flex items-center gap-3">
        <div className="w-6 h-6 rounded-full bg-brand-600 text-white flex items-center justify-center shrink-0">
          <Check className="w-3.5 h-3.5" strokeWidth={3} />
        </div>
        <div>
          <span className="text-[14px] font-bold text-slate-900">{stop.number}. {stop.outlet}</span>
          <span className="ml-2 text-[12px] text-slate-500">{stop.outletId}</span>
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-[12px] text-slate-500">{progress.total} items · {stop.weightKg} kg</span>
        <span className="text-[11px] font-bold text-brand-700 bg-brand-50 border border-brand-100 px-2 py-0.5 rounded">Complete</span>
      </div>
    </button>
  );
}

// ─── Future Stop ────────────────────────────────────────────────────────────────

function FutureStop({ stop, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full bg-white border border-slate-200 rounded px-4 py-3 flex items-center justify-between text-left hover:bg-slate-50 transition-colors"
    >
      <div className="flex items-center gap-3">
        <div className="w-6 h-6 rounded-full border-2 border-slate-300 flex items-center justify-center shrink-0 text-[11px] font-bold text-slate-400">
          {stop.number}
        </div>
        <div>
          <span className="text-[14px] font-semibold text-slate-700">{stop.outlet}</span>
          <span className="ml-2 text-[12px] text-slate-400">{stop.outletId}</span>
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-[12px] text-slate-400">{stop.items.length} items</span>
        <span className="text-[11px] font-medium text-slate-400 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">Waiting</span>
        <ChevronDown className="w-4 h-4 text-slate-300" />
      </div>
    </button>
  );
}

// ─── Active Stop ─────────────────────────────────────────────────────────────────

function ActiveStop({ stop, progress, itemState, attentionFilter, setAttentionFilter, getItemStatus, onSetLoaded, onOpenDiscrepancy, onComplete, readOnly, isComplete, onCollapse }) {
  const hasDiscrepancies = stop.items.some(item => itemState[item.id]?.discrepancy);
  const unresolved = stop.items.filter(item => {
    const st = getItemStatus(item);
    return st !== 'verified' && st !== 'mismatch';
  }).length;
  const canComplete = unresolved === 0;

  const filteredItems = attentionFilter === 'attention'
    ? stop.items.filter(item => {
        const st = getItemStatus(item);
        return st === 'mismatch' || (itemState[item.id]?.loaded !== item.assigned);
      })
    : stop.items;

  return (
    <div className="bg-white border-2 border-brand-500 rounded overflow-hidden shadow-sm">
      {/* Stop Header */}
      <div className="px-4 pt-4 pb-3 border-b border-slate-100">
        <div className="flex items-start justify-between mb-1.5">
          <div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-brand-600 text-white flex items-center justify-center text-[11px] font-bold shrink-0">
                {isComplete ? <Check className="w-3.5 h-3.5" strokeWidth={3} /> : stop.number}
              </div>
              <h3 className="text-[15px] font-bold text-slate-900">{stop.outlet}</h3>
              <span className="text-[12px] text-slate-400">{stop.outletId}</span>
            </div>
            <p className="text-[12px] text-slate-500 mt-1 ml-8">{stop.deliveryOrder}</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {isComplete ? (
              <span className="text-[11px] font-bold text-brand-700 bg-brand-50 border border-brand-100 px-2 py-0.5 rounded shrink-0">Complete</span>
            ) : (
              <span className="text-[11px] font-bold text-brand-700 bg-brand-50 border border-brand-100 px-2 py-0.5 rounded shrink-0">Active</span>
            )}
            <button onClick={onCollapse} className="p-1 hover:bg-slate-100 rounded text-slate-400">
              <ChevronDown className="w-4 h-4 rotate-180" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3 ml-8">
          <span className="text-[13px] font-bold text-slate-700">{stop.weightKg.toLocaleString()} kg · {stop.volumeM3} m³</span>
          <TempBadge temp={stop.tempRequirement} />
        </div>

        <div className="flex items-center justify-between mt-3 ml-8">
          <span className="text-[12px] font-semibold text-slate-600">
            {progress.done} of {progress.total} items verified
          </span>
          {/* Attention filter */}
          <div className="flex rounded-md overflow-hidden border border-slate-200 text-[11px] font-bold">
            <button
              onClick={() => setAttentionFilter('all')}
              className={`px-2.5 py-1 transition-colors ${attentionFilter === 'all' ? 'bg-slate-800 text-white' : 'bg-white text-slate-500 hover:bg-slate-50'}`}
            >
              All
            </button>
            <button
              onClick={() => setAttentionFilter('attention')}
              className={`px-2.5 py-1 transition-colors border-l border-slate-200 ${attentionFilter === 'attention' ? 'bg-amber-500 text-white' : 'bg-white text-slate-500 hover:bg-slate-50'}`}
            >
              Needs attention
            </button>
          </div>
        </div>
      </div>

      {/* Item Table Header */}
      <div className="px-4 py-2 bg-slate-50 border-b border-slate-100 grid grid-cols-[1fr_130px_120px_90px] gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
        <div>Product</div>
        <div className="text-right">Assigned</div>
        <div className="text-right">Loaded</div>
        <div className="text-right">Status</div>
      </div>

      {/* Item Rows */}
      <div className="divide-y divide-slate-100">
        {filteredItems.map(item => (
          <ItemVerificationRow
            key={item.id}
            item={item}
            state={itemState[item.id]}
            status={getItemStatus(item)}
            onSetLoaded={(val) => onSetLoaded(item.id, val)}
            onOpenDiscrepancy={() => onOpenDiscrepancy(item.id)}
            readOnly={readOnly}
          />
        ))}
        {filteredItems.length === 0 && (
          <div className="px-4 py-6 text-center text-[13px] text-slate-400">No items need attention.</div>
        )}
      </div>

      {/* Complete Stop Footer */}
      {!readOnly && (
        <div className="px-4 py-3 bg-slate-50 border-t border-slate-100">
          {hasDiscrepancies && (
            <p className="text-[12px] font-semibold text-amber-600 mb-2">
              {stop.items.filter(i => itemState[i.id]?.discrepancy).length} discrepancy recorded
            </p>
          )}
          {!canComplete && (
            <p className="text-[12px] text-slate-500 mb-2">{unresolved} item{unresolved !== 1 ? 's' : ''} still need checking</p>
          )}
          <button
            onClick={() => canComplete && onComplete()}
            disabled={!canComplete}
            className={`w-full py-2.5 text-[14px] font-semibold rounded transition-colors ${
              canComplete
                ? 'bg-brand-600 hover:bg-brand-700 text-white'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
            }`}
          >
            Complete loading
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Item Verification Row ────────────────────────────────────────────────────────

function ItemVerificationRow({ item, state, status, onSetLoaded, onOpenDiscrepancy, readOnly }) {
  const loaded = state?.loaded ?? item.assigned;
  const discrepancy = state?.discrepancy;

  return (
    <div className={`px-4 py-3 ${discrepancy ? 'bg-amber-50' : ''}`}>
      <div className="grid grid-cols-[1fr_130px_120px_90px] gap-2 items-start">
        {/* Product */}
        <div className="min-w-0">
          <div className="text-[13px] font-semibold text-slate-900 leading-tight break-words">{item.name}</div>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            <span className="text-[10px] text-slate-400">{item.sku}</span>
            {item.handling && (
              <span className="text-[10px] font-semibold text-amber-600 uppercase tracking-wide">{item.handling}</span>
            )}
          </div>
          {discrepancy && (
            <div className="mt-1.5 text-[11px] text-amber-700 font-semibold flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 shrink-0" />
              <span>Short by {item.assigned - loaded} · {discrepancy.type}</span>
            </div>
          )}
        </div>

        {/* Assigned */}
        <div className="text-right text-[13px] text-slate-700 font-medium pt-0.5 whitespace-nowrap">
          {item.assigned} {item.unit}
        </div>

        {/* Loaded — inline input */}
        <div className="flex items-center justify-end gap-1.5 pt-0.5">
          <input
            type="number"
            min={0}
            max={item.assigned + 10}
            step={item.unit === 'kg' ? 0.5 : 1}
            value={loaded}
            disabled={readOnly}
            onChange={(e) => onSetLoaded(Number(e.target.value))}
            className={`w-16 text-right text-[13px] font-semibold border rounded px-2 py-0.5 focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500 ${readOnly ? 'bg-transparent border-transparent text-slate-600' : 'border-slate-200 bg-white'}`}
          />
          <span className="text-[11px] text-slate-500 shrink-0 whitespace-nowrap">{item.unit}</span>
        </div>

        {/* Status */}
        <div className="flex items-center justify-end pt-0.5">
          {status === 'verified' && (
            <span className="text-[11px] font-bold text-brand-700 bg-brand-50 border border-brand-100 px-2 py-0.5 rounded whitespace-nowrap flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 shrink-0" /> Verified
            </span>
          )}
          {status === 'mismatch' && (
            <button
              onClick={onOpenDiscrepancy}
              className="text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded whitespace-nowrap flex items-center gap-1 hover:bg-amber-100 transition-colors"
            >
              <AlertTriangle className="w-3 h-3 shrink-0" /> Mismatch
            </button>
          )}
          {status === 'pending' && loaded === item.assigned && (
            <span className="text-[11px] text-slate-300">—</span>
          )}
          {status !== 'verified' && status !== 'mismatch' && loaded !== item.assigned && !readOnly && (
            <button
              onClick={onOpenDiscrepancy}
              className="text-[11px] font-bold text-slate-400 hover:text-amber-600 flex items-center gap-1 transition-colors"
              title="Report discrepancy"
            >
              <Flag className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Temperature Badge ────────────────────────────────────────────────────────────

function TempBadge({ temp }) {
  const styles = {
    Chilled: 'bg-blue-50 text-blue-700 border-blue-100',
    Frozen: 'bg-cyan-50 text-cyan-700 border-cyan-100',
    Ambient: 'bg-slate-100 text-slate-600 border-slate-200',
  };
  return (
    <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${styles[temp] ?? styles.Ambient}`}>
      {temp}
    </span>
  );
}

// ─── Discrepancy Modal ─────────────────────────────────────────────────────────────

function DiscrepancyModal({ item, itemState, onClose, onSave }) {
  const loaded = itemState?.loaded ?? item.assigned;
  const short = item.assigned - loaded;
  const [type, setType] = useState(itemState?.discrepancy?.type ?? 'Missing at dock');
  const [description, setDescription] = useState(itemState?.discrepancy?.description ?? '');

  const REASON_OPTIONS = ['Missing at dock', 'Damaged at staging', 'Wrong product', 'Quantity error'];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 p-4 sm:p-6">
      <div className="bg-white rounded w-full max-w-md border border-slate-200 flex flex-col max-h-full overflow-hidden shadow-xl">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between shrink-0">
          <div>
            <h2 className="text-[13px] font-bold text-slate-900 uppercase tracking-wide">Report Discrepancy</h2>
            <p className="text-[12px] text-slate-500 mt-0.5">{item.name} &middot; {item.sku}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors ml-4 shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5 overflow-y-auto min-h-0">

          {/* Quantity summary — plain aligned rows */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-[13px]">
              <span className="text-slate-500">Assigned</span>
              <span className="font-semibold text-slate-900">{item.assigned} {item.unit}</span>
            </div>
            <div className="flex justify-between text-[13px]">
              <span className="text-slate-500">Loaded</span>
              <span className="font-semibold text-slate-900">{loaded} {item.unit}</span>
            </div>
            <div className="border-t border-slate-100 pt-1.5 flex justify-between text-[13px]">
              <span className="font-semibold text-amber-700">Short by</span>
              <span className="font-bold text-amber-700">{short} {item.unit}</span>
            </div>
          </div>

          {/* Discrepancy type — radio-style list */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Discrepancy Type</label>
            <div className="space-y-0.5">
              {REASON_OPTIONS.map(opt => {
                const isSelected = type === opt;
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setType(opt)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded text-left transition-colors text-[13px] ${
                      isSelected ? 'bg-brand-50 text-slate-900' : 'text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <span className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center shrink-0 ${
                      isSelected ? 'border-brand-600' : 'border-slate-300'
                    }`}>
                      {isSelected && <span className="w-2 h-2 rounded-full bg-brand-600 block" />}
                    </span>
                    {opt}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Description <span className="font-normal normal-case text-slate-400">(optional)</span></label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={2}
              placeholder="e.g. Cartons found crushed at Bay 3"
              className="w-full text-[13px] text-slate-900 border border-slate-200 rounded px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500 resize-none placeholder:text-slate-300"
            />
          </div>
        </div>

        <div className="px-5 py-3 bg-slate-50 border-t border-slate-200 flex gap-2 shrink-0">
          <button
            onClick={onClose}
            className="flex-1 py-2 text-[13px] font-semibold text-slate-600 hover:bg-slate-100 rounded border border-slate-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave({ type, short, description })}
            className="flex-[2] py-2 text-[13px] font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded transition-colors"
          >
            Record Discrepancy
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Driver Details Sheet ─────────────────────────────────────────────────────────

function DriverDetailsSheet({ driver, vehicle, onClose }) {
  return (
    <div className="absolute inset-0 z-40 bg-slate-900/40 flex items-end">
      <div className="bg-white w-full rounded-t-2xl p-5 shadow-xl max-h-[70vh] overflow-y-auto">
        <div className="w-10 h-1 bg-slate-200 rounded-full mx-auto mb-5" />
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[16px] font-bold text-slate-900">Driver & Vehicle</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center gap-3 mb-5">
          <div className="w-11 h-11 rounded-full bg-brand-50 border border-brand-100 flex items-center justify-center text-[15px] font-bold text-brand-700">
            {driver.initials}
          </div>
          <div>
            <div className="text-[15px] font-bold text-slate-900">{driver.name}</div>
            <div className="text-[12px] text-slate-500">{driver.license}</div>
          </div>
        </div>

        <div className="space-y-2 text-[13px] text-slate-700 border border-slate-200 rounded divide-y divide-slate-100 mb-5">
          <div className="px-3 py-2.5 flex justify-between">
            <span className="text-slate-500">Vehicle</span>
            <span className="font-semibold">{vehicle.id} · {vehicle.type} · {vehicle.refrigeration}</span>
          </div>
          <div className="px-3 py-2.5 flex justify-between">
            <span className="text-slate-500">Plate</span>
            <span className="font-semibold">{vehicle.plate}</span>
          </div>
          <div className="px-3 py-2.5 flex justify-between">
            <span className="text-slate-500">Gate Pass</span>
            <span className="font-semibold">{driver.gatePass}</span>
          </div>
          <div className="px-3 py-2.5 flex justify-between">
            <span className="text-slate-500">Phone</span>
            <a href={`tel:${driver.phone}`} className="font-semibold text-brand-600">{driver.phone}</a>
          </div>
        </div>

        <div className="flex gap-3">
          <a
            href={`tel:${driver.phone}`}
            className="flex-1 py-2.5 text-[13px] font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded transition-colors flex items-center justify-center gap-2"
          >
            <Phone className="w-4 h-4" /> Call Driver
          </a>
          <button
            onClick={onClose}
            className="flex-1 py-2.5 text-[13px] font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Workbench Unavailable ────────────────────────────────────────────────────────

function WorkbenchUnavailable({ onToggle }) {
  const [reason, setReason] = useState('Engine Fault');

  return (
    <div className="bg-[#F8FAF9] min-h-full pb-12">
      <div className="max-w-3xl mx-auto p-4 md:p-6 space-y-4">

        {/* Toggle Card */}
        <div className="bg-white border border-slate-200 rounded px-4 py-3 flex items-center justify-between">
          <div>
            <span className="text-[14px] font-bold text-slate-900">Truck Available for Loading</span>
            <p className="text-[12px] text-red-500 font-semibold mt-0.5">Vehicle marked unavailable</p>
          </div>
          <button
            onClick={onToggle}
            className="w-12 h-6 bg-slate-200 rounded-full relative transition-colors border border-slate-200"
            aria-label="Mark vehicle as available"
          >
            <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-all" />
          </button>
        </div>

        {/* Alert Box */}
        <div className="bg-white border border-red-200 rounded overflow-hidden">
          <div className="px-4 py-3 border-b border-red-100 bg-red-50 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
            <span className="text-[13px] font-bold text-red-700 uppercase tracking-wide">Vehicle Out of Service — Dispatch Alerted</span>
          </div>
          <div className="px-4 py-4 space-y-4">
            <div>
              <label className="block text-[12px] font-semibold text-slate-700 mb-1.5">Reason</label>
              <select
                value={reason}
                onChange={e => setReason(e.target.value)}
                className="w-full border border-slate-200 rounded py-2 px-3 text-[13px] font-medium text-slate-900 bg-white focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500"
              >
                <option>Engine Fault</option>
                <option>Flat Tire</option>
                <option>Accident</option>
                <option>Reefer Failure</option>
                <option>Other</option>
              </select>
            </div>

            <p className="text-[13px] text-slate-600">
              Staging Status: <span className="font-bold text-slate-900">3 Orders (2,450 kg)</span> held at Bay 4. Awaiting dispatcher vehicle swap.
            </p>

            <div className="flex gap-2">
              <button className="flex-1 py-2 text-[13px] font-semibold text-slate-700 border border-slate-200 rounded hover:bg-slate-50 transition-colors">
                Update Dispatcher Note
              </button>
              <button
                onClick={onToggle}
                className="flex-1 py-2 text-[13px] font-semibold text-slate-700 border border-slate-200 rounded hover:bg-slate-50 transition-colors"
              >
                Cancel & Mark Available
              </button>
            </div>
          </div>
        </div>

        {/* Staged Cargo */}
        <div>
          <h4 className="text-[11px] font-bold text-slate-400 tracking-wider mb-2 uppercase">Staged Cargo — Awaiting Vehicle Swap</h4>
          <div className="space-y-2">
            {[
              { id: 'OUT-0122', name: 'Kandana Express', kg: 530, note: 'Pallet 1 staged at Bay' },
              { id: 'OUT-0091', name: 'Ja-Ela Central', kg: 1100, note: 'Pallet 2 staged at Bay' },
              { id: 'OUT-2041', name: 'Wattala Retail', kg: 820, note: 'Pallet 3 staged at Bay' },
            ].map(c => (
              <div key={c.id} className="bg-white border border-slate-200 rounded px-4 py-3 flex items-center justify-between">
                <div>
                  <span className="text-[13px] font-bold text-slate-900">{c.id}</span>
                  <span className="ml-1.5 text-[13px] text-slate-600">{c.name}</span>
                </div>
                <div className="text-right">
                  <div className="text-[13px] font-semibold text-slate-700">{c.kg} kg</div>
                  <div className="text-[11px] text-slate-400">{c.note}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
