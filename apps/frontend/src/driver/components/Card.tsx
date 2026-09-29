import { cn } from "@/lib/cn";
import { type ReactNode } from "react";

export function Card({
  variant = "surface",
  children,
  className,
}: {
  variant?: "surface" | "raised";
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl p-4",
        variant === "surface"
          ? "bg-white border border-slate-200"
          : "bg-slate-50 border border-slate-200",
        className,
      )}
    >
      {children}
    </div>
  );
}
