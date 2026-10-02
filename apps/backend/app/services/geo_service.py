"""
Geo Service: Geographic coordinates resolution, deterministic outlet positioning,
and OSRM road geometry fetching/caching for Waypoint routing.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import urllib.request
from typing import Any, Optional

# Authoritative coordinate locations for Kandy Hub and known outlets
KNOWN_COORDS: dict[str, tuple[float, float]] = {
    "DEPOT:KANDY_HUB": (7.2906, 80.6337),
    "DEPOT": (7.2906, 80.6337),
    "KANDY_HUB": (7.2906, 80.6337),
    "OUT042": (7.1666, 80.5666),
    "OUT047": (7.2931, 80.6350),
    "OUT049": (7.2936, 80.6360),
    "OUT052": (7.2941, 80.6380),
    "OUT055": (7.2880, 80.6200),
    "OUT058": (7.2850, 80.6250),
    "OUT061": (7.2667, 80.6000),
    "OUT064": (7.0500, 80.5333),
    "OUT070": (7.2941, 80.6380),
    "OUT071": (7.1666, 80.5666),
    "OUT072": (7.2936, 80.6360),
    "OUT073": (7.2667, 80.6000),
    "OUT074": (7.0500, 80.5333),
}


def get_outlet_coordinates(
    identifier: str,
    depot_id: str = "DEPOT:KANDY_HUB",
    distance_km: float = 10.0,
    db: Optional[sqlite3.Connection] = None,
) -> tuple[float, float]:
    """
    Get geographic coordinates (lat, lng) for an outlet or depot.

    If the entity is known, returns authoritative coordinates.
    If database connection is provided, looks up registered outlet or stop lat/lng.
    If only distance from depot is available, computes a deterministic bearing and coordinates
    based on the outlet ID hash, ensuring absolute consistency with the allocation engine.
    """
    clean_id = identifier.strip()
    if clean_id in KNOWN_COORDS:
        return KNOWN_COORDS[clean_id]

    # Check database if available
    if db is not None:
        try:
            row = db.execute(
                "SELECT lat, lng FROM stops WHERE outlet_id = ? AND lat IS NOT NULL LIMIT 1",
                (clean_id,),
            ).fetchone()
            if row and row["lat"] is not None and row["lng"] is not None:
                return float(row["lat"]), float(row["lng"])
        except Exception:
            pass

    # Deterministic generation from depot location and distance
    depot_coords = KNOWN_COORDS.get(depot_id, (7.2906, 80.6337))
    depot_lat, depot_lng = depot_coords

    # Hash the identifier to derive a consistent bearing in radians [0, 2*pi)
    h = int(hashlib.sha256(clean_id.encode("utf-8")).hexdigest()[:8], 16)
    bearing_rad = (h % 360) * (math.pi / 180.0)

    # 1 deg latitude ~ 111.0 km; 1 deg longitude ~ 111.0 * cos(lat) km
    lat_offset = (distance_km / 111.0) * math.cos(bearing_rad)
    lng_offset = (distance_km / (111.0 * math.cos(math.radians(depot_lat)))) * math.sin(bearing_rad)

    lat = round(depot_lat + lat_offset, 4)
    lng = round(depot_lng + lng_offset, 4)
    return (lat, lng)


def generate_spline_points(
    p1: tuple[float, float],
    p2: tuple[float, float],
    steps: int = 8,
) -> list[list[float]]:
    """
    Generate an interpolated spline/polyline safety net between two points.
    Returns coordinates in [lat, lng] format.
    """
    lat1, lng1 = p1
    lat2, lng2 = p2
    points: list[list[float]] = []
    for i in range(steps + 1):
        t = i / float(steps)
        # Small curvature perpendicular to line
        curvature = math.sin(t * math.pi) * 0.001
        lat = lat1 + (lat2 - lat1) * t + curvature
        lng = lng1 + (lng2 - lng1) * t + curvature
        points.append([round(lat, 6), round(lng, 6)])
    return points


def fetch_osrm_route(
    c1: tuple[float, float],
    c2: tuple[float, float],
    timeout: float = 6.0,
) -> dict[str, Any]:
    """
    Fetch road route geometry between two coordinates from OSRM.
    Coordinates input: (lat, lng).
    Returns dict with 'coords' as list of [lat, lng], 'distance_meters', and 'duration_seconds'.
    Falls back to spline interpolation if OSRM is unreachable.
    """
    lat1, lng1 = c1
    lat2, lng2 = c2

    # If start and end are practically identical
    if abs(lat1 - lat2) < 1e-6 and abs(lng1 - lng2) < 1e-6:
        return {
            "coords": [[lat1, lng1]],
            "distance_meters": 0.0,
            "duration_seconds": 0.0,
        }

    # OSRM expects {lng},{lat} in URL
    url = f"http://router.project-osrm.org/route/v1/driving/{lng1},{lat1};{lng2},{lat2}?overview=full&geometries=geojson"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Waypoint-Driver/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                # Convert OSRM [lng, lat] to Leaflet [lat, lng]
                coords = [[pt[1], pt[0]] for pt in route["geometry"]["coordinates"]]
                return {
                    "coords": coords,
                    "distance_meters": float(route.get("distance", 0.0)),
                    "duration_seconds": float(route.get("duration", 0.0)),
                }
    except Exception:
        # Network failure or timeout: fallback to spline
        pass

    # Safety-net fallback
    spline_coords = generate_spline_points(c1, c2)
    # Approximate distance
    d_km = math.sqrt((lat2 - lat1) ** 2 + ((lng2 - lng1) * math.cos(math.radians(lat1))) ** 2) * 111.0
    return {
        "coords": spline_coords,
        "distance_meters": round(d_km * 1000.0, 1),
        "duration_seconds": round(d_km * 120.0, 1),  # assume ~30 km/h average
    }


def lookup_or_fetch_edge(
    from_id: str,
    to_id: str,
    db: sqlite3.Connection,
    coord_version: int = 1,
) -> dict[str, Any]:
    """
    Query road_geometry for edge (from_id -> to_id).
    If directed edge is missing, checks reverse edge (to_id -> from_id).
    If reverse is found, reverses the coordinate array and persists directed edge.
    If completely absent, fetches via OSRM (or spline), saves to DB, and returns.
    """
    # 1. Exact directed hit
    row = db.execute(
        "SELECT from_id, to_id, coords, coord_version, distance_meters, duration_seconds "
        "FROM road_geometry WHERE from_id = ? AND to_id = ? AND coord_version = ?",
        (from_id, to_id, coord_version),
    ).fetchone()
    if row:
        coords = json.loads(row["coords"]) if isinstance(row["coords"], str) else row["coords"]
        return {
            "from_id": row["from_id"],
            "to_id": row["to_id"],
            "coords": coords,
            "coord_version": row["coord_version"],
            "distance_meters": row["distance_meters"],
            "duration_seconds": row["duration_seconds"],
        }

    # 2. Reverse cached hit
    rev_row = db.execute(
        "SELECT from_id, to_id, coords, coord_version, distance_meters, duration_seconds "
        "FROM road_geometry WHERE from_id = ? AND to_id = ? AND coord_version = ?",
        (to_id, from_id, coord_version),
    ).fetchone()
    if rev_row:
        rev_coords = json.loads(rev_row["coords"]) if isinstance(rev_row["coords"], str) else rev_row["coords"]
        reversed_coords = list(reversed(rev_coords))
        # Store directed copy for fast subsequent queries
        db.execute(
            "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                from_id,
                to_id,
                json.dumps(reversed_coords),
                coord_version,
                rev_row["distance_meters"],
                rev_row["duration_seconds"],
            ),
        )
        db.commit()
        return {
            "from_id": from_id,
            "to_id": to_id,
            "coords": reversed_coords,
            "coord_version": coord_version,
            "distance_meters": rev_row["distance_meters"],
            "duration_seconds": rev_row["duration_seconds"],
        }

    # 3. Compute coordinates and fetch
    c1 = get_outlet_coordinates(from_id, db=db)
    c2 = get_outlet_coordinates(to_id, db=db)
    route_data = fetch_osrm_route(c1, c2)

    db.execute(
        "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            from_id,
            to_id,
            json.dumps(route_data["coords"]),
            coord_version,
            route_data.get("distance_meters"),
            route_data.get("duration_seconds"),
        ),
    )
    db.commit()

    return {
        "from_id": from_id,
        "to_id": to_id,
        "coords": route_data["coords"],
        "coord_version": coord_version,
        "distance_meters": route_data.get("distance_meters"),
        "duration_seconds": route_data.get("duration_seconds"),
    }


def query_edges_batch(
    edges: list[list[str]],
    db: sqlite3.Connection,
    coord_version: int = 1,
) -> list[dict[str, Any]]:
    """
    Batch query or populate road geometries for an edge sequence.
    Returns list of dicts with from_id, to_id, coords, distance_meters, duration_seconds.
    """
    results: list[dict[str, Any]] = []
    for edge in edges:
        if len(edge) < 2:
            continue
        from_id, to_id = edge[0], edge[1]
        edge_data = lookup_or_fetch_edge(from_id, to_id, db, coord_version)
        results.append(edge_data)
    return results
