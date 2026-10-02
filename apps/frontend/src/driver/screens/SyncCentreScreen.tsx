import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { useDriverState } from "@/driver/state/useDriverState";

export function SyncCentreScreen() {
  const { push } = useNavigator();
  const { connection, setConnection, syncReviewForwarded } = useDriverState();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Sync Centre</h1>
        <p className="text-[13px] text-slate-500">
          {connection === "online" ? "Connection restored syncing · 2 of 4 updates complete" : "Working offline · 4 updates queued"}
        </p>
      </div>

      <Card variant="surface" className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-[13px] font-medium text-slate-900">OUT047 delivery</div>
          <div className="text-[12px] text-slate-500">Queued · photo + PIN</div>
        </div>
        <div className="flex items-center justify-between">
          <div className="text-[13px] font-medium text-slate-900">OUT052 photo upload</div>
          <div className="text-[12px] text-slate-500">1.8 MB · 67%</div>
        </div>
        <div className="flex items-center justify-between">
          <div className="text-[13px] font-medium text-slate-900">OUT058 delivery record conflict</div>
          <div className="text-[12px] text-slate-500">Detected discrepancy</div>
        </div>
        <div className="flex items-center justify-between">
          <div className="text-[13px] font-medium text-slate-900">Dispatcher route update</div>
          <div className="text-[12px] text-slate-500">OUT061 moved next</div>
        </div>
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => setConnection("online")}>
          <AppIcon name="refresh" size={16} className="mr-2" /> Sync now
        </Button>
        <Button variant="ghost" size="md" onClick={() => push("active-trip")}>
          <AppIcon name="arrow-left" size={16} className="mr-2" /> View map
        </Button>
      </div>
    </div>
  );
}
