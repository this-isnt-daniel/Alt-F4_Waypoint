import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";

export function OfflineSavedScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto text-center">
      <div className="pt-6">
        <div className="w-16 h-16 rounded-full bg-slate-100 mx-auto flex items-center justify-center mb-3">
          <AppIcon name="save" size={32} className="text-slate-600" />
        </div>
        <h1 className="text-lg font-bold text-slate-900">Delivery saved</h1>
        <p className="text-[13px] text-slate-500">OUT047 · 06:34</p>
      </div>

      <p className="text-[13px] text-slate-500 font-medium">Saved safely on this phone</p>
      
      <Card variant="surface" className="text-left">
        <p className="text-[13px] text-slate-500">
          You can continue the route. The photo and PIN will sync automatically when connection returns. No work will be lost.
        </p>
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("active-trip")}>
          Continue to next stop
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("sync-centre")}>
          Open Sync Centre
        </Button>
      </div>
    </div>
  );
}
