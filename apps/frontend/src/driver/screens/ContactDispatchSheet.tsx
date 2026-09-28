import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Toast } from "@/driver/components/Toast";
import { CONTACT_DISPATCH_PRESETS, VEHICLE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function ContactDispatchSheet() {
  const { push } = useNavigator();
  const { addSyncRecord, connection } = useDriverState();

  const [selectedPreset, setSelectedPreset] = useState<string>("Running late");
  const [toastVisible, setToastVisible] = useState<boolean>(false);

  const handleSendMessage = () => {
    addSyncRecord({
      type: "chat-message",
      state: connection === "online" ? "synced" : "pending",
      hasPhoto: false,
      pinVerified: false,
    });
    setToastVisible(true);
    setTimeout(() => {
      push("active-trip");
    }, 1000);
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 pt-6">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-green tracking-wider uppercase">
          Dispatch Support
        </span>
        <h1 className="text-xl font-extrabold text-ink">Need dispatch assistance?</h1>
        <p className="text-xs text-ink-muted">
          {VEHICLE.id} · {VEHICLE.depot} planning office
        </p>
      </div>

      <Card variant="surface" className="space-y-3">
        <div className="text-xs font-bold text-ink-muted uppercase">Select Preset Issue</div>
        <div className="grid grid-cols-2 gap-2">
          {CONTACT_DISPATCH_PRESETS.map((preset) => {
            const isSelected = selectedPreset === preset;
            return (
              <button
                key={preset}
                type="button"
                onClick={() => setSelectedPreset(preset)}
                className={`p-3 rounded-btn border text-xs font-semibold text-left transition-colors ${
                  isSelected
                    ? "border-green bg-green-fill text-green-ink"
                    : "border-line bg-surface text-ink hover:bg-raised"
                }`}
              >
                {preset}
              </button>
            );
          })}
        </div>
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={handleSendMessage}>
          Send preset message to dispatch
        </Button>
        <Button
          variant="secondary"
          size="md"
          onClick={() => push("call-overlay", { role: "dispatcher" })}
        >
          Call dispatcher
        </Button>
        <Button variant="ghost" size="md" onClick={() => push("active-trip")}>
          Back to map
        </Button>
      </div>

      <Toast
        message="Preset notification queued for dispatch"
        visible={toastVisible}
        onClose={() => setToastVisible(false)}
      />
    </div>
  );
}
