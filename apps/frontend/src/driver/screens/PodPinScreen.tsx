import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Delete } from "lucide-react";

export function PodPinScreen() {
  const { push, route, back } = useNavigator();
  const [pin, setPin] = useState("");
  const isCleanHandover = route.params.cleanHandover === "true";

  const addDigit = (d: string) => {
    if (pin.length < 4) setPin(pin + d);
  };

  const removeDigit = () => setPin(pin.slice(0, -1));

  const handleSubmit = () => {
    if (pin.length === 4) push("delivery-complete");
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-6">
      {/* Stepper with single source of truth */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-6">
        <span className="text-[13px] font-bold text-slate-400 uppercase tracking-wider">
          {isCleanHandover ? "Clean handover" : "Step 2 of 2"}
        </span>
        <span className="text-[13px] font-bold text-slate-900 uppercase tracking-wider">
          {isCleanHandover ? "No photo required" : "Confirmation"}
        </span>
      </div>

      <div className="mb-6">
        <h1 className="text-[24px] font-bold text-slate-900 mb-1">Manager PIN</h1>
        <p className="text-[15px] text-slate-500">
          Enter the 4-digit PIN. Ask Joseph Vijay for the PIN.
        </p>
      </div>

      {/* PIN display */}
      <div className="flex justify-center gap-4 py-6 mb-4">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`w-14 h-16 rounded-xl border-2 flex items-center justify-center text-3xl font-bold transition-colors ${
              pin[i] ? "border-green bg-green/5 text-slate-900" : "border-slate-200 bg-slate-50"
            }`}
            style={pin[i] ? { borderColor: "var(--c-green)" } : {}}
          >
            {pin[i] ? "•" : ""}
          </div>
        ))}
      </div>

      {/* Keypad */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        {["1","2","3","4","5","6","7","8","9"].map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => addDigit(d)}
            className="h-16 rounded-xl bg-slate-50 text-[22px] font-semibold text-slate-900 hover:bg-slate-100 transition-colors active:scale-95 cursor-pointer"
          >
            {d}
          </button>
        ))}
        <button
          type="button"
          onClick={() => push("delivery-complete")}
          className="h-16 rounded-xl text-[14px] font-semibold text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
        >
          Can't get PIN?
        </button>
        <button
          type="button"
          onClick={() => addDigit("0")}
          className="h-16 rounded-xl bg-slate-50 text-[22px] font-semibold text-slate-900 hover:bg-slate-100 transition-colors active:scale-95 cursor-pointer"
        >
          0
        </button>
        <button
          type="button"
          onClick={removeDigit}
          className="h-16 rounded-xl flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors active:scale-95 cursor-pointer"
          aria-label="Delete"
        >
          <Delete size={24} />
        </button>
      </div>

      <div className="mt-auto space-y-3">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={pin.length < 4}
          className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ backgroundColor: "var(--c-green)" }}
        >
          Confirm PIN
        </button>
        {!isCleanHandover && (
          <button
            type="button"
            onClick={back}
            className="w-full py-3 text-[14px] font-semibold text-slate-400 hover:text-slate-600 cursor-pointer"
          >
            Back to Photo
          </button>
        )}
      </div>
    </div>
  );
}
