"""
Waypoint Optimizer — CSV Adapter
==================================
Maps competition-like CSV data into domain model objects.

IMPORTANT:
  - This adapter understands the documented Task 2B CSV field names.
  - It does NOT bundle confidential competition data.
  - Use synthetic/mock CSV files for testing.
  - The adapter is pure Python (no SQLAlchemy, no FastAPI).

Supported CSV schemas:
  Orders CSV:      scenario, order_ref, outlet_id, brand, district, depot,
                   dock_type, parking_constraint, mall_window,
                   window_open_time, window_close_time, temp_requirement,
                   order_units, order_weight_kg, order_volume_m3,
                   deferred_prev, defer_count, is_urgent

  Fleet availability CSV: scenario, vehicle_id, status

  Vehicle reference CSV:  vehicle_id, type, temp, weight_cap_kg,
                          volume_cap_m3, depot, fuel_type, km_per_l,
                          weekly_fuel_quota_l

  District travel CSV:    district, depot, road_class, free_flow_kmh,
                          depot_to_district_km, depot_to_district_freeflow_min,
                          inter_stop_km, inter_stop_freeflow_min

  Service allowance CSV:  brand, dock_type, service_allowance_min
"""
from __future__ import annotations

import csv
import io
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence, Union

from waypoint_optimizer.domain import (
    DistrictTravel, Order, Outlet, ServiceAllowance, Vehicle,
)
from waypoint_optimizer.enums import (
    Brand, DockType, ParkingConstraint, TempRequirement,
    TempSpec, VehicleStatus, VehicleType,
)
from waypoint_optimizer.input_validation import InputValidationError


@dataclass(frozen=True)
class ReferenceData:
    """
    Authoritative reference data loaded from reference CSVs.

    Contains store outlets, vehicle reference profiles, static district travel
    times, and service handling allowances. Also retains operational context rows
    if present (calendar, traffic speed, road conditions).
    """
    outlets: dict[str, Outlet]
    vehicles: list[Vehicle]
    travel: list[DistrictTravel]
    allowances: list[ServiceAllowance]
    ref_dir: str
    calendar_rows: Optional[list[dict[str, str]]] = None
    traffic_speed_rows: Optional[list[dict[str, str]]] = None
    road_conditions_rows: Optional[list[dict[str, str]]] = None


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _opt_str(val: str) -> Optional[str]:
    v = val.strip()
    return v if v else None


def _opt_float(val: str) -> Optional[float]:
    v = val.strip()
    return float(v) if v else None


def _bool_field(val: str) -> bool:
    return val.strip().lower() in ("1", "true", "yes", "t")


