import { Check, Circle, Flag } from "lucide-react";
import { cn } from "@/lib/cn";

export type CheckState = "pending" | "delivered" | "flagged";

const VIEW: Record<
  CheckState,
  { icon: typeof Check; cls: string; label: string }
> = {
  pending: { icon: Circle, cls: "text-slate-400", label: "Awaiting check" },
  delivered: { icon: Check, cls: "text-emerald-500", label: "Delivered" },
  flagged: { icon: Flag, cls: "text-rose-500", label: "Not handed over" },
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
    <div className={cn(
      "flex items-center gap-3 rounded-lg border p-4 transition-colors",
      state === "flagged" ? "border-rose-200 bg-rose-50" : "border-slate-200 bg-white"
    )}>
      <button
        type="button"
        onClick={onRowTap}
        className="flex min-w-0 flex-1 items-center gap-3 text-left cursor-pointer"
      >
        <span
          aria-hidden="true"
          className={cn("grid h-7 w-7 place-items-center", v.cls)}
        >
          <Icon size={22} strokeWidth={state === "pending" ? 1.5 : 2.5} />
        </span>
        <span className="min-w-0">
          <span className="block truncate font-semibold text-slate-900 text-[15px]">
            {name} <span className="text-slate-500">×{qty}</span>
          </span>
          <span className="block text-[13px] text-slate-500">{meta}</span>
        </span>
      </button>
      <span className={cn("hidden text-[13px] font-medium sm:inline", v.cls)}>
        {v.label}
      </span>
      {state !== "flagged" && (
        <button
          type="button"
          onClick={onFlag}
          aria-label={`Flag ${name} as not handed over`}
          className="grid h-10 w-10 shrink-0 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors cursor-pointer"
        >
          <Flag size={18} />
        </button>
      )}
    </div>
  );
}
