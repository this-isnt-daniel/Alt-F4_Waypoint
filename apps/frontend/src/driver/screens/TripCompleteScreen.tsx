import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { AppIcon } from "@/driver/components/AppIcon";
import { TRIP_COMPLETE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function TripCompleteScreen() {
  const { push } = useNavigator();
  const { completeTrip1 } = useDriverState();
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">{TRIP_COMPLETE.title}</h1>
      </div>
      <div className="flex gap-2">
        <Chip kind="outcome" tone="delivered" label={`${TRIP_COMPLETE.delivered} delivered`} />
        <Chip kind="outcome" tone="partial" label={`${TRIP_COMPLETE.partial} partial`} count={TRIP_COMPLETE.partial} />
        <Chip kind="outcome" tone="failed" label={`${TRIP_COMPLETE.failed} failed`} count={TRIP_COMPLETE.failed} />
      </div>
      <Card variant="surface" className="space-y-2">
        <div className="flex justify-between text-[13px]"><span className="text-slate-500">Total trip time</span><span className="font-medium text-slate-900">{TRIP_COMPLETE.totalTripTime} — under budget</span></div>
        <div className="flex justify-between text-[13px]"><span className="text-slate-500">Distance</span><span className="font-medium text-slate-900">{TRIP_COMPLETE.distance}</span></div>
        <div className="flex justify-between text-[13px]"><span className="text-slate-500">Fuel</span><span className="font-medium text-slate-900">{TRIP_COMPLETE.fuelEconomy} · {TRIP_COMPLETE.fuelUsed} used</span></div>
      </Card>
      <Card variant="raised" className="space-y-1">
        <div className="text-[12px] font-semibold text-slate-500 uppercase tracking-wider">Route recap</div>
        {TRIP_COMPLETE.routeRecap.map((r) => (
          <div key={r.outletId} className="flex justify-between text-[13px] py-1">
            <span className="text-slate-900">{r.outletId} <span className={r.outcome === 'Partial' ? 'text-amber-600' : 'text-green'}>{r.outcome}</span></span>
            <span className="text-slate-500">{r.time}{r.suffix ? ` · ${r.suffix}` : ''}</span>
          </div>
        ))}
        <div className="text-[12px] text-slate-400">+{TRIP_COMPLETE.remainingRecapCount} stops delivered</div>
      </Card>
      <p className="text-[13px] text-slate-500">{TRIP_COMPLETE.returnGuidance}</p>
      <Button variant="primary" size="lg" onClick={() => { completeTrip1(); push("today-trips"); }}>
        {TRIP_COMPLETE.forwardCta}
      </Button>
    </div>
  );
}
