import { CloudOff, RefreshCw } from "lucide-react";
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
  online: "Online",
  offline: "Offline",
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
  offline: "text-offline bg-offline-fill",
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
            "h-2 w-2 rounded-full",
            tone === "success" || tone === "online" ? "bg-success" : "bg-offline",
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
        "inline-flex items-center gap-1.5 rounded-pill px-2.5 py-1 text-xs font-semibold",
        CLASS[tone],
      )}
    >
      {tone === "offline" && <CloudOff size={14} aria-hidden="true" />}
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
