import React, { useState, useCallback } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import {
  Moon,
  ChevronDown,
  Bell,
  ArrowLeft,
  Check,
  Truck,
  Snowflake,
  Wind,
  X,
  AlertTriangle,
  Wand2,
} from 'lucide-react';

// ─── Colour tokens ────────────────────────────────────────────────────────────
const C = {
  primary:       '#059669',
  primaryHover:  '#047857',
  primaryActive: '#065F46',
  darkest:       '#0B2019',
  dark:          '#256149',
  surface:       '#EBF6F0',
  border:        '#DCF0E5',
};

// ─── Order tag colour palette ─────────────────────────────────────────────────
const ORDER_COLOURS = [
  { bg: '#EDE9FE', text: '#5B21B6', border: '#C4B5FD' },
  { bg: '#FEF3C7', text: '#92400E', border: '#FDE68A' },
  { bg: '#FCE7F3', text: '#9D174D', border: '#F9A8D4' },
  { bg: '#DBEAFE', text: '#1E40AF', border: '#BFDBFE' },
  { bg: '#D1FAE5', text: '#065F46', border: '#6EE7B7' },
  { bg: '#FEE2E2', text: '#991B1B', border: '#FECACA' },
  { bg: '#E0F2FE', text: '#0C4A6E', border: '#BAE6FD' },
  { bg: '#FDF4FF', text: '#6B21A8', border: '#E9D5FF' },
];

const orderColour = (orderId) => {
  let hash = 0;
  for (let i = 0; i < orderId.length; i++) hash = (hash * 31 + orderId.charCodeAt(i)) >>> 0;
  return ORDER_COLOURS[hash % ORDER_COLOURS.length];
};

// ─── Initial data ─────────────────────────────────────────────────────────────
const buildInitialRows = () => [
  {
    vehicleId: 'VEH014', tripLabel: 'Trip 1 of 2', refrigeration: 'Reefer',
    capacityKg: 4500, capacityM3: 12.0, fuelPct: 54,
    cards: [
      { id: 'c1', orderId: 'ORD-4471', stop: 1, stopName: 'Nugegoda',   product: 'Fresh Strawberries Grade A 250g', qty: '120 punnets', weightKg: 30,  brand: 'Waypoint Fresh', refrigeration: 'Reefer' },
      { id: 'c2', orderId: 'ORD-4471', stop: 1, stopName: 'Nugegoda',   product: 'Fresh Whipping Cream 250ml',      qty: '100 units',   weightKg: 28,  brand: 'Waypoint Fresh', refrigeration: 'Reefer' },
      { id: 'c3', orderId: 'ORD-3390', stop: 2, stopName: 'Maharagama', product: 'Highland Drinking Yogurt 200ml', qty: '96 bottles',  weightKg: 22,  brand: 'Waypoint Fresh', refrigeration: 'Reefer' },
      { id: 'c4', orderId: 'ORD-3390', stop: 2, stopName: 'Maharagama', product: 'Chicken Drumsticks Marinated',   qty: '30 packs',    weightKg: 36,  brand: 'Waypoint Fresh', refrigeration: 'Reefer' },
    ],
  },
  {
    vehicleId: 'VEH009', tripLabel: 'Trip 2 of 2', refrigeration: 'Reefer',
    capacityKg: 6000, capacityM3: 18.5, fuelPct: 40,
    cards: [
      { id: 'c5', orderId: 'ORD-4471', stop: 1, stopName: 'Wattala', product: 'Anchor Full Cream Milk 1L', qty: '180 bottles', weightKg: 185, brand: 'Waypoint Fresh', refrigeration: 'Reefer' },
      { id: 'c6', orderId: 'ORD-5102', stop: 2, stopName: 'Ja-Ela',  product: 'Yogurt Cups 500g',         qty: '60 pots',     weightKg: 60,  brand: 'Waypoint Fresh', refrigeration: 'Reefer' },
    ],
  },
  {
    vehicleId: 'VEH001', tripLabel: 'Trip 1 of 2', refrigeration: 'Reefer',
    capacityKg: 6000, capacityM3: 18.5, fuelPct: 62,
    cards: [
      { id: 'c7', orderId: 'ORD-3390', stop: 1, stopName: 'Negombo',    product: 'Pasteurized Whole Milk 1L',     qty: '240 units', weightKg: 240, brand: 'Waypoint Fresh', refrigeration: 'Reefer' },
      { id: 'c8', orderId: 'ORD-6601', stop: 2, stopName: 'Katunayake', product: 'Chilled Chicken Portions 500g', qty: '250 packs', weightKg: 250, brand: 'Waypoint Fresh', refrigeration: 'Reefer' },
    ],
  },
  {
    vehicleId: 'VEH041', tripLabel: 'Trip 1 of 2', refrigeration: 'Ambient',
    capacityKg: 4500, capacityM3: 12.0, fuelPct: 88,
    cards: [
      { id: 'c9',  orderId: 'ORD-5102', stop: 1, stopName: 'Pettah', product: 'Basmati Rice 5kg Master Bags', qty: '25 bags',    weightKg: 125, brand: 'Waypoint Style', refrigeration: 'Ambient' },
      { id: 'c10', orderId: 'ORD-1188', stop: 2, stopName: 'Fort',   product: 'Ceylon BOPF Tea Cartons',      qty: '15 cartons', weightKg: 90,  brand: 'Waypoint Style', refrigeration: 'Ambient' },
    ],
  },
  {
    vehicleId: 'VEH004', tripLabel: 'Trip 1 of 1', refrigeration: 'Ambient',
    capacityKg: 1500, capacityM3: 6.0, fuelPct: 72,
    cards: [
      { id: 'c11', orderId: 'ORD-1188', stop: 1, stopName: 'Wellawatte', product: 'Red Split Lentils Dhal 1kg', qty: '150 kg', weightKg: 150, brand: 'Waypoint Style', refrigeration: 'Ambient' },
    ],
  },
];

