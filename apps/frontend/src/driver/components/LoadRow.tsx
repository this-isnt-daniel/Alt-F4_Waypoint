import { Check, Flag, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/cn";

export interface LoadRowProps {
  title: string; // "OUT058 · 12 units"
  subline?: string; // "10 deliverable · 2 return" (flagged only)
  state: "matches" | "flagged";
  expanded?: boolean;
  onToggle?: () => void;
}

export function LoadRow({
  title,
  subline,
  state,
  expanded,
  onToggle,
}: LoadRowProps) {
  const flagged = state === "flagged";
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={flagged ? !!expanded : undefined}
      className={cn(
        "flex w-full items-center gap-3 rounded-card border p-4 text-left transition-colors",
        flagged
          ? "border-warning/40 bg-warning-fill/40"
          : "border-line bg-surface hover:bg-raised/40",
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "grid h-9 w-9 shrink-0 place-items-center rounded-btn",
          flagged ? "bg-warning-fill text-warning" : "bg-raised text-ink-muted",
        )}
      >
        {flagged ? <Flag size={18} /> : <Check size={18} />}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate font-semibold text-ink">{title}</span>
        {subline && (
          <span className="block text-sm text-ink-muted">{subline}</span>
        )}
      </span>
      <span
        className={cn(
          "inline-flex items-center gap-1 text-sm font-medium",
          flagged ? "text-warning" : "text-ink-muted",
        )}
      >
        {flagged ? "Flagged" : "Matches"}
        {flagged && (expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />)}
      </span>
    </button>
  );
}
