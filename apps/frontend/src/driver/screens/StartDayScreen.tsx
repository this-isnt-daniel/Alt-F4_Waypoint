import { Button } from "@/driver/components/Button";
import { useNavigator } from "@/router/navigator";

export function StartDayScreen() {
  const { push } = useNavigator();
  return (
    <div className="px-4 pb-6 pt-2">
      <p className="text-2xs font-semibold uppercase tracking-wide text-ink-muted">Saturday · 26 September</p>
      <h1 className="mt-1 text-2xl font-bold text-ink">Good morning, Daniru</h1>

      {/* Vehicle facts: read-only orientation, NOT a task */}
      <section className="mt-4 rounded-card border border-line bg-surface p-4">
        <header className="flex items-baseline justify-between">
          <h2 className="font-bold text-ink">VEH014</h2>
          <span className="text-sm text-ink-muted">Refrigerated van</span>
        </header>
        <dl className="mt-2 divide-y divide-line text-sm">
          <div className="flex justify-between py-1.5"><dt className="text-ink-muted">Home depot</dt><dd className="font-medium text-ink">Kandy hub</dd></div>
          <div className="flex justify-between py-1.5"><dt className="text-ink-muted">Temperature</dt><dd className="font-medium text-success">3°C · in range</dd></div>
          <div className="flex justify-between py-1.5"><dt className="text-ink-muted">Fuel</dt><dd className="font-medium text-ink">42 L remaining</dd></div>
        </dl>
      </section>

      {/* Primary: straight through. No gating. */}
      <Button variant="primary" size="lg" fullWidth className="mt-4" onClick={() => push("today-trips")}>
        Start day
      </Button>
      {/* Rare escape hatch, not a chore */}
      <Button variant="ghost" fullWidth className="mt-2" onClick={() => push("contact-dispatch")}>
        Report a vehicle issue
      </Button>
    </div>
  );
}
