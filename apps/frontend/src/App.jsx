import React, { useState, useEffect } from 'react';
import DispatcherLogin from './pages/dispatcher/DispatcherLogin';
import DispatcherRoster from './pages/dispatcher/DispatcherRoster';
import StoreManagerLogin from './pages/storemanager/StoreManagerLogin';
import StoreManagerOverview from './pages/storemanager/StoreManagerOverview';
import StoreManagerTechLogin from './pages/storemanager_tech/StoreManagerLogin';
import StoreManagerTechOverview from './pages/storemanager_tech/StoreManagerOverview';
import StoreManagerStyleLogin from './pages/storemanager_style/StoreManagerLogin';
import StoreManagerStyleOverview from './pages/storemanager_style/StoreManagerOverview';
import LoaderLogin from './pages/loader/LoaderLogin';
import LoaderOverview from './pages/loader/LoaderOverview';
import CentralLogin from './pages/CentralLogin';
import { DriverApp } from './driver/DriverApp';
import { ThemeProvider } from './theme/ThemeProvider';
import { ThemeToggle } from './theme/ThemeToggle';

const PORTAL_TITLES = {
  dispatcher: 'Waypoint - Dispatcher Portal',
  loader: 'Waypoint - Loader Portal',
  driver: 'Waypoint - Driver Portal',
  grocery: 'Waypoint - Store Manager (Grocery)',
  'storemanager': 'Waypoint - Store Manager (Grocery)',
  'storemanager-fresh': 'Waypoint - Store Manager (Grocery)',
  tech: 'Waypoint - Store Manager (Tech)',
  'storemanager-tech': 'Waypoint - Store Manager (Tech)',
  'storemanager_tech': 'Waypoint - Store Manager (Tech)',
  style: 'Waypoint - Store Manager (Style)',
  'storemanager-style': 'Waypoint - Store Manager (Style)',
  'storemanager_style': 'Waypoint - Store Manager (Style)',
  central: 'Waypoint',
};

export default function App() {
  const getInitialPortal = () => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('portal')) {
        return params.get('portal').toLowerCase();
      }
    }
    return 'central';
  };

  const [portal, setPortal] = useState(getInitialPortal);
  const [currentPage, setCurrentPage] = useState('login');

  useEffect(() => {
    document.title = PORTAL_TITLES[portal] ?? 'Waypoint';
  }, [portal]);

  // Remove driver theme attribute when leaving driver portal
  useEffect(() => {
    if (portal !== 'driver') {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [portal]);

  // ── Driver Portal ── (handles its own ThemeProvider for dark mode theming)
  if (portal === 'driver') {
    return (
      <ThemeProvider>
        <DriverApp />
      </ThemeProvider>
    );
  }

  // Grocery State
  const [currentUser, setCurrentUser] = useState({ name: 'A. Perera', pin: '123456' });
  const [currentOutlet, setCurrentOutlet] = useState({ id: 'NGD-014', name: 'Nugegoda Outlet' });

  // Tech State
  const [currentTechUser, setCurrentTechUser] = useState({ name: 'K. Wickrema', pin: '123456' });
  const [currentTechOutlet, setCurrentTechOutlet] = useState({ id: 'TCH-001', name: 'Waypoint Tech Hub — Colombo 03' });

  // Style State
  const [currentStyleUser, setCurrentStyleUser] = useState({ name: 'S. Jayawardena', pin: '123456' });
  const [currentStyleOutlet, setCurrentStyleOutlet] = useState({ id: 'STY-001', name: 'Waypoint Style Boutique — Colombo 07' });

  // Loader mock state
  const [currentLoader, setCurrentLoader] = useState({ name: 'J. Silva', depot: 'peliyagoda', bay: 'Bay Lead A' });

  const renderPortal = () => {
    // ── Portal 1: Store Manager (Grocery & Fresh) ──
    if (portal === 'storemanager' || portal === 'grocery' || portal === 'storemanager-fresh' || portal === 'store-manager') {
      if (currentPage === 'overview') {
        return (
          <StoreManagerOverview
            user={currentUser}
            outlet={currentOutlet}
            onLogout={() => setCurrentPage('login')}
          />
        );
      }
      return (
        <StoreManagerLogin
          onLogin={(manager, outlet) => {
            setCurrentUser(manager);
            setCurrentOutlet(outlet);
            setCurrentPage('overview');
          }}
        />
      );
    }

    // ── Portal 2: Store Manager Tech ──
    if (portal === 'storemanager-tech' || portal === 'storemanager_tech' || portal === 'tech') {
      if (currentPage === 'overview') {
        return (
          <StoreManagerTechOverview
            user={currentTechUser}
            outlet={currentTechOutlet}
            onLogout={() => setCurrentPage('login')}
          />
        );
      }
      return (
        <StoreManagerTechLogin
          onLogin={(manager, outlet) => {
            setCurrentTechUser(manager);
            setCurrentTechOutlet(outlet);
            setCurrentPage('overview');
          }}
        />
      );
    }

    // ── Portal 3: Waypoint Style (Store Manager Style) ──
    if (portal === 'storemanager-style' || portal === 'storemanager_style' || portal === 'style') {
      if (currentPage === 'overview') {
        return (
          <StoreManagerStyleOverview
            user={currentStyleUser}
            outlet={currentStyleOutlet}
            onLogout={() => setCurrentPage('login')}
          />
        );
      }
      return (
        <StoreManagerStyleLogin
          onLogin={(manager, outlet) => {
            setCurrentStyleUser(manager);
            setCurrentStyleOutlet(outlet);
            setCurrentPage('overview');
          }}
        />
      );
    }

    // ── Portal 4: Loader Portal ──
    if (portal === 'loader') {
      if (currentPage === 'overview') {
        return <LoaderOverview user={currentLoader} onLogout={() => setCurrentPage('login')} />;
      }
      return (
        <LoaderLogin
          onLogin={(loader) => {
            setCurrentLoader(loader);
            setCurrentPage('overview');
          }}
        />
      );
    }

    // ── Portal 5: Dispatcher Portal ──
    if (portal === 'dispatcher') {
      if (currentPage === 'overview') {
        return <DispatcherRoster onLogout={() => setCurrentPage('login')} />;
      }
      return <DispatcherLogin onLogin={() => setCurrentPage('overview')} />;
    }

    // ── Default / Central ──
    return <CentralLogin />;
  };

  return (
    <ThemeProvider>
      <div className="relative min-h-screen bg-canvas text-ink transition-colors duration-200">
        {renderPortal()}
        <aside className="fixed bottom-4 right-4 z-50">
          <ThemeToggle />
        </aside>
      </div>
    </ThemeProvider>
  );
}
