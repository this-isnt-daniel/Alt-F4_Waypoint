import { type ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface ErrorStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  secondaryAction?: ReactNode;
  className?: string;
}

export function ErrorState({
  icon = "⚠️",
  title,
  description,
  action,
  secondaryAction,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "p-6 text-center bg-surface border border-line rounded-card flex flex-col items-center justify-center my-6 shadow-1",
        className,
      )}
      role="alert"
    >
      <div className="grid h-16 w-16 place-items-center rounded-circle bg-danger-fill text-danger text-2xl mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-bold text-ink mb-1">{title}</h3>
      <p className="text-sm text-ink-muted max-w-xs mb-6 leading-relaxed">
        {description}
      </p>
      <div className="w-full space-y-2">
        {action}
        {secondaryAction}
      </div>
    </div>
  );
}
