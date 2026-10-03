"""
Road Geometry API endpoints: Query and fetch road polyline geometry for routes.
"""

from __future__ import annotations

import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.models.schemas import (
    RoadGeometryRow,
    RoadGeometryQueryRequest,
    RoadGeometryQueryResponse,
    RoadSequenceRequest,
    RoadSequenceResponse,
)
from app.services.geo_service import (
    lookup_or_fetch_edge,
    query_edges_batch,
    resolve_sequence_road_geometries,
)

router = APIRouter()


@router.post("/query", response_model=RoadGeometryQueryResponse)
def query_road_geometry(
    req: RoadGeometryQueryRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Query road geometries for an edge sequence.
    If an edge is missing from the database, it is dynamically fetched/computed
    and cached so subsequent calls are fast.
    """
    if not req.edges:
        return RoadGeometryQueryResponse(rows=[])

    rows = query_edges_batch(req.edges, db, coord_version=req.coord_version)
    return RoadGeometryQueryResponse(
        rows=[
            RoadGeometryRow(
                from_id=r["from_id"],
                to_id=r["to_id"],
                coords=r["coords"],
                coord_version=r.get("coord_version", req.coord_version),
                distance_meters=r.get("distance_meters"),
                duration_seconds=r.get("duration_seconds"),
            )
            for r in rows
        ]
    )


@router.post("/sequence", response_model=RoadSequenceResponse)
def resolve_sequence(
    req: RoadSequenceRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Given an ordered sequence of outlet numbers/depot from dispatcher:
    1. Synthesizes coordinates for any unknown outlets.
    2. Downloads interconnected roads from OSRM in a single batch request to avoid rate-limiting.
    3. Persists road geometries into database.
    4. Stitches the continuous polyline (dropping duplicated junction points).
    """
    if len(req.sequence) < 2:
        return RoadSequenceResponse(
            sequence=req.sequence,
            polyline=[],
            edges=[],
            total_distance_meters=0.0,
            total_duration_seconds=0.0,
        )

    edge_dicts = resolve_sequence_road_geometries(req.sequence, db, coord_version=req.coord_version)

    rows = [
        RoadGeometryRow(
            from_id=r["from_id"],
            to_id=r["to_id"],
            coords=r["coords"],
            coord_version=r.get("coord_version", req.coord_version),
            distance_meters=r.get("distance_meters"),
            duration_seconds=r.get("duration_seconds"),
        )
        for r in edge_dicts
    ]

    # Stitch polyline: drop duplicated junction points
    stitched_polyline: list[list[float]] = []
    for i, r in enumerate(rows):
        pts = r.coords
        if i == 0:
            stitched_polyline.extend(pts)
        else:
            stitched_polyline.extend(pts[1:] if len(pts) > 1 else pts)

    total_dist = sum(r.distance_meters or 0.0 for r in rows)
    total_dur = sum(r.duration_seconds or 0.0 for r in rows)

    return RoadSequenceResponse(
        sequence=req.sequence,
        polyline=stitched_polyline,
        edges=rows,
        total_distance_meters=round(total_dist, 1),
        total_duration_seconds=round(total_dur, 1),
    )


@router.get("", response_model=RoadGeometryRow)
def get_edge_geometry(
    from_id: str = Query(..., description="Starting outlet/depot ID"),
    to_id: str = Query(..., description="Destination outlet/depot ID"),
    coord_version: int = Query(1, description="Coordinate version"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get road geometry for a single edge."""
    edge_data = lookup_or_fetch_edge(from_id, to_id, db, coord_version=coord_version)
    return RoadGeometryRow(
        from_id=edge_data["from_id"],
        to_id=edge_data["to_id"],
        coords=edge_data["coords"],
        coord_version=edge_data.get("coord_version", coord_version),
        distance_meters=edge_data.get("distance_meters"),
        duration_seconds=edge_data.get("duration_seconds"),
    )

