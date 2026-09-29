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
 * DriverApp — orchestrates Driver Authentication (Sign-in / Sign-up) and all 10 Driver operational screens.
 *
 * Auth Flow:
 *  Unauthenticated -> DriverAuth (Driver Sign-in / Sign-up)
 *  Authenticated   -> 01 (Start Shift) -> 02 (Today's Runs) -> 03 -> 04 -> 05 -> 06 -> 10
 */

const SCREENS = [
  'flow',
  '01-login',
  '02-runs',
  '03-checklist',
  '04-route',
  '05-stop',
  '06-pod',
  '07-problem',
  '08-offline',
  '09-route-change',
  '10-summary',
  'components',
  'tokens',
];

const SCREEN_LABELS = {
  'flow':           '🗺️ Flow & Persona',
  '01-login':       '01 Start Shift',
  '02-runs':        "02 Today's Runs",
  '03-checklist':   '03 Pre-departure',
  '04-route':       '04 Route',
  '05-stop':        '05 Stop Detail',
  '06-pod':         '06 POD',
  '07-problem':     '07 Problem',
  '08-offline':     '08 Offline',
  '09-route-change': '09 Route Change',
  '10-summary':     '10 Summary',
  'components':     '🧩 Components',
  'tokens':         '🎨 Tokens',
};

export default function DriverApp({ onBack }) {
  // Check if driver is already logged in (defaults to null for sign-in first)
  const [driverUser, setDriverUser] = useState(null);
  const [screen, setScreen] = useState('01-login');
  const [isOnline, setIsOnline] = useState(true);

  const nav = (s) => setScreen(s);

  // If driver is not authenticated yet, present the Driver sign-in / sign-up screen
  if (!driverUser) {
    return (
      <DriverAuth
        onAuthSuccess={(user) => {
          setDriverUser(user);
          setScreen('01-login');
        }}
      />
    );
  }

  // Once authenticated, unlock full driver portal & screens
  return (
    <div className="min-h-screen" style={{ background: '#F4F8F6' }}>
      {/* Persistent header with dynamic Driver user & Logout action */}
      <DriverHeader
        isOnline={screen === '08-offline' ? false : isOnline}
        driverUser={driverUser}
        onLogout={() => setDriverUser(null)}
      />

      {/* Navigation bar for all 10 operational screens + System pages */}
      <div
        className="w-full overflow-x-auto sticky top-16 z-30 shadow-xs"
        style={{ background: '#0B3D33', borderBottom: '1px solid rgba(255,255,255,0.1)' }}
      >
        <div className="flex items-center gap-1 px-4 py-2 min-w-max">
          {SCREENS.map((s) => (
            <button
              key={s}
              onClick={() => nav(s)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap cursor-pointer"
              style={{
                background: screen === s ? '#0F9D6C' : 'transparent',
                color: screen === s ? 'white' : '#A7D4C0',
              }}
            >
              {SCREEN_LABELS[s]}
            </button>
          ))}

          {/* Quick Online/Offline Demo toggle */}
          <div className="ml-4 flex items-center gap-2 pl-4" style={{ borderLeft: '1px solid rgba(255,255,255,0.15)' }}>
            <span className="text-xs font-medium" style={{ color: '#A7D4C0' }}>Signal:</span>
            <button
              onClick={() => setIsOnline(!isOnline)}
              className="px-2.5 py-1 rounded-full text-xs font-semibold cursor-pointer transition-all"
              style={{
                background: isOnline ? '#E6F6EC' : '#FDECEC',
                color: isOnline ? '#16A34A' : '#E5484D',
              }}
            >
              {isOnline ? '● Online' : '● Offline'}
            </button>
          </div>
        </div>
      </div>

      {/* Screen renderer */}
      {screen === 'flow' && (
        <DriverFlow onSelectScreen={nav} />
      )}
      {screen === '01-login' && (
        <Screen01Login onStart={() => nav('02-runs')} />
      )}
      {screen === '02-runs' && (
        <Screen02Runs onStartTrip={() => nav('03-checklist')} />
      )}
      {screen === '03-checklist' && (
        <Screen03Checklist onConfirm={() => nav('04-route')} />
      )}
      {screen === '04-route' && (
        <Screen04Route
          onNavigate={() => nav('05-stop')}
          onProblem={() => nav('07-problem')}
        />
      )}
      {screen === '05-stop' && (
        <Screen05StopDetail
          onArrived={() => nav('06-pod')}
          onProblem={() => nav('07-problem')}
        />
      )}
      {screen === '06-pod' && (
        <Screen06POD onConfirm={() => nav('10-summary')} />
      )}
      {screen === '07-problem' && (
        <Screen07Problem onSubmit={() => nav('04-route')} />
      )}
      {screen === '08-offline' && (
        <Screen08Offline
          onContinue={() => nav('04-route')}
          onReviewRoute={() => nav('09-route-change')}
        />
      )}
      {screen === '09-route-change' && (
        <Screen09RouteChange onAcknowledge={() => nav('04-route')} />
      )}
      {screen === '10-summary' && (
        <Screen10Summary onStartTrip2={() => nav('02-runs')} />
      )}
      {screen === 'components' && (
        <DriverComponents />
      )}
      {screen === 'tokens' && (
        <DriverTokens />
      )}
    </div>
  );
}
