import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { RETURN_DEPOT } from "@/driver/data/driverContent";

export function ReturnDepotScreen() {
  const { push } = useNavigator();
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Return to depot</h1>
        <p className="text-[13px] text-slate-500">{RETURN_DEPOT.items.reduce((s,i) => s + i.quantity, 0)} items · Kandy hub</p>
      </div>
      <Card variant="surface" className="space-y-2">
        <div className="text-[13px] font-medium text-slate-900">Return items are secured</div>
        {RETURN_DEPOT.items.map((item, i) => (
          <div key={i} className="py-2 border-t border-slate-100">
            <div className="text-[13px] text-slate-900">{item.name} ×{item.quantity} — Return pending</div>
            <div className="text-[12px] text-slate-500">Source {RETURN_DEPOT.sourceOutletId}</div>
            <div className="text-[12px] text-slate-500">Reason {RETURN_DEPOT.reason}</div>
            <div className="text-[12px] text-slate-500">Crate {RETURN_DEPOT.returnCrate}</div>
          </div>
        ))}
      </Card>
      <Card variant="raised" className="space-y-1">
        <div className="text-[13px] text-slate-500">Destination: {RETURN_DEPOT.destination}</div>
        <div className="text-[13px] text-slate-500">ETA: {RETURN_DEPOT.eta}</div>
        <div className="text-[13px] text-slate-500">Handover: {RETURN_DEPOT.handover}</div>
      </Card>
      <Button variant="primary" size="lg" onClick={() => push("depot-return")}>
        <AppIcon name="navigate" size={16} className="mr-2" /> Navigate to depot
      </Button>
    </div>
  );
}
