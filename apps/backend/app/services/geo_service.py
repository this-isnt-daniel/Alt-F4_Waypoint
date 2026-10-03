"""
Geo Service: Geographic coordinates resolution, deterministic outlet positioning,
and OSRM road geometry fetching/caching for Waypoint routing.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import urllib.request
from typing import Any, Optional

# Authoritative coordinate locations for Kandy Hub and known outlets
KNOWN_COORDS: dict[str, tuple[float, float]] = {
    "DEPOT:KANDY_HUB": (7.2906, 80.6337),
    "DEPOT": (7.2906, 80.6337),
    "KANDY_HUB": (7.2906, 80.6337),
    "OUT042": (7.2885, 80.6322),
    "OUT047": (7.2925, 80.6345),
    "OUT049": (7.2948, 80.6365),
    "OUT052": (7.2965, 80.6390),
    "OUT055": (7.2938, 80.6425),
    "OUT058": (7.2890, 80.6400),
    "OUT061": (7.2860, 80.6355),
    "OUT064": (7.2880, 80.6318),
    "OUT070": (7.2940, 80.6370),
    "OUT071": (7.2962, 80.6350),
    "OUT072": (7.2985, 80.6325),
    "OUT073": (7.2950, 80.6285),
    "OUT074": (7.2915, 80.6305),
}


def get_outlet_coordinates(
    identifier: str,
    depot_id: str = "DEPOT:KANDY_HUB",
    distance_km: Optional[float] = None,
    db: Optional[sqlite3.Connection] = None,
) -> tuple[float, float]:
    """
    Get or synthesize geographic coordinates (lat, lng) for ANY outlet or depot.

    If the entity has known GPS coordinates, returns them.
    If database connection is provided and the stop exists, returns stored coordinates.
    Otherwise, deterministically synthesizes realistic coordinates distributed around the depot
    based on the outlet number / ID, ensuring 100% stability with the allocation engine and frontend.
    """
    clean_id = str(identifier).strip()
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

    depot_coords = KNOWN_COORDS.get(depot_id, (7.2906, 80.6337))
    depot_lat, depot_lng = depot_coords

    # Extract numeric part (e.g. OUT005 -> 5)
    digits = re.findall(r"\d+", clean_id)
    num = int(digits[0]) if digits else 0

    # Deterministic hash
    h = int(hashlib.sha256(clean_id.encode("utf-8")).hexdigest()[:8], 16)

    # Determine radius: if explicit distance provided use it; else synthesize realistic radius 2.5km - 22km
    if distance_km is not None and distance_km > 0:
        radius_km = distance_km
    else:
        radius_km = 0.4 + ((num * 3 + (h % 7)) % 10) * 0.15

    # Deterministic bearing [0, 360)
    bearing_deg = (h ^ (num * 37)) % 360
    bearing_rad = bearing_deg * (math.pi / 180.0)

    # 1 deg latitude ~ 111.0 km; 1 deg longitude ~ 111.0 * cos(lat) km
    lat_offset = (radius_km / 111.0) * math.cos(bearing_rad)
    lng_offset = (radius_km / (111.0 * math.cos(math.radians(depot_lat)))) * math.sin(bearing_rad)

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
    Returns dict with 'coords' as list of [lat, lng], 'distance_meters', and 'duration_seconds'.
    """
    lat1, lng1 = c1
    lat2, lng2 = c2

    if abs(lat1 - lat2) < 1e-6 and abs(lng1 - lng2) < 1e-6:
        return {
            "coords": [[lat1, lng1]],
            "distance_meters": 0.0,
            "duration_seconds": 0.0,
        }

    url = f"http://router.project-osrm.org/route/v1/driving/{lng1},{lat1};{lng2},{lat2}?overview=full&geometries=geojson"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Waypoint-Driver/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                coords = [[pt[1], pt[0]] for pt in route["geometry"]["coordinates"]]
                return {
                    "coords": coords,
                    "distance_meters": float(route.get("distance", 0.0)),
                    "duration_seconds": float(route.get("duration", 0.0)),
                }
    except Exception:
        pass

    spline_coords = generate_spline_points(c1, c2)
    d_km = math.sqrt((lat2 - lat1) ** 2 + ((lng2 - lng1) * math.cos(math.radians(lat1))) ** 2) * 111.0
    return {
        "coords": spline_coords,
        "distance_meters": round(d_km * 1000.0, 1),
        "duration_seconds": round(d_km * 120.0, 1),
    }


def fetch_osrm_multi_waypoint(
    coords: list[tuple[float, float]],
    timeout: float = 8.0,
) -> list[dict[str, Any]]:
    """
    Batch-fetch interconnected road geometries for an entire sequence of waypoints in ONE single HTTP request.
    This completely avoids OSRM public rate-limiting by consolidating N legs into 1 call.
    Returns a list of dicts, one per leg between coords[i] and coords[i+1].
    """
    if len(coords) < 2:
        return []

    # Format: lng1,lat1;lng2,lat2;...
    coords_str = ";".join(f"{c[1]},{c[0]}" for c in coords)
    url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson&steps=true"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Waypoint-Driver/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                legs = route.get("legs", [])
                results: list[dict[str, Any]] = []
                for leg in legs:
                    leg_pts: list[list[float]] = []
                    for step in leg.get("steps", []):
                        for pt in step.get("geometry", {}).get("coordinates", []):
                            coord = [pt[1], pt[0]]
                            if not leg_pts or leg_pts[-1] != coord:
                                leg_pts.append(coord)
                    results.append({
                        "coords": leg_pts if leg_pts else generate_spline_points((0, 0), (0, 0)),
                        "distance_meters": float(leg.get("distance", 0.0)),
                        "duration_seconds": float(leg.get("duration", 0.0)),
                    })
                if len(results) == len(coords) - 1:
                    return results
    except Exception:
        pass

    # Fallback to spline for each leg if batch request fails or times out
    fallback: list[dict[str, Any]] = []
    for i in range(len(coords) - 1):
        c1, c2 = coords[i], coords[i + 1]
        spline_pts = generate_spline_points(c1, c2)
        d_km = math.sqrt((c2[0] - c1[0]) ** 2 + ((c2[1] - c1[1]) * math.cos(math.radians(c1[0]))) ** 2) * 111.0
        fallback.append({
            "coords": spline_pts,
            "distance_meters": round(d_km * 1000.0, 1),
            "duration_seconds": round(d_km * 120.0, 1),
        })
    return fallback


