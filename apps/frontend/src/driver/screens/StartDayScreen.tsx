import { useNavigator } from "@/router/navigator";

// ── START DAY SCREEN ─────────────────────────────────────────────
// Compact operational vehicle briefing. No decorative cards.
// Typography + spacing create structure, not borders.
export function StartDayScreen() {
  const { push } = useNavigator();

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-6">
      <p className="text-[12px] font-bold uppercase tracking-wider text-slate-400 mb-1">
        Monday · 29 September
      </p>
      <h1 className="text-[26px] font-bold text-slate-900 mb-6">Good morning, Daniru</h1>

      {/* Vehicle briefing – one clean section, no nested cards */}
      <section className="mb-6">
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-[18px] font-bold text-slate-900">VEH014</h2>
          <span className="text-[13px] text-slate-400">Refrigerated van</span>
        </div>

        <div className="space-y-0">
          <div className="flex items-center justify-between py-3 border-b border-slate-100">
            <span className="text-[14px] text-slate-500">Home depot</span>
            <span className="text-[14px] font-semibold text-slate-900">Kandy Hub</span>
          </div>
          <div className="flex items-center justify-between py-3 border-b border-slate-100">
            <span className="text-[14px] text-slate-500">Temperature</span>
            <span className="text-[14px] font-semibold text-emerald-600">3°C · In range</span>
          </div>
          <div className="flex items-center justify-between py-3">
            <span className="text-[14px] text-slate-500">Fuel</span>
            <span className="text-[14px] font-semibold text-slate-900">42 L remaining</span>
          </div>
        </div>
      </section>

      {/* Primary action */}
      <button
        type="button"
        onClick={() => push("today-trips")}
        className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer mb-3"
        style={{ backgroundColor: "var(--c-green)" }}
      >
        Start Day
      </button>

      {/* Escape hatch */}
      <button
        type="button"
        onClick={() => push("contact-dispatch")}
        className="w-full py-2 text-[14px] font-medium text-slate-400 hover:text-rose-600 cursor-pointer"
      >
        Report a vehicle issue
      </button>
    </div>
  );
}
