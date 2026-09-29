import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { AppIcon, type AppIconName } from "@/driver/components/AppIcon";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";

export function StopDetailScreen() {
  const { push, route } = useNavigator();
  const seq = Number(route.params.seq) || 2;
  const stop = TRIP_1_STOPS.find((s) => s.seq === seq) ?? TRIP_1_STOPS[1]!;

  const tempIcon: AppIconName = stop.temp.includes("Chilled") ? "snowflake" : "package";
  const dockIcon: AppIconName = stop.dock === "Mall bay" ? "building" : "package";

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">{stop.outletId}</h1>
        <p className="text-[14px] font-medium text-slate-700">{stop.name}</p>
        <p className="text-[13px] text-slate-500 mt-0.5">{stop.address}</p>
      </div>

      <Card variant="surface" className="space-y-3">
        <div className="flex items-center justify-between text-[13px]">
          <span className="text-slate-500">Window</span>
          <span className="font-semibold text-slate-900">{stop.window}</span>
        </div>
        {stop.dockDetail && (
          <div className="flex items-center justify-between text-[13px]">
            <span className="text-slate-500">Dock</span>
            <span className="font-medium text-slate-900">{stop.dock} · {stop.dockDetail}</span>
          </div>
        )}
        <div className="flex items-center justify-between text-[13px]">
          <span className="text-slate-500">Units</span>
          <span className="font-medium text-slate-900">{stop.units}</span>
        </div>
        <div className="flex items-center justify-between text-[13px]">
          <span className="text-slate-500">Service time</span>
          <span className="font-medium text-slate-900">{stop.serviceMin} min</span>
        </div>
      </Card>

      {/* Chips */}
      <div className="flex flex-wrap gap-1.5">
        <Chip kind="restriction" category="temperature" label={stop.temp} icon={tempIcon} />
        <Chip kind="restriction" category="dock" label={stop.dock} icon={dockIcon} />
        {stop.parking !== "Normal" && (
          <Chip kind="restriction" category="access" label={stop.parking} icon="truck" />
        )}
      </div>

      {stop.instructions && (
        <Card variant="raised">
          <p className="text-[13px] text-slate-600">{stop.instructions}</p>
        </Card>
      )}

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("mark-arrived", { seq: String(seq) })}>
          Mark arrived
        </Button>
        <div className="flex gap-2">
          <Button variant="secondary" size="md" fullWidth={false} className="flex-1" onClick={() => push("chat", { outletId: stop.outletId })}>
            <AppIcon name="message" size={16} className="mr-1" /> Chat
          </Button>
          <Button variant="secondary" size="md" fullWidth={false} className="flex-1" onClick={() => push("call-overlay", { outletId: stop.outletId })}>
            <AppIcon name="phone" size={16} className="mr-1" /> Call
          </Button>
        </div>
        <Button variant="ghost" size="md" onClick={() => push("active-trip")}>
          <AppIcon name="arrow-left" size={16} className="mr-2" /> Back to map
        </Button>
      </div>
    </div>
  );
}
