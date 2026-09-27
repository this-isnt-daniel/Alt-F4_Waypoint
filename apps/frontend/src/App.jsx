import React, { useState } from 'react';
import StoreManagerLogin from './pages/storemanager/StoreManagerLogin';
import StoreManagerOverview from './pages/storemanager/StoreManagerOverview';

export default function App() {
  const [currentPage, setCurrentPage] = useState('login');

  if (currentPage === 'overview') {
    return <StoreManagerOverview onLogout={() => setCurrentPage('login')} />;
  }

  return <StoreManagerLogin onLogin={() => setCurrentPage('overview')} />;
}
