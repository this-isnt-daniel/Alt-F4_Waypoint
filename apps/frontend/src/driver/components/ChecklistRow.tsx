import { Check, Circle, Flag } from "lucide-react";
import { cn } from "@/lib/cn";

export type CheckState = "pending" | "delivered" | "flagged";

const VIEW: Record<
  CheckState,
  { icon: typeof Check; cls: string; label: string }
> = {
  pending: { icon: Circle, cls: "text-ink-muted", label: "Awaiting check" },
  delivered: { icon: Check, cls: "text-success", label: "Delivered" },
  flagged: { icon: Flag, cls: "text-warning", label: "Not handed over" },
};

export function ChecklistRow({
  name,
  qty,
  meta,
  state,
  onRowTap,
  onFlag,
}: {
  name: string;
  qty: number;
  meta: string;
  state: CheckState;
  onRowTap: () => void;
  onFlag: () => void;
}) {
  const v = VIEW[state];
  const Icon = v.icon;
  return (
    <div className="flex items-center gap-3 rounded-card border border-line bg-surface p-4">
      <button
        type="button"
        onClick={onRowTap}
        className="flex min-w-0 flex-1 items-center gap-3 text-left"
      >
        <span
          aria-hidden="true"
          className={cn("grid h-7 w-7 place-items-center", v.cls)}
        >
          <Icon size={22} strokeWidth={state === "pending" ? 1.5 : 2.5} />
        </span>
        <span className="min-w-0">
          <span className="block truncate font-semibold text-ink">
            {name} ×{qty}
          </span>
          <span className="block text-sm text-ink-muted">{meta}</span>
        </span>
      </button>
      <span className={cn("hidden text-sm font-medium sm:inline", v.cls)}>
        {v.label}
      </span>
      {state !== "flagged" && (
        <button
          type="button"
          onClick={onFlag}
          aria-label={`Flag ${name} as not handed over`}
          className="grid h-12 w-12 shrink-0 place-items-center rounded-btn text-ink-muted hover:bg-raised hover:text-ink transition-colors"
        >
          <Flag size={18} />
        </button>
      )}
    </div>
  );
}
