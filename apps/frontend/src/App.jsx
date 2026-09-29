import React, { useState, useEffect } from 'react';
import DispatcherLogin from './pages/dispatcher/DispatcherLogin';
import DispatcherRoster from './pages/dispatcher/DispatcherRoster';
import StoreManagerLogin from './pages/storemanager/StoreManagerLogin';
import StoreManagerOverview from './pages/storemanager/StoreManagerOverview';
import LoaderLogin from './pages/loader/LoaderLogin';
import LoaderOverview from './pages/loader/LoaderOverview';
import { DriverApp } from './driver/DriverApp';
import { ThemeProvider } from './theme/ThemeProvider';

export default function App() {
  const getInitialPortal = () => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const p = params.get('portal');
      if (p) {
        if (p === 'store-manager' || p === 'storemanager') return 'storemanager';
        if (p === 'driver') return 'driver';
        if (p === 'loader') return 'loader';
        if (p === 'dispatcher') return 'dispatcher';
      }
    }
    return 'dispatcher';
  };

  const [portal, setPortal] = useState(getInitialPortal);
  const [currentPage, setCurrentPage] = useState('login');
  const [showRoleSwitcher, setShowRoleSwitcher] = useState(true);

  // Synchronize document data-theme when switching between portals
  useEffect(() => {
    if (portal !== 'driver') {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [portal]);

  const switchPortal = (newPortal) => {
    setPortal(newPortal);
    setCurrentPage('overview');
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('portal', newPortal);
      window.history.pushState({}, '', url.toString());
    }
  };

  const renderCurrentPortal = () => {
    if (portal === 'driver') {
      return (
        <ThemeProvider>
          <DriverApp />
        </ThemeProvider>
      );
    }

    if (portal === 'storemanager') {
      if (currentPage === 'overview') {
        return <StoreManagerOverview onLogout={() => setCurrentPage('login')} />;
      }
      return <StoreManagerLogin onLogin={() => setCurrentPage('overview')} />;
    }

    if (portal === 'loader') {
      if (currentPage === 'overview') {
        return <LoaderOverview onLogout={() => setCurrentPage('login')} />;
      }
      return <LoaderLogin onLogin={() => setCurrentPage('overview')} />;
    }

    // Default: Dispatcher Portal
    if (currentPage === 'overview') {
      return <DispatcherRoster onLogout={() => setCurrentPage('login')} />;
    }

    return <DispatcherLogin onLogin={() => setCurrentPage('overview')} />;
  };

  return (
    <div className="relative min-h-screen">
      {renderCurrentPortal()}

      {/* Floating Role Switcher Dock for Quick Cross-Role Evaluation */}
      <aside 
        aria-label="Role Switcher Dock" 
        className="fixed bottom-3 right-3 sm:bottom-4 sm:right-4 z-50 flex flex-col items-end gap-1.5"
      >
        {showRoleSwitcher && (
          <div className="bg-slate-900/95 backdrop-blur-md text-white rounded-2xl shadow-2xl p-2 border border-slate-700/60 flex items-center gap-1.5 animate-in fade-in slide-in-from-bottom-2 duration-150">
            <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase px-2">Role:</span>
            {[
              { id: 'dispatcher', label: 'Dispatcher', icon: '📊' },
              { id: 'loader', label: 'Loader', icon: '📦' },
              { id: 'driver', label: 'Driver', icon: '🚛' },
              { id: 'storemanager', label: 'Store Manager', icon: '🏪' },
            ].map((r) => {
              const active = portal === r.id;
              return (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => switchPortal(r.id)}
                  className={`px-2.5 py-1 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                    active
                      ? 'bg-emerald-500 text-slate-950 font-bold shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <span>{r.icon}</span>
                  <span>{r.label}</span>
                </button>
              );
            })}
          </div>
        )}

        <button
          type="button"
          onClick={() => setShowRoleSwitcher((prev) => !prev)}
          className="bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white text-[11px] font-medium px-2 py-0.5 rounded-full border border-slate-700/50 shadow-sm transition"
          title="Toggle Role Dock"
        >
          {showRoleSwitcher ? 'hide role dock' : '⚡ switch role'}
        </button>
      </aside>
    </div>
  );
}


