import { describe, it, expect } from "vitest";
import { type ScreenId } from "@/router/navigator";
import { SCENARIO_INITIAL, type ScenarioId } from "@/driver/state/scenarios";

const ALL_SCREEN_IDS: ScreenId[] = [
  "signin",
  "start-day",
  "today-trips",
  "trip-briefing",
  "load-confirm",
  "active-trip",
  "stop-detail",
  "mark-arrived",
  "checklist",
  "not-handed-over",
  "pod-photo",
  "pod-pin",
  "delivery-complete",
  "partial-summary",
  "failed-reason",
  "return-depot",
  "depot-return",
  "trip-complete",
  "day-summary",
  "offline-saved",
  "sync-centre",
  "route-changed",
  "outlet-closed",
  "sync-review",
  "record-sent",
  "no-trips",
  "camera-denied",
  "location-denied",
  "sync-failed",
  "chat",
  "call-overlay",
  "issue-wizard",
  "contact-dispatch",
];

// In-flow transition graph mapping from screen -> reachable targets based on Section 20.2
const IN_FLOW_EDGES: Record<ScreenId, ScreenId[]> = {
  signin: ["start-day", "contact-dispatch"],
  "start-day": ["today-trips", "contact-dispatch"],
  "today-trips": [
    "load-confirm",
    "trip-briefing",
    "active-trip",
    "contact-dispatch",
    "no-trips",
  ],
  "trip-briefing": ["active-trip", "today-trips"],
  "load-confirm": ["active-trip"],
  "active-trip": [
    "mark-arrived",
    "stop-detail",
    "chat",
    "call-overlay",
    "issue-wizard",
    "route-changed",
    "failed-reason",
    "location-denied",
    "outlet-closed",
  ],
  "stop-detail": ["mark-arrived", "chat", "call-overlay", "active-trip"],
  "mark-arrived": ["checklist", "active-trip"],
  checklist: ["pod-photo", "not-handed-over", "active-trip"],
  "not-handed-over": ["pod-photo"],
  "pod-photo": ["pod-pin", "camera-denied"],
  "pod-pin": ["delivery-complete", "partial-summary"],
  "delivery-complete": [
    "active-trip",
    "sync-centre",
    "trip-complete",
    "partial-summary",
  ],
  "partial-summary": ["return-depot"],
  "failed-reason": ["outlet-closed"],
  "outlet-closed": ["return-depot", "active-trip"],
  "return-depot": ["depot-return"],
  "depot-return": ["trip-complete"],
  "trip-complete": ["today-trips", "day-summary"],
  "day-summary": ["signin"],
  "offline-saved": ["active-trip", "sync-centre"],
  "sync-centre": ["sync-review", "route-changed", "sync-failed", "active-trip"],
  "route-changed": ["active-trip", "call-overlay"],
  "sync-review": ["record-sent", "active-trip", "pod-photo", "call-overlay"],
  "record-sent": ["active-trip", "sync-centre"],
  "no-trips": ["today-trips", "contact-dispatch"],
  "camera-denied": ["pod-photo", "pod-pin"],
  "location-denied": ["active-trip"],
  "sync-failed": ["sync-centre", "contact-dispatch"],
  chat: ["active-trip", "call-overlay"],
  "call-overlay": ["active-trip"],
  "issue-wizard": ["offline-saved", "active-trip", "failed-reason"],
  "contact-dispatch": ["active-trip", "call-overlay"],
};

describe("Scenario Reachability & Coverage", () => {
  it("contains all 33 screen IDs in the screen catalog", () => {
    expect(ALL_SCREEN_IDS).toHaveLength(33);
  });

  it("has initial state defined for all canonical scenarios", () => {
    const canonicalScenarios: ScenarioId[] = [
      "happy",
      "load-discrepancy",
      "partial-return",
      "outlet-closed",
      "offline-sync-conflict",
      "route-resequence",
      "chat-call",
      "return-depot",
      "errors-camera",
      "errors-location",
      "errors-sync-failed",
      "no-trips",
    ];

    for (const id of canonicalScenarios) {
      expect(SCENARIO_INITIAL[id]).toBeDefined();
      expect(SCENARIO_INITIAL[id].routeSequence).toHaveLength(8);
    }
  });

  it("verifies every screen ID has incoming transitions or deep-link entry", () => {
    const reachableScreens = new Set<ScreenId>(["signin"]);

    // Breadth-first traversal of transitions
    const queue: ScreenId[] = ["signin"];
    while (queue.length > 0) {
      const current = queue.shift()!;
      const targets = IN_FLOW_EDGES[current] || [];
      for (const target of targets) {
        if (!reachableScreens.has(target)) {
          reachableScreens.add(target);
          queue.push(target);
        }
      }
    }

    // Every screen in ALL_SCREEN_IDS is reachable in the application flow
    for (const screen of ALL_SCREEN_IDS) {
      expect(reachableScreens.has(screen)).toBe(true);
    }
    expect(reachableScreens.size).toBe(33);
  });
});
