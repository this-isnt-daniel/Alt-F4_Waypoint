import React, { useState } from 'react';
import DispatcherLogin from './pages/dispatcher/DispatcherLogin';
import DispatcherRoster from './pages/dispatcher/DispatcherRoster';
import StoreManagerLogin from './pages/storemanager/StoreManagerLogin';
import StoreManagerOverview from './pages/storemanager/StoreManagerOverview';
import LoaderLogin from './pages/loader/LoaderLogin';
import LoaderOverview from './pages/loader/LoaderOverview';

export default function App() {
  const getInitialPortal = () => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('portal')) {
        return params.get('portal');
      }
    }
    return 'dispatcher';
  };

  const [portal, setPortal] = useState(getInitialPortal);
  const [currentPage, setCurrentPage] = useState('login');

  if (portal === 'storemanager') {
    if (currentPage === 'overview') {
      return <StoreManagerOverview onLogout={() => setCurrentPage('login')} />;
    }
    return <StoreManagerLogin onLogin={() => setCurrentPage('overview')} />;
  }

  // Loader Portal
  if (portal === 'loader') {
    if (currentPage === 'overview') {
      return <LoaderOverview onLogout={() => setCurrentPage('login')} />;
    }
    return <LoaderLogin onLogin={() => setCurrentPage('overview')} />;
  }

  // Dispatcher Portal
  if (currentPage === 'overview') {
    return <DispatcherRoster onLogout={() => setCurrentPage('login')} />;
  }

  return (
    <DispatcherLogin onLogin={() => setCurrentPage('overview')} />
  );
}

