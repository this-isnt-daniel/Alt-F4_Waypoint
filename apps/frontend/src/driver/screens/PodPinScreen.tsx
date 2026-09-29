import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { AppIcon } from "@/driver/components/AppIcon";

export function PodPinScreen() {
  const { push } = useNavigator();
  const [pin, setPin] = useState("");

  const addDigit = (d: string) => {
    if (pin.length < 4) setPin(pin + d);
  };

  const removeDigit = () => setPin(pin.slice(0, -1));

  const handleSubmit = () => {
    if (pin.length === 4) push("delivery-complete");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Manager PIN</h1>
        <p className="text-[13px] text-slate-500">Step 2 of 2</p>
      </div>

      <p className="text-[13px] text-slate-500">
        Enter the 4-digit PIN. Ask Anjali Silva for the PIN.
      </p>

      {/* PIN display */}
      <div className="flex justify-center gap-3 py-4">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`w-12 h-14 rounded-lg border-2 flex items-center justify-center text-xl font-bold ${
              pin[i] ? "border-green bg-green-fill text-slate-900" : "border-slate-200 bg-white"
            }`}
          >
            {pin[i] ? "•" : ""}
          </div>
        ))}
      </div>

      {/* Keypad */}
      <div className="grid grid-cols-3 gap-2">
        {["1","2","3","4","5","6","7","8","9"].map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => addDigit(d)}
            className="h-14 rounded-lg bg-white border border-slate-200 text-lg font-semibold text-slate-900 hover:bg-slate-50 transition-colors"
          >
            {d}
          </button>
        ))}
        <button
          type="button"
          onClick={() => push("delivery-complete")}
          className="h-14 rounded-lg text-[13px] font-medium text-slate-500 hover:bg-slate-50"
        >
          Can't get PIN?
        </button>
        <button
          type="button"
          onClick={() => addDigit("0")}
          className="h-14 rounded-lg bg-white border border-slate-200 text-lg font-semibold text-slate-900 hover:bg-slate-50"
        >
          0
        </button>
        <button
          type="button"
          onClick={removeDigit}
          className="h-14 rounded-lg flex items-center justify-center text-slate-500 hover:bg-slate-50"
          aria-label="Delete"
        >
          <AppIcon name="arrow-left" size={20} />
        </button>
      </div>

      <Button variant="primary" size="lg" onClick={handleSubmit} disabled={pin.length < 4}>
        Confirm PIN
      </Button>
    </div>
  );
}
