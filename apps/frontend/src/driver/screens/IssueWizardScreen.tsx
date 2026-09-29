import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { ChoiceList, type ChoiceOption } from "@/driver/components/ChoiceList";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { PhotoTile } from "@/driver/components/PhotoTile";
import { Stepper } from "@/driver/components/Stepper";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function IssueWizardScreen() {
  const { route, push } = useNavigator();
  const { addSyncRecord, connection } = useDriverState();

  const outletId = route.params.outletId ?? "OUT058";
  const stop = TRIP_1_STOPS.find((s) => s.outletId === outletId) ?? TRIP_1_STOPS[5]!;

  const [step, setStep] = useState<number>(1);
  const [category, setCategory] = useState<string | null>("Access problem");
  const [detail, setDetail] = useState<string | null>("Mall bay unavailable");
  const [hasPhoto, setHasPhoto] = useState<boolean>(false);

  const categoryOptions: ChoiceOption[] = [
    { id: "Item problem", label: "Item problem", description: "Damaged or missing crates" },
    { id: "Access problem", label: "Access problem", description: "Bay closed or parking blocked" },
    { id: "Temperature concern", label: "Temperature concern", description: "Reefer threshold variance" },
    { id: "Receiver problem", label: "Receiver problem", description: "Manager absent or uncooperative" },
    { id: "Vehicle problem", label: "Vehicle problem", description: "Mechanical or tire issue" },
    { id: "Other", label: "Other", description: "General exception report" },
  ];

  const detailOptions: ChoiceOption[] = [
    { id: "Outlet closed", label: "Outlet closed" },
    { id: "Mall bay unavailable", label: "Mall bay unavailable" },
    { id: "Unsafe unloading area", label: "Unsafe unloading area" },
    { id: "Parking blocked", label: "Parking blocked" },
    { id: "Access code failed", label: "Access code failed" },
    { id: "Other access issue", label: "Other access issue" },
  ];

  const handleSaveAndSend = () => {
    addSyncRecord({
      type: "issue",
      outletId: stop.outletId,
      state: connection === "online" ? "synced" : "pending",
      hasPhoto,
      pinVerified: false,
    });
    push("active-trip");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <Stepper currentStep={step} totalSteps={4} label={`Step ${step} of 4`} />

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <h1 className="text-xl font-extrabold text-ink">What happened?</h1>
            <p className="text-xs text-ink-muted">Select issue category for {stop.outletId}</p>
          </div>
          <ChoiceList
            options={categoryOptions}
            selectedId={category}
            onSelect={(id) => setCategory(id)}
          />
          <Button variant="primary" size="lg" disabled={!category} onClick={() => setStep(2)}>
            Next: Specific detail
          </Button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <h1 className="text-xl font-extrabold text-ink">Which access problem?</h1>
            <p className="text-xs text-ink-muted">Specify details for dispatch</p>
          </div>
          <ChoiceList
            options={detailOptions}
            selectedId={detail}
            onSelect={(id) => setDetail(id)}
          />
          <div className="flex gap-2">
            <Button variant="secondary" size="lg" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button variant="primary" size="lg" disabled={!detail} onClick={() => setStep(3)}>
              Next: Evidence
            </Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <div>
            <h1 className="text-xl font-extrabold text-ink">Add evidence</h1>
            <p className="text-xs text-ink-muted">
              Evidence is optional, but helps dispatch resolve the issue faster.
            </p>
          </div>
          <PhotoTile
            onPhotoCaptured={() => setHasPhoto(true)}
            savedOfflineNote={connection === "offline"}
          />
          <div className="flex gap-2">
            <Button variant="secondary" size="lg" onClick={() => setStep(2)}>
              Back
            </Button>
            <Button variant="primary" size="lg" onClick={() => setStep(4)}>
              Review issue
            </Button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="space-y-4">
          <div>
            <h1 className="text-xl font-extrabold text-ink">Review issue</h1>
            <p className="text-xs text-ink-muted">Confirm report details before filing</p>
          </div>

          <Card variant="surface" className="space-y-2">
            <KeyValueRow label="Outlet" value={`${stop.outletId} · ${stop.name}`} />
            <KeyValueRow label="Category" value={category ?? "Access problem"} />
            <KeyValueRow label="Detail" value={detail ?? "Mall bay unavailable"} emphasis="strong" />
            <KeyValueRow label="Evidence" value={hasPhoto ? "1 photo attached" : "None"} />
            <KeyValueRow label="Time recorded" value="07:12" />
          </Card>

          <Card variant="raised" className="text-xs text-ink-muted leading-relaxed">
            <span className="font-bold text-ink block mb-0.5">Offline-safe report:</span>
            You can leave this screen after saving. The report remains on this phone until synced.
          </Card>

          <div className="space-y-2 pt-2">
            <Button variant="primary" size="lg" onClick={handleSaveAndSend}>
              Save and send
            </Button>
            <Button variant="secondary" size="md" onClick={() => setStep(1)}>
              Edit details
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
