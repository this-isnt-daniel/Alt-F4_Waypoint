import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { OUTLET_CLOSED } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function OutletClosedScreen() {
  const { push, route } = useNavigator();
  const { completeStop } = useDriverState();
  const outletId = route.params.outletId ?? OUTLET_CLOSED.outletId;

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Outlet unavailable</h1>
        <p className="text-[13px] text-slate-500">{outletId} · {OUTLET_CLOSED.outletName}</p>
      </div>
      <div className="text-[13px] font-medium text-amber-600">{OUTLET_CLOSED.reason}</div>
      <Card variant="surface" className="space-y-2">
        {OUTLET_CLOSED.affectedItems.map((item, i) => (
          <div key={i} className="flex justify-between text-[13px]">
            <span className="text-slate-900">{item.name} ×{item.quantity}</span>
            <span className="text-slate-500">{item.action}</span>
          </div>
        ))}
        <div className="text-[12px] text-slate-500 pt-1">Return crate: {OUTLET_CLOSED.returnCrate}</div>
        <div className="text-[12px] text-slate-500">Destination: {OUTLET_CLOSED.destination}</div>
      </Card>
      <div className="space-y-2 pt-2">
        <Button
          variant="primary"
          size="lg"
          onClick={() => {
            completeStop(outletId, "failed");
            push("return-depot", { outletId });
          }}
        >
          {OUTLET_CLOSED.result}
        </Button>
        <Button variant="ghost" size="md" onClick={() => push("active-trip")}>
          <AppIcon name="arrow-left" size={16} className="mr-2" /> Back to route
        </Button>
      </div>
    </div>
  );
}
