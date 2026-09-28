import { describe, it, expect } from "vitest";
import {
  TRIP_1,
  TRIP_2,
  RUN_TARGETS,
  LOAD_SUMMARY,
  TRIP_1_STOPS,
  TRIP_2_STOPS,
} from "@/driver/data/driverContent";

describe("Canonical Arithmetic & Domain Invariants", () => {
  it("asserts Trip 1 canonical numbers", () => {
    expect(TRIP_1.manifestUnits).toBe(1240);
    expect(TRIP_1.deliverableUnits).toBe(1238);
    expect(TRIP_1.returnUnits).toBe(2);
    expect(TRIP_1.deliveredCount).toBe(7);
    expect(TRIP_1.partialCount).toBe(1);
    expect(TRIP_1.failedCount).toBe(0);
  });

  it("asserts Trip 2 canonical numbers", () => {
    expect(TRIP_2.manifestUnits).toBe(860);
    expect(TRIP_2.deliveredCount).toBe(5);
  });

  it("asserts day run targets", () => {
    expect(RUN_TARGETS.stopCount).toBe(13);
    expect(RUN_TARGETS.unitCount).toBe(2100);
  });

  it("asserts pre-departure load confirmation summary", () => {
    expect(LOAD_SUMMARY.manifestUnits).toBe(1240);
    expect(LOAD_SUMMARY.deliverableUnits).toBe(1238);
    expect(LOAD_SUMMARY.returnUnits).toBe(2);
    expect(LOAD_SUMMARY.groupCount).toBe(4);
    expect(LOAD_SUMMARY.flaggedCount).toBe(1);
  });

  it("asserts stop domain invariants", () => {
    expect(TRIP_1_STOPS.every((s) => s.outletId.startsWith("OUT"))).toBe(true);
    expect(TRIP_1_STOPS.length).toBe(8);
    expect(TRIP_2_STOPS.length).toBe(5);

    expect(TRIP_1_STOPS.every((s) => s.brand === "Fresh")).toBe(true);
    expect(TRIP_1_STOPS.every((s) => s.district === "Kandy")).toBe(true);
    expect(TRIP_1_STOPS.every((s) => s.depot === "Kandy hub")).toBe(true);

    expect(TRIP_2_STOPS.every((s) => s.brand === "Style")).toBe(true);

    // No legacy conflicting outlet names
    expect(TRIP_1_STOPS.some((s) => s.name.includes("Tech"))).toBe(false);
    expect(TRIP_1_STOPS.some((s) => s.name.includes("Colombo"))).toBe(false);
    expect(TRIP_1_STOPS.some((s) => s.name.includes("Nugegoda"))).toBe(false);
  });
});
