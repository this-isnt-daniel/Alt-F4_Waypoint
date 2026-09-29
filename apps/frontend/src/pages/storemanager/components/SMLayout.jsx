import React, { useState } from 'react';
import waypointLogo from '../../../assets/icons/waypoint_logo.png';
import { Bell, ChevronDown, LogOut, Truck, KeyRound, Check } from 'lucide-react';
import DeliveryOtpModal from './DeliveryOtpModal';

const NAV_TABS = [
  { id: 'overview',  label: 'Overview'              },
  { id: 'order',     label: 'Place Order'            },
  { id: 'progress',  label: 'Orders in Progress'     },
  { id: 'receipts',  label: 'Receipts & Deferrals'  },
];

/**
 * SMLayout
 * Shared header + navigation shell for the Store Manager portal.
 * Desktop: full top nav bar with logo + tabs + right actions.
 * Mobile: compact header + scrollable tab bar below.
 */
export default function SMLayout({ 
  activeTab, 
  setActiveTab, 
  onLogout, 
  children, 
  basketCount = 0, 
  user, 
  outlet,
  deliveryArrived = true,
  deliveryOtp = '482 910',
  showOtpModal = false,
  setShowOtpModal,
  onConfirmDelivery
}) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showChangePin, setShowChangePin] = useState(false);

  return (
    <div className="h-[100dvh] bg-[#F8FAF9] font-sans antialiased text-slate-900 flex flex-col relative">

      {showChangePin && (
        <ChangePinModal 
          user={user} 
          onClose={() => setShowChangePin(false)} 
        />
      )}

      {/* ── Desktop Header ── */}
      <header className="hidden md:block sticky top-0 z-30 bg-white border-b border-slate-200">
        <div className="max-w-screen-xl mx-auto px-6 h-14 flex items-center justify-between gap-6">

          {/* Brand */}
          <div className="flex items-center gap-2.5 shrink-0">
            <img src={waypointLogo} alt="Waypoint Fresh" className="w-6 h-6 object-contain rounded-md" />
            <span className="text-[17px] font-bold text-[#0B2019] tracking-tight">Waypoint Fresh</span>
          </div>

          {/* Tabs */}
          <nav className="flex items-center gap-0.5 flex-1" aria-label="Store Manager Navigation">
            {NAV_TABS.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'bg-brand-50 text-brand-700 font-semibold'
                      : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                  }`}
                >
                  {tab.label}
                  {tab.id === 'order' && basketCount > 0 && (
                    <span className="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded-full bg-brand-600 text-white text-[10px] font-bold">
                      {basketCount}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right actions */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              className="h-8 px-3 rounded-full border border-slate-200 text-[13px] text-slate-600 font-medium flex items-center gap-1.5 hover:border-slate-300 transition-colors"
            >
              Nugegoda <ChevronDown size={12} className="text-slate-400" />
            </button>

            {/* Notification Bell with Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-800 hover:border-slate-300 transition-colors cursor-pointer"
                title="Notifications"
              >
                <Bell size={15} strokeWidth={2} />
                {deliveryArrived && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-emerald-500 rounded-full ring-2 ring-white animate-pulse" />
                )}
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 sm:w-88 bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[13px] font-bold text-slate-900">Notifications</span>
                      {deliveryArrived && (
                        <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          1 New
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowNotifications(false)}
                      className="text-[11px] font-semibold text-slate-400 hover:text-slate-600 cursor-pointer"
                    >
                      Close
                    </button>
                  </div>

                  <div className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
                    {deliveryArrived ? (
                      <div className="p-3">
                        <div className="bg-[#FFFFFF] border border-[#DCEEE1] rounded-2xl p-3.5" style={{ fontFamily: 'Inter, sans-serif' }}>
                          <div className="flex items-start gap-3">
                            <div className="w-[34px] h-[34px] rounded-[9px] bg-[#2EA85C] text-white flex items-center justify-center shrink-0">
                              <Truck size={18} strokeWidth={2.5} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#E7F6EC] text-[#2EA85C] border border-[#BFE6CC]">
                                  Arrived
                                </span>
                                <span className="text-[13px] font-semibold text-[#152B1E] truncate">
                                  Order ORD-10492
                                </span>
                              </div>
                              <p className="text-[12px] font-medium text-[#5E7365] leading-snug mb-3">
                                Vehicle VEH402 is at the loading bay. Driver Kamal Perera is waiting for confirmation OTP.
                              </p>
                              <div className="flex justify-end">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setShowNotifications(false);
                                    setShowOtpModal?.(true);
                                  }}
                                  className="px-4 py-1.5 bg-white text-[#2EA85C] text-[12px] font-semibold rounded-full border border-[#2EA85C] hover:bg-[#E7F6EC] transition-colors cursor-pointer"
                                >
                                  Provide OTP
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 text-center text-slate-400 text-[12px]">
                        No active arrival alerts
                      </div>
                    )}

                    <div className="p-3.5 opacity-70">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-500 flex items-center justify-center shrink-0 mt-0.5">
                          <Check size={16} />
                        </div>
                        <div>
                          <p className="text-[12px] font-semibold text-slate-800">Order ORD-10491 Verified</p>
                          <p className="text-[11px] text-slate-500 mt-0.5">All items received in good condition · Yesterday</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="relative">
              <button
                type="button"
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="w-8 h-8 rounded-full bg-brand-50 border border-brand-200 text-brand-700 text-[11px] font-bold flex items-center justify-center hover:bg-brand-100 transition-colors"
              >
                {user ? user.name.split(' ').map(n => n[0]).join('').substring(0,2) : 'DP'}
              </button>
              {showUserMenu && (
                <div className="absolute right-0 mt-1.5 w-44 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-50">
                  <div className="px-3 py-2.5 border-b border-slate-100">
                    <p className="text-[13px] font-semibold text-slate-900">Store Manager</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">{outlet?.name?.split(' ')[0] ?? 'Nugegoda'} · {outlet?.id ?? 'OUT-0043'}</p>
                  </div>
                  <button
                    onClick={() => { setShowUserMenu(false); setShowChangePin(true); }}
                    className="w-full text-left px-3 py-2 text-[12px] text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    Change PIN
                  </button>
                  <button
                    onClick={() => { setShowUserMenu(false); onLogout?.(); }}
                    className="w-full text-left px-3 py-2 text-[12px] text-red-500 hover:bg-red-50 flex items-center gap-2 transition-colors border-t border-slate-100"
                  >
                    <LogOut size={13} /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* ── Mobile Header ── */}
      <header className="md:hidden sticky top-0 z-30 bg-white border-b border-slate-200">
        <div className="px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src={waypointLogo} alt="Waypoint Fresh" className="w-7 h-7 object-contain rounded-md" />
            <span className="text-[17px] font-bold text-[#0B2019] tracking-tight">Waypoint Fresh</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="h-7 px-2.5 rounded-full border border-slate-200 text-[12px] text-slate-600 font-medium flex items-center gap-1"
            >
              Nugegoda <ChevronDown size={11} className="text-slate-400" />
            </button>
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-500"
              >
                <Bell size={15} strokeWidth={2} />
                {deliveryArrived && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-emerald-500 rounded-full ring-2 ring-white animate-pulse" />
                )}
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                    <span className="text-[13px] font-bold text-slate-900">Notifications</span>
                    <button
                      type="button"
                      onClick={() => setShowNotifications(false)}
                      className="text-[11px] font-semibold text-slate-400 hover:text-slate-600"
                    >
                      Close
                    </button>
                  </div>
                  <div className="p-3">
                    {deliveryArrived ? (
                      <div className="bg-[#FFFFFF] border border-[#DCEEE1] rounded-2xl p-3" style={{ fontFamily: 'Inter, sans-serif' }}>
                        <div className="flex items-start gap-2.5">
                          <div className="w-[32px] h-[32px] rounded-[8px] bg-[#2EA85C] text-white flex items-center justify-center shrink-0">
                            <Truck size={16} strokeWidth={2.5} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 mb-1">
                              <span className="px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#E7F6EC] text-[#2EA85C] border border-[#BFE6CC]">
                                Arrived
                              </span>
                              <span className="text-[12px] font-semibold text-[#152B1E] truncate">
                                Order ORD-10492
                              </span>
                            </div>
                            <p className="text-[11px] font-medium text-[#5E7365] leading-snug mb-2.5">
                              Vehicle VEH402 is at the loading bay. Driver waiting for OTP.
                            </p>
                            <div className="flex justify-end">
                              <button
                                type="button"
                                onClick={() => {
                                  setShowNotifications(false);
                                  setShowOtpModal?.(true);
                                }}
                                className="px-3.5 py-1.5 bg-white text-[#2EA85C] text-[11px] font-semibold rounded-full border border-[#2EA85C] hover:bg-[#E7F6EC] transition-colors cursor-pointer"
                              >
                                Provide OTP
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-center text-[12px] text-slate-400 py-2">No active notifications</p>
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="w-8 h-8 rounded-full bg-brand-50 border border-brand-200 text-brand-700 text-[11px] font-bold flex items-center justify-center"
              >
                {user ? user.name.split(' ').map(n => n[0]).join('').substring(0,2) : 'DP'}
              </button>
              {showUserMenu && (
                <div className="absolute right-0 mt-1.5 w-40 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-50">
                  <div className="px-3 py-2.5 border-b border-slate-100">
                    <p className="text-[12px] font-semibold text-slate-900">Store Manager</p>
                    <p className="text-[11px] text-slate-400">{outlet?.id ?? 'OUT-0043'}</p>
                  </div>
                  <button
                    onClick={() => { setShowUserMenu(false); setShowChangePin(true); }}
                    className="w-full text-left px-3 py-2 text-[12px] text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    Change PIN
                  </button>
                  <button
                    onClick={() => { setShowUserMenu(false); onLogout?.(); }}
                    className="w-full text-left px-3 py-2 text-[12px] text-red-500 hover:bg-red-50 flex items-center gap-2 border-t border-slate-100"
                  >
                    <LogOut size={12} /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Mobile tab bar */}
        <nav className="flex border-t border-slate-100 overflow-x-auto scrollbar-none" aria-label="Store Manager Navigation">
          {NAV_TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`shrink-0 px-4 py-2.5 text-[12px] font-semibold border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                  isActive
                    ? 'border-brand-600 text-brand-700'
                    : 'border-transparent text-slate-400 hover:text-slate-600'
                }`}
              >
                {tab.label}
                {tab.id === 'order' && basketCount > 0 && (
                  <span className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-brand-600 text-white text-[10px] font-bold">
                    {basketCount}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </header>

      {/* ── Page Content ── */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>

      {/* ── Delivery OTP Handover Modal ── */}
      <DeliveryOtpModal
        isOpen={showOtpModal}
        onClose={() => setShowOtpModal?.(false)}
        otp={deliveryOtp}
        outletName={outlet?.name ?? 'Nugegoda Outlet'}
        onConfirmHandover={onConfirmDelivery}
      />
    </div>
  );
}

function ChangePinModal({ user, onClose }) {
  const [currentPin, setCurrentPin] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  
  const [currentPinError, setCurrentPinError] = useState(null);
  const [newPinError, setNewPinError] = useState(null);
  const [confirmPinError, setConfirmPinError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setCurrentPinError(null);
    setNewPinError(null);
    setConfirmPinError(null);

    let isValid = true;
    
    // Mock user.pin (in real app, this would be a backend check)
    // If we're mocking, we can either pass the auth object, or simulate:
    // Just for the sake of the mock, assume we have user.pin if passed, else just mock check it
    if (user && user.pin !== currentPin) {
      setCurrentPinError('Incorrect current PIN');
      isValid = false;
    }

    if (newPin.length !== 6) {
      setNewPinError('PIN must contain 6 digits');
      isValid = false;
    }

    if (newPin === currentPin) {
      setNewPinError('New PIN must be different from current PIN');
      isValid = false;
    }

    if (newPin !== confirmPin) {
      setConfirmPinError('PINs do not match');
      isValid = false;
    }

    if (isValid) {
      // Success (update mock state if needed, but for now just show success message)
      if (user) user.pin = newPin; // Mutating mock data directly just for prototype
      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 1500);
    }
  };

  const handlePinInput = (val, setter) => {
    setter(val.replace(/\D/g, '').slice(0, 6));
  };

  return (
    <div className="absolute inset-0 z-[100] bg-slate-900/40 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-[340px] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="px-5 pt-5 pb-4 border-b border-slate-100">
          <h2 className="text-[15px] font-bold text-slate-900 tracking-wide">CHANGE PIN</h2>
        </div>
        
        {success ? (
          <div className="px-5 py-8 flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 bg-brand-100 text-brand-600 rounded-full flex items-center justify-center mb-3">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-[14px] font-bold text-slate-800">PIN changed successfully.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="px-5 py-5 space-y-5">
              <div>
                <label className="block text-[12px] font-semibold text-slate-700 mb-1.5">
                  Current PIN
                </label>
                <input
                  type="password"
                  inputMode="numeric"
                  value={currentPin}
                  onChange={(e) => handlePinInput(e.target.value, setCurrentPin)}
                  placeholder="• • • • • •"
                  className={`w-full h-10 px-3 text-[18px] tracking-[0.2em] border rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all ${
                    currentPinError ? 'border-red-300 ring-1 ring-red-300' : 'border-slate-300'
                  }`}
                  autoFocus
                />
                {currentPinError && <p className="text-[11px] text-red-500 mt-1 font-medium">{currentPinError}</p>}
              </div>

              <div>
                <label className="block text-[12px] font-semibold text-slate-700 mb-1.5">
                  New PIN
                </label>
                <input
                  type="password"
                  inputMode="numeric"
                  value={newPin}
                  onChange={(e) => handlePinInput(e.target.value, setNewPin)}
                  placeholder="• • • • • •"
                  className={`w-full h-10 px-3 text-[18px] tracking-[0.2em] border rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all ${
                    newPinError ? 'border-red-300 ring-1 ring-red-300' : 'border-slate-300'
                  }`}
                />
                {newPinError && <p className="text-[11px] text-red-500 mt-1 font-medium">{newPinError}</p>}
              </div>

              <div>
                <label className="block text-[12px] font-semibold text-slate-700 mb-1.5">
                  Confirm new PIN
                </label>
                <input
                  type="password"
                  inputMode="numeric"
                  value={confirmPin}
                  onChange={(e) => handlePinInput(e.target.value, setConfirmPin)}
                  placeholder="• • • • • •"
                  className={`w-full h-10 px-3 text-[18px] tracking-[0.2em] border rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all ${
                    confirmPinError ? 'border-red-300 ring-1 ring-red-300' : 'border-slate-300'
                  }`}
                />
                {confirmPinError && <p className="text-[11px] text-red-500 mt-1 font-medium">{confirmPinError}</p>}
              </div>
            </div>
            
            <div className="px-5 py-4 bg-slate-50 border-t border-slate-100 flex items-center gap-3">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-2 text-[13px] font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-200/50 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!currentPin || !newPin || !confirmPin}
                className="flex-1 py-2 text-[13px] font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Change PIN
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
