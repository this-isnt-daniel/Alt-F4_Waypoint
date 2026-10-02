import { useDriverState } from "@/driver/state/useDriverState";
import { useNavigator } from "@/router/navigator";
import { TRIP_1, TRIP_2 } from "@/driver/data/driverContent";
import { Lock, Check, Phone } from "lucide-react";

// ── TODAY'S TRIPS SCREEN ─────────────────────────────────────────
// Simple trip list. No analytics banner. No "13 stops · 2,100 cases" hero.
// Driver needs: trip context → start action. That is all.
export function TodayTripsScreen() {
  const {
    trip1Started,
    trip1Completed,
    trip2Unlocked,
    trip2Started,
  } = useDriverState();
  const { push } = useNavigator();

  const isTrip1Done = trip1Completed || trip2Started;

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-6">
      {/* Page heading */}
      <p className="text-[12px] font-bold uppercase tracking-wider text-slate-400 mb-1">Today</p>
      <h1 className="text-[24px] font-bold text-slate-900 mb-6">Your trips</h1>

      {/* ── TRIP 1 ── */}
      <section className={`mb-4 rounded-xl border ${isTrip1Done ? "border-slate-200 bg-slate-50 opacity-70" : "border-green/30 bg-white shadow-sm"}`}>
        <div className="px-4 py-4">
          <div className="flex items-start justify-between mb-1">
            <div>
              <p className="text-[16px] font-bold text-slate-900">Trip 1 · Fresh</p>
              <p className="text-[13px] text-slate-500 mt-0.5">{TRIP_1.stopCount} stops · Depart {TRIP_1.depart}</p>
            </div>
            {isTrip1Done && (
              <span className="flex items-center gap-1 text-[12px] font-semibold text-emerald-600">
                <Check size={14} /> Done
              </span>
            )}
          </div>

          {/* Compact info row */}
          <div className="flex items-center gap-4 mt-3 mb-4 text-[13px] text-slate-500">
            <span>Return {TRIP_1.etaReturn}</span>
            <span>·</span>
            <span>Chilled reefer</span>
          </div>

          {/* CTA */}
          {isTrip1Done ? (
            <div className="flex items-center justify-center gap-2 py-2.5 rounded-lg bg-slate-100 text-[13px] font-semibold text-slate-400">
              <Check size={15} className="text-emerald-500" /> Completed
            </div>
          ) : trip1Started ? (
            <button
              type="button"
              onClick={() => push("active-trip")}
              className="w-full bg-green text-white font-bold text-[15px] py-3.5 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
              style={{ backgroundColor: "var(--c-green)" }}
            >
              Resume Trip 1
            </button>
          ) : (
            <button
              type="button"
              onClick={() => push("trip-briefing", { trip: "1" })}
              className="w-full bg-green text-white font-bold text-[15px] py-3.5 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
              style={{ backgroundColor: "var(--c-green)" }}
            >
              Start Trip 1
            </button>
          )}
        </div>
      </section>

      {/* ── TRIP 2 ── */}
      <section className={`mb-6 rounded-xl border ${trip2Unlocked || trip2Started ? "border-green/30 bg-white shadow-sm" : "border-slate-200 bg-slate-50 opacity-60"}`}>
        <div className="px-4 py-4">
          <div className="flex items-start justify-between mb-1">
            <div>
              <p className={`text-[16px] font-bold ${trip2Unlocked || trip2Started ? "text-slate-900" : "text-slate-400"}`}>
                Trip 2 · Style
              </p>
              <p className="text-[13px] text-slate-500 mt-0.5">{TRIP_2.stopCount} stops · Ambient</p>
            </div>
            {!trip2Unlocked && !trip2Started && (
              <Lock size={16} className="text-slate-300 mt-0.5" />
            )}
          </div>

          <div className="flex items-center gap-4 mt-3 mb-4 text-[13px] text-slate-400">
            <span>Available after Trip 1</span>
          </div>

          {trip2Started ? (
            <button
              type="button"
              onClick={() => push("active-trip")}
              className="w-full bg-green text-white font-bold text-[15px] py-3.5 rounded-lg cursor-pointer"
              style={{ backgroundColor: "var(--c-green)" }}
            >
              Resume Trip 2
            </button>
          ) : trip2Unlocked ? (
            <button
              type="button"
              onClick={() => push("trip-briefing", { trip: "2" })}
              className="w-full bg-green text-white font-bold text-[15px] py-3.5 rounded-lg cursor-pointer"
              style={{ backgroundColor: "var(--c-green)" }}
            >
              Start Trip 2
            </button>
          ) : (
            <div className="flex items-center justify-center gap-2 py-2.5 rounded-lg bg-slate-100 text-[13px] font-semibold text-slate-400">
              <Lock size={14} /> Locked until Trip 1 done
            </div>
          )}
        </div>
      </section>

      {/* Dispatch link */}
      <button
        type="button"
        onClick={() => push("contact-dispatch")}
        className="flex items-center justify-center gap-1.5 text-[13px] font-medium text-slate-400 hover:text-slate-700 cursor-pointer py-1"
      >
        <Phone size={14} />
        Contact dispatch
      </button>
    </div>
  );
}
