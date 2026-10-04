import { type ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface KeyValueRowProps {
  label: string;
  value: ReactNode;
  trailing?: ReactNode;
  emphasis?: "normal" | "strong";
  className?: string;
}

export function KeyValueRow({
  label,
  value,
  trailing,
  emphasis = "normal",
  className,
}: KeyValueRowProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between py-2.5 border-b border-line/50 last:border-0 text-sm",
        className,
      )}
    >
      <span className="text-ink-muted">{label}</span>
      <div className="flex items-center gap-2 text-right">
        <span
          className={cn(
            "text-ink",
            emphasis === "strong" ? "font-bold text-base" : "font-medium",
          )}
        >
          {value}
        </span>
        {trailing}
      </div>
    </div>
  );
}
