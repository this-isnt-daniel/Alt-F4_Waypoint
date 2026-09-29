import { useState, type ReactNode } from "react";
import { type DriverStop } from "@/driver/data/driverContent";
import { Button } from "./Button";
import { Chip } from "./Chip";
import { AppIcon, type AppIconName } from "./AppIcon";
import { cn } from "@/lib/cn";

export interface StopBottomSheetProps {
  stop: DriverStop;
  etaMin: number;
  windowClosingMin: number;
  onMarkArrived: () => void;
  onChat?: () => void;
  onCall?: () => void;
  onDetails?: () => void;
  open?: never;
  onClose?: never;
  title?: never;
  subtitle?: never;
  children?: never;
}

export interface ModalBottomSheetProps {
  open?: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  children?: ReactNode;
  stop?: never;
  etaMin?: never;
  windowClosingMin?: never;
  onMarkArrived?: never;
  onChat?: never;
  onCall?: never;
  onDetails?: never;
}

export type BottomSheetProps = StopBottomSheetProps | ModalBottomSheetProps;

export function BottomSheet(props: BottomSheetProps) {
  const [expanded, setExpanded] = useState(false);

  // Modal variant for forms / confirmation sheets
  if ("onClose" in props || "open" in props) {
    if (!props.open) return null;
    return (
      <div
        className="fixed inset-0 z-50 flex items-end justify-center bg-black/40"
        onClick={props.onClose}
      >
        <div
          className="max-h-[85vh] w-full max-w-[430px] overflow-y-auto rounded-t-2xl border-t border-line bg-surface p-4 shadow-xl"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between pb-2 border-b border-line mb-3">
            <div>
              {props.title && (
                <h3 className="text-base font-bold text-ink">{props.title}</h3>
              )}
              {props.subtitle && (
                <p className="text-xs text-ink-muted">{props.subtitle}</p>
              )}
            </div>
            <button
              type="button"
              onClick={props.onClose}
              className="p-1 rounded-lg text-ink-muted hover:bg-raised"
              aria-label="Close"
            >
              <AppIcon name="x" size={18} />
            </button>
          </div>
          <div>{props.children}</div>
        </div>
      </div>
    );
  }

  // Active Trip Stop Bottom Sheet variant
  if (!("stop" in props) || !props.stop) {
    return null;
  }

  const {
    stop,
    etaMin,
    windowClosingMin,
    onMarkArrived,
    onChat,
    onCall,
    onDetails,
  } = props as StopBottomSheetProps;

  const tempIcon: AppIconName = stop.temp.includes("Chilled")
    ? "snowflake"
    : "package";
  const dockIcon: AppIconName =
    stop.dock === "Mall bay" ? "building" : "package";
  const parkingIcon: AppIconName =
    stop.parking === "Van only" || stop.parking === "Mall dock"
      ? "truck"
      : "pin";

  return (
    <div className="w-full bg-white border-t border-slate-200 rounded-t-2xl shadow-lg px-4 pt-3 pb-5">
      {/* Handle */}
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="w-full flex justify-center pb-2"
          aria-label={expanded ? "Collapse details" : "Expand details"}
        >
          <div className="w-10 h-1 rounded-full bg-slate-300" />
        </button>

        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <span className="text-[10px] font-bold tracking-wider uppercase text-green">
              NEXT
            </span>
            <div className="text-[15px] font-bold text-slate-900">
              {stop.outletId}
            </div>
            <div className="text-[13px] text-slate-500">{stop.name}</div>
          </div>
          <div className="text-right">
            <div className="text-[12px] font-semibold text-slate-900">
              ETA {etaMin} min
            </div>
            <div className="text-[11px] text-amber-600">
              Closes in {windowClosingMin} min
            </div>
          </div>
        </div>

        {/* Restriction chips */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          <Chip
            kind="restriction"
            category="temperature"
            label={stop.temp}
            icon={tempIcon}
          />
          <Chip
            kind="restriction"
            category="dock"
            label={stop.dock}
            icon={dockIcon}
          />
          {stop.parking !== "Normal" && (
            <Chip
              kind="restriction"
              category="access"
              label={stop.parking}
              icon={parkingIcon}
            />
          )}
        </div>

        {/* Expanded content */}
        {expanded && (
          <div className="space-y-2 mb-3 py-3 border-t border-slate-100">
            {stop.dockDetail && (
              <div className="text-[12px] text-slate-500">
                Dock: {stop.dock} · {stop.dockDetail}
              </div>
            )}
            {stop.instructions && (
              <div className="text-[12px] text-slate-700">
                {stop.instructions}
              </div>
            )}
            <div className="text-[12px] text-slate-500">
              Window: {stop.window}
            </div>
          </div>
        )}

        {/* Actions */}
        <Button variant="primary" size="lg" onClick={onMarkArrived}>
          Mark arrived
        </Button>

        {/* Secondary action row */}
        <div className="flex items-center justify-center gap-6 mt-3">
          {onChat && (
            <button
              type="button"
              onClick={onChat}
              className="flex flex-col items-center gap-0.5 text-slate-500 hover:text-green"
            >
              <AppIcon name="message" size={20} />
              <span className="text-[10px]">Chat</span>
            </button>
          )}
          {onCall && (
            <button
              type="button"
              onClick={onCall}
              className="flex flex-col items-center gap-0.5 text-slate-500 hover:text-green"
            >
              <AppIcon name="phone" size={20} />
              <span className="text-[10px]">Call</span>
            </button>
          )}
          {onDetails && (
            <button
              type="button"
              onClick={onDetails}
              className="flex flex-col items-center gap-0.5 text-slate-500 hover:text-green"
            >
              <AppIcon name="list" size={20} />
              <span className="text-[10px]">Details</span>
            </button>
          )}
        </div>
      </div>
  );
}
