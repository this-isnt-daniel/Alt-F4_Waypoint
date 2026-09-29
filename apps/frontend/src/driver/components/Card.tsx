import { type HTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "surface" | "raised" | "hero";
  children: ReactNode;
}

export function Card({
  variant = "surface",
  className,
  children,
  ...props
}: CardProps) {
  const variantStyles = {
    surface: "bg-surface text-ink border border-line shadow-1",
    raised: "bg-raised text-ink border border-line",
    hero: "bg-hero text-hero-ink shadow-2",
  };

  return (
    <div
      className={cn("rounded-card p-4 transition-colors", variantStyles[variant], className)}
      {...props}
    >
      {children}
    </div>
  );
}