def _read_csv(source: Union[str, Path, io.TextIOBase]) -> list[dict[str, str]]:
    if isinstance(source, (str, Path)):
        p = Path(source)
        if not p.exists():
            raise FileNotFoundError(f"CSV file not found: {p}")
        with open(p, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    elif isinstance(source, io.TextIOBase):
        return list(csv.DictReader(source))
    elif isinstance(source, str):
        return list(csv.DictReader(io.StringIO(source)))
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")


# ──────────────────────────────────────────────────────────────────────────────
# Outlet reference loader
# ──────────────────────────────────────────────────────────────────────────────

def outlets_from_csv(source: Union[str, Path, io.TextIOBase]) -> dict[str, Outlet]:
    """
    Load Outlet domain objects from an authoritative outlets CSV.

    Preserves original outlet identifiers, including leading zeros (e.g. 'OUT001').
    Detects and rejects duplicate outlet IDs.

    Args:
        source: CSV file path, Path, or text stream.

    Returns:
        Dict mapping outlet_id -> Outlet domain object.

    Raises:
        InputValidationError: If duplicate outlet_id is found or required attributes are invalid.
    """
    rows = _read_csv(source)
    outlets: dict[str, Outlet] = {}
    for idx, row in enumerate(rows):
        outlet_id = row.get("outlet_id", "").strip()
        if not outlet_id:
            raise InputValidationError(f"Outlet row at index {idx} has an empty outlet_id.")
        if outlet_id in outlets:
            raise InputValidationError(
                f"Duplicate outlet_id {outlet_id!r} found in outlets reference at row {idx}."
            )

        try:
            brand = Brand(row["brand"].strip().lower())
        except (KeyError, ValueError) as e:
            raise InputValidationError(
                f"Outlet {outlet_id!r} has invalid brand: {row.get('brand')!r}"
            ) from e

        try:
            dock_type = DockType(row["dock_type"].strip().lower())
        except (KeyError, ValueError) as e:
            raise InputValidationError(
                f"Outlet {outlet_id!r} has invalid dock_type: {row.get('dock_type')!r}"
            ) from e

        try:
            parking = ParkingConstraint(row["parking_constraint"].strip().lower())
        except (KeyError, ValueError) as e:
            raise InputValidationError(
                f"Outlet {outlet_id!r} has invalid parking_constraint: {row.get('parking_constraint')!r}"
            ) from e

        district = row.get("district", "").strip()
        if not district:
            raise InputValidationError(f"Outlet {outlet_id!r} has an empty district.")

        depot = row.get("depot", "").strip()
        if not depot:
            raise InputValidationError(f"Outlet {outlet_id!r} has an empty depot.")

        outlets[outlet_id] = Outlet(
            outlet_id=outlet_id,
            brand=brand,
            district=district,
            depot=depot,
            dock_type=dock_type,
            parking_constraint=parking,
            mall_window=_opt_str(row.get("mall_window", "")),
            window_open_time=_opt_str(row.get("window_open_time", "")),
            window_close_time=_opt_str(row.get("window_close_time", "")),
        )
    return outlets


# ──────────────────────────────────────────────────────────────────────────────
# Order CSV adapters (with and without authoritative outlets)
# ──────────────────────────────────────────────────────────────────────────────

def load_orders_with_outlets(
    orders_source: Union[str, Path, io.TextIOBase],
    outlets: dict[str, Outlet],
    scenario_filter: Optional[str] = None,
) -> list[Order]:
    """
    Load Order domain objects by joining orders CSV against authoritative outlets.

    Contract:
      Required fields in orders CSV:
        order_ref, outlet_id, order_units, order_weight_kg, order_volume_m3,
        temp_requirement, deferred_prev, defer_count, is_urgent

      Authoritative outlet attributes (brand, district, depot, dock_type,
      parking_constraint, mall_window, window_open_time, window_close_time)
      are populated from `outlets`. If orders CSV contains any of these columns,
      the values are verified for consistency; mismatches raise an InputValidationError.

    Raises:
        InputValidationError: If unknown outlet_id, duplicate order_ref, conflicting
                              attributes, or invalid values are detected.
    """
    rows = _read_csv(orders_source)
    orders: list[Order] = []
    seen_order_refs: set[str] = set()

    for idx, row in enumerate(rows):
        if scenario_filter and row.get("scenario", "").strip() != scenario_filter:
            continue

        order_ref = row.get("order_ref", "").strip()
        if not order_ref:
            raise InputValidationError(f"Order row at index {idx} has an empty order_ref.")
        if order_ref in seen_order_refs:
            raise InputValidationError(f"Duplicate order_ref {order_ref!r} found in orders at row {idx}.")
        seen_order_refs.add(order_ref)

        outlet_id = row.get("outlet_id", "").strip()
        if not outlet_id:
            raise InputValidationError(f"Order {order_ref!r} has an empty outlet_id.")

        outlet = outlets.get(outlet_id)
        if outlet is None:
            raise InputValidationError(
                f"Order {order_ref!r} references unknown outlet_id {outlet_id!r}. "
                "All orders must reference an authoritative outlet from outlets.csv."
            )

        # Detect conflicting attributes if provided in the orders file
        if "brand" in row and row["brand"].strip():
            raw_b = row["brand"].strip().lower()
            if raw_b != outlet.brand.value:
                raise InputValidationError(
                    f"Order {order_ref!r} specifies brand {row['brand']!r} which conflicts with "
                    f"authoritative outlet {outlet_id!r} brand {outlet.brand.value!r}."
                )

        if "district" in row and row["district"].strip():
            raw_d = row["district"].strip()
            if raw_d != outlet.district:
                raise InputValidationError(
                    f"Order {order_ref!r} specifies district {raw_d!r} which conflicts with "
                    f"authoritative outlet {outlet_id!r} district {outlet.district!r}."
                )

        if "depot" in row and row["depot"].strip():
            raw_depot = row["depot"].strip()
            if raw_depot != outlet.depot:
                raise InputValidationError(
                    f"Order {order_ref!r} specifies depot {raw_depot!r} which conflicts with "
                    f"authoritative outlet {outlet_id!r} depot {outlet.depot!r}."
                )

        if "dock_type" in row and row["dock_type"].strip():
            raw_dock = row["dock_type"].strip().lower()
            if raw_dock != outlet.dock_type.value:
                raise InputValidationError(
                    f"Order {order_ref!r} specifies dock_type {row['dock_type']!r} which conflicts with "
                    f"authoritative outlet {outlet_id!r} dock_type {outlet.dock_type.value!r}."
                )

        if "parking_constraint" in row and row["parking_constraint"].strip():
            raw_park = row["parking_constraint"].strip().lower()
            if raw_park != outlet.parking_constraint.value:
                raise InputValidationError(
                    f"Order {order_ref!r} specifies parking_constraint {row['parking_constraint']!r} which conflicts with "
                    f"authoritative outlet {outlet_id!r} parking_constraint {outlet.parking_constraint.value!r}."
                )

        # Numeric and enum fields from order transaction
        try:
            temp_req = TempRequirement(row["temp_requirement"].strip().lower())
        except (KeyError, ValueError) as e:
            raise InputValidationError(
                f"Order {order_ref!r} has invalid temp_requirement: {row.get('temp_requirement')!r}."
            ) from e

        try:
            units = int(row["order_units"].strip())
            if units < 0:
                raise ValueError("order_units must be >= 0")
        except (KeyError, ValueError) as e:
            raise InputValidationError(
                f"Order {order_ref!r} has invalid order_units: {row.get('order_units')!r}."
            ) from e

        try:
            weight = float(row["order_weight_kg"].strip())
            if not math.isfinite(weight) or weight <= 0:
                raise ValueError("order_weight_kg must be finite and positive")
        except (KeyError, ValueError) as e:
            raise InputValidationError(
                f"Order {order_ref!r} has invalid order_weight_kg: {row.get('order_weight_kg')!r}."
            ) from e

        try:
            vol = float(row["order_volume_m3"].strip())
            if not math.isfinite(vol) or vol <= 0:
                raise ValueError("order_volume_m3 must be finite and positive")
        except (KeyError, ValueError) as e:
            raise InputValidationError(
                f"Order {order_ref!r} has invalid order_volume_m3: {row.get('order_volume_m3')!r}."
            ) from e

        # deferred_prev (with deprecated alias deferred_yesterday accepted)
        # days_since_last_served is NOT accepted: raise migration error
        if "days_since_last_served" in row:
            raise InputValidationError(
                f"Order {order_ref!r}: field 'days_since_last_served' has been removed. "
                "Use 'defer_count' (total number of deferrals, >= 0) instead. "
                "Note: defer_count counts deferral occurrences, not days."
            )
        if "deferred_prev" in row:
            deferred_prev = _bool_field(row.get("deferred_prev", "0"))
        elif "deferred_yesterday" in row:
            deferred_prev = _bool_field(row.get("deferred_yesterday", "0"))
        else:
            deferred_prev = False

        # defer_count (canonical integer >= 0)
        try:
            defer_count_raw = row.get("defer_count", "0").strip() or "0"
            defer_count = int(defer_count_raw)
            if defer_count < 0:
                raise ValueError("defer_count must be >= 0")
        except ValueError as e:
            raise InputValidationError(
                f"Order {order_ref!r} has invalid defer_count: {row.get('defer_count')!r}."
            ) from e

        # is_urgent (dispatcher-approved urgency signal)
        is_urgent = _bool_field(row.get("is_urgent", "0"))

        orders.append(Order(
            order_ref=order_ref,
            outlet_id=outlet_id,
            brand=outlet.brand,
            district=outlet.district,
            depot=outlet.depot,
            dock_type=outlet.dock_type,
            parking_constraint=outlet.parking_constraint,
            mall_window=outlet.mall_window,
            window_open_time=outlet.window_open_time,
            window_close_time=outlet.window_close_time,
            temp_requirement=temp_req,
            order_units=units,
            order_weight_kg=weight,
            order_volume_m3=vol,
            deferred_prev=deferred_prev,
            defer_count=defer_count,
            is_urgent=is_urgent,
        ))

    return orders


def orders_from_csv(
    source: Union[str, Path, io.TextIOBase],
    scenario_filter: Optional[str] = None,
    outlets: Optional[dict[str, Outlet]] = None,
) -> list[Order]:
    """
    Load Order objects from a CSV file.

    If ``outlets`` mapping is provided, outlet-owned attributes are joined from
    the authoritative outlets reference.
    If ``outlets`` is omitted, rows must be self-contained with outlet attributes.

    Args:
        source:          CSV file path, Path, or text stream.
        scenario_filter: If set, only rows where scenario == this value.
        outlets:         Optional dict of authoritative Outlet objects.

    Returns:
        List of Order domain objects.
    """
    if outlets is not None:
        return load_orders_with_outlets(source, outlets=outlets, scenario_filter=scenario_filter)

    rows = _read_csv(source)
    orders = []
    seen_refs = set()
    for row in rows:
        if scenario_filter and row.get("scenario", "").strip() != scenario_filter:
            continue
        order_ref = row["order_ref"].strip()
        if order_ref in seen_refs:
            raise InputValidationError(f"Duplicate order_ref {order_ref!r} found in orders.")
        seen_refs.add(order_ref)

        # Check required fields
        if "brand" not in row or "district" not in row or "dock_type" not in row:
            raise InputValidationError(
                f"Order {order_ref!r} is missing authoritative outlet attributes (brand/district/dock_type). "
                "Provide authoritative outlets to load_orders_with_outlets() or supply full fields."
            )

        # Reject legacy field that has different semantics from defer_count
        if "days_since_last_served" in row:
            raise InputValidationError(
                f"Order {order_ref!r}: field 'days_since_last_served' has been removed. "
                "Use 'defer_count' (total number of deferrals, >= 0) instead. "
                "Note: defer_count counts deferral occurrences, not days."
            )

        # defer_count: canonical integer >= 0 (guard in self-contained path too)
        try:
            defer_count_raw = row.get("defer_count", "0").strip() or "0"
            defer_count = int(defer_count_raw)
            if defer_count < 0:
                raise ValueError("defer_count must be >= 0")
        except ValueError as e:
            raise InputValidationError(
                f"Order {order_ref!r} has invalid defer_count: {row.get('defer_count')!r}."
            ) from e

        orders.append(Order(
            order_ref=order_ref,
            outlet_id=row["outlet_id"].strip(),
            brand=Brand(row["brand"].strip().lower()),
            district=row["district"].strip(),
            depot=row["depot"].strip(),
            dock_type=DockType(row["dock_type"].strip().lower()),
            parking_constraint=ParkingConstraint(row["parking_constraint"].strip().lower()),
            mall_window=_opt_str(row.get("mall_window", "")),
            window_open_time=_opt_str(row.get("window_open_time", "")),
            window_close_time=_opt_str(row.get("window_close_time", "")),
            temp_requirement=TempRequirement(row["temp_requirement"].strip().lower()),
            order_units=int(row["order_units"].strip()),
            order_weight_kg=float(row["order_weight_kg"].strip()),
            order_volume_m3=float(row["order_volume_m3"].strip()),
            deferred_prev=_bool_field(row.get("deferred_prev", row.get("deferred_yesterday", "0"))),
            defer_count=defer_count,
            is_urgent=_bool_field(row.get("is_urgent", "0")),
        ))
    return orders


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle CSV adapters
# ──────────────────────────────────────────────────────────────────────────────

def vehicles_from_csv(
    fleet_availability_csv: Optional[Union[str, Path, io.TextIOBase]] = None,
    vehicle_reference_csv: Optional[Union[str, Path, io.TextIOBase]] = None,
    scenario_filter: Optional[str] = None,
) -> list[Vehicle]:
    """
    Load Vehicle objects.

    Supported modes:
    1. Joined mode: fleet_availability_csv + vehicle_reference_csv.
    2. Single reference file mode: vehicle_reference_csv alone (or fleet_availability_csv
       alone if it contains the vehicle reference schema). Status defaults to AVAILABLE
       unless a status column is present.
    """
    # Detect single-file vs two-file call
    if vehicle_reference_csv is None and fleet_availability_csv is not None:
        # Caller passed a single file as first positional argument
        ref_source = fleet_availability_csv
        avail_source = None
    elif vehicle_reference_csv is not None and fleet_availability_csv is None:
        ref_source = vehicle_reference_csv
        avail_source = None
    else:
        ref_source = vehicle_reference_csv
        avail_source = fleet_availability_csv

    if ref_source is None:
        raise ValueError("Must provide at least one vehicle source CSV.")

    ref_rows = _read_csv(ref_source)

    # If availability is provided, load it
    availability: Optional[dict[str, dict[str, Any]]] = None
    if avail_source is not None:
        avail_rows = _read_csv(avail_source)
        availability = {}
        for row in avail_rows:
            if scenario_filter and row.get("scenario", "").strip() != scenario_filter:
                continue
            vid = row["vehicle_id"].strip()
            availability[vid] = {
                "status": row.get("status", "available").strip().lower(),
                "is_selected_for_planning": _bool_field(row.get("is_selected_for_planning", row.get("selected", "1"))),
                "remaining_trips": int(row.get("remaining_trips", "2").strip() or "2"),
                "earliest_availability_iso": _opt_str(row.get("earliest_availability_iso", row.get("earliest_availability", ""))),
                "weekly_fuel_used_l": _opt_float(row.get("weekly_fuel_used_l", row.get("fuel_used_l", ""))),
                "external_reservations_l": _opt_float(row.get("external_reservations_l", row.get("fuel_reserved_l", ""))) or 0.0,
                "exclusion_reason": _opt_str(row.get("exclusion_reason", "")),
            }

    vehicles = []
    seen_vids = set()

    for r in ref_rows:
        vid = r["vehicle_id"].strip()
        if not vid:
            continue

        # If availability table was provided, vehicle must be in it (or filtered by scenario)
        if availability is not None:
            if vid not in availability:
                continue
            avail_info = availability[vid]
            status_str = avail_info["status"]
            is_selected = avail_info["is_selected_for_planning"]
            rem_trips = avail_info["remaining_trips"]
            earliest_avail = avail_info["earliest_availability_iso"]
            fuel_used = avail_info["weekly_fuel_used_l"]
            fuel_res = avail_info["external_reservations_l"]
            excl_reason = avail_info["exclusion_reason"]
        else:
            # Fallback to status column in ref if present, else AVAILABLE
            status_str = r.get("status", "available").strip().lower()
            is_selected = _bool_field(r.get("is_selected_for_planning", r.get("selected", "1")))
            rem_trips = int(r.get("remaining_trips", "2").strip() or "2")
            earliest_avail = _opt_str(r.get("earliest_availability_iso", r.get("earliest_availability", "")))
            fuel_used = _opt_float(r.get("weekly_fuel_used_l", r.get("fuel_used_l", "")))
            fuel_res = _opt_float(r.get("external_reservations_l", r.get("fuel_reserved_l", ""))) or 0.0
            excl_reason = _opt_str(r.get("exclusion_reason", ""))

        if vid in seen_vids:
            raise InputValidationError(f"Duplicate vehicle_id {vid!r} found in vehicle reference.")
        seen_vids.add(vid)

        vehicles.append(Vehicle(
            vehicle_id=vid,
            status=VehicleStatus(status_str),
            type=VehicleType(r["type"].strip().lower()),
            temp=TempSpec(r["temp"].strip().lower()),
            weight_cap_kg=float(r["weight_cap_kg"].strip()),
            volume_cap_m3=float(r["volume_cap_m3"].strip()),
            depot=r["depot"].strip(),
            fuel_type=_opt_str(r.get("fuel_type", "")),
            km_per_l=_opt_float(r.get("km_per_l", "")),
            weekly_fuel_quota_l=_opt_float(r.get("weekly_fuel_quota_l", "")),
            weekly_fuel_used_l=fuel_used,
            is_selected_for_planning=is_selected,
            remaining_trips=rem_trips,
            earliest_availability_iso=earliest_avail,
            external_reservations_l=fuel_res,
            exclusion_reason=excl_reason,
        ))

    return vehicles


def load_fleet_state_from_csv(
    fleet_state_csv: Union[str, Path, io.TextIOBase],
    vehicle_reference: Union[dict[str, Vehicle], list[Vehicle], Path, str],
) -> list[Vehicle]:
    """
    Load authoritative daily fleet state and join with master vehicle reference.

    Enforces explicit inputs for:
      - Dispatcher selection (is_selected_for_planning)
      - Mechanical availability (status: available, in_workshop, reserved, etc.)
      - Remaining trips (0, 1, 2)
      - Earliest availability timestamp
      - Weekly fuel used to date (L)
      - External reservations (L)
      - Exclusion reason (if unselected or workshop)
    """
    if isinstance(vehicle_reference, (str, Path)):
        ref_vehicles = {v.vehicle_id: v for v in vehicles_from_csv(vehicle_reference_csv=vehicle_reference)}
    elif isinstance(vehicle_reference, list):
        ref_vehicles = {v.vehicle_id: v for v in vehicle_reference}
    elif isinstance(vehicle_reference, dict):
        ref_vehicles = dict(vehicle_reference)
    else:
        raise TypeError(f"Unsupported vehicle_reference type: {type(vehicle_reference)}")

    rows = _read_csv(fleet_state_csv)
    updated_vehicles: list[Vehicle] = []
    seen_vids = set()

    for row in rows:
        vid = row.get("vehicle_id", "").strip()
        if not vid:
            continue
        if vid not in ref_vehicles:
            raise InputValidationError(
                f"Fleet state references vehicle {vid!r} not found in master vehicle reference."
            )
        if vid in seen_vids:
            raise InputValidationError(
                f"Duplicate vehicle_id {vid!r} in fleet state input."
            )
        seen_vids.add(vid)

        base_v = ref_vehicles[vid]
        status_raw = row.get("status", base_v.status.value).strip().lower()
        try:
            status_val = VehicleStatus(status_raw)
        except ValueError:
            raise InputValidationError(
                f"Vehicle {vid!r} has invalid status {status_raw!r}. "
                f"Valid values are: {[s.value for s in VehicleStatus]}."
            )
        is_selected = _bool_field(row.get("is_selected_for_planning", row.get("selected", "1")))
        rem_trips = int(row.get("remaining_trips", "2").strip() or "2")
        earliest_avail = _opt_str(row.get("earliest_availability_iso", row.get("earliest_availability", "")))
        fuel_used = _opt_float(row.get("weekly_fuel_used_l", row.get("fuel_used_l", "")))
        fuel_res = _opt_float(row.get("external_reservations_l", row.get("fuel_reserved_l", "")))
        if is_selected:
            if fuel_used is None:
                raise InputValidationError(
                    f"Vehicle {vid!r} is selected for planning but missing required live fleet state 'weekly_fuel_used_l'. "
                    "Fuel usage must not be converted to zero."
                )
            if fuel_res is None:
                raise InputValidationError(
                    f"Vehicle {vid!r} is selected for planning but missing required live fleet state 'external_reservations_l'. "
                    "External reservations must not be converted to zero."
                )
        excl_reason = _opt_str(row.get("exclusion_reason", ""))

        updated_vehicles.append(Vehicle(
            vehicle_id=base_v.vehicle_id,
            status=status_val,
            type=base_v.type,
            temp=base_v.temp,
            weight_cap_kg=base_v.weight_cap_kg,
            volume_cap_m3=base_v.volume_cap_m3,
            depot=base_v.depot,
            fuel_type=base_v.fuel_type,
            km_per_l=base_v.km_per_l,
            weekly_fuel_quota_l=base_v.weekly_fuel_quota_l,
            weekly_fuel_used_l=fuel_used if fuel_used is not None else base_v.weekly_fuel_used_l,
            is_selected_for_planning=is_selected,
            remaining_trips=rem_trips,
            earliest_availability_iso=earliest_avail or base_v.earliest_availability_iso,
            external_reservations_l=fuel_res,
            exclusion_reason=excl_reason,
        ))

    # Include any reference vehicles not listed in fleet_state as unselected
    for vid, base_v in ref_vehicles.items():
        if vid not in seen_vids:
            updated_vehicles.append(Vehicle(
                vehicle_id=base_v.vehicle_id,
                status=base_v.status,
                type=base_v.type,
                temp=base_v.temp,
                weight_cap_kg=base_v.weight_cap_kg,
                volume_cap_m3=base_v.volume_cap_m3,
                depot=base_v.depot,
                fuel_type=base_v.fuel_type,
                km_per_l=base_v.km_per_l,
                weekly_fuel_quota_l=base_v.weekly_fuel_quota_l,
                weekly_fuel_used_l=base_v.weekly_fuel_used_l,
                is_selected_for_planning=False,
                remaining_trips=0,
                earliest_availability_iso=None,
                external_reservations_l=0.0,
                exclusion_reason="Not listed in daily fleet state input",
            ))

    return updated_vehicles



# ──────────────────────────────────────────────────────────────────────────────
# Travel and allowance CSV adapters
# ──────────────────────────────────────────────────────────────────────────────

def travel_from_csv(source: Union[str, Path, io.TextIOBase]) -> list[DistrictTravel]:
    """Load DistrictTravel objects from a CSV file."""
    rows = _read_csv(source)
    return [
        DistrictTravel(
            district=row["district"].strip(),
            depot=row["depot"].strip(),
            road_class=row.get("road_class", "A").strip(),
            free_flow_kmh=float(row.get("free_flow_kmh", "60").strip()),
            depot_to_district_km=float(row["depot_to_district_km"].strip()),
            depot_to_district_freeflow_min=float(row["depot_to_district_freeflow_min"].strip()),
            inter_stop_km=float(row["inter_stop_km"].strip()),
            inter_stop_freeflow_min=float(row["inter_stop_freeflow_min"].strip()),
        )
        for row in rows
    ]


def allowances_from_csv(source: Union[str, Path, io.TextIOBase]) -> list[ServiceAllowance]:
    """Load ServiceAllowance objects from a CSV file."""
    rows = _read_csv(source)
    return [
        ServiceAllowance(
            brand=Brand(row["brand"].strip().lower()),
            dock_type=DockType(row["dock_type"].strip().lower()),
            service_allowance_min=float(row["service_allowance_min"].strip()),
        )
        for row in rows
    ]


# ──────────────────────────────────────────────────────────────────────────────
# CSV writers (for exporting plans to CSV)
# ──────────────────────────────────────────────────────────────────────────────

def assignments_to_csv(
    served_assignments: list["OrderAssignment"],
    deferred_orders: list["DeferredOrder"],
    output: Union[str, Path, io.TextIOBase],
) -> None:
    """
    Export a plan to CSV for inspection or backend import.

    Columns: order_ref, vehicle_id, trip_number, status, deferral_reason
    """
    from waypoint_optimizer.domain import OrderAssignment, DeferredOrder

    rows = []
    for a in served_assignments:
        rows.append({
            "order_ref": a.order_ref,
            "vehicle_id": a.vehicle_id,
            "trip_number": a.trip_number,
            "status": "planned",
            "deferral_reason": "",
        })
    for d in deferred_orders:
        rows.append({
            "order_ref": d.order_ref,
            "vehicle_id": "",
            "trip_number": "",
            "status": "deferred",
            "deferral_reason": d.reason.value,
        })

    rows.sort(key=lambda r: r["order_ref"])

    fieldnames = ["order_ref", "vehicle_id", "trip_number", "status", "deferral_reason"]

    if isinstance(output, (str, Path)):
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def scenario_to_csv_dir(
    orders: Sequence[Order],
    vehicles: Sequence[Vehicle],
    travel: Sequence[DistrictTravel],
    allowances: Sequence[ServiceAllowance],
    output_dir: Union[str, Path],
    scenario_name: str = "synthetic_01",
) -> None:
    """
    Export full scenario domain objects to standard CSV files in a directory.

    Creates:
      - orders.csv
      - fleet_availability.csv
      - vehicle_reference.csv
      - district_travel.csv
      - service_allowances.csv
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. orders.csv
    order_fields = [
        "scenario", "order_ref", "outlet_id", "brand", "district", "depot",
        "dock_type", "parking_constraint", "mall_window",
        "window_open_time", "window_close_time", "temp_requirement",
        "order_units", "order_weight_kg", "order_volume_m3",
        "deferred_prev", "defer_count", "is_urgent",
    ]
    with open(out_path / "orders.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=order_fields)
        writer.writeheader()
        for o in orders:
            writer.writerow({
                "scenario": scenario_name,
                "order_ref": o.order_ref,
                "outlet_id": o.outlet_id,
                "brand": o.brand.value,
                "district": o.district,
                "depot": o.depot,
                "dock_type": o.dock_type.value,
                "parking_constraint": o.parking_constraint.value,
                "mall_window": o.mall_window or "",
                "window_open_time": o.window_open_time or "",
                "window_close_time": o.window_close_time or "",
                "temp_requirement": o.temp_requirement.value,
                "order_units": o.order_units,
                "order_weight_kg": o.order_weight_kg,
                "order_volume_m3": o.order_volume_m3,
                "deferred_prev": "1" if o.deferred_prev else "0",
                "defer_count": o.defer_count,
                "is_urgent": "1" if o.is_urgent else "0",
            })

    # 2. fleet_availability.csv
    with open(out_path / "fleet_availability.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scenario", "vehicle_id", "status"])
        writer.writeheader()
        for v in vehicles:
            writer.writerow({
                "scenario": scenario_name,
                "vehicle_id": v.vehicle_id,
                "status": v.status.value,
            })

    # 3. vehicle_reference.csv
    veh_ref_fields = [
        "vehicle_id", "type", "temp", "weight_cap_kg", "volume_cap_m3",
        "depot", "fuel_type", "km_per_l", "weekly_fuel_quota_l",
    ]
    with open(out_path / "vehicle_reference.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=veh_ref_fields)
        writer.writeheader()
        for v in vehicles:
            writer.writerow({
                "vehicle_id": v.vehicle_id,
                "type": v.type.value,
                "temp": v.temp.value,
                "weight_cap_kg": v.weight_cap_kg,
                "volume_cap_m3": v.volume_cap_m3,
                "depot": v.depot,
                "fuel_type": v.fuel_type or "diesel",
                "km_per_l": v.km_per_l or 4.0,
                "weekly_fuel_quota_l": v.weekly_fuel_quota_l or 200.0,
            })

    # 4. district_travel.csv
    travel_fields = [
        "district", "depot", "road_class", "free_flow_kmh",
        "depot_to_district_km", "depot_to_district_freeflow_min",
        "inter_stop_km", "inter_stop_freeflow_min",
    ]
    with open(out_path / "district_travel.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=travel_fields)
        writer.writeheader()
        for t in travel:
            writer.writerow({
                "district": t.district,
                "depot": t.depot,
                "road_class": t.road_class or "A",
                "free_flow_kmh": t.free_flow_kmh or 40.0,
                "depot_to_district_km": t.depot_to_district_km,
                "depot_to_district_freeflow_min": t.depot_to_district_freeflow_min,
                "inter_stop_km": t.inter_stop_km,
                "inter_stop_freeflow_min": t.inter_stop_freeflow_min,
            })

    # 5. service_allowances.csv
    with open(out_path / "service_allowances.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["brand", "dock_type", "service_allowance_min"])
        writer.writeheader()
        for sa in allowances:
            writer.writerow({
                "brand": sa.brand.value,
                "dock_type": sa.dock_type.value,
                "service_allowance_min": sa.service_allowance_min,
            })


# ──────────────────────────────────────────────────────────────────────────────
# Production reference data loader
# ──────────────────────────────────────────────────────────────────────────────

def load_reference_data(
    ref_dir: Union[str, Path],
    fleet_availability_source: Optional[Union[str, Path]] = None,
    scenario: Optional[str] = None,
) -> ReferenceData:
    """
    Load and validate authoritative reference data from a directory.

    Discovers:
      - outlets.csv (required)
      - district_travel.csv (required)
      - service_allowance.csv or service_allowances.csv (required)
      - vehicles.csv or vehicle_reference.csv (required)
      - fleet_availability.csv (optional)
      - calendar.csv, traffic_speed.csv, road_conditions.csv (optional operational data)

    Validates relational consistency across reference tables:
      - Every outlet's (district, depot) must exist in district_travel.
      - Every outlet's (brand, dock_type) must exist in service_allowances.
      - Every vehicle's depot must exist in district_travel depots.

    Raises:
        FileNotFoundError: If ref_dir or any required file is missing.
        InputValidationError: If duplicate keys, malformed data, or missing relationships occur.
    """
    ref_path = Path(ref_dir)
    if not ref_path.exists() or not ref_path.is_dir():
        raise FileNotFoundError(f"Reference data directory does not exist or is not a directory: {ref_path}")

    # 1. outlets.csv
    outlets_file = ref_path / "outlets.csv"
    if not outlets_file.exists():
        raise FileNotFoundError(f"Required outlets reference file not found: {outlets_file}")
    outlets = outlets_from_csv(outlets_file)

    # 2. district_travel.csv
    travel_file = ref_path / "district_travel.csv"
    if not travel_file.exists():
        raise FileNotFoundError(f"Required district travel reference file not found: {travel_file}")
    travel = travel_from_csv(travel_file)

    # 3. service_allowance.csv or service_allowances.csv
    sa_file = ref_path / "service_allowance.csv"
    if not sa_file.exists():
        sa_file = ref_path / "service_allowances.csv"
    if not sa_file.exists():
        raise FileNotFoundError(
            f"Required service allowance reference file not found in {ref_path} "
            "(expected service_allowance.csv or service_allowances.csv)"
        )
    allowances = allowances_from_csv(sa_file)

    # 4. vehicles.csv or vehicle_reference.csv
    veh_file = ref_path / "vehicles.csv"
    if not veh_file.exists():
        veh_file = ref_path / "vehicle_reference.csv"
    if not veh_file.exists():
        raise FileNotFoundError(
            f"Required vehicle reference file not found in {ref_path} "
            "(expected vehicles.csv or vehicle_reference.csv)"
        )

    avail_file = None
    if fleet_availability_source:
        avail_file = Path(fleet_availability_source)
    elif (ref_path / "fleet_availability.csv").exists():
        avail_file = ref_path / "fleet_availability.csv"

    vehicles = vehicles_from_csv(
        fleet_availability_csv=avail_file,
        vehicle_reference_csv=veh_file,
        scenario_filter=scenario,
    )

    # 5. Operational context files (Task 1 / Task 2A operational scheduling context)
    calendar_rows = _read_csv(ref_path / "calendar.csv") if (ref_path / "calendar.csv").exists() else None
    traffic_rows = _read_csv(ref_path / "traffic_speed.csv") if (ref_path / "traffic_speed.csv").exists() else None
    road_rows = _read_csv(ref_path / "road_conditions.csv") if (ref_path / "road_conditions.csv").exists() else None

    # 6. Relational consistency checks
    travel_keys = {(t.district, t.depot) for t in travel}
    allowance_keys = {(a.brand, a.dock_type) for a in allowances}
    known_depots = {t.depot for t in travel}

    for outlet in outlets.values():
        if (outlet.district, outlet.depot) not in travel_keys:
            raise InputValidationError(
                f"Outlet {outlet.outlet_id!r} has (district={outlet.district!r}, depot={outlet.depot!r}), "
                "which has no matching record in district_travel reference."
            )
        if (outlet.brand, outlet.dock_type) not in allowance_keys:
            raise InputValidationError(
                f"Outlet {outlet.outlet_id!r} has (brand={outlet.brand.value!r}, dock_type={outlet.dock_type.value!r}), "
                "which has no matching record in service_allowance reference."
            )

    for v in vehicles:
        if v.depot not in known_depots:
            raise InputValidationError(
                f"Vehicle {v.vehicle_id!r} references depot {v.depot!r}, "
                "which is not a recognized depot in district_travel reference."
            )

    return ReferenceData(
        outlets=outlets,
        vehicles=vehicles,
        travel=travel,
        allowances=allowances,
        ref_dir=str(ref_path.resolve()),
        calendar_rows=calendar_rows,
        traffic_speed_rows=traffic_rows,
        road_conditions_rows=road_rows,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Strict JSON Plan Exporter & Loader
# ──────────────────────────────────────────────────────────────────────────────

def export_plan_json(
    result: "OptimizationResult",
    output_path: Union[str, Path],
    provenance: Optional[dict[str, Any]] = None,
) -> Path:
    """
    Export an OptimizationResult to strict JSON, strictly disallowing NaN or infinity.

    Guarantees:
      - Destination cannot overwrite any input CSV.
      - Uses allow_nan=False to ensure strict standard-compliant JSON.
      - Includes full served assignments, deferred orders with evidence-based reasons,
        trips, independently validated metrics, and targeted CP-SAT status.

    Returns:
        Resolved Path to the saved JSON file.
    """
    out_file = Path(output_path).resolve()
    if out_file.suffix.lower() == ".csv":
        raise ValueError(
            f"Output file {out_file} must be a JSON file, not a CSV file (preventing source CSV overwrite)."
        )

    if out_file.exists() and out_file.suffix.lower() != ".json":
        raise ValueError(f"Output file {out_file} already exists and is not a JSON file.")

    plan_dict = {
        "status": result.status.value,
        "engine_name": result.engine_name,
        "engine_mode": result.engine_mode.value,
        "runtime_seconds": round(result.runtime_seconds, 4),
        "objective_value": round(result.objective_value, 4),
        "provenance": provenance or {},
        "metrics": {
            "total_orders": result.metrics.total_orders,
            "served_count": result.metrics.served_count,
            "deferred_count": result.metrics.deferred_count,
            "total_deferral_penalty": round(result.metrics.total_deferral_penalty, 4),
            "trips_created": result.metrics.trips_created,
            "vehicles_used": result.metrics.vehicles_used,
            "reefer_vehicles_used": result.metrics.reefer_vehicles_used,
            "van_vehicles_used": result.metrics.van_vehicles_used,
            "fresh_time_used_by_vehicle": {
                k: round(v, 2) for k, v in result.metrics.fresh_time_used_by_vehicle.items()
            },
            "style_tech_time_used_by_vehicle": {
                k: round(v, 2) for k, v in result.metrics.style_tech_time_used_by_vehicle.items()
            },
        },
        "validation": {
            "valid": result.validation.valid,
            "recomputed_served_count": result.validation.served_count,
            "recomputed_deferred_count": result.validation.deferred_count,
            "recomputed_total_deferral_penalty": round(result.validation.total_deferral_penalty, 4),
            "errors": [
                {
                    "rule": err.rule,
                    "detail": err.detail,
                    "order_ref": err.order_ref,
                    "vehicle_id": err.vehicle_id,
                }
                for err in result.validation.errors
            ],
        },
        "targeted_improvement": {
            "accepted": result.cpsat_improvements_accepted,
            "solver_status": result.cpsat_solver_status.value if result.cpsat_solver_status else None,
            "diagnostic_message": result.diagnostic_message,
        },
        "trips": [
            {
                "vehicle_id": tr.vehicle_id,
                "trip_number": tr.trip_number,
                "brand": tr.brand.value,
                "district": tr.district,
                "order_refs": list(tr.order_refs),
                "stop_sequence": list(tr.stop_sequence),
                "total_weight_kg": round(tr.total_weight_kg, 4),
                "total_volume_m3": round(tr.total_volume_m3, 4),
                "trip_minutes": round(tr.trip_minutes, 4),
                "remaining_weight_kg": round(tr.remaining_weight_kg, 4),
                "remaining_volume_m3": round(tr.remaining_volume_m3, 4),
            }
            for tr in result.trips
        ],
        "served_assignments": [
            {
                "order_ref": a.order_ref,
                "vehicle_id": a.vehicle_id,
                "trip_number": a.trip_number,
            }
            for a in result.served_assignments
        ],
        "deferred_orders": [
            {
                "order_ref": d.order_ref,
                "reason": d.reason.value,
                "detail": d.detail,
            }
            for d in result.deferred_orders
        ],
    }

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(plan_dict, f, indent=2, allow_nan=False)

    return out_file


def load_plan_json(path: Union[str, Path]) -> dict[str, Any]:
    """Load and parse an exported plan JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Plan file not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


