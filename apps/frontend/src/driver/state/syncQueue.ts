export type SyncRecordType =
  | "load-confirmation"
  | "arrival"
  | "delivery"
  | "partial"
  | "failed"
  | "issue"
  | "delay"
  | "return"
  | "chat-message";

export interface SyncRecord {
  id: string;
  type: SyncRecordType;
  outletId?: string;
  createdAt: string;
  state: "pending" | "syncing" | "synced" | "failed" | "inReview" | "forwarded";
  hasPhoto: boolean;
  pinVerified: boolean;
  sizeLabel?: string;
  syncKind?: string;
  targetId?: string;
  syncPayload?: Record<string, unknown>;
}