const INITIAL_TRAY = [
  { id: 't1', orderId: 'ORD-3390', stop: 3, stopName: 'Ja-Ela Central',  product: 'Cream Cheese Philadelphia 200g', qty: 'x30', weightKg: 15, brand: 'Waypoint Fresh', refrigeration: 'Reefer'   },
  { id: 't2', orderId: 'ORD-5102', stop: 2, stopName: 'Kandana Express', product: 'Denim Jackets Assorted Men',     qty: 'x12', weightKg: 12, brand: 'Waypoint Style', refrigeration: 'Ambient'  },
  { id: 't3', orderId: 'ORD-1188', stop: 1, stopName: 'Colombo South',   product: 'Blender Unit Compact 600W',     qty: 'x1',  weightKg: 4,  brand: 'Waypoint Tech',  refrigeration: 'Ambient'  },
  { id: 't4', orderId: 'ORD-6601', stop: 3, stopName: 'Negombo Express', product: 'Bairaha Chicken Breast 500g',   qty: 'x80', weightKg: 40, brand: 'Waypoint Fresh', refrigeration: 'Reefer'   },
  { id: 't5', orderId: 'ORD-7720', stop: 1, stopName: 'Kollupitiya',     product: 'Smart LED Bulbs 9W Pack 4',     qty: 'x24', weightKg: 6,  brand: 'Waypoint Tech',  refrigeration: 'Ambient'  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────
const rowWeightKg  = (row) => row.cards.reduce((s, c) => s + c.weightKg, 0);
const rowWeightPct = (row) => Math.min((rowWeightKg(row) / row.capacityKg) * 100, 100);
const canAccept    = (row, card) => row.refrigeration === card.refrigeration;
const barColour    = (pct) => pct < 75 ? C.primary : pct < 90 ? '#F59E0B' : '#EF4444';

// ─── OrderTag ─────────────────────────────────────────────────────────────────
function OrderTag({ orderId, isSplit, isDraggingSameOrder, onClick }) {
  const col = orderColour(orderId);
  return (
    <button
      type="button"
      onClick={onClick}
      style={{ background: col.bg, color: col.text, border: `1px solid ${col.border}` }}
      className="group inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold whitespace-nowrap cursor-pointer hover:opacity-80 transition-opacity"
    >
      {orderId}
      {isSplit && (
        <span style={{ color: C.dark }} className={`${isDraggingSameOrder ? 'inline' : 'hidden group-hover:inline'}`}>
          · split
        </span>
      )}
    </button>
  );
}

// ─── ProductCard ─────────────────────────────────────────────────────────────
function ProductCard({ card, isDragging, isSplit, isDraggingSameOrder, onOrderTagClick }) {
  return (
    <div
      className={`relative flex-shrink-0 w-36 rounded-xl px-[12px] py-[10px] select-none transition-all ${
        isDragging ? 'bg-white shadow-sm border border-[#DCEEE1]' : 'bg-[#FAFBFA] border border-transparent'
      }`}
      style={{ opacity: isDragging ? 0.4 : 1 }}
    >
      <div className="mb-1.5">
        <OrderTag orderId={card.orderId} isSplit={isSplit} isDraggingSameOrder={isDraggingSameOrder} onClick={() => onOrderTagClick(card.orderId)} />
      </div>
      <p className="text-[10px] text-gray-400 mb-0.5 truncate">Stop {card.stop} - {card.stopName}</p>
      <p className="text-[11px] font-semibold text-[#0B2019] leading-tight line-clamp-2">{card.product}</p>
      <p className="text-[10px] text-gray-500 mt-0.5">{card.qty}</p>
    </div>
  );
}

// ─── RowDropArea ──────────────────────────────────────────────────────────────
function RowDropArea({ vehicleId, onDrop, isCompatible, isDraggingAny, children }) {
  const [over, setOver] = useState(false);
  const active = over && isCompatible;

  let outline = '1px solid #F3F4F6';
  let bg = '#FFFFFF';

  if (isDraggingAny && isCompatible) {
    outline = '2px dashed #A7D7C5';
  }
  if (active) {
    outline = `2px dashed ${C.primary}`;
    bg = '#F2FDF5';
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
          setOver(false);
        }
      }}
      onDrop={(e) => { e.preventDefault(); setOver(false); if (isCompatible) onDrop(vehicleId); }}
      className="flex-1 rounded-2xl overflow-x-auto transition-all duration-150"
      style={{
        outline: outline,
        outlineOffset: '-2px',
        boxShadow: active ? `0 0 0 4px ${C.primary}10` : '0 1px 3px rgba(0,0,0,0.04)',
        background: bg,
      }}
    >
      {children}
    </div>
  );
}

