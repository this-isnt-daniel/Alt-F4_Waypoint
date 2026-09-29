import React, { useState } from 'react';
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

  // Grocery State
  const [currentUser, setCurrentUser] = useState({ name: 'A. Perera', pin: '123456' });
  const [currentOutlet, setCurrentOutlet] = useState({ id: 'NGD-014', name: 'Nugegoda Outlet' });

  // Tech State
  const [currentTechUser, setCurrentTechUser] = useState({ name: 'K. Wickrema', pin: '123456' });
  const [currentTechOutlet, setCurrentTechOutlet] = useState({ id: 'TCH-001', name: 'Waypoint Tech Hub — Colombo 03' });

  // Style State
  const [currentStyleUser, setCurrentStyleUser] = useState({ name: 'S. Jayawardena', pin: '123456' });
  const [currentStyleOutlet, setCurrentStyleOutlet] = useState({ id: 'STY-001', name: 'Waypoint Style Boutique — Colombo 07' });

  // ── Driver Portal ──
  if (portal === 'driver') {
    return <DriverApp />;
  }

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
      return <LoaderOverview onLogout={() => setCurrentPage('login')} />;
    }
    return <LoaderLogin onLogin={() => setCurrentPage('overview')} />;
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
}
