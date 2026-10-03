import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { AppIcon } from "@/driver/components/AppIcon";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";

export function MarkArrivedScreen() {
  const { push, route } = useNavigator();
  const seq = Number(route.params.seq) || 2;
  const stop = TRIP_1_STOPS.find((s) => s.seq === seq) ?? TRIP_1_STOPS[1]!;

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Confirm arrival</h1>
        <p className="text-[13px] text-slate-500">{stop.outletId} · {stop.name.split(' ').pop()}</p>
      </div>

      <Card variant="surface" className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-[13px] text-slate-500">Arrived at</div>
          <div className="text-[13px] font-semibold text-slate-900">06:18</div>
        </div>
        <div className="flex items-center justify-between">
          <div className="text-[13px] text-slate-500">Window</div>
          <div className="text-[13px] font-medium text-slate-900">{stop.window}</div>
        </div>
        <div className="flex items-center justify-between">
          <div className="text-[13px] text-slate-500">Status</div>
          <Chip kind="status" tone="onTime" label="On time" />
        </div>
        {stop.dockDetail && (
          <div className="flex items-center justify-between">
            <div className="text-[13px] text-slate-500">Dock</div>
            <div className="text-[13px] font-medium text-slate-900">{stop.dock} · {stop.dockDetail}</div>
          </div>
        )}
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("checklist", { seq: String(seq) })}>
          Confirm arrival
        </Button>
        <Button variant="ghost" size="md" onClick={() => push("active-trip")}>
          <AppIcon name="arrow-left" size={16} className="mr-2" />
          Back to map
        </Button>
      </div>
    </div>
  );
}