// ─── CapacityBar ─────────────────────────────────────────────────────────────
function CapacityBar({ label, value, max }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] text-gray-400 font-medium">{label}</span>
        <span className="text-[10px] text-gray-400 font-normal">{value.toLocaleString()} / {max.toLocaleString()}</span>
      </div>
      <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-300" style={{ width: `${pct}%`, background: barColour(pct) }} />
      </div>
    </div>
  );
}

// ─── SplitPopover ────────────────────────────────────────────────────────────
function SplitPopover({ orderId, rows, onClose }) {
  const involved = rows.flatMap(row =>
    row.cards.filter(c => c.orderId === orderId).map(c => ({ vehicleId: row.vehicleId, stop: c.stopName }))
  );
  const vehicleCount = new Set(involved.map(i => i.vehicleId)).size;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white border border-gray-200 rounded-xl shadow-xl p-4 w-72" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-xs font-bold text-[#0B2019]">{orderId}</p>
            <p className="text-[10px] text-gray-500">{involved.length} item{involved.length > 1 ? 's' : ''} placed - arriving on {vehicleCount} vehicle{vehicleCount > 1 ? 's' : ''}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 cursor-pointer"><X size={14} /></button>
        </div>
        <div className="space-y-1.5">
          {involved.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-[10px] bg-gray-50 rounded-lg px-2.5 py-1.5">
              <Truck size={11} className="text-gray-400 flex-shrink-0" />
              <span className="font-semibold text-[#0B2019]">{item.vehicleId}</span>
              <span className="text-gray-400 mx-0.5">to</span>
              <span className="text-gray-600 truncate">{item.stop}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── AllocationConfirmModal (two-step) ───────────────────────────────────────
function AllocationConfirmModal({ isOpen, onClose, onGoToFleet, onBackToAllocation, onFinalConfirm }) {
  const [step, setStep]         = useState(1); // 1 = warning, 2 = note+confirm
  const [note, setNote]         = useState('');
  const [confirmText, setConfirmText] = useState('');

  const reset = () => { setStep(1); setNote(''); setConfirmText(''); };
  const handleClose = () => { reset(); onClose(); };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      style={{ background: 'rgba(15,23,42,0.45)', backdropFilter: 'blur(2px)' }}
      onClick={handleClose}
    >
      <div
        className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-[640px] overflow-hidden flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {step === 1 ? (
          <>
            {/* Warning header */}
            <div className="p-7 pb-4">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center">
                  <AlertTriangle size={18} className="text-amber-500" />
                </div>
                <div className="flex-1">
                  <h2 className="text-base font-bold text-slate-900 tracking-tight">You have changed the allocations</h2>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    The manual allocation differs from the CP-SAT solver plan. Proceeding will override the optimised plan and lock the manual allocation as the active dispatch.
                  </p>
                </div>
                <button onClick={handleClose} className="text-slate-400 hover:text-slate-600 cursor-pointer transition-colors flex-shrink-0">
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Warning body */}
            <div className="px-7 pb-4">
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
                <p className="text-xs text-amber-800 font-semibold mb-1">Before you proceed, confirm:</p>
                <ul className="text-xs text-amber-700 space-y-1 list-disc list-inside">
                  <li>Temperature compatibility has been manually verified</li>
                  <li>Vehicle capacities are not exceeded</li>
                  <li>Delivery time windows remain achievable</li>
                </ul>
              </div>
            </div>

            {/* Footer — 3 actions */}
            <div className="px-7 pb-7 pt-2 border-t border-slate-100 flex flex-col sm:flex-row items-center gap-2.5">
              <button
                type="button"
                onClick={() => { reset(); onGoToFleet(); }}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold transition cursor-pointer whitespace-nowrap"
              >
                Go to Fleet Availability
              </button>
              <button
                type="button"
                onClick={() => { reset(); onBackToAllocation(); }}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold transition cursor-pointer whitespace-nowrap"
              >
                Back to Manual Allocation
              </button>
              <button
                type="button"
                onClick={() => setStep(2)}
                className="w-full sm:flex-1 px-4 py-2.5 rounded-xl text-white text-xs font-bold transition cursor-pointer whitespace-nowrap"
                style={{ background: C.primary }}
                onMouseEnter={e => e.currentTarget.style.background = C.primaryHover}
                onMouseLeave={e => e.currentTarget.style.background = C.primary}
              >
                Proceed Further
              </button>
            </div>
          </>
        ) : (
          <>
            {/* Step 2 header */}
            <div className="p-7 pb-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-base font-bold text-slate-900 tracking-tight">Confirm manual allocation</h2>
                  <p className="text-xs text-slate-500 mt-1">Add a note and type <span className="font-mono font-bold text-slate-700">confirm</span> to lock this plan.</p>
                </div>
                <button onClick={handleClose} className="text-slate-400 hover:text-slate-600 cursor-pointer transition-colors flex-shrink-0">
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Step 2 body */}
            <div className="px-7 pb-4 space-y-4">
              {/* Note box */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Reason / note <span className="text-slate-400 font-normal">(optional)</span></label>
                <textarea
                  value={note}
                  onChange={e => setNote(e.target.value)}
                  placeholder="e.g. VEH027 had spare reefer capacity and outlet OUT-2041 is time-critical..."
                  rows={3}
                  className="w-full text-xs text-slate-800 placeholder-slate-400 border border-slate-200 rounded-xl px-3.5 py-2.5 resize-none focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ focusRingColor: C.primary }}
                  onFocus={e => { e.target.style.borderColor = C.primary; e.target.style.boxShadow = `0 0 0 2px ${C.primary}30`; }}
                  onBlur={e => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none'; }}
                />
              </div>

              {/* Confirm text box */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Type <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-800">confirm</span> to unlock
                </label>
                <input
                  type="text"
                  value={confirmText}
                  onChange={e => setConfirmText(e.target.value)}
                  placeholder="confirm"
                  className="w-full text-xs text-slate-800 placeholder-slate-400 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:outline-none"
                  onFocus={e => { e.target.style.borderColor = C.primary; e.target.style.boxShadow = `0 0 0 2px ${C.primary}30`; }}
                  onBlur={e => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none'; }}
                />
              </div>
            </div>

            {/* Step 2 footer */}
            <div className="px-7 pb-7 pt-2 border-t border-slate-100 flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold transition cursor-pointer"
              >
                Back
              </button>
              <button
                type="button"
                disabled={confirmText.trim().toLowerCase() !== 'confirm'}
                onClick={() => { reset(); onFinalConfirm(note); }}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-white text-xs font-bold transition"
                style={{
                  background: confirmText.trim().toLowerCase() === 'confirm' ? C.primary : '#A7D7C5',
                  cursor:     confirmText.trim().toLowerCase() === 'confirm' ? 'pointer' : 'not-allowed',
                  boxShadow:  confirmText.trim().toLowerCase() === 'confirm' ? '0 1px 3px rgba(0,0,0,0.12)' : 'none',
                }}
                onMouseEnter={e => { if (confirmText.trim().toLowerCase() === 'confirm') e.currentTarget.style.background = C.primaryHover; }}
                onMouseLeave={e => { if (confirmText.trim().toLowerCase() === 'confirm') e.currentTarget.style.background = C.primary; }}
              >
                <Check size={13} />
                Confirm manual allocation
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function RouteAllocationBoard({ onBack, onConfirmAllocations }) {
  const [rows, setRows]             = useState(buildInitialRows);
  const [tray, setTray]             = useState(INITIAL_TRAY);
  const [sortBy, setSortBy]         = useState('vehicleId');
  const [trayFilter, setTrayFilter] = useState('all');
  const [dragCard, setDragCard]     = useState(null);
  const [notifications, setNotifications] = useState(true);
  const [showUserMenu, setShowUserMenu]   = useState(false);
  const [splitPopover, setSplitPopover]   = useState(null);
  const [confirmed, setConfirmed]         = useState(false);
  const [showToast, setShowToast]         = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [trayHeight, setTrayHeight]       = useState(180);

  const startResize = useCallback((e) => {
    e.preventDefault();
    const startY = e.clientY;
    const startHeight = trayHeight;

    const onMouseMove = (moveEvent) => {
      const deltaY = startY - moveEvent.clientY;
      const newHeight = Math.max(120, Math.min(window.innerHeight * 0.8, startHeight + deltaY));
      setTrayHeight(newHeight);
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = 'default';
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    document.body.style.cursor = 'row-resize';
  }, [trayHeight]);

  // Detect split orders (same orderId on 2+ vehicles)
  const splitOrderIds = (() => {
    const map = {};
    rows.forEach(row => row.cards.forEach(c => {
      if (!map[c.orderId]) map[c.orderId] = new Set();
      map[c.orderId].add(row.vehicleId);
    }));
    return new Set(Object.entries(map).filter(([, v]) => v.size > 1).map(([k]) => k));
  })();

  const allPlaced = tray.length === 0;

  const handleDragStart = useCallback((card, sourceType, sourceVehicleId = null) => {
    setDragCard({ card, sourceType, sourceVehicleId });
  }, []);

  const handleDropOnRow = useCallback((targetVehicleId) => {
    if (!dragCard) return;
    const { card, sourceType, sourceVehicleId } = dragCard;
    const targetRow = rows.find(r => r.vehicleId === targetVehicleId);
    if (!targetRow || !canAccept(targetRow, card)) { setDragCard(null); return; }
    if (sourceType === 'tray') {
      setTray(prev => prev.filter(c => c.id !== card.id));
    } else if (sourceType === 'row' && sourceVehicleId) {
      setRows(prev => prev.map(r => r.vehicleId === sourceVehicleId ? { ...r, cards: r.cards.filter(c => c.id !== card.id) } : r));
    }
    setRows(prev => prev.map(r => r.vehicleId === targetVehicleId ? { ...r, cards: [...r.cards, card] } : r));
    setDragCard(null);
  }, [dragCard, rows]);

  const handleDropOnTray = useCallback(() => {
    if (!dragCard || dragCard.sourceType === 'tray') { setDragCard(null); return; }
    const { card, sourceVehicleId } = dragCard;
    setRows(prev => prev.map(r => r.vehicleId === sourceVehicleId ? { ...r, cards: r.cards.filter(c => c.id !== card.id) } : r));
    setTray(prev => [...prev, card]);
    setDragCard(null);
  }, [dragCard]);

  const sortedRows = [...rows].sort((a, b) => {
    if (sortBy === 'vehicleId') return a.vehicleId.localeCompare(b.vehicleId);
    if (sortBy === 'fuel')      return a.fuelPct - b.fuelPct;
    if (sortBy === 'type')      return a.refrigeration.localeCompare(b.refrigeration);
    if (sortBy === 'fill')      return rowWeightPct(b) - rowWeightPct(a);
    return 0;
  });

  const filteredTray = tray.filter(c => trayFilter === 'all' || c.brand === trayFilter);

  const handleAutoAllocate = useCallback(() => {
    setRows(prevRows => {
      let newRows = [...prevRows].map(r => ({ ...r, cards: [...r.cards] }));
      let unplacedTray = [];
      
      tray.forEach(card => {
        let targetRow = newRows.find(r => 
          r.refrigeration === card.refrigeration && 
          (rowWeightKg(r) + card.weightKg) <= r.capacityKg
        );
        if (!targetRow) {
          targetRow = newRows.find(r => r.refrigeration === card.refrigeration);
        }
        
        if (targetRow) {
          targetRow.cards.push(card);
        } else {
          unplacedTray.push(card);
        }
      });
      
      setTray(unplacedTray);
      return newRows;
    });
  }, [tray]);

  const handleConfirm = () => {
    if (!allPlaced) return;
    setShowConfirmModal(true);
  };

  const handleFinalConfirm = (_note) => {
    setShowConfirmModal(false);
    if (onConfirmAllocations) {
      onConfirmAllocations();
    } else {
      setConfirmed(true);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 4000);
    }
  };

  const SORT_OPTIONS = [
    { key: 'vehicleId', label: 'Vehicle ID'     },
    { key: 'fuel',      label: 'Fuel Remaining' },
    { key: 'type',      label: 'Type'           },
    { key: 'fill',      label: 'Fill %'         },
  ];

  const BRAND_FILTERS = [
    { key: 'all',            label: 'All'            },
    { key: 'Waypoint Fresh', label: 'Waypoint Fresh' },
    { key: 'Waypoint Style', label: 'Waypoint Style' },
    { key: 'Waypoint Tech',  label: 'Waypoint Tech'  },
  ];

  return (
    <div
      className="flex flex-col h-screen w-full overflow-hidden"
      style={{ background: '#FAFBFA', fontFamily: "'Inter', sans-serif" }}
      onDragOver={e => e.preventDefault()}
    >
      {/* Header */}
      <header className="w-full border-b border-gray-100 bg-white z-30 flex-shrink-0" style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
        <div className="max-w-[1600px] mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3 sm:gap-4">
            {/* Top-Left Back Arrow Button */}
            <button
              type="button"
              onClick={onBack}
              title="Back to Fleet Availability"
              className="w-8 h-8 rounded-xl border border-gray-200 hover:border-gray-300 bg-white hover:bg-gray-50 flex items-center justify-center text-gray-700 hover:text-gray-900 transition-colors shadow-2xs cursor-pointer flex-shrink-0"
            >
              <ArrowLeft size={15} strokeWidth={2.2} />
            </button>

            <div className="flex items-center gap-2.5 cursor-pointer" onClick={onBack}>
              <img src={waypointLogo} alt="Waypoint" className="w-7 h-7 object-contain rounded-lg" />
              <span className="text-base font-bold tracking-tight text-[#0B2019] whitespace-nowrap">Waypoint Dispatcher</span>
            </div>
            <nav className="hidden md:flex items-center gap-1.5">
              {['Overview', 'Route Allocation & Capacity', 'Contingency Dispatch', 'Deferral Log'].map(tab => (
                <button key={tab} type="button"
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${tab === 'Route Allocation & Capacity' ? 'bg-[#E8F7F0] text-[#059669]' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}
                >{tab}</button>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-2.5">
            <button type="button" className="w-8 h-8 rounded-full border border-gray-200 bg-white flex items-center justify-center text-gray-600 hover:text-gray-900 transition-colors cursor-pointer">
              <Moon size={15} strokeWidth={2} />
            </button>
            <button type="button" className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-gray-700 bg-white border border-gray-200 rounded-full cursor-pointer">
              <span>Thu, Oct 1</span><ChevronDown size={13} className="text-gray-500" />
            </button>
            <button type="button" onClick={() => setNotifications(n => !n)}
              className="relative w-8 h-8 rounded-full border border-gray-200 bg-white flex items-center justify-center text-gray-600 transition-colors cursor-pointer">
              <Bell size={15} strokeWidth={2} />
              {notifications && <span className="absolute top-1 right-1 w-2 h-2 bg-[#059669] rounded-full ring-2 ring-white" />}
            </button>
            <div className="relative">
              <button type="button" onClick={() => setShowUserMenu(s => !s)}
                className="w-8 h-8 rounded-full bg-[#E0F2E9] border border-[#C6E7D5] text-[#059669] text-xs font-bold flex items-center justify-center cursor-pointer">RM</button>
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-44 bg-white border border-gray-100 rounded-xl shadow-lg py-1 z-50">
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="text-xs font-medium text-gray-900">Lead Dispatcher</p>
                    <p className="text-[11px] text-gray-500">hub/Peliyagoda</p>
                  </div>
                  <button onClick={() => { setShowUserMenu(false); onBack(); }} className="w-full text-left px-3 py-2 text-xs text-gray-700 hover:bg-gray-50 cursor-pointer">Sign Out</button>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleConfirm}
              disabled={!allPlaced || confirmed}
              className="inline-flex items-center gap-2 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all flex-shrink-0"
              style={{
                background: allPlaced && !confirmed ? C.primary : '#A7D7C5',
                cursor: allPlaced && !confirmed ? 'pointer' : 'not-allowed',
                boxShadow: allPlaced && !confirmed ? '0 1px 3px rgba(0,0,0,0.12)' : 'none',
              }}
              onMouseEnter={e => { if (allPlaced && !confirmed) e.currentTarget.style.background = C.primaryHover; }}
              onMouseLeave={e => { if (allPlaced && !confirmed) e.currentTarget.style.background = C.primary; }}
              onMouseDown={e =>  { if (allPlaced && !confirmed) e.currentTarget.style.background = C.primaryActive; }}
              onMouseUp={e =>    { if (allPlaced && !confirmed) e.currentTarget.style.background = C.primaryHover; }}
            >
              {confirmed ? <><Check size={13} /> Allocation Confirmed</> : 'Confirm Allocation'}
            </button>
          </div>
        </div>
        {/* Breadcrumb */}
        <div className="max-w-[1600px] mx-auto px-6 pb-2.5">
          <p className="text-[11px] text-gray-400">
            <span className="text-gray-600 font-medium">Allocation Board</span>
            <span className="mx-1.5 text-gray-300">·</span>Peliyagoda Hub
            <span className="mx-1.5 text-gray-300">·</span>Thu, Oct 1
          </p>
        </div>
      </header>

      {/* Sort pills */}
      <div className="flex-shrink-0 flex items-center px-6 py-2.5 bg-white border-b" style={{ borderColor: C.border }}>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-gray-500 mr-1 font-medium">Sort by:</span>
          {SORT_OPTIONS.map(opt => (
            <button key={opt.key} type="button" onClick={() => setSortBy(opt.key)}
              className="px-3 py-1 rounded-full text-[11px] font-semibold transition-colors cursor-pointer"
              style={sortBy === opt.key
                ? { background: C.primary, color: '#fff', border: `1px solid ${C.primary}` }
                : { background: C.surface, color: C.dark, border: `1px solid ${C.border}` }
              }
            >{opt.label}</button>
          ))}
        </div>

        <button
          type="button"
          onClick={handleAutoAllocate}
          disabled={tray.length === 0}
          className="ml-auto inline-flex items-center gap-1.5 text-gray-700 hover:text-gray-900 bg-white border border-gray-200 text-[11px] font-semibold px-3 py-1 rounded-full transition-all cursor-pointer hover:bg-gray-50 shadow-2xs disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Wand2 size={12} className="text-gray-500" /> Auto Allocate
        </button>
      </div>

      {/* Scrollable vehicle rows */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3" style={{ paddingBottom: `${trayHeight + 20}px` }}>
        {sortedRows.map(row => {
          const weightKg     = rowWeightKg(row);
          const volumeEst    = Math.round((weightKg / row.capacityKg) * row.capacityM3 * 10) / 10;
          const isDimmed     = dragCard?.card && !canAccept(row, dragCard.card);
          const isCompatible = dragCard?.card ? canAccept(row, dragCard.card) : false;

          const stopGroups = row.cards.reduce((acc, c) => {
            const key = `${c.stop}-${c.stopName}`;
            if (!acc[key]) acc[key] = { stop: c.stop, stopName: c.stopName, cards: [] };
            acc[key].cards.push(c);
            return acc;
          }, {});

          return (
            <div key={row.vehicleId} className="flex gap-4 items-stretch"
              style={{ opacity: isDimmed ? 0.35 : 1, transition: 'opacity 0.15s ease' }}>
              {/* Vehicle card */}
              <div className="flex-shrink-0 w-52 bg-white rounded-2xl p-4 flex flex-col"
                style={{
                  border: '1px solid transparent',
                  boxShadow: isCompatible && dragCard ? `0 0 0 2px ${C.primary}40` : '0 2px 8px rgba(0,0,0,0.04)',
                  transition: 'box-shadow 0.15s',
                }}>
                <div className="flex items-start justify-between gap-1 mb-1">
                  <span className="text-sm font-bold tracking-tight" style={{ color: C.darkest }}>{row.vehicleId}</span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-semibold flex-shrink-0"
                    style={{ background: C.surface, color: C.dark, border: `1px solid ${C.border}` }}>
                    {row.refrigeration === 'Reefer' ? <Snowflake size={9} /> : <Wind size={9} />}
                    {row.refrigeration}
                  </span>
                </div>
                <p className="text-[10px] text-gray-400 mb-3">{row.tripLabel}</p>
                <div className="flex flex-col gap-1 mb-2">
                  <CapacityBar label="Weight (kg)" value={weightKg} max={row.capacityKg} />
                  <CapacityBar label="Volume (m3)" value={volumeEst} max={row.capacityM3} />
                </div>
                <p className="text-[10px] font-mono text-gray-400 mt-auto pt-1">Fuel {row.fuelPct}%</p>
              </div>

              {/* Product cards area */}
              <RowDropArea vehicleId={row.vehicleId} onDrop={handleDropOnRow} isCompatible={isCompatible} isDraggingAny={!!dragCard}>
                <div className="flex items-stretch gap-0 h-full p-4" style={{ minHeight: '108px', minWidth: '100%', width: 'fit-content' }}>
                  {row.cards.length === 0 ? (
                    <div className="flex items-center justify-center w-full h-full text-gray-400 text-[11px] font-medium min-h-[80px]">
                      {isDraggingAny && isCompatible ? 'Drop items here' : 'Empty'}
                    </div>
                  ) : (
                    Object.values(stopGroups).map((group, gi) => (
                      <React.Fragment key={`${group.stop}-${group.stopName}`}>
                        {gi > 0 && <div className="flex-shrink-0 w-px bg-gray-100 mx-4 self-stretch" />}
                        <div className="flex flex-col gap-2 flex-shrink-0">
                          <p className="text-[9px] font-semibold text-gray-400 uppercase tracking-wide px-0.5">
                            Stop {group.stop} · {group.stopName}
                          </p>
                          <div className="flex gap-3">
                            {group.cards.map(card => (
                              <div key={card.id} draggable
                                onDragStart={() => handleDragStart(card, 'row', row.vehicleId)}
                                onDragEnd={() => setDragCard(null)}
                                className="cursor-grab active:cursor-grabbing">
                                <ProductCard
                                  card={card}
                                  isDragging={dragCard?.card?.id === card.id}
                                  isSplit={splitOrderIds.has(card.orderId)}
                                  isDraggingSameOrder={dragCard?.card?.orderId === card.orderId}
                                  onOrderTagClick={id => setSplitPopover(splitOrderIds.has(id) ? id : null)}
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                      </React.Fragment>
                    ))
                  )}
                </div>
              </RowDropArea>
            </div>
          );
        })}
      </div>

      {/* Bottom tray */}
      <div className="fixed bottom-0 left-0 right-0 z-20 flex flex-col"
        style={{ background: '#FFFFFF', borderTop: '1px solid #F3F4F6', height: `${trayHeight}px` }}
        onDragOver={e => e.preventDefault()}
        onDrop={e => { e.preventDefault(); handleDropOnTray(); }}>
        
        {/* Resizer Handle */}
        <div 
          className="w-full h-3 flex items-center justify-center cursor-row-resize absolute top-0 left-0 -mt-1.5 z-30 group"
          onMouseDown={startResize}
        >
          <div className="w-12 h-1 bg-gray-200 rounded-full group-hover:bg-gray-400 transition-colors" />
        </div>

        <div className="max-w-[1600px] w-full mx-auto px-6 pt-3 pb-4 flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-3 mb-3 flex-wrap flex-shrink-0">
            <p className="text-xs font-bold" style={{ color: C.darkest }}>
              Unassigned line items ({filteredTray.length})
            </p>
            <div className="flex items-center gap-1.5 flex-wrap">
              {BRAND_FILTERS.map(f => (
                <button key={f.key} type="button" onClick={() => setTrayFilter(f.key)}
                  className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold transition-colors cursor-pointer"
                  style={trayFilter === f.key
                    ? { background: C.primary, color: '#fff', border: `1px solid ${C.primary}` }
                    : { background: '#fff', color: C.dark, border: `1px solid ${C.border}` }
                  }>{f.label}</button>
              ))}
            </div>
            {allPlaced && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold"
                style={{ background: '#D1FAE5', color: '#065F46', border: '1px solid #6EE7B7' }}>
                <Check size={10} /> All items placed
              </span>
            )}
            <p className="ml-auto text-[10px] text-gray-400 hidden lg:block">
              Same order tag = same order · Drag to assign · Drag back to unassign
            </p>
          </div>
          <div className="flex gap-3 overflow-y-auto overflow-x-hidden pb-2 flex-1 content-start flex-wrap">
            {filteredTray.length === 0 ? (
              <p className="text-[11px] text-gray-400 py-2 italic w-full">
                {trayFilter === 'all' ? 'All items assigned - ready to confirm.' : 'No unassigned items in this category.'}
              </p>
            ) : (
              filteredTray.map(card => (
                <div key={card.id} draggable
                  onDragStart={() => handleDragStart(card, 'tray')}
                  onDragEnd={() => setDragCard(null)}
                  className="cursor-grab active:cursor-grabbing">
                  <ProductCard
                    card={card}
                    isDragging={dragCard?.card?.id === card.id}
                    isSplit={splitOrderIds.has(card.orderId)}
                    isDraggingSameOrder={dragCard?.card?.orderId === card.orderId}
                    onOrderTagClick={id => setSplitPopover(splitOrderIds.has(id) ? id : null)}
                  />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Split order popover */}
      {splitPopover && (
        <SplitPopover orderId={splitPopover} rows={rows} onClose={() => setSplitPopover(null)} />
      )}

      {/* Allocation confirmation modal */}
      <AllocationConfirmModal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        onGoToFleet={() => { setShowConfirmModal(false); onBack(); }}
        onBackToAllocation={() => setShowConfirmModal(false)}
        onFinalConfirm={handleFinalConfirm}
      />

      {/* Confirm toast */}
      {showToast && (
        <div className="fixed top-20 right-6 z-50 flex items-center gap-2.5 bg-white border rounded-xl shadow-lg px-4 py-3 text-sm font-semibold"
          style={{ borderColor: C.border, color: C.darkest }}>
          <span className="w-6 h-6 rounded-full flex items-center justify-center text-white flex-shrink-0" style={{ background: C.primary }}>
            <Check size={12} />
          </span>
          Allocation confirmed - dispatch plan locked.
        </div>
      )}
    </div>
  );
}

