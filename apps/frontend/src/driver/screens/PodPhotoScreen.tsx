import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { PhotoTile } from "@/driver/components/PhotoTile";
import { Stepper } from "@/driver/components/Stepper";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function PodPhotoScreen() {
  const { route, push } = useNavigator();
  const { addSyncRecord, connection } = useDriverState();
  const outletId = route.params.outletId ?? "OUT047";
  const stop = TRIP_1_STOPS.find((s) => s.outletId === outletId) ?? TRIP_1_STOPS[1]!;

  const [hasPhoto, setHasPhoto] = useState<boolean>(false);

  const handleUsePhoto = () => {
    addSyncRecord({
      type: "delivery",
      outletId: stop.outletId,
      state: connection === "online" ? "synced" : "pending",
      hasPhoto: true,
      pinVerified: false,
    });
    push("pod-pin", { outletId: stop.outletId });
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <Stepper currentStep={1} totalSteps={2} label="Step 1 of 2 · photo" />

      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-green tracking-wider uppercase">
          Proof of Delivery
        </span>
        <h1 className="text-xl font-extrabold text-ink">Photograph the handover</h1>
        <p className="text-xs text-ink-muted">{stop.outletId} · {stop.name}</p>
      </div>

      <PhotoTile
        onPhotoCaptured={() => setHasPhoto(true)}
        savedOfflineNote={connection === "offline"}
      />

      <div className="pt-2">
        <Button
          variant="primary"
          size="lg"
          onClick={handleUsePhoto}
        >
          {hasPhoto ? "Use photo & continue" : "Skip photo & enter PIN"}
        </Button>
      </div>
    </div>
  );
}
