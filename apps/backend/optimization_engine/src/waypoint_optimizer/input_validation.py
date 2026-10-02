"""
Waypoint Optimizer — Input Validation Gateway
==============================================
Defensive validation layer for public optimization entry points and adapters.
Reconstructs checks from authoritative raw inputs and ensures strict data integrity
before optimization algorithms execute.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, Optional

from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.domain import (
    DistrictTravel, Order, ServiceAllowance, Vehicle,
)
from waypoint_optimizer.enums import (
    Brand, DockType, ParkingConstraint, TempRequirement,
    TempSpec, VehicleStatus, VehicleType,
)


@dataclass(frozen=True)
class InputErrorDetail:
    """Detailed record of an input validation error."""
    field: str
    message: str
    entity_id: Optional[str] = None


class InputValidationError(ValueError):
    """
    Raised when input data fails pre-optimization validation.
    Contains structured error records for programmatic handling.
    """
    def __init__(self, message: str, errors: list[InputErrorDetail] | None = None) -> None:
        super().__init__(message)
        self.errors: list[InputErrorDetail] = errors or []


def validate_inputs(
    orders: Sequence[Order],
    vehicles: Sequence[Vehicle],
    district_travel: Sequence[DistrictTravel],
    service_allowances: Sequence[ServiceAllowance],
    config: Optional[OptimizerConfig] = None,
) -> None:
    """
    Validate input collections, reference data, and configuration before optimization.

    Raises:
        InputValidationError: If any validation checks fail.
    """
    errors: list[InputErrorDetail] = []

    # ── 1. Unique Order IDs & Field Constraints ──────────────────────────────
    seen_order_refs: set[str] = set()
    for idx, o in enumerate(orders):
        if not o.order_ref or not isinstance(o.order_ref, str):
            errors.append(InputErrorDetail(
                field="order_ref",
                message=f"Order at index {idx} has an empty or non-string order_ref.",
                entity_id=str(o.order_ref),
            ))
        elif o.order_ref in seen_order_refs:
            errors.append(InputErrorDetail(
                field="order_ref",
                message=f"Duplicate order_ref {o.order_ref!r} found.",
                entity_id=o.order_ref,
            ))
        else:
            seen_order_refs.add(o.order_ref)

        if not o.outlet_id or not isinstance(o.outlet_id, str):
            errors.append(InputErrorDetail(
                field="outlet_id",
                message=f"Order {o.order_ref!r} has an empty or non-string outlet_id.",
                entity_id=o.order_ref,
            ))

        if not o.district or not isinstance(o.district, str):
            errors.append(InputErrorDetail(
                field="district",
                message=f"Order {o.order_ref!r} has an empty or non-string district.",
                entity_id=o.order_ref,
            ))

        if not o.depot or not isinstance(o.depot, str):
            errors.append(InputErrorDetail(
                field="depot",
                message=f"Order {o.order_ref!r} has an empty or non-string depot.",
                entity_id=o.order_ref,
            ))

        # Enums
        if not isinstance(o.brand, Brand):
            errors.append(InputErrorDetail(
                field="brand",
                message=f"Order {o.order_ref!r} has invalid brand {o.brand!r}.",
                entity_id=o.order_ref,
            ))
        if not isinstance(o.dock_type, DockType):
            errors.append(InputErrorDetail(
                field="dock_type",
                message=f"Order {o.order_ref!r} has invalid dock_type {o.dock_type!r}.",
                entity_id=o.order_ref,
            ))
        if not isinstance(o.parking_constraint, ParkingConstraint):
            errors.append(InputErrorDetail(
                field="parking_constraint",
                message=f"Order {o.order_ref!r} has invalid parking_constraint {o.parking_constraint!r}.",
                entity_id=o.order_ref,
            ))
        if not isinstance(o.temp_requirement, TempRequirement):
            errors.append(InputErrorDetail(
                field="temp_requirement",
                message=f"Order {o.order_ref!r} has invalid temp_requirement {o.temp_requirement!r}.",
                entity_id=o.order_ref,
            ))

        # Finite numeric checks & non-negativity
        if not math.isfinite(o.order_weight_kg) or o.order_weight_kg < 0:
            errors.append(InputErrorDetail(
                field="order_weight_kg",
                message=f"Order {o.order_ref!r} weight ({o.order_weight_kg}) must be finite and non-negative.",
                entity_id=o.order_ref,
            ))
        if not math.isfinite(o.order_volume_m3) or o.order_volume_m3 < 0:
            errors.append(InputErrorDetail(
                field="order_volume_m3",
                message=f"Order {o.order_ref!r} volume ({o.order_volume_m3}) must be finite and non-negative.",
                entity_id=o.order_ref,
            ))
        if not isinstance(o.order_units, int) or o.order_units < 0:
            errors.append(InputErrorDetail(
                field="order_units",
                message=f"Order {o.order_ref!r} order_units ({o.order_units}) must be a non-negative integer.",
                entity_id=o.order_ref,
            ))
        if not isinstance(o.days_since_last_served, int) or o.days_since_last_served < 0:
            errors.append(InputErrorDetail(
                field="days_since_last_served",
                message=f"Order {o.order_ref!r} days_since_last_served ({o.days_since_last_served}) must be non-negative integer.",
                entity_id=o.order_ref,
            ))

    # ── 2. Unique Vehicle IDs & Vehicle Constraints ──────────────────────────
    seen_vehicle_ids: set[str] = set()
    for idx, v in enumerate(vehicles):
        if not v.vehicle_id or not isinstance(v.vehicle_id, str):
            errors.append(InputErrorDetail(
                field="vehicle_id",
                message=f"Vehicle at index {idx} has an empty or non-string vehicle_id.",
                entity_id=str(v.vehicle_id),
            ))
        elif v.vehicle_id in seen_vehicle_ids:
            errors.append(InputErrorDetail(
                field="vehicle_id",
                message=f"Duplicate vehicle_id {v.vehicle_id!r} found.",
                entity_id=v.vehicle_id,
            ))
        else:
            seen_vehicle_ids.add(v.vehicle_id)

        if not v.depot or not isinstance(v.depot, str):
            errors.append(InputErrorDetail(
                field="depot",
                message=f"Vehicle {v.vehicle_id!r} has an empty or non-string depot.",
                entity_id=v.vehicle_id,
            ))

        if not isinstance(v.status, VehicleStatus):
            errors.append(InputErrorDetail(
                field="status",
                message=f"Vehicle {v.vehicle_id!r} has invalid status {v.status!r}.",
                entity_id=v.vehicle_id,
            ))
        if not isinstance(v.type, VehicleType):
            errors.append(InputErrorDetail(
                field="type",
                message=f"Vehicle {v.vehicle_id!r} has invalid type {v.type!r}.",
                entity_id=v.vehicle_id,
            ))
        if not isinstance(v.temp, TempSpec):
            errors.append(InputErrorDetail(
                field="temp",
                message=f"Vehicle {v.vehicle_id!r} has invalid temp {v.temp!r}.",
                entity_id=v.vehicle_id,
            ))

        # Capacities must be positive finite values
        if not math.isfinite(v.weight_cap_kg) or v.weight_cap_kg <= 0:
            errors.append(InputErrorDetail(
                field="weight_cap_kg",
                message=f"Vehicle {v.vehicle_id!r} weight_cap_kg ({v.weight_cap_kg}) must be finite and positive.",
                entity_id=v.vehicle_id,
            ))
        if not math.isfinite(v.volume_cap_m3) or v.volume_cap_m3 <= 0:
            errors.append(InputErrorDetail(
                field="volume_cap_m3",
                message=f"Vehicle {v.vehicle_id!r} volume_cap_m3 ({v.volume_cap_m3}) must be finite and positive.",
                entity_id=v.vehicle_id,
            ))

    # ── 3. Reference Data Uniqueness & Bounds ─────────────────────────────────
    travel_keys: set[tuple[str, str]] = set()
    for dt in district_travel:
        key = (dt.district, dt.depot)
        if key in travel_keys:
            errors.append(InputErrorDetail(
                field="district_travel",
                message=f"Duplicate district travel record for district={dt.district!r}, depot={dt.depot!r}.",
            ))
        travel_keys.add(key)

        for num_field, val in [
            ("depot_to_district_freeflow_min", dt.depot_to_district_freeflow_min),
            ("inter_stop_freeflow_min", dt.inter_stop_freeflow_min),
            ("depot_to_district_km", dt.depot_to_district_km),
            ("inter_stop_km", dt.inter_stop_km),
        ]:
            if not math.isfinite(val) or val < 0:
                errors.append(InputErrorDetail(
                    field=f"district_travel.{num_field}",
                    message=f"District travel for {key} has non-finite or negative {num_field}: {val}.",
                ))

    allowance_keys: set[tuple[Brand, DockType]] = set()
    for sa in service_allowances:
        key = (sa.brand, sa.dock_type)
        if key in allowance_keys:
            errors.append(InputErrorDetail(
                field="service_allowances",
                message=f"Duplicate service allowance record for brand={sa.brand.value!r}, dock_type={sa.dock_type.value!r}.",
            ))
        allowance_keys.add(key)

        if not math.isfinite(sa.service_allowance_min) or sa.service_allowance_min < 0:
            errors.append(InputErrorDetail(
                field="service_allowance_min",
                message=f"Service allowance for {key} has non-finite or negative value: {sa.service_allowance_min}.",
            ))

    # ── 4. Relational Integrity: Reference Coverage for Orders ────────────────
    # Check that required references exist for every order
    for o in orders:
        if (o.district, o.depot) not in travel_keys:
            errors.append(InputErrorDetail(
                field="district_travel",
                message=(
                    f"Order {o.order_ref!r} requires district_travel for "
                    f"district={o.district!r}, depot={o.depot!r}, but no record exists."
                ),
                entity_id=o.order_ref,
            ))
        if (o.brand, o.dock_type) not in allowance_keys:
            errors.append(InputErrorDetail(
                field="service_allowances",
                message=(
                    f"Order {o.order_ref!r} requires service_allowance for "
                    f"brand={o.brand.value!r}, dock_type={o.dock_type.value!r}, but no record exists."
                ),
                entity_id=o.order_ref,
            ))

    # ── 5. Configuration Validation ───────────────────────────────────────────
    if config is not None:
        if not math.isfinite(config.fresh_daily_budget_min) or config.fresh_daily_budget_min <= 0:
            errors.append(InputErrorDetail(
                field="fresh_daily_budget_min",
                message=f"Invalid fresh_daily_budget_min: {config.fresh_daily_budget_min}.",
            ))
        if not math.isfinite(config.style_tech_daily_budget_min) or config.style_tech_daily_budget_min <= 0:
            errors.append(InputErrorDetail(
                field="style_tech_daily_budget_min",
                message=f"Invalid style_tech_daily_budget_min: {config.style_tech_daily_budget_min}.",
            ))
        if config.max_trips_per_vehicle < 1:
            errors.append(InputErrorDetail(
                field="max_trips_per_vehicle",
                message=f"max_trips_per_vehicle must be >= 1, got {config.max_trips_per_vehicle}.",
            ))
        if not config.valid_trip_numbers:
            errors.append(InputErrorDetail(
                field="valid_trip_numbers",
                message="valid_trip_numbers cannot be empty.",
            ))

    if errors:
        msg = f"Input validation failed with {len(errors)} error(s):\n" + "\n".join(
            f"  - [{e.field}] {e.message}" for e in errors[:10]
        )
        if len(errors) > 10:
            msg += f"\n  ... and {len(errors) - 10} more error(s)."
        raise InputValidationError(msg, errors=errors)


def validate_operational_inputs(
    orders: Sequence[Order],
    fleet: Sequence[Vehicle],
    reference_data: Any,
    context: Any,
    config: Optional[OptimizerConfig] = None,
) -> None:
    """
    Strict operational input validation gateway at the Python API boundary.
    Reconstructs checks from authoritative raw inputs and ensures strict data integrity
    before operational optimization begins.
    """
    errors: list[InputErrorDetail] = []

    # ── 1. Orders Validation ──────────────────────────────────────────────────
    seen_order_refs: set[str] = set()
    outlets = reference_data.outlets if hasattr(reference_data, "outlets") else {}

    for idx, o in enumerate(orders):
        if not o.order_ref or not isinstance(o.order_ref, str):
            errors.append(InputErrorDetail(
                field="order_ref",
                message=f"Order at index {idx} has an empty or non-string order_ref.",
                entity_id=str(o.order_ref),
            ))
        elif o.order_ref in seen_order_refs:
            errors.append(InputErrorDetail(
                field="order_ref",
                message=f"Duplicate order_ref {o.order_ref!r} found.",
                entity_id=o.order_ref,
            ))
        else:
            seen_order_refs.add(o.order_ref)

        if not o.outlet_id or not isinstance(o.outlet_id, str):
            errors.append(InputErrorDetail(
                field="outlet_id",
                message=f"Order {o.order_ref!r} has an empty or non-string outlet_id.",
                entity_id=o.order_ref,
            ))
        elif o.outlet_id not in outlets:
            errors.append(InputErrorDetail(
                field="outlet_id",
                message=f"Order {o.order_ref!r} references unknown outlet_id {o.outlet_id!r}.",
                entity_id=o.order_ref,
            ))
        else:
            # Check relational consistency against authoritative outlet
            u = outlets[o.outlet_id]
            if o.brand != u.brand:
                errors.append(InputErrorDetail(
                    field="brand",
                    message=f"Order {o.order_ref!r} brand '{o.brand.value}' conflicts with authoritative outlet '{u.outlet_id}' brand '{u.brand.value}'.",
                    entity_id=o.order_ref,
                ))
            if o.district != u.district:
                errors.append(InputErrorDetail(
                    field="district",
                    message=f"Order {o.order_ref!r} district '{o.district}' conflicts with authoritative outlet '{u.outlet_id}' district '{u.district}'.",
                    entity_id=o.order_ref,
                ))
            if o.depot != u.depot:
                errors.append(InputErrorDetail(
                    field="depot",
                    message=f"Order {o.order_ref!r} depot '{o.depot}' conflicts with authoritative outlet '{u.outlet_id}' depot '{u.depot}'.",
                    entity_id=o.order_ref,
                ))
            if o.dock_type != u.dock_type:
                errors.append(InputErrorDetail(
                    field="dock_type",
                    message=f"Order {o.order_ref!r} dock_type '{o.dock_type.value}' conflicts with authoritative outlet '{u.outlet_id}' dock_type '{u.dock_type.value}'.",
                    entity_id=o.order_ref,
                ))
            if o.parking_constraint != u.parking_constraint:
                errors.append(InputErrorDetail(
                    field="parking_constraint",
                    message=f"Order {o.order_ref!r} parking_constraint '{o.parking_constraint.value}' conflicts with authoritative outlet '{u.outlet_id}' parking_constraint '{u.parking_constraint.value}'.",
                    entity_id=o.order_ref,
                ))

        if not math.isfinite(o.order_weight_kg) or o.order_weight_kg < 0:
            errors.append(InputErrorDetail(
                field="order_weight_kg",
                message=f"Order {o.order_ref!r} weight ({o.order_weight_kg}) must be finite and non-negative.",
                entity_id=o.order_ref,
            ))
        if not math.isfinite(o.order_volume_m3) or o.order_volume_m3 < 0:
            errors.append(InputErrorDetail(
                field="order_volume_m3",
                message=f"Order {o.order_ref!r} volume ({o.order_volume_m3}) must be finite and non-negative.",
                entity_id=o.order_ref,
            ))
        if not isinstance(o.order_units, int) or o.order_units < 0:
            errors.append(InputErrorDetail(
                field="order_units",
                message=f"Order {o.order_ref!r} order_units ({o.order_units}) must be non-negative integer.",
                entity_id=o.order_ref,
            ))
        if not isinstance(o.days_since_last_served, int) or o.days_since_last_served < 0:
            errors.append(InputErrorDetail(
                field="days_since_last_served",
                message=f"Order {o.order_ref!r} days_since_last_served ({o.days_since_last_served}) must be non-negative integer.",
                entity_id=o.order_ref,
            ))

    # ── 2. Fleet & Live State Validation ──────────────────────────────────────
    seen_vids: set[str] = set()
    for idx, v in enumerate(fleet):
        if not v.vehicle_id or not isinstance(v.vehicle_id, str):
            errors.append(InputErrorDetail(
                field="vehicle_id",
                message=f"Vehicle at index {idx} has empty or non-string vehicle_id.",
                entity_id=str(v.vehicle_id),
            ))
        elif v.vehicle_id in seen_vids:
            errors.append(InputErrorDetail(
                field="vehicle_id",
                message=f"Duplicate vehicle_id {v.vehicle_id!r} found in fleet.",
                entity_id=v.vehicle_id,
            ))
        else:
            seen_vids.add(v.vehicle_id)

        if not v.depot or not isinstance(v.depot, str):
            errors.append(InputErrorDetail(
                field="depot",
                message=f"Vehicle {v.vehicle_id!r} has empty or non-string depot.",
                entity_id=v.vehicle_id,
            ))

        if not math.isfinite(v.weight_cap_kg) or v.weight_cap_kg <= 0:
            errors.append(InputErrorDetail(
                field="weight_cap_kg",
                message=f"Vehicle {v.vehicle_id!r} weight_cap_kg ({v.weight_cap_kg}) must be finite and positive.",
                entity_id=v.vehicle_id,
            ))
        if not math.isfinite(v.volume_cap_m3) or v.volume_cap_m3 <= 0:
            errors.append(InputErrorDetail(
                field="volume_cap_m3",
                message=f"Vehicle {v.vehicle_id!r} volume_cap_m3 ({v.volume_cap_m3}) must be finite and positive.",
                entity_id=v.vehicle_id,
            ))

        # Strict Live Fleet State for Selected Vehicles
        if v.is_selected_for_planning:
            if v.status == VehicleStatus.IN_WORKSHOP:
                errors.append(InputErrorDetail(
                    field="status",
                    message=f"Vehicle {v.vehicle_id!r} is in workshop and cannot be selected for planning.",
                    entity_id=v.vehicle_id,
                ))
            else:
                if v.weekly_fuel_used_l is None:
                    errors.append(InputErrorDetail(
                        field="weekly_fuel_used_l",
                        message=(
                            f"Vehicle {v.vehicle_id!r} is selected for planning but missing required live fleet state "
                            "'weekly_fuel_used_l'. Fuel usage must not be silently defaulted to zero."
                        ),
                        entity_id=v.vehicle_id,
                    ))
                elif not math.isfinite(v.weekly_fuel_used_l) or v.weekly_fuel_used_l < 0:
                    errors.append(InputErrorDetail(
                        field="weekly_fuel_used_l",
                        message=f"Vehicle {v.vehicle_id!r} weekly_fuel_used_l ({v.weekly_fuel_used_l}) must be finite and non-negative.",
                        entity_id=v.vehicle_id,
                    ))

                if v.external_reservations_l is None:
                    errors.append(InputErrorDetail(
                        field="external_reservations_l",
                        message=(
                            f"Vehicle {v.vehicle_id!r} is selected for planning but missing required live fleet state "
                            "'external_reservations_l'. External reservations must not be silently defaulted to zero."
                        ),
                        entity_id=v.vehicle_id,
                    ))
                elif not math.isfinite(v.external_reservations_l) or v.external_reservations_l < 0:
                    errors.append(InputErrorDetail(
                        field="external_reservations_l",
                        message=f"Vehicle {v.vehicle_id!r} external_reservations_l ({v.external_reservations_l}) must be finite and non-negative.",
                        entity_id=v.vehicle_id,
                    ))

                if v.km_per_l is None:
                    errors.append(InputErrorDetail(
                        field="km_per_l",
                        message=f"Vehicle {v.vehicle_id!r} is selected for planning but missing required 'km_per_l'.",
                        entity_id=v.vehicle_id,
                    ))
                elif not math.isfinite(v.km_per_l) or v.km_per_l <= 0:
                    errors.append(InputErrorDetail(
                        field="km_per_l",
                        message=f"Vehicle {v.vehicle_id!r} km_per_l ({v.km_per_l}) must be finite and positive.",
                        entity_id=v.vehicle_id,
                    ))

                if v.weekly_fuel_quota_l is None:
                    errors.append(InputErrorDetail(
                        field="weekly_fuel_quota_l",
                        message=f"Vehicle {v.vehicle_id!r} is selected for planning but missing required 'weekly_fuel_quota_l'.",
                        entity_id=v.vehicle_id,
                    ))
                elif not math.isfinite(v.weekly_fuel_quota_l) or v.weekly_fuel_quota_l <= 0:
                    errors.append(InputErrorDetail(
                        field="weekly_fuel_quota_l",
                        message=f"Vehicle {v.vehicle_id!r} weekly_fuel_quota_l ({v.weekly_fuel_quota_l}) must be finite and positive.",
                        entity_id=v.vehicle_id,
                    ))

                if not isinstance(v.remaining_trips, int) or v.remaining_trips < 0 or v.remaining_trips > 2:
                    errors.append(InputErrorDetail(
                        field="remaining_trips",
                        message=f"Vehicle {v.vehicle_id!r} remaining_trips ({v.remaining_trips}) must be integer in [0, 1, 2].",
                        entity_id=v.vehicle_id,
                    ))

    # ── 3. Reference Coverage ─────────────────────────────────────────────────
    travel_keys = set(reference_data.travel.keys()) if isinstance(reference_data.travel, dict) else {(dt.district, dt.depot) for dt in reference_data.travel}
    allowance_keys = set(reference_data.allowances.keys()) if isinstance(reference_data.allowances, dict) else {(sa.brand, sa.dock_type) for sa in reference_data.allowances}

    for o in orders:
        if (o.district, o.depot) not in travel_keys:
            errors.append(InputErrorDetail(
                field="district_travel",
                entity_id=f"{o.district}::{o.depot}",
                message=f"Order {o.order_ref!r} requires travel for district {o.district!r} and depot {o.depot!r}, but no record exists.",
            ))
        if (o.brand, o.dock_type) not in allowance_keys:
            errors.append(InputErrorDetail(
                field="service_allowances",
                entity_id=f"{o.brand.value}::{o.dock_type.value}",
                message=f"Order {o.order_ref!r} requires service allowance for brand {o.brand.value!r} and dock {o.dock_type.value!r}, but no record exists.",
            ))

    # ── 4. Dynamic Travel Policy Checks ───────────────────────────────────────
    from waypoint_optimizer.operational.models import (
        REFERENCE_DATA_MAX_DATE, REFERENCE_DATA_MIN_DATE, TravelPolicy,
    )
    if hasattr(context, "travel_policy") and context.travel_policy == TravelPolicy.DYNAMIC_CONDITIONS:
        if hasattr(context, "planning_date") and (context.planning_date < REFERENCE_DATA_MIN_DATE or context.planning_date > REFERENCE_DATA_MAX_DATE):
            errors.append(InputErrorDetail(
                field="travel_policy.planning_date",
                entity_id="dynamic_conditions",
                message=(
                    f"Dynamic conditions travel policy cannot be evaluated: planning date {context.planning_date!r} "
                    f"is outside calendar and road condition coverage ({REFERENCE_DATA_MIN_DATE} to {REFERENCE_DATA_MAX_DATE})."
                ),
            ))
        if hasattr(context, "speed_factor_fn") and context.speed_factor_fn is None:
            errors.append(InputErrorDetail(
                field="travel_policy.speed_factor_fn",
                entity_id="dynamic_conditions",
                message=(
                    "Dynamic conditions travel policy was requested, but no dynamic speed provider or speed_factor_fn "
                    "is configured. Never silently execute static travel under a dynamic label."
                ),
            ))

    if errors:
        msg = f"Operational input validation failed with {len(errors)} error(s):\n" + "\n".join(
            f"  - [{e.field}] {e.message}" for e in errors[:10]
        )
        if len(errors) > 10:
            msg += f"\n  ... and {len(errors) - 10} more error(s)."
        raise InputValidationError(msg, errors=errors)
