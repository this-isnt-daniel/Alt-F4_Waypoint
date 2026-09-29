import { useEffect } from "react";
import { cn } from "@/lib/cn";

export interface ToastProps {
  message: string;
  visible: boolean;
  onClose?: () => void;
  durationMs?: number;
  className?: string;
}

export function Toast({
  message,
  visible,
  onClose,
  durationMs = 4000,
  className,
}: ToastProps) {
  useEffect(() => {
    if (visible && onClose) {
      const timer = setTimeout(() => {
        onClose();
      }, durationMs);
      return () => clearTimeout(timer);
    }
  }, [visible, onClose, durationMs]);

  if (!visible) return null;

  return (
    <div
      className={cn(
        "fixed bottom-6 left-1/2 -translate-x-1/2 z-50 max-w-sm w-[90%] bg-surface text-ink border border-line shadow-2 rounded-btn px-4 py-3 flex items-center justify-between gap-3 text-sm font-medium animate-in fade-in slide-in-from-bottom-3",
        className,
      )}
      aria-live="polite"
      role="status"
    >
      <div className="flex items-center gap-2">
        <span className="text-green font-bold" aria-hidden="true">
          ✓
        </span>
        <span>{message}</span>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="text-ink-muted text-xs hover:text-ink"
          aria-label="Close notification"
        >
          ✕
        </button>
      )}
    </div>
  );
}
