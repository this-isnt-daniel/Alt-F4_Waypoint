import { cn } from "@/lib/cn";

export function HeroBand({
  label,
  title,
  subline,
  className,
}: {
  label: string;
  title: string;
  subline?: string;
  className?: string;
}) {
  return (
    <div className={cn("bg-hero px-4 py-6 mb-4", className)}>
      <span className="text-[10px] font-bold tracking-wider uppercase text-hero-label">
        {label}
      </span>
      <h1 className="text-2xl font-extrabold text-hero-ink mt-1">{title}</h1>
      {subline && (
        <p className="text-[12px] text-hero-label mt-1 font-medium">{subline}</p>
      )}
    </div>
  );
}
