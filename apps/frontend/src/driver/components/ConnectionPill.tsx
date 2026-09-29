import { useDriverState } from "@/driver/state/useDriverState";
import { AppIcon } from "./AppIcon";

export function ConnectionPill() {
  const { connection } = useDriverState();

  if (connection === "online") {
    return (
      <span className="relative flex h-2 w-2" title="Online">
        <span className="absolute inline-flex h-full w-full rounded-full bg-green opacity-40 animate-ping" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-green" />
        <span className="sr-only">Online</span>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-raised text-ink-muted border border-line">
      <AppIcon name="cloud-off" size={12} />
      Offline
    </span>
  );
}
