import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { DRIVER, VEHICLE } from "@/driver/data/driverContent";
import waypointLogo from "@/assets/icons/waypoint_logo.png";

// ── SIGN IN SCREEN ────────────────────────────────────────────────
// Clean, operational mobile login.
// Waypoint logo + wordmark at top, then form, then Sign In.
// No marketing, no hero, no cards, no gradients.
export function SignInScreen() {
  const { push } = useNavigator();
  const { startTrip1 } = useDriverState();
  const [pin, setPin] = useState<string>("");

  const handleSignIn = () => {
    startTrip1();
    push("active-trip");
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-6 py-8">

      {/* Waypoint identity */}
      <div className="flex flex-col items-center mb-10">
        <img src={waypointLogo} alt="Waypoint" className="w-12 h-12 object-contain rounded-lg mb-3" />
        <span className="text-[22px] font-bold text-[#0B2019] tracking-tight">Waypoint</span>
        <span className="text-[13px] text-slate-400 mt-0.5">Driver sign in</span>
      </div>

      {/* Form */}
      <div className="space-y-4 mb-8">
        <div>
          <label htmlFor="depot" className="block text-[13px] font-bold text-slate-700 mb-1.5">
            Depot
          </label>
          <input
            id="depot"
            type="text"
            readOnly
            value={VEHICLE.depot}
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-[15px] font-semibold text-slate-900 outline-none"
          />
        </div>

        <div>
          <label htmlFor="driver-id" className="block text-[13px] font-bold text-slate-700 mb-1.5">
            ID / Username
          </label>
          <input
            id="driver-id"
            type="text"
            readOnly
            value={DRIVER.name}
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-[15px] font-semibold text-slate-900 outline-none"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-[13px] font-bold text-slate-700 mb-1.5">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="••••"
            className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-[18px] font-bold text-slate-900 tracking-widest focus:border-[#059669] outline-none transition-colors"
          />
        </div>
      </div>

      {/* Sign in button */}
      <button
        type="button"
        onClick={handleSignIn}
        className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer mb-3"
        style={{ backgroundColor: "var(--c-green)" }}
      >
        Sign In
      </button>

    </div>
  );
}
