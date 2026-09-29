import React, { useState, useEffect } from 'react';
import StoreManagerLogin from './pages/storemanager/StoreManagerLogin';
import StoreManagerOverview from './pages/storemanager/StoreManagerOverview';
import DriverApp from '../driver/src/DriverApp';

export default function App() {
  // Check URL params (?portal=driver vs default store manager)
  const getInitialState = () => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const portalParam = params.get('portal');
      if (portalParam === 'driver') {
        return { isDriver: true, storePageState: 'login' };
      }
    }
    // Default flow: Store Manager Login first
    return { isDriver: false, storePageState: 'login' };
  };

  const [portalState, setPortalState] = useState(getInitialState);

  useEffect(() => {
    const handleUrlChange = () => {
      setPortalState(getInitialState());
    };
    window.addEventListener('popstate', handleUrlChange);
    return () => window.removeEventListener('popstate', handleUrlChange);
  }, []);

  // When ?portal=driver is in URL, render Driver Portal directly without extraneous switcher buttons
  if (portalState.isDriver) {
    return <DriverApp />;
  }

  // Default flow: Store Manager Login -> Store Manager Overview
  if (portalState.storePageState === 'overview') {
    return (
      <StoreManagerOverview
        onLogout={() => setPortalState({ isDriver: false, storePageState: 'login' })}
      />
    );
  }

  return (
    <StoreManagerLogin
      onLogin={() => setPortalState({ isDriver: false, storePageState: 'overview' })}
    />
  );
}
