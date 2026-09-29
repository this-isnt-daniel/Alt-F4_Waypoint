export type ConnectionState = "online" | "offline";

export type SyncState =
  | "idle"
  | "saving"
  | "pending"
  | "syncing"
  | "success"
  | "failed"
  | "inReview"
  | "routeUpdated"
  | "forwarded";
