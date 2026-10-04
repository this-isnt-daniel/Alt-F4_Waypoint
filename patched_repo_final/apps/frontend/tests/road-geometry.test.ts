import { describe, it, expect } from "vitest";
import {
  buildRoadGeometry,
  centroid,
  spline,
} from "@/driver/lib/roadGeometry";

describe("roadGeometry", () => {
  it("derives accurate centroids for depots and outlets", () => {
    const depot = centroid("DEPOT:KANDY_HUB");
    expect(depot[0]).toBeCloseTo(7.2906, 3);
    expect(depot[1]).toBeCloseTo(80.6337, 3);

    const out42 = centroid("OUT042");
    expect(out42[0]).toBeCloseTo(7.2885, 3);
    expect(out42[1]).toBeCloseTo(80.6322, 3);

    // Arbitrary outlet deterministic coordinates
    const arb1 = centroid("OUT999");
    const arb2 = centroid("OUT999");
    expect(arb1).toEqual(arb2);
    expect(typeof arb1[0]).toBe("number");
    expect(typeof arb1[1]).toBe("number");
  });

  it("generates interpolated spline fallback points connecting endpoints", () => {
    const p1: [number, number] = [7.2906, 80.6337];
    const p2: [number, number] = [7.1666, 80.5666];
    const pts = spline([p1, p2], 4);
    expect(pts.length).toBe(5);
    expect(pts[0]).toEqual(p1);
    expect(pts[pts.length - 1]).toEqual(p2);
  });

  it("builds continuous road geometry for standard Trip 1 sequence", async () => {
    const sequence = [
      "DEPOT:KANDY_HUB",
      "OUT042",
      "OUT047",
      "OUT049",
      "OUT052",
      "OUT055",
      "OUT058",
      "OUT061",
      "OUT064",
      "DEPOT:KANDY_HUB",
    ];

    const polyline = await buildRoadGeometry(sequence);
    expect(polyline.length).toBeGreaterThan(100);

    // Verify first coordinate is at Kandy Hub
    expect(polyline[0]![0]).toBeCloseTo(7.29, 1);
    expect(polyline[0]![1]).toBeCloseTo(80.63, 1);

    // Verify last coordinate returns to Kandy Hub
    const last = polyline[polyline.length - 1]!;
    expect(last[0]).toBeCloseTo(7.29, 1);
    expect(last[1]).toBeCloseTo(80.63, 1);
  });

  it("builds road geometry for resequenced sequence", async () => {
    const resequenced = [
      "DEPOT:KANDY_HUB",
      "OUT042",
      "OUT047",
      "OUT061",
      "OUT049",
      "OUT055",
      "OUT052",
      "OUT058",
      "OUT064",
    ];

    const polyline = await buildRoadGeometry(resequenced);
    expect(polyline.length).toBeGreaterThan(100);
  });

  it("handles single point or empty sequences gracefully", async () => {
    expect(await buildRoadGeometry([])).toEqual([]);
    const single = await buildRoadGeometry(["OUT042"]);
    expect(single.length).toBe(1);
    expect(single[0]).toEqual(centroid("OUT042"));
  });
});
