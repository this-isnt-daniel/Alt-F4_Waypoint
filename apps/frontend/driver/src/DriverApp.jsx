import React, { useState } from 'react';
import DriverHeader from './DriverHeader';
import DriverAuth from './DriverAuth';
import Screen01Login from './Screen01Login';
import Screen02Runs from './Screen02Runs';
import Screen03Checklist from './Screen03Checklist';
import Screen04Route from './Screen04Route';
import Screen05StopDetail from './Screen05StopDetail';
import Screen06POD from './Screen06POD';
import Screen07Problem from './Screen07Problem';
import Screen08Offline from './Screen08Offline';
import Screen09RouteChange from './Screen09RouteChange';
import Screen10Summary from './Screen10Summary';
import DriverFlow from './DriverFlow';
import DriverComponents from './DriverComponents';
import DriverTokens from './DriverTokens';

/**
 * Primary Operational Tabs (mirrors Store Manager 3-tab simplicity)
 * Overview (Shift/Runs), Active Route (Route/Stop/POD), History & System
 */
const DRIVER_CORE_TABS = [
  { id: '01-login', label: 'Shift Overview' },
  { id: '02-runs', label: 'Assigned Trips' },
  { id: '04-route', label: 'Active Route' },
  { id: '10-summary', label: 'Trip Summary' },
];

/**
 * All 10 screens and system pages accessible via secondary selector
 */
const ALL_DRIVER_VIEWS = [
  { id: '01-login', label: 'Shift Overview' },
  { id: '02-runs', label: 'Assigned Trips' },
  { id: '03-checklist', label: 'Pre-departure' },
  { id: '04-route', label: 'Active Route' },
  { id: '05-stop', label: 'Stop Detail' },
  { id: '06-pod', label: 'Proof of Delivery' },
  { id: '07-problem', label: 'Report Problem' },
  { id: '08-offline', label: 'Offline Mode' },
  { id: '09-route-change', label: 'Route Update' },
  { id: '10-summary', label: 'Trip Summary' },
  { id: 'flow', label: 'Flow' },
  { id: 'components', label: 'Components' },
  { id: 'tokens', label: 'Tokens' },
];

export default function DriverApp({ onBack }) {
  const [driverUser, setDriverUser] = useState(null);
  const [screen, setScreen] = useState('01-login');
  const [isOnline, setIsOnline] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [hasUnreadNotifications, setHasUnreadNotifications] = useState(true);
  const [currentDepot, setCurrentDepot] = useState('Peliyagoda Depot');

  const nav = (s) => setScreen(s);

  // If driver is not authenticated yet, present the Driver sign-in / sign-up screen
  if (!driverUser) {
    return (
      <div className={`min-h-screen w-full ${darkMode ? 'dark bg-[#081C17]' : 'bg-[#081C17]'}`}>
        <DriverAuth
          onAuthSuccess={(user) => {
            setDriverUser(user);
            if (user?.depot) setCurrentDepot(user.depot);
            setScreen('01-login');
          }}
        />
      </div>
    );
  }

  // Once authenticated, unlock full driver portal & screens with unified StoreManager style header
  return (
    <div 
      className={`min-h-screen font-sans antialiased transition-colors duration-200 ${
        darkMode ? 'dark bg-[#0B1A16] text-gray-100' : 'bg-[#FAFBFA] text-gray-900'
      }`}
      style={{ fontFamily: "'Inter', sans-serif" }}
    >
      {/* ── Driver Header matching StoreManager navbar styling ── */}
      <DriverHeader
        navTabs={DRIVER_CORE_TABS}
        activeTab={screen}
        onSelectTab={nav}
        driverUser={driverUser}
        onLogout={() => setDriverUser(null)}
        isOnline={screen === '08-offline' ? false : isOnline}
        onToggleSignal={() => setIsOnline(!isOnline)}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode(!darkMode)}
        hasUnreadNotifications={hasUnreadNotifications}
        onToggleNotifications={() => setHasUnreadNotifications(!hasUnreadNotifications)}
        currentDepot={currentDepot}
        onSelectDepot={(d) => setCurrentDepot(d)}
      />

      {/* ── Secondary Pill Strip for Direct Screen Inspection ── */}
      <div
        className={`w-full overflow-x-auto border-b px-4 sm:px-6 py-2 flex items-center gap-1.5 transition-colors select-none ${
          darkMode ? 'bg-[#10241F] border-[#1A3830]' : 'bg-white border-gray-100'
        }`}
      >
        <span className={`text-[11px] font-bold uppercase tracking-wider mr-1.5 ${darkMode ? 'text-gray-400' : 'text-gray-400'}`}>
          Workflow:
        </span>
        {ALL_DRIVER_VIEWS.map((tab) => {
          const isActive = screen === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => nav(tab.id)}
              className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
                isActive
                  ? darkMode
                    ? 'bg-[#16483A] text-[#34D399]'
                    : 'bg-[#E8F7F0] text-[#059669]'
                  : darkMode
                    ? 'text-gray-400 hover:text-white hover:bg-[#153128]'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ── Screen Rendering Container (Matching StoreManager max-w-7xl mx-auto px-6 dimensions) ── */}
      <main className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
        {screen === 'flow' && (
          <DriverFlow onSelectScreen={nav} darkMode={darkMode} />
        )}
        {screen === '01-login' && (
          <Screen01Login onStart={() => nav('02-runs')} darkMode={darkMode} />
        )}
        {screen === '02-runs' && (
          <Screen02Runs onStartTrip={() => nav('03-checklist')} darkMode={darkMode} />
        )}
        {screen === '03-checklist' && (
          <Screen03Checklist onConfirm={() => nav('04-route')} darkMode={darkMode} />
        )}
        {screen === '04-route' && (
          <Screen04Route
            onNavigate={() => nav('05-stop')}
            onProblem={() => nav('07-problem')}
            darkMode={darkMode}
          />
        )}
        {screen === '05-stop' && (
          <Screen05StopDetail
            onArrived={() => nav('06-pod')}
            onProblem={() => nav('07-problem')}
            darkMode={darkMode}
          />
        )}
        {screen === '06-pod' && (
          <Screen06POD onConfirm={() => nav('10-summary')} darkMode={darkMode} />
        )}
        {screen === '07-problem' && (
          <Screen07Problem onSubmit={() => nav('04-route')} darkMode={darkMode} />
        )}
        {screen === '08-offline' && (
          <Screen08Offline
            onContinue={() => nav('04-route')}
            onReviewRoute={() => nav('09-route-change')}
            darkMode={darkMode}
          />
        )}
        {screen === '09-route-change' && (
          <Screen09RouteChange onAcknowledge={() => nav('04-route')} darkMode={darkMode} />
        )}
        {screen === '10-summary' && (
          <Screen10Summary onStartTrip2={() => nav('02-runs')} darkMode={darkMode} />
        )}
        {screen === 'components' && (
          <DriverComponents darkMode={darkMode} />
        )}
        {screen === 'tokens' && (
          <DriverTokens darkMode={darkMode} />
        )}
      </main>
    </div>
  );
}