def lookup_or_fetch_edge(
    from_id: str,
    to_id: str,
    db: sqlite3.Connection,
    coord_version: int = 1,
) -> dict[str, Any]:
    """
    Query road_geometry for edge (from_id -> to_id).
    Checks directed -> reverse -> live fetch with persistence.
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
    # Also save reverse
    db.execute(
        "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            to_id,
            from_id,
            json.dumps(list(reversed(route_data["coords"]))),
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


def resolve_sequence_road_geometries(
    sequence: list[str],
    db: sqlite3.Connection,
    coord_version: int = 1,
) -> list[dict[str, Any]]:
    """
    Given an ordered sequence of outlets/depot:
    1. Checks which edges are already in DB.
    2. If missing edges exist, downloads the interconnected roads from OSRM in a single batch request.
    3. Persists all edges in the database.
    4. Returns the list of road geometry records.
    """
    if len(sequence) < 2:
        return []

    edges = [(sequence[i], sequence[i + 1]) for i in range(len(sequence) - 1)]

    # Check which edges need fetching
    missing_indices: list[int] = []
    resolved: dict[str, dict[str, Any]] = {}

    for i, (f, t) in enumerate(edges):
        row = db.execute(
            "SELECT from_id, to_id, coords, coord_version, distance_meters, duration_seconds "
            "FROM road_geometry WHERE from_id = ? AND to_id = ? AND coord_version = ?",
            (f, t, coord_version),
        ).fetchone()
        if row:
            resolved[f"{f}|{t}"] = {
                "from_id": f,
                "to_id": t,
                "coords": json.loads(row["coords"]) if isinstance(row["coords"], str) else row["coords"],
                "coord_version": row["coord_version"],
                "distance_meters": row["distance_meters"],
                "duration_seconds": row["duration_seconds"],
            }
        else:
            # Check reverse
            rev_row = db.execute(
                "SELECT from_id, to_id, coords, coord_version, distance_meters, duration_seconds "
                "FROM road_geometry WHERE from_id = ? AND to_id = ? AND coord_version = ?",
                (t, f, coord_version),
            ).fetchone()
            if rev_row:
                rev_coords = json.loads(rev_row["coords"]) if isinstance(rev_row["coords"], str) else rev_row["coords"]
                rev_list = list(reversed(rev_coords))
                db.execute(
                    "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (f, t, json.dumps(rev_list), coord_version, rev_row["distance_meters"], rev_row["duration_seconds"]),
                )
                resolved[f"{f}|{t}"] = {
                    "from_id": f,
                    "to_id": t,
                    "coords": rev_list,
                    "coord_version": coord_version,
                    "distance_meters": rev_row["distance_meters"],
                    "duration_seconds": rev_row["duration_seconds"],
                }
            else:
                missing_indices.append(i)

    # If any edges are missing, fetch the whole sequence via batch OSRM call
    if missing_indices:
        coords_list = [get_outlet_coordinates(stop_id, db=db) for stop_id in sequence]
        batch_legs = fetch_osrm_multi_waypoint(coords_list)
        for i, leg_data in enumerate(batch_legs):
            f, t = edges[i]
            # Save directed
            db.execute(
                "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (f, t, json.dumps(leg_data["coords"]), coord_version, leg_data["distance_meters"], leg_data["duration_seconds"]),
            )
            # Save reverse
            db.execute(
                "INSERT OR REPLACE INTO road_geometry (from_id, to_id, coords, coord_version, distance_meters, duration_seconds) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (t, f, json.dumps(list(reversed(leg_data["coords"]))), coord_version, leg_data["distance_meters"], leg_data["duration_seconds"]),
            )
            resolved[f"{f}|{t}"] = {
                "from_id": f,
                "to_id": t,
                "coords": leg_data["coords"],
                "coord_version": coord_version,
                "distance_meters": leg_data["distance_meters"],
                "duration_seconds": leg_data["duration_seconds"],
            }
        db.commit()

    return [resolved.get(f"{f}|{t}", lookup_or_fetch_edge(f, t, db, coord_version)) for f, t in edges]


def query_edges_batch(
    edges: list[list[str]],
    db: sqlite3.Connection,
    coord_version: int = 1,
) -> list[dict[str, Any]]:
    """
    Batch query or populate road geometries for an edge sequence.
    """
    if not edges:
        return []

    # Check if edges form a contiguous sequence
    is_contiguous = True
    for i in range(len(edges) - 1):
        if edges[i][1] != edges[i + 1][0]:
            is_contiguous = False
            break

    if is_contiguous and len(edges) > 1:
        sequence = [edges[0][0]] + [e[1] for e in edges]
        return resolve_sequence_road_geometries(sequence, db, coord_version)

    results: list[dict[str, Any]] = []
    for edge in edges:
        if len(edge) < 2:
            continue
        from_id, to_id = edge[0], edge[1]
        edge_data = lookup_or_fetch_edge(from_id, to_id, db, coord_version)
        results.append(edge_data)
    return results
