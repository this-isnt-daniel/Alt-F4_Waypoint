import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { DEPOT_RETURN } from "@/driver/data/driverContent";

export function DepotReturnScreen() {
  const { push } = useNavigator();
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto text-center">
      <div className="pt-6">
        <div className="w-16 h-16 rounded-full bg-green-fill mx-auto flex items-center justify-center mb-3">
          <AppIcon name="check" size={32} className="text-green" />
        </div>
        <h1 className="text-lg font-bold text-slate-900">Depot return</h1>
        <p className="text-[13px] text-slate-500">{DEPOT_RETURN.location}</p>
      </div>
      <Card variant="surface" className="text-left space-y-2">
        <div className="text-[13px] text-slate-900 font-medium">Return handed over</div>
        <div className="text-[13px] text-slate-500">Officer {DEPOT_RETURN.officer} confirmed at {DEPOT_RETURN.confirmedAt}</div>
        {DEPOT_RETURN.items.map((item, i) => (
          <div key={i} className="text-[13px] text-slate-500">{item.name} ×{item.quantity}</div>
        ))}
        <div className="text-[13px] text-slate-500">Crate {DEPOT_RETURN.returnCrate}</div>
        <div className="text-[13px] text-slate-500">{DEPOT_RETURN.condition}</div>
        <div className="text-[13px] text-slate-500">Officer PIN {DEPOT_RETURN.officerPin.toLowerCase()}</div>
      </Card>
      <Button variant="primary" size="lg" onClick={() => push("trip-complete")}>
        Record synced
      </Button>
    </div>
  );
}
