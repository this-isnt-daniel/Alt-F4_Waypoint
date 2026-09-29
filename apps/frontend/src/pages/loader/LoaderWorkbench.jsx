import React, { useState } from 'react';
import { Phone, Flag, Minus, Plus, X, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function LoaderWorkbench() {
  const [vehicleAvailable, setVehicleAvailable] = useState(true);
  const [showDiscrepancyModal, setShowDiscrepancyModal] = useState(false);
  const [selectedDiscrepancyItem, setSelectedDiscrepancyItem] = useState(null);
  const [showDriverDetails, setShowDriverDetails] = useState(false);
  
  // Data State
  const [items, setItems] = useState({
    item1: { id: 'item1', name: 'Fresh Whole Milk 1L - 20 Crates', assigned: 20, actual: 20, status: 'Verified' },
    item2: { id: 'item2', name: 'Chilled Chicken Drumsticks - 15 Cartons', assigned: 15, actual: 15, status: 'Verified' },
    item3: { id: 'item3', name: 'Fresh Pasteurised Milk 1L - 40 Crates', assigned: 40, actual: 40, status: 'Verified' },
    item4: { 
      id: 'item4', 
      name: 'Chilled Dairy Butter 200g', 
      assigned: 25, 
      actual: 23, 
      status: 'Discrepancy',
      reason: 'Damaged at Dock',
      shortfall: 2
    },
  });

  const handleOpenDiscrepancy = (itemId) => {
    setSelectedDiscrepancyItem(itemId);
    setShowDiscrepancyModal(true);
  };

  const handleConfirmDiscrepancy = (actualQty, reason) => {
    if (selectedDiscrepancyItem) {
      const item = items[selectedDiscrepancyItem];
      const shortfall = item.assigned - actualQty;
      
      setItems({
        ...items,
        [selectedDiscrepancyItem]: {
          ...item,
          actual: actualQty,
          status: actualQty === item.assigned ? 'Verified' : 'Discrepancy',
          reason: actualQty === item.assigned ? null : reason,
          shortfall: actualQty === item.assigned ? 0 : shortfall
        }
      });
    }
    setShowDiscrepancyModal(false);
  };

  if (!vehicleAvailable) {
    return <WorkbenchUnavailable onToggle={() => setVehicleAvailable(true)} />;
  }

  return (
    <div className="bg-[#f8fbf9] min-h-full pb-24 relative overflow-hidden">
      <div className="p-6 space-y-6">
        
        {/* Toggle Card */}
        <div className="border border-slate-200 rounded-xl p-4 bg-white shadow-sm flex items-center justify-between">
          <span className="font-bold text-slate-900 text-[17px]">Truck Available for Loading</span>
          <button onClick={() => setVehicleAvailable(false)} className="w-14 h-8 bg-slate-800 rounded-full relative transition-colors">
            <div className="absolute right-1 top-1 w-6 h-6 bg-white rounded-full"></div>
          </button>
        </div>

        {/* Driver Card */}
        <div className="border border-slate-200 rounded-xl p-4 bg-white shadow-sm flex items-center justify-between cursor-pointer hover:bg-slate-50 transition-colors" onClick={() => setShowDriverDetails(true)}>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-600 text-[17px]">
              KR
            </div>
            <div>
              <div className="font-bold text-slate-900 text-[17px]">K. Rathnayake</div>
              <div className="text-slate-500 text-[13px]">Driver · VEH011</div>
            </div>
          </div>
          <button className="w-10 h-10 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-100">
            <Phone className="w-5 h-5" />
          </button>
        </div>
        <div className="text-xs text-slate-400 mt-[-16px] ml-2">Tap for contact details & vehicle info</div>

        {/* Packing Sequence */}
        <div>
          <h2 className="text-[19px] font-bold text-slate-900 mb-0.5">Packing Sequence</h2>
          <p className="text-slate-500 text-sm mb-4">Pack from the back first, doors last</p>

          <div className="space-y-4">
            {/* Stop 1 */}
            <div className="border border-[#DCF0E5] dark:border-emerald-900/50 bg-[#F4FAF6] dark:bg-[#111827] rounded-xl p-5 shadow-sm transition-colors">
              <div className="flex justify-between items-start mb-1.5">
                <h3 className="font-bold text-slate-900 dark:text-[#F8FAFC] text-[16px]">1. Pack First - Kandana Express (OUT-0122)</h3>
                <span className="px-3 py-1 bg-brand-50 dark:bg-emerald-950/50 text-brand-600 dark:text-emerald-400 text-xs font-bold rounded-full border border-brand-100 dark:border-emerald-800/40">Packed</span>
              </div>
              <div className="text-[13px] text-slate-500 dark:text-slate-400 mb-3 flex items-center gap-2">
                Delivers last · Stop 3
              </div>
              <div className="flex items-center gap-2 mb-4">
                <span className="font-bold text-slate-700 dark:text-slate-300 text-[13px]">530 kg · 3.5 m³</span>
                <span className="px-2 py-0.5 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 text-[11px] font-bold rounded border border-blue-100 dark:border-blue-900/40">Chilled</span>
              </div>

              {/* Items */}
              <div className="space-y-3">
                <ItemRow item={items.item1} onFlag={() => handleOpenDiscrepancy('item1')} />
                <ItemRow item={items.item2} onFlag={() => handleOpenDiscrepancy('item2')} />
              </div>
            </div>

            {/* Stop 2 */}
            <div className="border-2 border-brand-500 dark:border-emerald-500 bg-white dark:bg-[#111827] rounded-xl p-5 shadow-sm transition-colors">
              <div className="flex justify-between items-start mb-1.5">
                <h3 className="font-bold text-slate-900 dark:text-[#F8FAFC] text-[16px]">2. Pack Second - Ja-Ela Central (OUT-0091)</h3>
                <span className="px-3 py-1 bg-brand-50 dark:bg-emerald-950/50 text-brand-600 dark:text-emerald-400 text-xs font-bold rounded-full border border-brand-100 dark:border-emerald-800/40">Active</span>
              </div>
              <div className="text-[13px] text-slate-500 dark:text-slate-400 mb-3 flex items-center gap-2">
                Delivers 2nd · Stop 2
              </div>
              <div className="flex items-center gap-2 mb-4">
                <span className="font-bold text-slate-700 dark:text-slate-300 text-[13px]">1,100 kg · 4.5 m³</span>
                <span className="px-2 py-0.5 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 text-[11px] font-bold rounded border border-blue-100 dark:border-blue-900/40">Chilled</span>
              </div>

              {/* Items */}
              <div className="space-y-3">
                <ItemRow item={items.item3} onFlag={() => handleOpenDiscrepancy('item3')} />
                <ItemRow item={items.item4} onFlag={() => handleOpenDiscrepancy('item4')} />
              </div>
            </div>

          </div>
        </div>
      </div>

      {showDiscrepancyModal && (
        <DiscrepancyModal 
          item={items[selectedDiscrepancyItem]} 
          onClose={() => setShowDiscrepancyModal(false)}
          onConfirm={handleConfirmDiscrepancy}
        />
      )}

      {/* Driver Details Modal */}
      {showDriverDetails && (
        <div className="absolute inset-0 z-40 bg-slate-900/40 flex items-end">
          <div className="bg-white w-full rounded-t-3xl p-6 shadow-2xl">
            <div className="w-12 h-1 bg-slate-200 rounded-full mx-auto mb-6"></div>
            <h2 className="text-xl font-bold text-slate-900 mb-6">Driver & Vehicle Details</h2>
            
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 rounded-full bg-[#EBF6F0] text-brand-700 flex items-center justify-center font-bold text-[17px]">
                KR
              </div>
              <div>
                <div className="font-bold text-slate-900 text-[17px]">K. Rathnayake</div>
                <div className="text-slate-500 text-[13px]">CDL · 8 years experience</div>
              </div>
            </div>

            <div className="flex gap-3 mb-6">
              <button className="flex-1 py-3.5 bg-black rounded-xl text-white font-bold flex items-center justify-center gap-2">
                <Phone className="w-4 h-4" /> Call Driver
              </button>
              <button className="flex-1 py-3.5 bg-white border border-slate-200 rounded-xl text-slate-700 font-bold hover:bg-slate-50">
                Send Bay Alert
              </button>
            </div>

            <div className="border border-slate-200 rounded-xl p-4 text-sm text-slate-600 space-y-2.5">
              <div>Plate: WP-KA-4521</div>
              <div>Reefer Cert: Valid until 2026-03</div>
              <div>Gate Pass: GP-0411 (Active)</div>
            </div>
            
            <button onClick={() => setShowDriverDetails(false)} className="w-full mt-6 py-3 text-slate-500 font-bold">Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

// Item Row Component (Implementing the Deviation)
function ItemRow({ item, onFlag }) {
  const isDiscrepancy = item.status === 'Discrepancy';
  
  if (isDiscrepancy) {
    return (
      <div className="bg-emerald-500/10 dark:bg-emerald-950/30 border border-emerald-500/20 dark:border-emerald-800/30 rounded-lg p-3">
        <div className="flex items-start justify-between">
          <div className="flex gap-3">
            <div className="mt-0.5 w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
              <Minus className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-slate-900 dark:text-[#F8FAFC] text-[14px]">{item.name}</div>
              
              {/* DEVIATION: Verification State */}
              <div className="flex items-center gap-3 mt-1.5 text-[12px]">
                <span className="text-slate-500 dark:text-slate-400">Assigned: <span className="font-bold text-slate-700 dark:text-slate-200">{item.assigned}</span></span>
                <span className="text-slate-500 dark:text-slate-400">Actual: <span className="font-bold text-emerald-700 dark:text-emerald-400">{item.actual}</span></span>
                <span className="px-1.5 py-0.5 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 font-bold rounded">Mismatch</span>
              </div>
              
              <div className="mt-2 text-[13px] font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                Shortfall: {item.shortfall} Crates {item.reason} (Logged)
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="text-[12px] font-bold text-slate-500 dark:text-slate-400">{item.actual} of {item.assigned} Loaded</div>
            <button onClick={onFlag} className="px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold rounded-full flex items-center gap-1.5 hover:bg-slate-50 dark:hover:bg-slate-700 shadow-sm cursor-pointer">
              <Flag className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Edit
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Normal / Verified state
  return (
    <div className="flex items-start justify-between p-1">
      <div className="flex gap-3">
        <div className="mt-0.5 w-[20px] h-[20px] rounded border-2 border-slate-300"></div>
        <div>
          <div className="font-medium text-slate-800 text-[14px] leading-tight">{item.name}</div>
          
          {/* DEVIATION: Verification State */}
          <div className="flex items-center gap-3 mt-1.5 text-[12px]">
            <span className="text-slate-500">Assigned: <span className="font-bold text-slate-700">{item.assigned}</span></span>
            <span className="text-slate-500">Actual: <span className="font-bold text-slate-700">{item.actual}</span></span>
            <span className="px-1.5 py-0.5 bg-brand-50 text-brand-600 font-bold rounded flex items-center gap-1 text-[11px]">
               Verified
            </span>
          </div>
        </div>
      </div>
      <button onClick={onFlag} className="text-slate-400 hover:text-slate-600 p-1">
        <Flag className="w-4 h-4" />
      </button>
    </div>
  );
}

// Discrepancy Modal Component
function DiscrepancyModal({ item, onClose, onConfirm }) {
  const [reason, setReason] = useState(item.reason || 'Damaged at Staging');
  const [qty, setQty] = useState(item.shortfall || 2);

  const actualLoad = item.assigned - qty;

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col">
        <div className="p-6 relative">
          <button onClick={onClose} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600">
            <X className="w-6 h-6" />
          </button>
          
          <h2 className="text-xl font-bold text-slate-900 mb-1">Report Missing or Damaged Cargo</h2>
          <p className="text-slate-500 text-[13px] mb-6">{item.name.split(' - ')[0]} · Ja-Ela Central</p>
          
          <div className="mb-4">
            <label className="block text-[13px] font-bold text-slate-700 mb-2">Discrepancy Reason</label>
            <div className="grid grid-cols-2 gap-3">
              <button 
                onClick={() => setReason('Missing at Dock')}
                className={`py-2.5 px-3 text-[13px] font-bold rounded-lg border cursor-pointer ${reason === 'Missing at Dock' ? 'border-emerald-600 bg-emerald-600 text-white' : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800'}`}
              >
                Missing at Dock
              </button>
              <button 
                onClick={() => setReason('Damaged at Staging')}
                className={`py-2.5 px-3 text-[13px] font-bold rounded-lg border cursor-pointer ${reason === 'Damaged at Staging' ? 'border-emerald-600 bg-emerald-600 text-white' : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800'}`}
              >
                Damaged at Staging
              </button>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-[13px] font-bold text-slate-700 dark:text-slate-300 mb-2">Quantity Affected</label>
            <div className="flex items-center justify-center gap-6 py-2">
              <button onClick={() => setQty(Math.max(1, qty - 1))} className="w-12 h-12 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer">
                <Minus className="w-5 h-5" />
              </button>
              <span className="text-xl font-bold text-slate-900 dark:text-[#F8FAFC] w-24 text-center">{qty} Crates</span>
              <button onClick={() => setQty(Math.min(item.assigned, qty + 1))} className="w-12 h-12 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer">
                <Plus className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 mb-4">
            <div className="flex justify-between text-[13px] font-bold text-slate-600 dark:text-slate-400 mb-2">
              <span>Manifest Order</span>
              <span className="text-slate-900 dark:text-[#F8FAFC]">{item.assigned} Crates</span>
            </div>
            <div className="flex justify-between text-[13px] font-bold text-emerald-700 dark:text-emerald-400 mb-3 pb-3 border-b border-slate-100 dark:border-slate-800">
              <span>Damaged / Shortfall</span>
              <span>- {qty} Crates</span>
            </div>
            <div className="flex justify-between text-[15px] font-extrabold text-slate-900">
              <span>Load Onto Truck</span>
              <span className="text-brand-600 flex items-center gap-1">{actualLoad} Crates <CheckCircle2 className="w-4 h-4" /></span>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 flex gap-3 text-[13px] text-blue-700 mb-6">
            <div className="bg-blue-200 text-blue-700 w-4 h-4 rounded-sm flex items-center justify-center font-bold text-[10px] mt-0.5 shrink-0">i</div>
            <p className="leading-snug">Driver manifest will auto-adjust to {actualLoad} units. Store receipt will pre-populate the {qty}-crate shortfall.</p>
          </div>

          <div className="flex gap-3">
            <button onClick={onClose} className="flex-1 py-3 bg-white border border-slate-200 rounded-xl text-slate-700 font-bold hover:bg-slate-50 text-[14px]">
              Cancel
            </button>
            <button onClick={() => onConfirm(actualLoad, reason)} className="flex-[2] py-3 bg-black rounded-xl text-white font-bold hover:bg-slate-800 text-[14px]">
              Confirm Shortfall & Pack {actualLoad}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Unavailable State Component
function WorkbenchUnavailable({ onToggle }) {
  return (
    <div className="bg-[#f8fbf9] min-h-full pb-24">
      <div className="p-6 space-y-6">
        
        {/* Toggle Card */}
        <div className="border border-slate-200 rounded-xl p-4 bg-white shadow-sm flex items-center justify-between">
          <span className="font-bold text-slate-900 text-[17px]">Truck Available for Loading</span>
          <button onClick={onToggle} className="w-14 h-8 bg-slate-200 rounded-full relative transition-colors border border-slate-300">
            <div className="absolute left-1 top-1 w-6 h-6 bg-white rounded-full shadow-sm"></div>
          </button>
        </div>

        {/* Driver Card */}
        <div className="border border-slate-200 rounded-xl p-4 bg-white shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-600 text-[17px]">
              SP
            </div>
            <div>
              <div className="font-bold text-slate-900 text-[17px]">S. Perera <span className="text-slate-400">›</span></div>
              <div className="text-slate-500 text-[13px]">Driver · +94 77 234 5678</div>
            </div>
          </div>
          <button className="w-10 h-10 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-100">
            <Phone className="w-5 h-5" />
          </button>
        </div>

        {/* Alert Box */}
        <div className="border-2 border-[#E53E3E] rounded-xl bg-white overflow-hidden shadow-sm">
          <div className="p-5">
            <h3 className="text-[#C53030] font-extrabold text-[13px] flex items-center gap-2 mb-4 tracking-wide uppercase">
              <AlertTriangle className="w-4 h-4" /> VEHICLE OUT OF SERVICE — DISPATCH ALERTED
            </h3>
            
            <label className="block text-[13px] font-bold text-[#C53030] mb-1">Reason</label>
            <div className="relative mb-4">
              <select className="w-full appearance-none border border-slate-300 rounded-lg py-2.5 px-4 text-slate-900 font-bold bg-white focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 text-[15px]">
                <option>Engine Fault</option>
                <option>Flat Tire</option>
                <option>Accident</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
                <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
              </div>
            </div>

            <div className="text-[14px] text-slate-600 mb-5 leading-relaxed">
              Staging Status: <span className="font-bold text-slate-900">3 Orders (2,450 kg)</span> held at Bay 4. Awaiting dispatcher vehicle swap.
            </div>

            <div className="flex gap-3">
              <button className="flex-1 py-2.5 border border-slate-200 rounded-lg text-slate-700 font-bold text-[13px] hover:bg-slate-50">
                Update Dispatcher Note
              </button>
              <button className="flex-1 py-2.5 border border-slate-200 rounded-lg text-slate-700 font-bold text-[13px] hover:bg-slate-50">
                Cancel & Mark Available
              </button>
            </div>
          </div>
        </div>

        {/* Staged Cargo */}
        <div>
          <h4 className="text-[11px] font-bold text-slate-400 tracking-wider mb-3 uppercase">Staged Cargo (Frozen / Ready for Swap)</h4>
          <div className="space-y-3">
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm text-[14px] text-slate-700">
              <span className="font-bold text-slate-900">OUT-0122</span> Kandana Express — 530 kg (Pallet 1 Staged at Bay)
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm text-[14px] text-slate-700">
              <span className="font-bold text-slate-900">OUT-0091</span> Ja-Ela Central — 1,100 kg (Pallet 2 Staged at Bay)
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm text-[14px] text-slate-700">
              <span className="font-bold text-slate-900">OUT-2041</span> Wattala Retail — 820 kg (Pallet 3 Staged at Bay)
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 bg-[#f8fbf9] pt-2">
        <button className="w-full py-3.5 bg-[#E53E3E] hover:bg-red-700 text-white font-bold rounded-xl shadow-sm">
          Mark as Unavailable
        </button>
      </div>
    </div>
  );
}
