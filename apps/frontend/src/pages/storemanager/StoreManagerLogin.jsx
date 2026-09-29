import React, { useState, useEffect } from 'react';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import { OUTLETS, MANAGERS } from './data/auth';

export default function StoreManagerLogin({ onLogin }) {
  const [storeCode, setStoreCode] = useState('');
  const [selectedOutlet, setSelectedOutlet] = useState(null);
  const [availableManagers, setAvailableManagers] = useState([]);
  
  const [selectedManager, setSelectedManager] = useState(null);
  const [pin, setPin] = useState('');
  
  const [error, setError] = useState(null);

  // 1. Handle Store Code Input
  useEffect(() => {
    if (storeCode.length >= 7) { // e.g. NGD-014
      const outlet = OUTLETS.find(o => o.id === storeCode);
      if (outlet) {
        setSelectedOutlet(outlet);
        setAvailableManagers(MANAGERS.filter(m => m.outletId === outlet.id));
        setError(null);
      } else {
        setSelectedOutlet(null);
        setAvailableManagers([]);
        setError('Store not found.');
      }
    } else {
      setSelectedOutlet(null);
      setAvailableManagers([]);
      setError(null);
    }
  }, [storeCode]);

  const handleStoreCodeChange = (e) => {
    // Format uppercase automatically
    setStoreCode(e.target.value.toUpperCase());
    setError(null);
  };

  const handleChangeStore = () => {
    setStoreCode('');
    setSelectedOutlet(null);
    setAvailableManagers([]);
    setSelectedManager(null);
    setPin('');
    setError(null);
  };

  const handleSelectManager = (manager) => {
    setSelectedManager(manager);
    setPin('');
    setError(null);
  };

  const handleChangeManager = () => {
    setSelectedManager(null);
    setPin('');
    setError(null);
  };

  const handlePinChange = (e) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 6);
    setPin(val);
    setError(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedManager) return;
    
    if (pin === selectedManager.pin) {
      onLogin(selectedManager, selectedOutlet); // Success
    } else {
      setError('Incorrect PIN. Please try again.');
      setPin(''); // Reset PIN on failure
    }
  };

  return (
    <main className="min-h-screen w-full bg-white flex flex-col items-center justify-center px-4 select-none">
      <div className="flex flex-col items-center max-w-sm w-full">
        {/* Logo and Brand Heading */}
        <div className="flex items-center justify-center gap-3.5 mb-5">
          <img
            src={waypointLogo}
            alt="Waypoint Logo"
            className="w-12 h-12 object-contain rounded-xl shadow-sm"
          />
          <h1
            className="text-[48px] font-extrabold text-[#0B2019] tracking-tight leading-none"
            style={{ fontFamily: "'Inter', sans-serif" }}
          >
            Waypoint
          </h1>
        </div>

        {/* Portal Pill Badge */}
        <div className="mb-8">
          <span className="inline-flex items-center px-4 py-1.5 rounded-full text-[11px] font-semibold tracking-[0.16em] uppercase text-[#256149] bg-[#EBF6F0] border border-[#DCF0E5]">
            Store Manager Portal
          </span>
        </div>

        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-6">
          {/* STEP 1: Store Code */}
          {!selectedOutlet ? (
            <div className="w-full">
              <label className="block text-[13px] font-semibold text-slate-700 mb-1.5">
                Store Code
              </label>
              <input
                type="text"
                value={storeCode}
                onChange={handleStoreCodeChange}
                placeholder="e.g. NGD-014"
                className="w-full h-11 px-3 border border-slate-300 rounded-lg text-[14px] focus:outline-none focus:ring-2 focus:ring-[#059669] focus:border-transparent transition-all"
                autoFocus
              />
              {error && (
                <p className="text-[12px] text-red-600 mt-1.5 font-medium">{error}</p>
              )}
            </div>
          ) : (
            <div className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Store</p>
                <p className="text-[14px] font-bold text-slate-900">{selectedOutlet.name}</p>
              </div>
              <button
                type="button"
                onClick={handleChangeStore}
                className="text-[12px] font-semibold text-brand-600 hover:text-brand-800"
              >
                Change
              </button>
            </div>
          )}

          {/* STEP 2: Manager Selection */}
          {selectedOutlet && !selectedManager && (
            <div className="w-full animate-in fade-in slide-in-from-bottom-2 duration-200">
              <label className="block text-[13px] font-semibold text-slate-700 mb-2">
                Managers at this store
              </label>
              <div className="flex flex-col gap-2">
                {availableManagers.map(manager => (
                  <button
                    key={manager.id}
                    type="button"
                    onClick={() => handleSelectManager(manager)}
                    className="w-full text-left px-4 py-3 border border-slate-200 rounded-lg hover:border-brand-300 hover:bg-brand-50 transition-colors flex items-center gap-3"
                  >
                    <div className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center shrink-0">
                      {/* Empty circle for unselected */}
                    </div>
                    <span className="text-[14px] font-medium text-slate-800">{manager.name}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* STEP 3: PIN Input */}
          {selectedManager && (
            <div className="w-full animate-in fade-in zoom-in-95 duration-200">
              <div className="w-full bg-brand-50 border border-brand-200 rounded-lg p-3 flex items-center justify-between mb-5">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-brand-600" />
                  <div>
                    <p className="text-[11px] font-bold text-brand-700 uppercase tracking-wide">Selected Manager</p>
                    <p className="text-[14px] font-bold text-brand-900">{selectedManager.name}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleChangeManager}
                  className="text-[12px] font-semibold text-brand-600 hover:text-brand-800"
                >
                  Change
                </button>
              </div>

              <div className="w-full">
                <label className="block text-[13px] font-semibold text-slate-700 mb-1.5 text-center">
                  Enter PIN
                </label>
                <input
                  type="password"
                  inputMode="numeric"
                  maxLength={6}
                  value={pin}
                  onChange={handlePinChange}
                  placeholder="• • • • • •"
                  className="w-full h-12 text-center tracking-[0.5em] text-[20px] border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#059669] focus:border-transparent transition-all"
                  autoFocus
                />
                {error && (
                  <p className="text-[12px] text-red-600 mt-2 font-medium text-center">{error}</p>
                )}
              </div>
            </div>
          )}

          {/* Submit Action */}
          <button
            type="submit"
            disabled={!selectedManager || pin.length < 6}
            aria-label="Log in to Store Manager Portal"
            className="w-[230px] mx-auto h-11 bg-[#059669] hover:bg-[#047857] active:bg-[#065f46] text-white text-sm font-medium rounded-lg transition-all duration-150 ease-in-out shadow-sm hover:shadow flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-[#059669] focus-visible:ring-offset-2 mt-2"
          >
            Sign In
          </button>
        </form>
      </div>
    </main>
  );
}
