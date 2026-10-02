"""Module B -- Trip / route snapshot read APIs."""

from fastapi import APIRouter, Depends, HTTPException
import sqlite3

from app.database import get_db
from app.models.schemas import (
    TodayTripsResponse, TripSummary, TripManifestResponse,
    TripBriefingResponse, StopDTO, ManifestLineDTO, RouteLegDTO, Coords,
)
from app.middleware.auth_middleware import get_current_driver

router = APIRouter()


def _trip_summary(row) -> TripSummary:
    """Build a TripSummary from a trips row."""
    return TripSummary(
        trip_id=row["id"],
        trip_no=row["trip_no"],
        brand=row["brand"],
        district=row["district"],
        depot=row["depot"],
        vehicle_id=row["vehicle_id"],
        status=row["status"],
        stop_count=row["stop_count"],
        manifest_units=row["manifest_units"],
        deliverable_units=row["deliverable_units"],
        return_units=row["return_units"],
        weight_kg=row["weight_kg"],
        volume_m3=row["volume_m3"],
        depart_time=row["depart_time"],
        eta_return=row["eta_return"],
        capability=row["capability"],
        distance_km=row["distance_km"],
        drive_time=row["drive_time"],
    )


def _stop_dto(sr) -> StopDTO:
    """Build a StopDTO from a stops row."""
    coords = None
    if sr["lat"] is not None and sr["lng"] is not None:
        coords = Coords(lat=sr["lat"], lng=sr["lng"])
    return StopDTO(
        stop_id=sr["id"],
        seq=sr["seq"],
        outlet_id=sr["outlet_id"],
        name=sr["name"],
        address=sr["address"],
        coords=coords,
        window_open=sr["window_open"],
        window_close=sr["window_close"],
        mall_window=sr["mall_window"],
        dock_type=sr["dock_type"],
        parking_constraint=sr["parking_constraint"],
        temp_requirement=sr["temp_requirement"],
        order_units=sr["order_units"],
        deliverable_units=sr["deliverable_units"],
        return_units=sr["return_units"],
        return_crate=sr["return_crate"],
        manager_name=sr["manager_name"],
        manager_phone_masked=sr["manager_phone_masked"],
        service_allowance_min=sr["service_allowance_min"],
        special_instructions=sr["special_instructions"],
        status=sr["status"],
        row_version=sr["row_version"],
    )


# ── GET /today ───────────────────────────────────────────────────────────

@router.get("/today", response_model=TodayTripsResponse)
def get_today_trips(
    payload: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    driver_id = payload["sub"]
    cur = db.cursor()

    cur.execute("SELECT name FROM drivers WHERE id = ?", (driver_id,))
    driver_row = cur.fetchone()
    if not driver_row:
        raise HTTPException(status_code=404, detail="Driver not found")

    cur.execute("SELECT * FROM trips WHERE driver_id = ? ORDER BY trip_no", (driver_id,))
    trip_rows = cur.fetchall()

    trips = [_trip_summary(r) for r in trip_rows]

    return TodayTripsResponse(
        date="2026-09-26",
        driver_id=driver_id,
        driver_name=driver_row["name"],
        vehicle_id=trip_rows[0]["vehicle_id"] if trip_rows else "VEH014",
        trips=trips,
    )


# ── GET /{trip_id} ───────────────────────────────────────────────────────

@router.get("/{trip_id}", response_model=TripSummary)
def get_trip(
    trip_id: str,
    payload: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    driver_id = payload["sub"]
    cur = db.cursor()

    cur.execute("SELECT * FROM trips WHERE id = ? AND driver_id = ?", (trip_id, driver_id))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Trip not found")

    return _trip_summary(row)


# ── GET /{trip_id}/manifest ──────────────────────────────────────────────

@router.get("/{trip_id}/manifest", response_model=TripManifestResponse)
def get_trip_manifest(
    trip_id: str,
    payload: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    driver_id = payload["sub"]
    cur = db.cursor()

    # Trip
    cur.execute("SELECT * FROM trips WHERE id = ? AND driver_id = ?", (trip_id, driver_id))
    trip_row = cur.fetchone()
    if not trip_row:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Stops
    cur.execute("SELECT * FROM stops WHERE trip_id = ? ORDER BY seq", (trip_id,))
    stops = [_stop_dto(sr) for sr in cur.fetchall()]

    # Manifest lines
    cur.execute("SELECT * FROM manifest_lines WHERE trip_id = ?", (trip_id,))
    manifest_lines = []
    for ml in cur.fetchall():
        manifest_lines.append(ManifestLineDTO(
            stop_id=ml["stop_id"],
            outlet_id=ml["outlet_id"],
            item=ml["item_name"],
            manifest_qty=ml["manifest_qty"],
            deliverable_qty=ml["deliverable_qty"],
            return_qty=ml["return_qty"],
            reason=ml["reason"],
            return_crate=ml["return_crate"],
            loader_id=ml["loader_id"],
            loader_note=ml["loader_note"],
            pre_flagged=bool(ml["pre_flagged"]),
        ))

    # Route legs
    cur.execute("SELECT * FROM route_legs WHERE trip_id = ?", (trip_id,))
    legs = []
    for leg in cur.fetchall():
        legs.append(RouteLegDTO(
            from_point=leg["from_point"],
            to_stop_id=leg["to_stop_id"],
            to_outlet=leg["to_outlet_id"],
            distance_km=leg["distance_km"],
            planned_travel_duration_min=leg["planned_travel_duration_min"],
        ))

    return TripManifestResponse(
        trip=_trip_summary(trip_row),
        stops=stops,
        manifest_lines=manifest_lines,
        legs=legs,
    )


# ── GET /{trip_id}/briefing ──────────────────────────────────────────────

@router.get("/{trip_id}/briefing", response_model=TripBriefingResponse)
def get_trip_briefing(
    trip_id: str,
    payload: dict = Depends(get_current_driver),
    db: sqlite3.Connection = Depends(get_db),
):
    driver_id = payload["sub"]
    cur = db.cursor()

    cur.execute("SELECT * FROM trips WHERE id = ? AND driver_id = ?", (trip_id, driver_id))
    trip_row = cur.fetchone()
    if not trip_row:
        raise HTTPException(status_code=404, detail="Trip not found")

    cur.execute("SELECT * FROM stops WHERE trip_id = ? ORDER BY seq", (trip_id,))
    stop_rows = cur.fetchall()

    stops = []
    flagged_stop_ids = []
    for sr in stop_rows:
        stops.append(_stop_dto(sr))
        if sr["deliverable_units"] != sr["order_units"] or sr["return_units"] > 0:
            flagged_stop_ids.append(sr["id"])

    cur.execute("SELECT * FROM route_legs WHERE trip_id = ?", (trip_id,))
    legs = []
    total_km = 0.0
    for leg in cur.fetchall():
        legs.append(RouteLegDTO(
            from_point=leg["from_point"],
            to_stop_id=leg["to_stop_id"],
            to_outlet=leg["to_outlet_id"],
            distance_km=leg["distance_km"],
            planned_travel_duration_min=leg["planned_travel_duration_min"],
        ))
        total_km += (leg["distance_km"] or 0)

    return TripBriefingResponse(
        trip=_trip_summary(trip_row),
        stops=stops,
        legs=legs,
        flagged_stops=flagged_stop_ids,
        total_distance_km=round(total_km, 1),
        estimated_duration=trip_row["drive_time"],
    )
