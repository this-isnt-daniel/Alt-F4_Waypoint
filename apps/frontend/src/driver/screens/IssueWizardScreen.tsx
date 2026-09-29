import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { useDriverState } from "@/driver/state/useDriverState";

export function IssueWizardScreen() {
  const { route, push } = useNavigator();
  const { addSyncRecord, connection } = useDriverState();
  const outletId = route.params.outletId ?? "OUT058";

  const [step, setStep] = useState(1);
  const [category, setCategory] = useState<string | null>(null);
  const [detail, setDetail] = useState<string | null>(null);
  const [hasPhoto, setHasPhoto] = useState(false);

  const categories = ["Item problem", "Access problem", "Temperature concern", "Receiver problem", "Vehicle problem", "Other"];
  const details = ["Outlet closed", "Mall bay unavailable", "Unsafe unloading area", "Parking blocked", "Access code failed", "Other access issue"];

  const handleSaveAndSend = () => {
    addSyncRecord({
      type: "issue",
      outletId,
      state: connection === "online" ? "synced" : "pending",
      hasPhoto,
      pinVerified: false,
    });
    push("active-trip");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Step {step} of 4</div>

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <h1 className="text-lg font-bold text-slate-900">What happened?</h1>
            <p className="text-[13px] text-slate-500">Select issue category for {outletId}</p>
          </div>
          <div className="space-y-2">
            {categories.map((c) => (
              <button key={c} type="button" onClick={() => setCategory(c)}
                className={`w-full flex items-center justify-between p-3 rounded-xl border transition-colors ${category === c ? "border-green/30 bg-green-fill" : "border-slate-200 bg-white"}`}>
                <span className="text-[13px] font-medium text-slate-900">{c}</span>
                {category === c && <AppIcon name="check" size={18} className="text-green" />}
              </button>
            ))}
          </div>
          <Button variant="primary" size="lg" disabled={!category} onClick={() => setStep(2)}>Next</Button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <h1 className="text-lg font-bold text-slate-900">Which {category?.toLowerCase()}?</h1>
            <p className="text-[13px] text-slate-500">Specify details for dispatch</p>
          </div>
          <div className="space-y-2">
            {details.map((d) => (
              <button key={d} type="button" onClick={() => setDetail(d)}
                className={`w-full flex items-center justify-between p-3 rounded-xl border transition-colors ${detail === d ? "border-green/30 bg-green-fill" : "border-slate-200 bg-white"}`}>
                <span className="text-[13px] font-medium text-slate-900">{d}</span>
                {detail === d && <AppIcon name="check" size={18} className="text-green" />}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="lg" fullWidth={false} className="flex-1" onClick={() => setStep(1)}>Back</Button>
            <Button variant="primary" size="lg" fullWidth={false} className="flex-[2]" disabled={!detail} onClick={() => setStep(3)}>Next</Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <div>
            <h1 className="text-lg font-bold text-slate-900">Add evidence</h1>
            <p className="text-[13px] text-slate-500">Evidence is optional, but helps dispatch resolve the issue faster.</p>
          </div>
          <div
            className="w-full aspect-[4/3] rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-green/40 transition-colors"
            onClick={() => setHasPhoto(true)}
          >
            {hasPhoto ? (
              <>
                <AppIcon name="check-circle" size={40} className="text-green" />
                <span className="text-[13px] font-medium text-green">Photo captured</span>
              </>
            ) : (
              <>
                <AppIcon name="camera" size={40} className="text-slate-300" />
                <span className="text-[13px] text-slate-400">Tap to capture</span>
              </>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="lg" fullWidth={false} className="flex-1" onClick={() => setStep(2)}>Back</Button>
            <Button variant="primary" size="lg" fullWidth={false} className="flex-[2]" onClick={() => setStep(4)}>Review issue</Button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="space-y-4">
          <div>
            <h1 className="text-lg font-bold text-slate-900">Review issue</h1>
            <p className="text-[13px] text-slate-500">Confirm report details before filing</p>
          </div>
          <Card variant="surface" className="space-y-2">
            <div className="flex justify-between text-[13px]"><span className="text-slate-500">Outlet</span><span className="font-medium text-slate-900">{outletId}</span></div>
            <div className="flex justify-between text-[13px]"><span className="text-slate-500">Category</span><span className="font-medium text-slate-900">{category}</span></div>
            <div className="flex justify-between text-[13px]"><span className="text-slate-500">Detail</span><span className="font-medium text-slate-900">{detail}</span></div>
            <div className="flex justify-between text-[13px]"><span className="text-slate-500">Evidence</span><span className="font-medium text-slate-900">{hasPhoto ? "1 photo attached" : "None"}</span></div>
          </Card>
          <div className="space-y-2 pt-2">
            <Button variant="primary" size="lg" onClick={handleSaveAndSend}>Save and send</Button>
            <Button variant="secondary" size="md" onClick={() => setStep(1)}>Edit details</Button>
          </div>
        </div>
      )}
    </div>
  );
}
