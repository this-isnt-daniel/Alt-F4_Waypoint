import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { ChoiceList, type ChoiceOption } from "@/driver/components/ChoiceList";

export function NotHandedOverReasonScreen() {
  const { route, push } = useNavigator();
  const outletId = route.params.outletId ?? "OUT058";
  const [selectedReason, setSelectedReason] = useState<string | null>("Damaged");

  const options: ChoiceOption[] = [
    { id: "Damaged", label: "Damaged", description: "Item damaged in staging or transit" },
    { id: "Missing at loading", label: "Missing at loading", description: "Not loaded at depot" },
    { id: "Wrong item", label: "Wrong item", description: "Item does not match manifest specification" },
    { id: "Store refused", label: "Store refused", description: "Store manager rejected item" },
    { id: "Access issue", label: "Access issue", description: "Cannot access bay or freezer" },
    { id: "Other", label: "Other", description: "Specify reason below" },
  ];

  const handleContinue = () => {
    push("pod-photo", { outletId });
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-warning tracking-wider uppercase">
          Handover Exception
        </span>
        <h1 className="text-xl font-extrabold text-ink">Item not handed over</h1>
        <p className="text-xs text-ink-muted">Frozen produce · 2 items (Return Crate R-04)</p>
      </div>

      <p className="text-xs text-ink-muted">
        Why wasn’t it handed over? Choose one reason. You can add evidence next.
      </p>

      <ChoiceList
        options={options}
        selectedId={selectedReason}
        onSelect={(id) => setSelectedReason(id)}
      />

      <div className="pt-2">
        <Button
          variant="primary"
          size="lg"
          disabled={!selectedReason}
          onClick={handleContinue}
        >
          Continue
        </Button>
      </div>
    </div>
  );
}
