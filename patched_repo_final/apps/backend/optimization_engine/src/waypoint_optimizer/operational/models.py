"""
Waypoint Optimizer — Operational Data Models (Hackathon H1)
===========================================================
Defines typed models for operational scheduling, delivery window evaluation,
stop consolidation, fuel quota tracking, and multi-trip vehicle timelines.

Guarantees:
  - All timestamps use timezone-aware ISO-8601 formatting.
  - Distinguishes physical stop visits from order counts.
  - Independent from Task 2B exact benchmark logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from waypoint_optimizer.domain import Brand, DockType, LineItem, Order, ParkingConstraint, Vehicle


# ──────────────────────────────────────────────────────────────────────────────
# Operational Enums & Policy Named Constants
# ──────────────────────────────────────────────────────────────────────────────

class TravelPolicy(str, Enum):
    """Supported travel time and distance evaluation policies."""
    STATIC_FREEFLOW = "static_freeflow"
    DYNAMIC_CONDITIONS = "dynamic_conditions"


class WindowPolicy(str, Enum):
    """
    Supported delivery window compliance rules.

    - ARRIVAL_BEFORE_CLOSE (default): Planned arrival <= window close.
      Note: Unloading service may finish after window close if arrival occurred before closing.
    - SERVICE_START_BEFORE_CLOSE: Service start <= window close.
    - SERVICE_END_BEFORE_CLOSE: Service completion <= window close.
    """
    ARRIVAL_BEFORE_CLOSE = "arrival_before_close"
    SERVICE_START_BEFORE_CLOSE = "service_start_before_close"
    SERVICE_END_BEFORE_CLOSE = "service_end_before_close"


class TurnaroundPolicy(str, Enum):
    """Turnaround estimation policies between consecutive trips at depot."""
    EXPLICIT = "explicit"
    DEFAULT_ESTIMATED = "default_estimated"


# Documented named policy constants (No unexplained magic numbers)
ESTIMATED_DEPOT_TURNAROUND_MIN: float = 30.0
DEFAULT_TIMEZONE: str = "Asia/Colombo"
REFERENCE_DATA_MIN_DATE: str = "2024-01-01"
REFERENCE_DATA_MAX_DATE: str = "2026-06-28"
DEFAULT_FRESH_DEPARTURE_TIME: str = "04:00:00"
DEFAULT_STYLE_TECH_DEPARTURE_TIME: str = "06:30:00"
FRESH_DEADLINE_TIME: str = "08:00:00"


# ──────────────────────────────────────────────────────────────────────────────
# Operational Diagnostics & Violations
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OperationalViolation:
    """A structured hard or operational constraint violation."""
    rule: str
    detail: str
    order_ref: Optional[str] = None
    outlet_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    trip_number: Optional[int] = None


@dataclass(frozen=True)
class OperationalMissingData:
    """Identifies missing authoritative reference or operational input data."""
    field: str
    entity_id: str
    detail: str


# ──────────────────────────────────────────────────────────────────────────────
# Operational Context & Scheduling Entities
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OperationalContext:
    """
    Operational execution parameters passed from the backend.

    Attributes:
        planning_date: Target delivery date in 'YYYY-MM-DD' format.
        timezone: Authoritative timezone (default: 'Asia/Colombo').
        depot_turnaround_duration_min: Duration for unloading/reloading at depot.
            Must be explicitly provided or set to ESTIMATED_DEPOT_TURNAROUND_MIN.
        travel_policy: STATIC_FREEFLOW or DYNAMIC_CONDITIONS.
        window_policy: Window compliance rule to enforce.
        speed_factor_fn: Pluggable function returning speed factor >= 0.0.
            Marked UNRESOLVED in booklet; caller may supply domain-specific model.
    """
    planning_date: str
    timezone: str = DEFAULT_TIMEZONE
    depot_turnaround_duration_min: float = ESTIMATED_DEPOT_TURNAROUND_MIN
    travel_policy: TravelPolicy = TravelPolicy.STATIC_FREEFLOW
    window_policy: WindowPolicy = WindowPolicy.ARRIVAL_BEFORE_CLOSE
    speed_factor_fn: Optional[Callable[[str, int, int, str], float]] = None


@dataclass(frozen=True)
class OperationalStop:
    """
    A single physical stop visit at an outlet, potentially serving multiple orders.
    """
    stop_number: int
    outlet_id: str
    order_refs: list[str]
    dock_type: DockType
    parking_constraint: ParkingConstraint
    window_open_iso: Optional[str]
    window_close_iso: Optional[str]
    arrival_time_iso: str
    waiting_duration_min: float
    service_start_time_iso: str
    service_duration_min: float
    departure_time_iso: str
    window_compliant: bool
    lateness_margin_min: float
    violation_detail: Optional[str] = None
    line_items_delivered: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class EvaluatedTripSchedule:
    """
    Complete pure schedule and feasibility evaluation for a single vehicle trip.
    """
    trip_id: str
    vehicle_id: str
    trip_number: int
    brand: Brand
    district: str
    depot: str
    departure_time_iso: str
    stops: list[OperationalStop]
    depot_return_arrival_iso: str
    vehicle_next_available_iso: str
    outbound_distance_km: float
    inter_stop_distance_km: float
    return_distance_km: float
    total_distance_km: float
    total_duration_min: float
    fuel_consumed_l: float
    cumulative_fuel_used_l: float
    weekly_quota_l: Optional[float]
    fuel_compliant: bool
    windows_compliant: bool
    capacity_compliant: bool
    total_weight_kg: float
    weight_cap_kg: float
    total_volume_m3: float
    volume_cap_m3: float
    violations: list[OperationalViolation] = field(default_factory=list)
    missing_data: list[OperationalMissingData] = field(default_factory=list)
    travel_model_notice: str = (
        "Estimated travel based on static district averages from district_travel.csv; "
        "does not represent turn-by-turn GIS route optimization."
    )

    @property
    def is_feasible(self) -> bool:
        return (
            len(self.violations) == 0
            and len(self.missing_data) == 0
            and self.windows_compliant
            and self.capacity_compliant
            and self.fuel_compliant
        )

    @property
    def assigned_order_refs(self) -> list[str]:
        refs = []
        for s in self.stops:
            for r in s.order_refs:
                if r not in refs:
                    refs.append(r)
        return refs


@dataclass(frozen=True)
class VehicleScheduleTimeline:
    """
    Multi-trip chronological timeline and cumulative fuel tracking for a vehicle.
    """
    vehicle_id: str
    trips: list[EvaluatedTripSchedule]
    chronology_valid: bool
    weekly_fuel_valid: bool
    cumulative_fuel_l: float
    weekly_fuel_quota_l: Optional[float]
    violations: list[OperationalViolation] = field(default_factory=list)
    missing_data: list[OperationalMissingData] = field(default_factory=list)

    @property
    def is_feasible(self) -> bool:
        return (
            self.chronology_valid
            and self.weekly_fuel_valid
            and len(self.violations) == 0
            and len(self.missing_data) == 0
            and all(t.is_feasible for t in self.trips)
        )
