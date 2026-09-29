import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";

export function SyncFailedScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto text-center pt-8">
      <div className="w-16 h-16 rounded-full bg-red-50 mx-auto flex items-center justify-center mb-3">
        <AppIcon name="alert" size={32} className="text-red-500" />
      </div>
      <h1 className="text-lg font-bold text-slate-900">Sync failed</h1>
      <p className="text-[13px] text-slate-500">
        Records are safe on this phone. Waypoint couldn't reach the server. 4 records waiting to sync.
      </p>
      
      <div className="space-y-2 pt-4">
        <Button variant="primary" size="lg" onClick={() => push("sync-centre")}>
          <AppIcon name="refresh" size={16} className="mr-2" /> Retry sync
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("active-trip")}>
          Continue offline
        </Button>
        <Button variant="ghost" size="md" onClick={() => push("contact-dispatch")}>
          Call support
        </Button>
      </div>
    </div>
  );
}
