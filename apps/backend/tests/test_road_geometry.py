"""
Tests for road geometry database storage, OSRM routing, deterministic outlet coordinates,
and API endpoints.
"""

import math
import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db_connection, init_db
from app.seed import seed
from app.services.geo_service import (
    get_outlet_coordinates,
    generate_spline_points,
    lookup_or_fetch_edge,
    query_edges_batch,
    KNOWN_COORDS,
)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    seed()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_outlet_coordinates_known():
    """Verify known outlets and depots return accurate canonical coordinates."""
    coords = get_outlet_coordinates("DEPOT:KANDY_HUB")
    assert coords == (7.2906, 80.6337)

    out42 = get_outlet_coordinates("OUT042")
    assert out42 == (7.1666, 80.5666)


def test_outlet_coordinates_deterministic_arbitrary():
    """Verify arbitrary outlets with only distance return deterministic coordinates."""
    # Distance: 15 km from Kandy Hub
    c1 = get_outlet_coordinates("OUT999", distance_km=15.0)
    c2 = get_outlet_coordinates("OUT999", distance_km=15.0)
    assert c1 == c2, "Coordinates must be strictly deterministic"

    # Different outlet ID produces different coordinates
    c3 = get_outlet_coordinates("OUT888", distance_km=15.0)
    assert c1 != c3

    # Check that distance from depot is approximately 15 km
    depot_lat, depot_lng = KNOWN_COORDS["DEPOT:KANDY_HUB"]
    d_km = math.sqrt(
        (c1[0] - depot_lat) ** 2 + ((c1[1] - depot_lng) * math.cos(math.radians(depot_lat))) ** 2
    ) * 111.0
    assert abs(d_km - 15.0) < 1.0, f"Expected distance ~15 km, got {d_km}"


def test_spline_generation():
    """Test safety-net spline interpolation between two points."""
    p1 = (7.2906, 80.6337)
    p2 = (7.1666, 80.5666)
    pts = generate_spline_points(p1, p2, steps=6)
    assert len(pts) == 7
    assert pts[0] == [7.2906, 80.6337]
    assert pts[-1] == [7.1666, 80.5666]


def test_road_geometry_db_query_and_reverse_hit():
    """Test directed lookup, reverse caching, and persistence in road_geometry table."""
    conn = get_db_connection()
    try:
        # Pre-seeded edge
        edge = lookup_or_fetch_edge("DEPOT:KANDY_HUB", "OUT042", conn)
        assert edge["from_id"] == "DEPOT:KANDY_HUB"
        assert edge["to_id"] == "OUT042"
        assert len(edge["coords"]) > 10
        assert edge["distance_meters"] is not None

        # Reverse lookup for edge that only had directed hit
        # Test edge OUT049 -> OUT052 is seeded; query OUT052 -> OUT049
        rev_edge = lookup_or_fetch_edge("OUT052", "OUT049", conn)
        assert rev_edge["from_id"] == "OUT052"
        assert rev_edge["to_id"] == "OUT049"
        assert len(rev_edge["coords"]) > 0

        # Query batch
        batch = query_edges_batch(
            [["DEPOT:KANDY_HUB", "OUT042"], ["OUT042", "OUT047"]],
            conn,
        )
        assert len(batch) == 2
        assert batch[0]["from_id"] == "DEPOT:KANDY_HUB"
        assert batch[1]["from_id"] == "OUT042"
    finally:
        conn.close()


def test_road_geometry_api_query_endpoint(client):
    """Test POST /api/v1/driver/road-geometry/query."""
    payload = {
        "edges": [
            ["DEPOT:KANDY_HUB", "OUT042"],
            ["OUT042", "OUT047"],
            ["OUT047", "OUT049"],
        ],
        "coord_version": 1,
    }
    res = client.post("/api/v1/driver/road-geometry/query", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "rows" in data
    assert len(data["rows"]) == 3
    assert data["rows"][0]["from_id"] == "DEPOT:KANDY_HUB"
    assert data["rows"][0]["to_id"] == "OUT042"
    assert len(data["rows"][0]["coords"]) > 0
    # First point should be near Kandy Hub lat ~7.29, lng ~80.63
    first_pt = data["rows"][0]["coords"][0]
    assert 7.0 < first_pt[0] < 7.5
    assert 80.0 < first_pt[1] < 81.0


def test_road_geometry_api_single_edge(client):
    """Test GET /api/v1/driver/road-geometry?from_id=...&to_id=..."""
    res = client.get(
        "/api/v1/driver/road-geometry",
        params={"from_id": "DEPOT:KANDY_HUB", "to_id": "OUT042"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["from_id"] == "DEPOT:KANDY_HUB"
    assert data["to_id"] == "OUT042"
    assert len(data["coords"]) > 0


def test_road_sequence_endpoint_arbitrary_outlets(client):
    """Test POST /api/v1/driver/road-geometry/sequence with arbitrary outlet numbers."""
    payload = {
        "sequence": ["DEPOT", "OUT101", "OUT102", "OUT103"],
        "coord_version": 1,
    }
    res = client.post("/api/v1/driver/road-geometry/sequence", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["sequence"] == payload["sequence"]
    assert len(data["edges"]) == 3
    assert len(data["polyline"]) > 10
    assert data["total_distance_meters"] > 0
    # Edges should be stored in road_geometry DB
    edge0 = data["edges"][0]
    assert edge0["from_id"] == "DEPOT"
    assert edge0["to_id"] == "OUT101"

