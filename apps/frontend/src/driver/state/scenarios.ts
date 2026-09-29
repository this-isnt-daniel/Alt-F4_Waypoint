export type ScenarioId =
  | "happy"
  | "load-discrepancy"
  | "partial-return"
  | "outlet-closed"
  | "offline-sync-conflict"
  | "route-resequence"
  | "chat-call"
  | "return-depot"
  | "errors-camera"
  | "errors-location"
  | "errors-sync-failed"
  | "no-trips"
  // Legacy/alias fallbacks
  | "default"
  | "load-confirm"
  | "offline-sync"
  | "route-update"
  | "errors";

export interface ScenarioState {
  tripStarted: boolean;
  loadConfirmed: boolean;
  connection: "online" | "offline";
  syncState: string;
  currentStopId: string;
  currentStopIndex: number;
  routeSequence: string[];
  flaggedStopIds: string[];
  completedStopIds: string[];
  failedStopIds: string[];
  photoState?: string;
  locationDenied?: boolean;
  trip2Unlocked?: boolean;
  emptyTrips?: boolean;
  syncReviewOutletId?: string;
  syncReviewForwarded: boolean;
  routeUpdateAccepted: boolean;
}

const DEFAULT_SEQUENCE = [
  "OUT042",
  "OUT047",
  "OUT049",
  "OUT052",
  "OUT055",
  "OUT058",
  "OUT061",
  "OUT064",
];

export const SCENARIO_INITIAL: Record<ScenarioId, ScenarioState> = {
  happy: {
    tripStarted: false,
    loadConfirmed: false,
    connection: "online",
    syncState: "idle",
    currentStopId: "OUT042",
    currentStopIndex: 0,
    routeSequence: [...DEFAULT_SEQUENCE],
    flaggedStopIds: [],
    completedStopIds: [],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "load-discrepancy": {
    tripStarted: false,
    loadConfirmed: false,
    connection: "online",
    syncState: "idle",
    currentStopId: "OUT042",
    currentStopIndex: 0,
    routeSequence: [...DEFAULT_SEQUENCE],
    flaggedStopIds: ["OUT058"],
    completedStopIds: [],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "partial-return": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "online",
    syncState: "pending",
    currentStopId: "OUT058",
    currentStopIndex: 5,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042", "OUT047", "OUT049", "OUT052", "OUT055"],
    flaggedStopIds: ["OUT058"],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "outlet-closed": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "offline",
    syncState: "pending",
    currentStopId: "OUT052",
    currentStopIndex: 3,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042", "OUT047", "OUT049"],
    flaggedStopIds: [],
    failedStopIds: ["OUT052"],
    photoState: "pending",
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "offline-sync-conflict": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "online",
    syncState: "inReview",
    currentStopId: "OUT058",
    currentStopIndex: 5,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042", "OUT047", "OUT049", "OUT052", "OUT055"],
    flaggedStopIds: ["OUT058"],
    failedStopIds: [],
    syncReviewOutletId: "OUT058",
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "route-resequence": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "online",
    syncState: "routeUpdated",
    currentStopId: "OUT049",
    currentStopIndex: 2,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042", "OUT047"],
    flaggedStopIds: [],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "chat-call": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "online",
    syncState: "idle",
    currentStopId: "OUT047",
    currentStopIndex: 1,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042"],
    flaggedStopIds: [],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "return-depot": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "online",
    syncState: "pending",
    currentStopId: "OUT058",
    currentStopIndex: 5,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042", "OUT047", "OUT049", "OUT052", "OUT055"],
    flaggedStopIds: ["OUT058"],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "errors-camera": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "online",
    syncState: "idle",
    currentStopId: "OUT047",
    currentStopIndex: 1,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042"],
    flaggedStopIds: [],
    failedStopIds: [],
    photoState: "denied",
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "errors-location": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "online",
    syncState: "idle",
    currentStopId: "OUT047",
    currentStopIndex: 1,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042"],
    flaggedStopIds: [],
    failedStopIds: [],
    locationDenied: true,
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "errors-sync-failed": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "offline",
    syncState: "failed",
    currentStopId: "OUT047",
    currentStopIndex: 1,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042"],
    flaggedStopIds: [],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "no-trips": {
    tripStarted: false,
    loadConfirmed: false,
    connection: "online",
    syncState: "idle",
    currentStopId: "OUT042",
    currentStopIndex: 0,
    routeSequence: [...DEFAULT_SEQUENCE],
    flaggedStopIds: [],
    completedStopIds: [],
    failedStopIds: [],
    emptyTrips: true,
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },

  // Aliases for backward compatibility
  default: {
    tripStarted: false,
    loadConfirmed: false,
    connection: "online",
    syncState: "idle",
    currentStopId: "OUT042",
    currentStopIndex: 0,
    routeSequence: [...DEFAULT_SEQUENCE],
    flaggedStopIds: [],
    completedStopIds: [],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "load-confirm": {
    tripStarted: false,
    loadConfirmed: false,
    connection: "online",
    syncState: "idle",
    currentStopId: "OUT042",
    currentStopIndex: 0,
    routeSequence: [...DEFAULT_SEQUENCE],
    flaggedStopIds: ["OUT058"],
    completedStopIds: [],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "offline-sync": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "online",
    syncState: "inReview",
    currentStopId: "OUT058",
    currentStopIndex: 5,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042", "OUT047", "OUT049", "OUT052", "OUT055"],
    flaggedStopIds: ["OUT058"],
    failedStopIds: [],
    syncReviewOutletId: "OUT058",
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  "route-update": {
    tripStarted: true,
    loadConfirmed: true,
    connection: "online",
    syncState: "routeUpdated",
    currentStopId: "OUT049",
    currentStopIndex: 2,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042", "OUT047"],
    flaggedStopIds: [],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
  errors: {
    tripStarted: true,
    loadConfirmed: true,
    connection: "offline",
    syncState: "failed",
    currentStopId: "OUT047",
    currentStopIndex: 1,
    routeSequence: [...DEFAULT_SEQUENCE],
    completedStopIds: ["OUT042"],
    flaggedStopIds: [],
    failedStopIds: [],
    syncReviewForwarded: false,
    routeUpdateAccepted: false,
  },
};
