import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { ChoiceList, type ChoiceOption } from "@/driver/components/ChoiceList";
import { OUTLET_CLOSED } from "@/driver/data/driverContent";

export function FailedReasonScreen() {
  const { push } = useNavigator();
  const [selectedReason, setSelectedReason] = useState<string | null>("Mall bay unavailable");

  const options: ChoiceOption[] = [
    { id: "Outlet closed", label: "Outlet closed", description: "Store is shut or unstaffed" },
    { id: "Mall bay unavailable", label: "Mall bay unavailable", description: "Rear bay closed by security" },
    { id: "Store refused delivery", label: "Store refused delivery", description: "Manager rejected shipment" },
    { id: "Unsafe access", label: "Unsafe access", description: "Hazardous unloading area" },
    { id: "Receiver unavailable", label: "Receiver unavailable", description: "Authorized personnel missing" },
    { id: "Other", label: "Other", description: "Describe reason below" },
  ];

  const handleContinue = () => {
    push("outlet-closed");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-danger tracking-wider uppercase">
          Delivery Exception
        </span>
        <h1 className="text-xl font-extrabold text-ink">Failed delivery</h1>
        <p className="text-xs font-semibold text-ink-muted">
          {OUTLET_CLOSED.outletId} · {OUTLET_CLOSED.outletName}
        </p>
      </div>

      <p className="text-xs text-ink-muted">
        Why couldn’t you deliver? Choose the closest reason. Evidence and return items come next.
      </p>

      <ChoiceList
        options={options}
        selectedId={selectedReason}
        onSelect={(id) => setSelectedReason(id)}
      />

      <Card variant="raised" className="text-2xs text-ink-muted">
        <span className="font-bold text-ink block mb-0.5">Safety note:</span>
        If you’re still in traffic, stop safely to continue.
      </Card>

      <div className="pt-2">
        <Button
          variant="primary"
          size="lg"
          disabled={!selectedReason}
          onClick={handleContinue}
        >
          Continue to evidence
        </Button>
      </div>
    </div>
  );
}
