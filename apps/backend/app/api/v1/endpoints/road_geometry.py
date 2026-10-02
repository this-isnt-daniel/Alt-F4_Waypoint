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
)
from app.services.geo_service import (
    lookup_or_fetch_edge,
    query_edges_batch,
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
