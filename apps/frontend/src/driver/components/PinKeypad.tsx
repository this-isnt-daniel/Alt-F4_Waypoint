import { useState } from "react";
import { maskPin } from "@/lib/security";
import { cn } from "@/lib/cn";

export interface PinKeypadProps {
  managerName: string;
  onPinSubmit: (pin: string) => void;
  onReportUnavailable?: () => void;
  className?: string;
}

export function PinKeypad({
  managerName,
  onPinSubmit,
  onReportUnavailable,
  className,
}: PinKeypadProps) {
  const [pin, setPin] = useState<string>("");
  const [attemptsLeft, setAttemptsLeft] = useState<number | null>(null);

  const handleDigit = (digit: string) => {
    if (pin.length < 4) {
      const nextPin = pin + digit;
      setPin(nextPin);
      if (nextPin.length === 4) {
        // Submit on 4th digit
        setTimeout(() => {
          if (nextPin === "1234" || nextPin === "0000" || nextPin.length === 4) {
            onPinSubmit(nextPin);
          } else {
            setAttemptsLeft((prev) => (prev === null ? 2 : prev - 1));
            setPin("");
          }
        }, 150);
      }
    }
  };

  const handleBackspace = () => {
    setPin((prev) => prev.slice(0, -1));
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div className="text-center py-2">
        <p className="text-xs text-ink-muted mb-3">
          Ask {managerName} for the receiver PIN. The PIN is hidden after confirmation.
        </p>

        {/* Masked Dots */}
        <div className="flex justify-center gap-3 my-3" aria-label={`PIN entered: ${maskPin(pin)}`}>
          {[0, 1, 2, 3].map((index) => {
            const hasValue = pin.length > index;
            return (
              <div
                key={index}
                className={cn(
                  "h-11 w-11 rounded-circle border flex items-center justify-center text-xl font-bold transition-all",
                  hasValue
                    ? "border-green bg-green-fill text-green-ink scale-105"
                    : "border-line bg-raised text-ink-muted",
                )}
              >
                {hasValue ? "•" : ""}
              </div>
            );
          })}
        </div>

        {attemptsLeft !== null && (
          <div className="text-xs text-danger font-semibold mt-1">
            {attemptsLeft} attempts remaining
          </div>
        )}
      </div>

      {/* Numeric Keypad Grid */}
      <div className="grid grid-cols-3 gap-2.5 max-w-[280px] mx-auto">
        {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((digit) => (
          <button
            key={digit}
            type="button"
            onClick={() => handleDigit(digit)}
            className="h-14 rounded-btn border border-line bg-surface text-xl font-bold text-ink hover:bg-raised active:bg-raised focus:outline-none focus:ring-2 focus:ring-green"
          >
            {digit}
          </button>
        ))}
        <div />
        <button
          type="button"
          onClick={() => handleDigit("0")}
          className="h-14 rounded-btn border border-line bg-surface text-xl font-bold text-ink hover:bg-raised active:bg-raised focus:outline-none focus:ring-2 focus:ring-green"
        >
          0
        </button>
        <button
          type="button"
          onClick={handleBackspace}
          aria-label="Delete digit"
          className="h-14 rounded-btn border border-line bg-surface text-lg font-semibold text-ink-muted hover:bg-raised active:bg-raised focus:outline-none focus:ring-2 focus:ring-green"
        >
          ⌫
        </button>
      </div>

      {onReportUnavailable && (
        <div className="text-center pt-2">
          <button
            type="button"
            onClick={onReportUnavailable}
            className="text-xs text-green font-semibold underline hover:opacity-80"
          >
            Can’t get the PIN? Report receiver unavailable
          </button>
        </div>
      )}
    </div>
  );
}
