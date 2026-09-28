import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Toast } from "@/driver/components/Toast";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";
import { isSafeExternalHref } from "@/lib/security";

export function CallOverlayScreen() {
  const { route, push, back } = useNavigator();
  const outletId = route.params.outletId ?? "OUT047";
  const stop = TRIP_1_STOPS.find((s) => s.outletId === outletId) ?? TRIP_1_STOPS[1]!;

  const [toastVisible, setToastVisible] = useState<boolean>(false);

  const handleCall = () => {
    const safeHref = "tel:+94770000042";
    if (isSafeExternalHref(safeHref)) {
      setToastVisible(true);
      setTimeout(() => {
        window.location.href = safeHref;
      }, 800);
    }
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 pt-12 text-center">
      <div className="grid h-20 w-20 place-items-center rounded-circle bg-green-fill text-green text-3xl mx-auto mb-2">
        📞
      </div>

      <div className="space-y-1">
        <h1 className="text-xl font-extrabold text-ink">Call {stop.manager}?</h1>
        <p className="text-xs text-ink-muted">
          Store manager · {stop.outletId} · {stop.phoneMasked}
        </p>
      </div>

      <Card variant="raised" className="text-2xs text-ink-muted max-w-xs mx-auto leading-relaxed">
        Your personal number stays hidden. Standard call rates may apply.
      </Card>

      <div className="space-y-2 pt-4 max-w-xs mx-auto">
        <Button variant="primary" size="lg" onClick={handleCall}>
          Call
        </Button>
        <Button variant="secondary" size="md" onClick={() => back()}>
          Cancel
        </Button>
      </div>

      <Toast
        message="Opening masked dialer..."
        visible={toastVisible}
        onClose={() => setToastVisible(false)}
      />
    </div>
  );
}
