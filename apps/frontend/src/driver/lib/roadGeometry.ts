import { KANDY_HUB_COORDS, STOP_COORDS } from "@/driver/data/driverContent";
import precomputedData from "@/driver/data/precomputedRoadGeometries.json";

export interface RoadGeometryRecord {
  from_id: string;
  to_id: string;
  coords: [number, number][];
  coord_version?: number;
  distance_meters?: number;
  duration_seconds?: number;
}

export interface DbQueryResult {
  rows: RoadGeometryRecord[];
}

export interface DatabaseClient {
  query(sql: string, params: any[]): Promise<DbQueryResult>;
}

// In-memory geometry cache
const LOCAL_GEOMETRY_CACHE = new Map<string, RoadGeometryRecord>();

// Prepopulate cache from precomputed OSRM road geometry
if (precomputedData && typeof precomputedData === "object") {
  for (const [, value] of Object.entries(precomputedData)) {
    const entry = value as any;
    if (entry && entry.from_id && entry.to_id && Array.isArray(entry.coords)) {
      LOCAL_GEOMETRY_CACHE.set(`${entry.from_id}|${entry.to_id}`, {
        from_id: entry.from_id,
        to_id: entry.to_id,
        coords: entry.coords,
        coord_version: entry.coord_version ?? 1,
        distance_meters: entry.distance_meters,
        duration_seconds: entry.duration_seconds,
      });
    }
  }
}

/**
 * Returns the [lat, lng] center coordinates for an outlet or depot identifier.
 */
export function centroid(id: string): [number, number] {
  const cleanId = String(id).trim();
  if (
    cleanId === "DEPOT:KANDY_HUB" ||
    cleanId === "DEPOT" ||
    cleanId === "KANDY_HUB"
  ) {
    return [KANDY_HUB_COORDS.lat, KANDY_HUB_COORDS.lng];
  }
  const stop = STOP_COORDS[cleanId];
  if (stop) {
    return [stop.lat, stop.lng];
  }
  // Synthesize realistic coordinates for arbitrary outlet numbers
  const digits = cleanId.replace(/\D/g, "");
  const num = digits ? parseInt(digits, 10) : 0;
  let hash = 0;
  for (let i = 0; i < cleanId.length; i++) {
    hash = (hash << 5) - hash + cleanId.charCodeAt(i);
    hash |= 0;
  }
  const absH = Math.abs(hash);
  const radiusKm = 0.4 + ((num * 3 + (absH % 7)) % 10) * 0.15;
  const bearingDeg = (absH ^ (num * 37)) % 360;
  const bearingRad = (bearingDeg * Math.PI) / 180.0;

  const latOffset = (radiusKm / 111.0) * Math.cos(bearingRad);
  const lngOffset =
    (radiusKm / (111.0 * Math.cos((KANDY_HUB_COORDS.lat * Math.PI) / 180.0))) *
    Math.sin(bearingRad);
  return [
    Number((KANDY_HUB_COORDS.lat + latOffset).toFixed(4)),
    Number((KANDY_HUB_COORDS.lng + lngOffset).toFixed(4)),
  ];
}

/**
 * Generates an interpolated spline path between two points as a fallback safety net.
 */
export function spline(
  points: [[number, number], [number, number]],
  steps = 6
): [number, number][] {
  const [p0, p1] = points;
  if (!p0 || !p1) return [];
  const res: [number, number][] = [];
  for (let s = 0; s <= steps; s++) {
    const t = s / steps;
    const curvature = Math.sin(t * Math.PI) * 0.001;
    const lat = p0[0] + (p1[0] - p0[0]) * t + curvature;
    const lng = p0[1] + (p1[1] - p0[1]) * t + curvature;
    res.push([Number(lat.toFixed(6)), Number(lng.toFixed(6))]);
  }
  return res;
}

/**
 * Database client executing road_geometry queries with API integration and offline caching.
 */
export const db: DatabaseClient = {
  async query(_sql: string, params: any[] = []): Promise<DbQueryResult> {
    const edges: [string, string][] = [];
    for (let i = 0; i < params.length; i += 2) {
      if (params[i] !== undefined && params[i + 1] !== undefined) {
        edges.push([String(params[i]), String(params[i + 1])]);
      }
    }

    // Try fetching from backend API if running in browser
    if (typeof window !== "undefined" && typeof fetch === "function") {
      try {
        const response = await fetch("/api/v1/driver-platform/road-geometry/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ edges, coord_version: 1 }),
        });
        if (response.ok) {
          const json = await response.json();
          if (json && Array.isArray(json.rows)) {
            const fetchedRows: RoadGeometryRecord[] = json.rows.map((r: any) => {
              const rec: RoadGeometryRecord = {
                from_id: r.from_id,
                to_id: r.to_id,
                coords: typeof r.coords === "string" ? JSON.parse(r.coords) : r.coords,
                coord_version: r.coord_version,
                distance_meters: r.distance_meters,
                duration_seconds: r.duration_seconds,
              };
              LOCAL_GEOMETRY_CACHE.set(`${r.from_id}|${r.to_id}`, rec);
              return rec;
            });
            if (fetchedRows.length > 0) {
              return { rows: fetchedRows };
            }
          }
        }
      } catch {
        // Fall back to local cache if network/backend is unavailable
      }
    }

    // Retrieve from local pre-cached geometry store
    const matched: RoadGeometryRecord[] = [];
    for (const [fromId, toId] of edges) {
      const hit =
        LOCAL_GEOMETRY_CACHE.get(`${fromId}|${toId}`) ||
        LOCAL_GEOMETRY_CACHE.get(
          `${fromId.replace("DEPOT:KANDY_HUB", "DEPOT")}|${toId}`
        ) ||
        LOCAL_GEOMETRY_CACHE.get(
          `${fromId}|${toId.replace("DEPOT:KANDY_HUB", "DEPOT")}`
        );
      if (hit) {
        matched.push(hit);
      }
    }
    return { rows: matched };
  },
};

// src/driver/lib/roadGeometry.ts  — replaces the old fetch-per-leg version
export async function buildRoadGeometry(sequence: string[]): Promise<[number,number][]> {
  // sequence = ['DEPOT:KANDY_HUB','OUT042','OUT047',...] in CURRENT order (post-resequence)
  if (sequence.length <= 1) {
    return sequence.length === 1 ? [centroid(sequence[0]!)] : [];
  }
  const edges = sequence.slice(0,-1).map((f,i) => [f, sequence[i+1]!] as const);
  const { rows } = await db.query(
    `SELECT from_id, to_id, coords FROM road_geometry
     WHERE coord_version = 1 AND (from_id, to_id) IN (${edges.map((_,i)=>`(\$${1+i*2},\$${2+i*2})`).join(",")})`,
    edges.flat()
  );
  const byPair = new Map(rows.map((r:any)=>[`${r.from_id}|${r.to_id}`, r.coords as [number,number][]]));
  return edges.flatMap(([f,t], i) => {
    const c = byPair.get(`${f}|${t}`)                    // exact directed hit
      ?? byPair.get(`${t}|${f}`)?.slice().reverse()      // approximation if only reverse cached
      ?? spline([centroid(f), centroid(t)]);             // safety net; should essentially never fire
    return i === 0 ? c : c.slice(1);                     // drop duplicated junction point
  });
}
