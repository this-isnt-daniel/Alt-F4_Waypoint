import { useNavigator } from "@/router/navigator";
import { PinKeypad } from "@/driver/components/PinKeypad";
import { Stepper } from "@/driver/components/Stepper";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function PodPinScreen() {
  const { route, push } = useNavigator();
  const { addSyncRecord, connection } = useDriverState();
  const outletId = route.params.outletId ?? "OUT047";
  const stop = TRIP_1_STOPS.find((s) => s.outletId === outletId) ?? TRIP_1_STOPS[1]!;

  const handlePinSubmit = (_pin: string) => {
    addSyncRecord({
      type: "delivery",
      outletId: stop.outletId,
      state: connection === "online" ? "synced" : "pending",
      hasPhoto: true,
      pinVerified: true,
    });
    push("delivery-complete", { outletId: stop.outletId });
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <Stepper currentStep={2} totalSteps={2} label={`Step 2 of 2 · ${stop.outletId}`} />

      <div className="space-y-1 text-center">
        <span className="text-2xs font-extrabold text-green tracking-wider uppercase">
          Receiver Verification
        </span>
        <h1 className="text-xl font-extrabold text-ink">Manager PIN</h1>
        <p className="text-xs text-ink-muted">{stop.name}</p>
      </div>

      <PinKeypad
        managerName={stop.manager}
        onPinSubmit={handlePinSubmit}
        onReportUnavailable={() =>
          push("issue-wizard", { outletId: stop.outletId, preset: "receiver-unavailable" })
        }
      />
    </div>
  );
}
