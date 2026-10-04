import { CloudOff, RefreshCw, WifiOff } from "lucide-react";
import { cn } from "@/lib/cn";

export type ConnectionTone =
  | "online"
  | "offline"
  | "pending"
  | "syncing"
  | "success"
  | "failed"
  | "inReview"
  | "routeUpdated"
  | "forwarded";

const ATTENTION: ConnectionTone[] = [
  "offline",
  "pending",
  "syncing",
  "failed",
  "inReview",
  "routeUpdated",
];

const LABEL: Record<ConnectionTone, string> = {
  online: "Signal good",
  offline: "No signal",
  pending: "Saved",
  syncing: "Syncing",
  success: "Synced",
  failed: "Sync failed",
  inReview: "In review",
  routeUpdated: "Route updated",
  forwarded: "Sent",
};

const CLASS: Record<ConnectionTone, string> = {
  online: "",
  offline: "text-amber-800 bg-amber-50 border border-amber-300 shadow-sm",
  pending: "text-offline bg-offline-fill",
  syncing: "text-offline bg-offline-fill",
  success: "",
  failed: "text-danger bg-danger-fill",
  inReview: "text-warning bg-warning-fill",
  routeUpdated: "text-offline bg-offline-fill",
  forwarded: "text-offline bg-offline-fill",
};

export function ConnectionIndicator({
  tone,
  count,
}: {
  tone: ConnectionTone;
  count?: number;
}) {
  const needsPill = ATTENTION.includes(tone);
  if (!needsPill) {
    // quiet dot + accessible label; NO visible "ONLINE"/"SYNCED" text
    return (
      <span className="inline-flex items-center gap-1.5" title={LABEL[tone]}>
        <span
          aria-hidden="true"
          className={cn(
            "h-2.5 w-2.5 rounded-full",
            tone === "success" || tone === "online" ? "bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.7)]" : "bg-offline",
            tone === "syncing" && "animate-pulse",
          )}
        />
        <span className="sr-only">
          {LABEL[tone]}
          {count ? `, ${count} pending` : ""}
        </span>
      </span>
    );
  }
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full whitespace-nowrap px-2.5 py-1 text-xs font-semibold",
        CLASS[tone],
      )}
    >
      {tone === "offline" && <WifiOff size={13} aria-hidden="true" />}
      {tone === "syncing" && (
        <RefreshCw size={14} className="animate-spin" aria-hidden="true" />
      )}
      <span>
        {LABEL[tone]}
        {count ? ` · ${count}` : ""}
      </span>
    </span>
  );
}
