import { type SyncState } from "@/driver/state/connection";
import { AppIcon, type AppIconName } from "./AppIcon";
import { cn } from "@/lib/cn";

export function SyncPill({ tone }: { tone: SyncState }) {
  if (tone === "idle" || tone === "success") {
    return null;
  }

  const labels: Record<string, string> = {
    saving: "Saving", pending: "Pending", syncing: "Syncing",
    failed: "Sync failed", inReview: "In review", routeUpdated: "Route updated",
    forwarded: "Sent",
  };

  const styles: Record<string, string> = {
    saving: "bg-raised text-ink-muted border-line",
    pending: "bg-raised text-ink-muted border-line",
    syncing: "bg-raised text-ink-muted border-line animate-pulse",
    failed: "bg-danger-fill text-danger border-danger/30",
    inReview: "bg-warning-fill text-warning border-warning/30",
    routeUpdated: "bg-raised text-ink-muted border-line",
    forwarded: "bg-raised text-ink-muted border-line",
  };

  const icons: Record<string, AppIconName> = {
    saving: "refresh", pending: "clock", syncing: "refresh",
    failed: "alert", inReview: "eye", routeUpdated: "route",
    forwarded: "send",
  };

  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border",
      styles[tone] ?? "bg-raised text-ink-muted border-line",
    )}>
      <AppIcon name={icons[tone] ?? "dot"} size={12} />
      {labels[tone] ?? tone}
    </span>
  );
}
