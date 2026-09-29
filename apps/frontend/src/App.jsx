import React, { useState, useEffect } from 'react';
import StoreManagerLogin from './pages/storemanager/StoreManagerLogin';
import StoreManagerOverview from './pages/storemanager/StoreManagerOverview';
import DriverApp from '../driver/src/DriverApp';

export default function App() {
  // Read portal from URL params e.g. ?portal=driver or ?portal=storemanager
  const getInitialPortal = () => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const portalParam = params.get('portal');
      if (portalParam === 'driver') return 'driver';
      if (portalParam === 'storemanager' || portalParam === 'storemanager-overview') return 'storemanager-overview';
      if (portalParam === 'storemanager-login') return 'storemanager-login';
    }
    return 'driver';
  };

  const [currentPortal, setCurrentPortal] = useState(getInitialPortal);

  // Sync to URL when portal changes
  const switchPortal = (newPortal) => {
    setCurrentPortal(newPortal);
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('portal', newPortal.startsWith('storemanager') ? 'storemanager' : newPortal);
      window.history.replaceState({}, '', url.toString());
    }
  };

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPortal(getInitialPortal());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  return (
    <div className="relative min-h-screen">
      {/* Portal Switcher Floating Bar */}
      <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2 bg-[#0B3D33] text-white p-1.5 rounded-full shadow-2xl border border-[#0F9D6C]/40 text-xs select-none">
        <span className="px-2 font-bold text-[#A7D4C0]">Portal:</span>
        <button
          type="button"
          onClick={() => switchPortal('driver')}
          className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer ${
            currentPortal === 'driver'
              ? 'bg-[#0F9D6C] text-white'
              : 'text-gray-300 hover:text-white'
          }`}
        >
          Driver
        </button>
        <button
          type="button"
          onClick={() => switchPortal(currentPortal.startsWith('storemanager') ? currentPortal : 'storemanager-overview')}
          className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer ${
            currentPortal.startsWith('storemanager')
              ? 'bg-[#0F9D6C] text-white'
              : 'text-gray-300 hover:text-white'
          }`}
        >
          Store Manager
        </button>
      </div>

      {/* Driver Portal */}
      {currentPortal === 'driver' && (
        <DriverApp onBack={() => switchPortal('storemanager-overview')} />
      )}

      {/* Store Manager Portal */}
      {currentPortal === 'storemanager-login' && (
        <StoreManagerLogin onLogin={() => switchPortal('storemanager-overview')} />
      )}
      {currentPortal === 'storemanager-overview' && (
        <StoreManagerOverview
          onLogout={() => switchPortal('storemanager-login')}
          onSwitchToDriver={() => switchPortal('driver')}
        />
      )}
    </div>
  );
}
