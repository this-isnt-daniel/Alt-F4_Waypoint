import { type SyncState } from "@/driver/state/connection";
import { Chip } from "./Chip";
import { useNavigator } from "@/router/navigator";

export function SyncPill({ tone = "success" }: { tone?: SyncState }) {
  const { push } = useNavigator();

  const labels: Record<SyncState, string> = {
    idle: "SYNCED",
    saving: "SAVING",
    pending: "QUEUED",
    syncing: "SYNCING",
    success: "SYNCED",
    failed: "SYNC ERROR",
    inReview: "IN REVIEW",
    routeUpdated: "ROUTE UPDATE",
    forwarded: "FORWARDED",
  };

  const chipTone = tone === "idle" ? "success" : tone;

  return (
    <button
      type="button"
      onClick={() => push("sync-centre")}
      aria-label={`Sync status: ${labels[tone]}. Tap for Sync Centre.`}
      title="Open Sync Centre"
    >
      <Chip kind="sync" tone={chipTone} label={labels[tone]} />
    </button>
  );
}
