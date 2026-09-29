import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { DAY_SUMMARY } from "@/driver/data/driverContent";

export function DaySummaryScreen() {
  const { push } = useNavigator();
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto text-center">
      <div className="pt-6">
        <div className="w-16 h-16 rounded-full bg-green-fill mx-auto flex items-center justify-center mb-3">
          <AppIcon name="check" size={32} className="text-green" />
        </div>
        <h1 className="text-lg font-bold text-slate-900">{DAY_SUMMARY.title}</h1>
        <p className="text-[13px] text-slate-500">{DAY_SUMMARY.driver} · 26 September</p>
      </div>
      <Card variant="surface" className="text-left space-y-2">
        <div className="flex justify-between text-[13px]"><span className="text-slate-500">Stops visited</span><span className="font-medium text-slate-900">{DAY_SUMMARY.stops}</span></div>
        <div className="flex justify-between text-[13px]"><span className="text-slate-500">Deliveries</span><span className="font-medium text-slate-900">{DAY_SUMMARY.deliveries}</span></div>
        <div className="flex justify-between text-[13px]"><span className="text-slate-500">Returns</span><span className="font-medium text-slate-900">{DAY_SUMMARY.returns}</span></div>
        <div className="flex justify-between text-[13px]"><span className="text-slate-500">Sync</span><span className="font-medium text-green">{DAY_SUMMARY.sync}</span></div>
      </Card>
      <p className="text-[13px] text-slate-500">{DAY_SUMMARY.closing}</p>
      <Button variant="primary" size="lg" onClick={() => push("signin")}>
        Finish day
      </Button>
    </div>
  );
}
