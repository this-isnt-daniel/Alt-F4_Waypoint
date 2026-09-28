import { type ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface BannerProps {
  tone?: "warning" | "info" | "success" | "danger";
  title?: string;
  body: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function Banner({
  tone = "warning",
  title,
  body,
  action,
  className,
}: BannerProps) {
  const toneStyles = {
    warning: "bg-warning-fill text-ink border-warning/30",
    info: "bg-raised text-ink border-line",
    success: "bg-success-fill text-ink border-success/30",
    danger: "bg-danger-fill text-ink border-danger/30",
  };

  const iconGlyphs = {
    warning: "⚠",
    info: "ℹ",
    success: "✓",
    danger: "✕",
  };

  return (
    <div
      className={cn(
        "rounded-card p-3.5 border text-sm mb-4 flex items-start gap-3",
        toneStyles[tone],
        className,
      )}
      role="alert"
    >
      <span className="text-base shrink-0 font-bold" aria-hidden="true">
        {iconGlyphs[tone]}
      </span>
      <div className="min-w-0 flex-1">
        {title && <div className="font-bold text-ink mb-0.5">{title}</div>}
        <div className="text-xs leading-relaxed opacity-95">{body}</div>
        {action && <div className="mt-2">{action}</div>}
      </div>
    </div>
  );
}
