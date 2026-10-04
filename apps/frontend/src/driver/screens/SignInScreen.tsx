import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import waypointLogo from "@/assets/icons/waypoint_logo.png";
import { apiFetch } from "@/lib/api";
import { safeStorage } from "@/lib/security";

export function SignInScreen() {
  const { push } = useNavigator();
  const { startTrip1 } = useDriverState();
  const [username, setUsername] = useState<string>("driver");
  const [password, setPassword] = useState<string>("password123");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleSignIn = async () => {
    setError("");
    setLoading(true);
    try {
      const response = await apiFetch<any>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      safeStorage.set("token", response.access_token);
      
      // Tell state provider to initialize data
      startTrip1();
      push("active-trip");
    } catch (err: any) {
      setError(err.message || "Failed to sign in");
    } finally {
      setLoading(false);
    }
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
        {error && <div className="text-red-500 text-[14px] font-bold text-center bg-red-50 py-2 rounded-lg">{error}</div>}
        <div>
          <label htmlFor="driver-id" className="block text-[13px] font-bold text-slate-700 mb-1.5">
            Username
          </label>
          <input
            id="driver-id"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-[15px] font-semibold text-slate-900 outline-none focus:border-[#059669]"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-[13px] font-bold text-slate-700 mb-1.5">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••"
            className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-[18px] font-bold text-slate-900 tracking-widest focus:border-[#059669] outline-none transition-colors"
          />
        </div>
      </div>

      {/* Sign in button */}
      <button
        type="button"
        onClick={handleSignIn}
        disabled={loading}
        className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer mb-3 disabled:opacity-50"
        style={{ backgroundColor: "var(--c-green)" }}
      >
        {loading ? "Signing in..." : "Sign In"}
      </button>

      <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-[12px] text-emerald-900 text-center font-medium">
        Demo credentials: <span className="font-mono font-bold">driver</span> / <span className="font-mono font-bold">password123</span>
      </div>

    </div>
  );
}
