import React from 'react';
import waypointLogo from '../../src/assets/icons/waypoint_logo.png';

export default function DispatcherLogin({ onLogin }) {
  return (
    <main className="min-h-screen w-full bg-white flex flex-col items-center justify-center px-4 select-none">
      <div className="flex flex-col items-center max-w-sm w-full">
        {/* Logo and Brand Heading */}
        <div className="flex items-center justify-center gap-3.5">
          <img
            src={waypointLogo}
            alt="Waypoint Logo"
            className="w-12 h-12 object-contain rounded-xl shadow-sm"
          />
          <h1
            className="text-[48px] font-extrabold text-[#0B2019] tracking-tight leading-none"
            style={{ fontFamily: "'Inter', sans-serif" }}
          >
            Waypoint
          </h1>
        </div>

        {/* Portal Pill Badge */}
        <div className="mt-5">
          <span className="inline-flex items-center px-4 py-1.5 rounded-full text-[11px] font-semibold tracking-[0.16em] uppercase text-[#256149] bg-[#EBF6F0] border border-[#DCF0E5]">
            Dispatcher Portal
          </span>
        </div>

        {/* Geist-style Action Button */}
        <button
          type="button"
          onClick={onLogin}
          aria-label="Log in to Dispatcher Portal"
          className="mt-6 w-[230px] h-11 bg-[#059669] hover:bg-[#047857] active:bg-[#065f46] text-white text-sm font-medium rounded-lg transition-all duration-150 ease-in-out shadow-sm hover:shadow flex items-center justify-center cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#059669] focus-visible:ring-offset-2"
        >
          Log in
        </button>
      </div>
    </main>
  );
}
