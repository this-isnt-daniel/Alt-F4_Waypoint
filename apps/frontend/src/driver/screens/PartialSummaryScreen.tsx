import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { OUT058_PARTIAL } from "@/driver/data/driverContent";

export function PartialSummaryScreen() {
  const { push } = useNavigator();
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Partial delivery</h1>
        <p className="text-[13px] text-slate-500">{OUT058_PARTIAL.outletId} · {OUT058_PARTIAL.outletName}</p>
      </div>
      <div className="text-[14px] font-medium text-slate-900">
        {OUT058_PARTIAL.handedOver} of {OUT058_PARTIAL.manifest} handed over
      </div>
      <p className="text-[13px] text-slate-500">
        {OUT058_PARTIAL.manifest - OUT058_PARTIAL.handedOver} frozen items return to Kandy hub
      </p>
      <Card variant="surface" className="space-y-2">
        {OUT058_PARTIAL.returnItems.map((item, i) => (
          <div key={i} className="flex items-center justify-between">
            <span className="text-[13px] text-slate-900">{item.name} ×{item.quantity}</span>
            <span className="text-[12px] text-amber-600">{item.reason} · {item.returnCrate}</span>
          </div>
        ))}
      </Card>
      <Button variant="primary" size="lg" onClick={() => push("return-depot")}>
        Continue
      </Button>
    </div>
  );
}
