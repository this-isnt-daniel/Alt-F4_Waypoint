import { type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { AppIcon } from "./AppIcon";

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "p-8 text-center bg-surface border border-line rounded-card flex flex-col items-center justify-center my-6",
        className,
      )}
    >
      <div className="grid h-16 w-16 place-items-center rounded-full bg-raised text-ink-muted mb-4">
        {icon ?? <AppIcon name="package" size={28} />}
      </div>
      <h3 className="text-lg font-bold text-ink mb-1">{title}</h3>
      <p className="text-sm text-ink-muted max-w-xs mb-6 leading-relaxed">
        {description}
      </p>
      {action}
    </div>
  );
}
