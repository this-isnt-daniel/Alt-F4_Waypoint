import { useDriverState } from "@/driver/state/useDriverState";
import { Chip } from "./Chip";

export function ConnectionPill() {
  const { connection, setConnection } = useDriverState();

  return (
    <button
      type="button"
      onClick={() => setConnection(connection === "online" ? "offline" : "online")}
      aria-label={`Connection status: ${connection}. Tap to toggle.`}
      title="Tap to toggle simulated network"
    >
      <Chip
        kind="sync"
        tone={connection === "online" ? "online" : "offline"}
        label={connection === "online" ? "ONLINE" : "OFFLINE"}
      />
    </button>
  );
}
