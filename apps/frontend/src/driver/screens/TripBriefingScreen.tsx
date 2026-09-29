import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";

export function TripBriefingScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Trip 1 Briefing</h1>
        <p className="text-[13px] text-slate-500">Waypoint Fresh · Kandy District</p>
      </div>

      <Card variant="surface" className="grid grid-cols-3 gap-2 text-center p-3">
        <div>
          <div className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Route</div>
          <div className="text-[14px] font-bold text-slate-900">42 km</div>
        </div>
        <div className="border-x border-slate-200">
          <div className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Time</div>
          <div className="text-[14px] font-bold text-slate-900">3h 45m</div>
        </div>
        <div>
          <div className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Stops</div>
          <div className="text-[14px] font-bold text-slate-900">8</div>
        </div>
      </Card>

      <Card variant="raised" className="space-y-2">
        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">First Stop Preview</div>
        <h2 className="text-[14px] font-bold text-slate-900">OUT047 · Waypoint Fresh Peradeniya</h2>
        <div className="text-[13px] text-slate-500">Window: 05:30 - 06:30</div>
        <div className="text-[13px] text-slate-500">Rear loading dock · Van only</div>
        <div className="flex gap-1.5 pt-1">
          <span className="inline-flex items-center px-2 py-1 rounded-md bg-slate-100 text-slate-700 text-[11px] font-medium">
            <AppIcon name="snowflake" size={12} className="mr-1" /> Chilled
          </span>
          <span className="inline-flex items-center px-2 py-1 rounded-md bg-slate-100 text-slate-700 text-[11px] font-medium">
            <AppIcon name="truck" size={12} className="mr-1" /> Van access
          </span>
        </div>
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("active-trip")}>Start Trip 1</Button>
      </div>
    </div>
  );
}
