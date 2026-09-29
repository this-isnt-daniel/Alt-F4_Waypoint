import { type ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface HeroBandProps {
  label: string;
  title: string;
  subline?: string;
  meta?: ReactNode;
  className?: string;
}

export function HeroBand({
  label,
  title,
  subline,
  meta,
  className,
}: HeroBandProps) {
  return (
    <div
      className={cn(
        "bg-hero text-hero-ink p-5 rounded-b-[24px] shadow-2 mb-4",
        className,
      )}
    >
      <div className="text-2xs font-bold tracking-wider uppercase text-hero-label mb-1">
        {label}
      </div>
      <h1 className="text-xl font-extrabold tracking-tight mb-1">{title}</h1>
      {subline && <p className="text-sm opacity-90">{subline}</p>}
      {meta && <div className="mt-3 pt-3 border-t border-hero-label/20">{meta}</div>}
    </div>
  );
}
