import { useState, type ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface ListRowProps {
  title: ReactNode;
  subtitle?: ReactNode;
  status?: "pending" | "matches" | "flagged" | "delivered" | "partial" | "failed" | "returned" | "syncing";
  statusLabel?: string;
  trailing?: ReactNode;
  expandable?: boolean;
  expandedContent?: ReactNode;
  onClick?: () => void;
  className?: string;
}

export function ListRow({
  title,
  subtitle,
  status = "pending",
  statusLabel,
  trailing,
  expandable = false,
  expandedContent,
  onClick,
  className,
}: ListRowProps) {
  const [expanded, setExpanded] = useState<boolean>(false);

  const statusIcons: Record<string, string> = {
    pending: "○",
    matches: "✓",
    flagged: "⚠",
    delivered: "✓",
    partial: "⚠",
    failed: "✕",
    returned: "↩",
    syncing: "⟳",
  };

  const statusStyles: Record<string, string> = {
    pending: "bg-raised text-ink-muted border-line",
    matches: "bg-raised text-ink border-line",
    flagged: "bg-warning-fill text-warning border-warning/30 font-semibold",
    delivered: "bg-success-fill text-success border-success/30",
    partial: "bg-warning-fill text-warning border-warning/30",
    failed: "bg-danger-fill text-danger border-danger/30",
    returned: "bg-offline-fill text-offline border-line",
    syncing: "bg-offline-fill text-offline border-line animate-spin",
  };

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else if (expandable) {
      setExpanded((prev) => !prev);
    }
  };

  return (
    <div
      className={cn(
        "rounded-btn border border-line bg-surface p-3.5 mb-2 transition-colors",
        (onClick || expandable) && "cursor-pointer hover:border-green/40",
        className,
      )}
      onClick={handleClick}
      role={onClick || expandable ? "button" : undefined}
      tabIndex={onClick || expandable ? 0 : undefined}
      onKeyDown={(e) => {
        if ((onClick || expandable) && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span
            className={cn(
              "grid h-8 w-8 shrink-0 place-items-center rounded-circle border text-xs font-bold",
              statusStyles[status],
            )}
            aria-hidden="true"
          >
            {statusIcons[status]}
          </span>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-ink truncate">{title}</div>
            {subtitle && <div className="text-xs text-ink-muted truncate">{subtitle}</div>}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {statusLabel && (
            <span className="text-xs font-medium text-ink-muted">{statusLabel}</span>
          )}
          {trailing}
          {expandable && (
            <span className="text-ink-muted text-xs" aria-hidden="true">
              {expanded ? "▲" : "▼"}
            </span>
          )}
        </div>
      </div>
      {expandable && expanded && expandedContent && (
        <div className="mt-3 pt-3 border-t border-line text-sm text-ink-muted">
          {expandedContent}
        </div>
      )}
    </div>
  );
}
