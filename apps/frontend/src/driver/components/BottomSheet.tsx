import { type ReactNode } from "react";
import { type DriverStop } from "@/driver/data/driverContent";
import { X } from "lucide-react";

export interface StopBottomSheetProps {
  stop: DriverStop;
  etaMin: number;
  windowClosingMin: number;
  onMarkArrived: () => void;
  onChat?: () => void;
  onCall?: () => void;
  onDetails?: () => void;
  onFailed?: () => void;
  onContactDispatch?: () => void;
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
  // Modal variant for forms / confirmation sheets
  if ("onClose" in props || "open" in props) {
    if (!props.open) return null;
    return (
      <div
        className="fixed inset-0 z-50 flex items-end justify-center bg-black/40"
        onClick={props.onClose}
      >
        <div
          className="max-h-[85vh] w-full overflow-y-auto rounded-t-2xl border-t border-line bg-surface p-4 shadow-xl"
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
              <X size={18} />
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
    onFailed,
    onContactDispatch,
  } = props as StopBottomSheetProps;

  return (
    <div className="w-full bg-white rounded-t-3xl pt-5 pb-6 px-6">
      {/* Header Info */}
      <div className="mb-5">
        <span className="text-[12px] font-bold tracking-wider uppercase text-slate-500 mb-1.5 block">
          NEXT STOP
        </span>
        <div className="text-[22px] font-bold text-slate-900 leading-tight">
          {stop.outletId}
        </div>
        <div className="text-[16px] text-slate-600 mb-3">{stop.name}</div>
        
        <div className="flex items-center gap-2 text-[15px] font-semibold text-slate-800 mb-1">
          <span>{etaMin} min</span>
          <span className="text-slate-300">•</span>
          <span>5.4 km</span>
        </div>
        <div className="text-[14px] text-slate-500 mb-4">
          Window closes {stop.window.split("–")[1] || stop.window}
        </div>

        {/* Tags / Restrictions */}
        <div className="flex flex-wrap gap-2">
          {stop.temp && (
            <span className="text-[13px] font-medium text-slate-700 bg-slate-100 px-2.5 py-1 rounded-md">
              {stop.temp}
            </span>
          )}
          {stop.dock && (
            <span className="text-[13px] font-medium text-slate-700 bg-slate-100 px-2.5 py-1 rounded-md">
              {stop.dock}
            </span>
          )}
          {stop.parking !== "Normal" && (
            <span className="text-[13px] font-medium text-slate-700 bg-slate-100 px-2.5 py-1 rounded-md">
              {stop.parking}
            </span>
          )}
        </div>
      </div>

      {/* Primary Action */}
      <div className="mb-5">
        <button
          type="button"
          onClick={onMarkArrived}
          className="w-full bg-green hover:bg-[#008A57] text-white font-bold text-[16px] py-4 rounded-xl shadow-sm transition-colors cursor-pointer"
        >
          MARK ARRIVED
        </button>
      </div>

      {/* Secondary Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-100">
        {onCall && (
          <button
            type="button"
            onClick={onCall}
            className="text-[14px] font-semibold text-slate-500 hover:text-slate-800 cursor-pointer"
          >
            Call
          </button>
        )}
        {onDetails && (
          <button
            type="button"
            onClick={onDetails}
            className="text-[14px] font-semibold text-slate-500 hover:text-slate-800 cursor-pointer"
          >
            Details
          </button>
        )}
        {onContactDispatch && (
          <button
            type="button"
            onClick={onContactDispatch}
            className="text-[14px] font-semibold text-slate-500 hover:text-slate-800 cursor-pointer"
          >
            Dispatch
          </button>
        )}
        {onFailed && (
          <button
            type="button"
            onClick={onFailed}
            className="text-[14px] font-semibold text-slate-500 hover:text-rose-600 cursor-pointer"
          >
            Issue
          </button>
        )}
      </div>
    </div>
  );
}
