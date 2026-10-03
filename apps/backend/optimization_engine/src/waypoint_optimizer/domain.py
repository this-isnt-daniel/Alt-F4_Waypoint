"""
Waypoint Optimizer — Domain Models
=====================================
All core business entities are defined here as frozen dataclasses.

Design decisions:
- Frozen dataclasses (immutable): easier to reason about, safe to use as
  dict keys, no accidental mutation inside the optimizer.
- No ORM imports, no HTTP objects, no FastAPI types.
- The optimizer accepts these objects; the backend is responsible for
  converting its persistence layer objects into these domain types.

Entity overview:
  Order            — a confirmed delivery request
  Vehicle          — a delivery vehicle with capacity and status
  DistrictTravel   — travel time/distance data from depot to a district
  ServiceAllowance — handling time per (brand, dock_type) combination
  Trip             — an in-progress or proposed trip being built
  TripResult       — immutable trip in the final output plan
  OrderAssignment  — maps an order_ref to vehicle + trip in the final plan
  DeferredOrder    — an order that could not be placed, with reason
  OptimizationResult — complete output of the optimization engine
  ValidationError  — a single constraint violation found by the Validator
  ValidationResult — aggregated validator output
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from waypoint_optimizer.enums import (
    Brand, DeferralReason, DockType, EngineMode, ParkingConstraint,
    SolverStatus, TempRequirement, TempSpec, VehicleStatus, VehicleType,
)


# ══════════════════════════════════════════════════════════════════════════════
# INPUT MODELS
# ══════════════════════════════════════════════════════════════════════════════

from enum import Enum


@dataclass(frozen=True)
class LineItem:
    """
    A discrete line-item demand within an order (Hackathon operational mode).

    Preserves original order and line-item identities across split allocations.
    """
    line_item_id: str
    quantity: float
    quantity_unit: str
    unit_weight_kg: float
    unit_volume_m3: float
    description: Optional[str] = None


@dataclass(frozen=True)
class Outlet:
    """
    An authoritative store outlet location.

    Authoritative source for outlet-owned attributes:
    brand, district, depot, dock_type, parking_constraint, delivery windows.
    """
    outlet_id: str
    brand: Brand
    district: str
    depot: str
    dock_type: DockType
    parking_constraint: ParkingConstraint
    mall_window: Optional[str] = None
    window_open_time: Optional[str] = None
    window_close_time: Optional[str] = None


@dataclass(frozen=True)
class Order:
    """
    A confirmed delivery order from a store manager.

    The allocation key is ``order_ref`` — NOT ``outlet_id``.
    One outlet may have multiple orders.
    """
    order_ref: str
    outlet_id: str

    brand: Brand
    district: str
    depot: str

    dock_type: DockType
    parking_constraint: ParkingConstraint

    # Optional mall time window
    mall_window: Optional[str]           # e.g. "07:00-09:00"
    window_open_time: Optional[str]      # e.g. "07:00"
    window_close_time: Optional[str]     # e.g. "09:00"

    temp_requirement: TempRequirement

    order_units: int
    order_weight_kg: float
    order_volume_m3: float

    # Repeat-deferral signals (used by TEAM-DEFINED priority policy)
    deferred_yesterday: bool
    days_since_last_served: int

    # Line-item breakdown (Hackathon operational mode)
    line_items: list[LineItem] = field(default_factory=list)

    @property
    def requires_refrigeration(self) -> bool:
        return self.temp_requirement == TempRequirement.CHILLED


@dataclass(frozen=True)
class Vehicle:
    """
    A vehicle in the fleet with its capacity profile and operational status.

    Rules:
    - ``status == in_workshop`` → must NEVER be allocated (hard constraint).
    - ``temp == reefer``        → may carry both chilled and ambient orders.
    - ``temp == ambient``       → must NEVER carry chilled orders.
    - ``type == van``           → required for van_only parking constraints.
    """
    vehicle_id: str
    status: VehicleStatus
    type: VehicleType
    temp: TempSpec
    weight_cap_kg: float
    volume_cap_m3: float
    depot: str

    # Optional fuel profile (used in Hackathon operational mode only)
    fuel_type: Optional[str] = None
    km_per_l: Optional[float] = None
    weekly_fuel_quota_l: Optional[float] = None
    weekly_fuel_used_l: Optional[float] = None

    # Operational fleet state (Hackathon operational mode)
    is_selected_for_planning: bool = True
    remaining_trips: int = 2
    earliest_availability_iso: Optional[str] = None
    # Committed fuel outside the current draft plan (including other delivery plans,
    # regional runs, maintenance transfers, or inter-depot movements)
    external_reservations_l: Optional[float] = None
    exclusion_reason: Optional[str] = None

    @property
    def earliest_available_time(self) -> Optional[str]:
        return self.earliest_availability_iso

    @property
    def is_available(self) -> bool:
        return self.status == VehicleStatus.AVAILABLE

    @property
    def is_refrigerated(self) -> bool:
        return self.temp == TempSpec.REEFER

    @property
    def weight_capacity_kg(self) -> float:
        return self.weight_cap_kg

    @property
    def volume_capacity_m3(self) -> float:
        return self.volume_cap_m3


class OrderAllocationStatus(str, Enum):
    """Allocation status of an order evaluated per line item."""
    FULLY_SERVED = "fully_served"
    PARTIALLY_SERVED = "partially_served"
    FULLY_DEFERRED = "fully_deferred"


def classify_order_allocation(
    order: Order,
    assigned_quantities_by_item: dict[str, float],
) -> OrderAllocationStatus:
    """
    Classify order allocation status without summing across incompatible quantity units.

    - Fully Served: Every line item's requested quantity is 100% assigned.
    - Partially Served: At least one line item has partial assignment, or some items
      are assigned while others are unassigned.
    - Fully Deferred: Zero quantity assigned across all line items.

    For aggregated orders without line-item breakdown, evaluates against order_units.
    """
    if not order.line_items:
        # Aggregated order fallback: check order_ref, '{order_ref}-ALL', or sum of values
        assigned = (
            assigned_quantities_by_item.get(order.order_ref)
            or assigned_quantities_by_item.get(f"{order.order_ref}-ALL")
            or sum(assigned_quantities_by_item.values())
        )
        if assigned >= order.order_units and order.order_units > 0:
            return OrderAllocationStatus.FULLY_SERVED
        elif assigned > 0.0:
            return OrderAllocationStatus.PARTIALLY_SERVED
        else:
            return OrderAllocationStatus.FULLY_DEFERRED

    all_fully_served = True
    all_zero = True

    for item in order.line_items:
        assigned = assigned_quantities_by_item.get(item.line_item_id, 0.0)
        if assigned > 0.0:
            all_zero = False
        if abs(assigned - item.quantity) > 1e-6:
            all_fully_served = False

    if all_zero:
        return OrderAllocationStatus.FULLY_DEFERRED
    if all_fully_served:
        return OrderAllocationStatus.FULLY_SERVED
    return OrderAllocationStatus.PARTIALLY_SERVED


@dataclass(frozen=True)
class DistrictTravel:
    """
    Travel data from a depot to a district.

    IMPORTANT: The official Task 2B trip-time formula uses the MINUTE fields
    (``depot_to_district_freeflow_min``, ``inter_stop_freeflow_min``).
    The kilometre fields are available for future fuel/ETA calculations but
    are NOT used in the Task 2B exact trip-time formula.
    """
    district: str
    depot: str
    road_class: str

    free_flow_kmh: float

    depot_to_district_km: float
    depot_to_district_freeflow_min: float

    inter_stop_km: float
    inter_stop_freeflow_min: float


@dataclass(frozen=True)
class ServiceAllowance:
    """
    Handling time at a stop, keyed by (brand, dock_type).

    Example: (fresh, rear_dock) → 15 minutes.
    Used in Step 3 of the official Task 2B trip-time formula.
    """
    brand: Brand
    dock_type: DockType
    service_allowance_min: float


# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL MUTABLE TRIP REPRESENTATION (used by the optimizer during building)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Trip:
    """
    A mutable trip being assembled by the optimizer.

    Hard invariant: all orders in a trip share the same brand AND district.
    This is enforced by the compatibility module, never assumed.

    ``trip_number`` must be 1 or 2 (official rule: max 2 trips per vehicle).
    """
    vehicle_id: str
    trip_number: int   # 1 or 2
    brand: Brand
    district: str
    orders: list[Order] = field(default_factory=list)

    @property
    def total_weight_kg(self) -> float:
        return sum(o.order_weight_kg for o in self.orders)

    @property
    def total_volume_m3(self) -> float:
        return sum(o.order_volume_m3 for o in self.orders)

    @property
    def order_count(self) -> int:
        return len(self.orders)


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT MODELS (immutable, returned to the caller)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class TripResult:
    """
    An immutable description of a completed trip in the final plan.

    ``stop_sequence`` is deterministic but NOT claimed to be route-optimal.
    It is a stable ordering (by order_ref) that the backend can use as a
    placeholder until a routing engine provides an optimal sequence.
    """
    vehicle_id: str
    trip_number: int
    brand: Brand
    district: str

    order_refs: tuple[str, ...]    # deterministic, stable ordering
    stop_sequence: tuple[str, ...] # same refs in a stop-visit order

    total_weight_kg: float
    total_volume_m3: float
    trip_minutes: float

    # Remaining capacity (convenience for diagnostics)
    remaining_weight_kg: float
    remaining_volume_m3: float


@dataclass(frozen=True)
class OrderAssignment:
    """Maps a served order_ref to its vehicle and trip."""
    order_ref: str
    vehicle_id: str
    trip_number: int


@dataclass(frozen=True)
class DeferredOrder:
    """
    A record of an order that could not be placed in the current plan.

    IMPORTANT: ``reason`` describes why the order was not placed in THIS plan.
    It does NOT prove the deferral was globally unavoidable unless the solver
    explicitly establishes that.
    """
    order_ref: str
    reason: DeferralReason
    detail: str   # human-readable elaboration


@dataclass(frozen=True)
class PlanMetrics:
    """Aggregate statistics for a complete allocation plan."""
    total_orders: int
    served_count: int
    deferred_count: int
    total_deferral_penalty: float
    reefer_vehicles_used: int
    van_vehicles_used: int
    vehicles_used: int
    trips_created: int
    # Time budget usage (informational)
    fresh_time_used_by_vehicle: dict[str, float]
    style_tech_time_used_by_vehicle: dict[str, float]


@dataclass(frozen=True)
class ValidationError:
    """A single constraint violation detected by the independent Validator."""
    rule: str
    detail: str
    order_ref: Optional[str] = None
    vehicle_id: Optional[str] = None


@dataclass(frozen=True)
class ValidationResult:
    """
    Output of the independent Validator.

    IMPORTANT: ``valid == True`` means the plan is FEASIBLE — it satisfies
    all hard constraints. It does NOT imply GLOBAL OPTIMALITY.
    """
    valid: bool
    errors: list[ValidationError]
    # Summary metrics recomputed independently by the Validator
    served_count: int
    deferred_count: int
    total_deferral_penalty: float


@dataclass(frozen=True)
class OptimizationResult:
    """
    Complete output of the optimization engine.

    The engine never writes to a database. The backend is responsible for
    persisting trip rows, order.trip_id, stop_sequence, and DeferralRecords.
    """
    status: SolverStatus
    engine_name: str
    engine_mode: EngineMode

    trips: list[TripResult]
    served_assignments: list[OrderAssignment]
    deferred_orders: list[DeferredOrder]

    metrics: PlanMetrics
    validation: ValidationResult

    runtime_seconds: float
    objective_value: float  # total deferral penalty (lower = better)

    # CP-SAT specific (None for pure Greedy runs)
    cpsat_improvements_accepted: Optional[int] = None
    cpsat_solver_status: Optional[SolverStatus] = None
    diagnostic_message: Optional[str] = None
