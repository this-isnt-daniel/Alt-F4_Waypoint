import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";

export function LocationDeniedScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto text-center pt-8">
      <div className="w-16 h-16 rounded-full bg-amber-50 mx-auto flex items-center justify-center mb-3">
        <AppIcon name="navigate" size={32} className="text-amber-500" />
      </div>
      <h1 className="text-lg font-bold text-slate-900">Location access needed</h1>
      <p className="text-[13px] text-slate-500">
        Location keeps ETA, arrival confirmation, and route changes accurate while a trip is active.
      </p>
      
      <Card variant="surface" className="text-left mt-4">
        <div className="text-[13px] text-slate-500">• Route and ETA calculation</div>
        <div className="text-[13px] text-slate-500">• Arrival confirmation</div>
        <div className="text-[13px] text-slate-500">• Tracking automatically stops after trip</div>
      </Card>

      <div className="space-y-2 pt-4">
        <Button variant="primary" size="lg" onClick={() => push("active-trip")}>
          Turn on precise location
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("active-trip")}>
          Continue offline
        </Button>
      </div>
    </div>
  );
}
