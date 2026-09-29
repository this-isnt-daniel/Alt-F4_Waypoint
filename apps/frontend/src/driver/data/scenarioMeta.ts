import type { ScenarioId } from "@/driver/state/scenarios";
import type { ScreenId } from "@/router/navigator";

export interface ScenarioMeta {
  id: ScenarioId;
  title: string;
  blurb: string;
  tags: ("FC" | "DEG" | "FID" | "ENG")[]; // rubric: functional / degradation / fidelity / engineering
  entry: ScreenId;
  params: Record<string, string>;
}

export const SCENARIO_META: ScenarioMeta[] = [
  {
    id: "happy",
    title: "Happy path",
    blurb: "Sign-in → load confirm → drive → photo+PIN → trip → day.",
    tags: ["FC", "FID"],
    entry: "today-trips",
    params: {},
  },
  {
    id: "load-discrepancy",
    title: "Pre-departure load flag",
    blurb: "Loader pre-flag on OUT058 surfaces before wheels roll.",
    tags: ["FC", "FID"],
    entry: "load-confirm",
    params: {},
  },
  {
    id: "partial-return",
    title: "Partial + return custody",
    blurb: "Flag 2 frozen at OUT058 → crate R-04 → depot handover.",
    tags: ["FC", "DEG"],
    entry: "checklist",
    params: { outletId: "OUT058" },
  },
  {
    id: "outlet-closed",
    title: "Degradation · outlet closed",
    blurb: "Mall bay shut at OUT052, offline, 3 items return.",
    tags: ["DEG", "FID"],
    entry: "outlet-closed",
    params: { outletId: "OUT052" },
  },
  {
    id: "offline-sync-conflict",
    title: "Degradation · sync conflict",
    blurb: "Deliver offline → reconnect → preserve & forward (no keep/erase).",
    tags: ["DEG", "FID", "ENG"],
    entry: "sync-review",
    params: { outletId: "OUT058" },
  },
  {
    id: "route-resequence",
    title: "Dispatcher resequencing",
    blurb: "OUT061 moved next; goods unchanged.",
    tags: ["FC"],
    entry: "route-changed",
    params: {},
  },
  {
    id: "chat-call",
    title: "Chat / call",
    blurb: "Uber-like thread + masked call overlay.",
    tags: ["FC"],
    entry: "chat",
    params: { outletId: "OUT047" },
  },
  {
    id: "return-depot",
    title: "Return to depot",
    blurb: "Secured crate → navigate → officer confirms.",
    tags: ["FC", "DEG"],
    entry: "return-depot",
    params: { outletId: "OUT058" },
  },
  {
    id: "errors-camera",
    title: "Error · camera denied",
    blurb: "Save without photo, never a silent skip.",
    tags: ["DEG", "ENG"],
    entry: "camera-denied",
    params: {},
  },
  {
    id: "errors-location",
    title: "Error · location denied",
    blurb: "Continue offline; stop-safety copy.",
    tags: ["DEG", "ENG"],
    entry: "location-denied",
    params: {},
  },
  {
    id: "errors-sync-failed",
    title: "Error · sync failed",
    blurb: "Records safe on phone; retry / continue.",
    tags: ["DEG", "ENG"],
    entry: "sync-failed",
    params: {},
  },
  {
    id: "no-trips",
    title: "Empty · no trips",
    blurb: "Nothing scheduled; refresh / call dispatch.",
    tags: ["ENG"],
    entry: "no-trips",
    params: {},
  },
];
