import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { ROUTE_UPDATE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function RouteChangedScreen() {
  const { push } = useNavigator();
  const { acceptRouteUpdate } = useDriverState();
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Route updated</h1>
        <p className="text-[13px] text-slate-500">Dispatcher · {ROUTE_UPDATE.dispatcherTime}</p>
      </div>
      <div className="text-[15px] font-bold text-slate-900">{ROUTE_UPDATE.headline}</div>
      <p className="text-[13px] text-slate-500">{ROUTE_UPDATE.body}</p>
      <Card variant="surface" className="space-y-2">
        {ROUTE_UPDATE.changes.map((c) => (
          <div key={c.outletId} className="flex items-center gap-2 text-[13px]">
            <AppIcon name={c.type === 'moved_next' ? 'chevron-up' : 'chevron-down'} size={16} className={c.type === 'moved_next' ? 'text-green' : 'text-slate-400'} />
            <span className="text-slate-900 font-medium">{c.type === 'moved_next' ? 'Moved next' : 'Moved later'}: {c.outletId}</span>
          </div>
        ))}
        <div className="text-[13px] text-slate-500 pt-1">New ETA {ROUTE_UPDATE.newEta}</div>
      </Card>
      <p className="text-[13px] text-slate-500">{ROUTE_UPDATE.reassurance}</p>
      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => { acceptRouteUpdate(); push("active-trip"); }}>{ROUTE_UPDATE.primary}</Button>
        <Button variant="secondary" size="md" onClick={() => push("call-overlay")}>
          <AppIcon name="phone" size={16} className="mr-2" /> Call dispatcher
        </Button>
      </div>
    </div>
  );
}
