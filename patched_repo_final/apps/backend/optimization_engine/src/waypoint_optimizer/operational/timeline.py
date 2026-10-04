"""
Waypoint Optimizer — Vehicle Schedule Timeline & Multi-Trip Feasibility (Hackathon H1)
========================================================================================
Evaluates consecutive trip chronology, depot turnaround compliance, fleet mechanical
availability, dispatcher selection, and cumulative weekly fuel quota across all trips.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from waypoint_optimizer.domain import Vehicle, VehicleStatus
from waypoint_optimizer.operational.models import (
    EvaluatedTripSchedule, OperationalContext, OperationalMissingData,
    OperationalViolation, VehicleScheduleTimeline,
)


def evaluate_vehicle_timeline(
    vehicle: Vehicle,
    trips: list[EvaluatedTripSchedule],
    context: OperationalContext,
) -> VehicleScheduleTimeline:
    """
    Evaluates cumulative operational feasibility across all trips for a vehicle.

    Checks:
      1. Mechanical availability (workshop status).
      2. Dispatcher selection (vehicle selected for planning).
      3. Maximum trip count (daily limit <= 2 and <= remaining_trips).
      4. Consecutive trip chronology:
         Trip 2 Departure >= Trip 1 Depot Return + Depot Turnaround Duration.
      5. Cumulative weekly fuel consumption against weekly quota:
         Fuel Used + External Reservations + SUM(Proposed Trip Fuel) <= Weekly Quota.
    """
    violations: list[OperationalViolation] = []
    missing_data: list[OperationalMissingData] = []
    tz = ZoneInfo(context.timezone)

    # 1. Mechanical Status
    if vehicle.status == VehicleStatus.IN_WORKSHOP:
        violations.append(OperationalViolation(
            rule="VEHICLE_IN_WORKSHOP",
            detail=f"Vehicle {vehicle.vehicle_id!r} is currently in workshop and cannot be dispatched.",
            vehicle_id=vehicle.vehicle_id,
        ))

    # 2. Dispatcher Selection
    if not vehicle.is_selected_for_planning:
        reason = vehicle.exclusion_reason or "Excluded by dispatcher"
        violations.append(OperationalViolation(
            rule="VEHICLE_NOT_SELECTED",
            detail=f"Vehicle {vehicle.vehicle_id!r} is not selected for planning: {reason}",
            vehicle_id=vehicle.vehicle_id,
        ))

    # 3. Maximum Trip Limits
    max_trips = min(2, vehicle.remaining_trips)
    if len(trips) > max_trips:
        violations.append(OperationalViolation(
            rule="TRIP_COUNT_EXCEEDED",
            detail=(
                f"Vehicle {vehicle.vehicle_id!r} assigned {len(trips)} trips, exceeding "
                f"allowable limit of {max_trips} (remaining_trips={vehicle.remaining_trips})."
            ),
            vehicle_id=vehicle.vehicle_id,
        ))

    # 4. Consecutive Trip Chronology
    sorted_trips = sorted(trips, key=lambda t: t.trip_number)
    chronology_valid = True

    if len(sorted_trips) >= 2:
        for i in range(len(sorted_trips) - 1):
            prev_trip = sorted_trips[i]
            next_trip = sorted_trips[i + 1]

            prev_avail_dt = datetime.fromisoformat(prev_trip.vehicle_next_available_iso)
            next_dep_dt = datetime.fromisoformat(next_trip.departure_time_iso)

            if next_dep_dt < prev_avail_dt:
                chronology_valid = False
                overlap_min = (prev_avail_dt - next_dep_dt).total_seconds() / 60.0
                violations.append(OperationalViolation(
                    rule="CONSECUTIVE_TRIP_OVERLAP",
                    detail=(
                        f"Trip {next_trip.trip_number} departs at {next_trip.departure_time_iso}, "
                        f"which is before vehicle {vehicle.vehicle_id!r} is ready at depot "
                        f"({prev_trip.vehicle_next_available_iso}, required turnaround="
                        f"{context.depot_turnaround_duration_min:.1f} min). Overlap: {overlap_min:.1f} min."
                    ),
                    vehicle_id=vehicle.vehicle_id,
                    trip_number=next_trip.trip_number,
                ))

    # 5. Cumulative Weekly Fuel Quota
    prior_used = vehicle.weekly_fuel_used_l or 0.0
    external_reservations = vehicle.external_reservations_l or 0.0
    proposed_trips_fuel = sum(t.fuel_consumed_l for t in trips)
    cumulative_fuel_l = prior_used + external_reservations + proposed_trips_fuel
    weekly_fuel_valid = True

    if vehicle.weekly_fuel_quota_l is not None:
        if cumulative_fuel_l > vehicle.weekly_fuel_quota_l:
            weekly_fuel_valid = False
            violations.append(OperationalViolation(
                rule="CUMULATIVE_WEEKLY_FUEL_EXCEEDED",
                detail=(
                    f"Cumulative weekly fuel {cumulative_fuel_l:.2f} L exceeds vehicle "
                    f"{vehicle.vehicle_id!r} weekly quota of {vehicle.weekly_fuel_quota_l:.2f} L "
                    f"(prior used={prior_used:.2f} L, external reservations={external_reservations:.2f} L, "
                    f"proposed {len(trips)} trip(s) fuel={proposed_trips_fuel:.2f} L)."
                ),
                vehicle_id=vehicle.vehicle_id,
            ))

    # Propagate any trip-level missing data or violations
    for t in trips:
        missing_data.extend(t.missing_data)
        violations.extend(t.violations)

    return VehicleScheduleTimeline(
        vehicle_id=vehicle.vehicle_id,
        trips=sorted_trips,
        chronology_valid=chronology_valid,
        weekly_fuel_valid=weekly_fuel_valid,
        cumulative_fuel_l=round(cumulative_fuel_l, 2),
        weekly_fuel_quota_l=vehicle.weekly_fuel_quota_l,
        violations=violations,
        missing_data=missing_data,
    )
