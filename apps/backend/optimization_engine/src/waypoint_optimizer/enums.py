"""
Waypoint Optimizer — Enumerations
==================================
All domain enumerations live here. Using str-based enums so values
serialize/deserialize cleanly from CSV/JSON without a custom encoder.
"""
from enum import Enum


class Brand(str, Enum):
    FRESH = "fresh"
    STYLE = "style"
    TECH = "tech"


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    IN_WORKSHOP = "in_workshop"


class VehicleType(str, Enum):
    TRUCK = "truck"
    VAN = "van"


class TempSpec(str, Enum):
    AMBIENT = "ambient"
    REEFER = "reefer"


class DockType(str, Enum):
    REAR_DOCK = "rear_dock"
    STREET = "street"
    MALL_BAY = "mall_bay"


class ParkingConstraint(str, Enum):
    NORMAL = "normal"
    VAN_ONLY = "van_only"
    MALL_DOCK = "mall_dock"


class TempRequirement(str, Enum):
    AMBIENT = "ambient"
    CHILLED = "chilled"


class EngineMode(str, Enum):
    """
    TASK2B_EXACT     — implements the official Datathon Task 2B formulation
                       exactly with no extra operational policies.
    HACKATHON_OPERATIONAL — same hard constraints + extra operational checks
                       (delivery windows, fuel quotas, route distance, ETA).
    """
    TASK2B_EXACT = "task2b_exact"
    HACKATHON_OPERATIONAL = "hackathon_operational"


class SolverStatus(str, Enum):
    """Maps to OR-Tools CP-SAT status strings or validator outcome."""
    UNKNOWN = "UNKNOWN"
    FEASIBLE = "FEASIBLE"
    OPTIMAL = "OPTIMAL"
    INFEASIBLE = "INFEASIBLE"
    INVALID = "INVALID"
    ERROR = "ERROR"


class DeferralReason(str, Enum):
    """
    Structured reason codes for why an order was deferred.

    IMPORTANT: A reason code describes why the order could not be placed
    in THIS plan. It does NOT claim the deferral was mathematically
    unavoidable unless the engine can explicitly prove it.
    """
    NO_COMPATIBLE_VEHICLE = "NO_COMPATIBLE_VEHICLE"
    REEFER_CAPACITY_EXHAUSTED = "REEFER_CAPACITY_EXHAUSTED"
    VAN_CAPACITY_EXHAUSTED = "VAN_CAPACITY_EXHAUSTED"
    WEIGHT_CAPACITY = "WEIGHT_CAPACITY"
    VOLUME_CAPACITY = "VOLUME_CAPACITY"
    TRIP_LIMIT = "TRIP_LIMIT"
    FRESH_TIME_BUDGET = "FRESH_TIME_BUDGET"
    STYLE_TECH_TIME_BUDGET = "STYLE_TECH_TIME_BUDGET"
    LOWER_PRIORITY_THAN_SELECTED_ORDERS = "LOWER_PRIORITY_THAN_SELECTED_ORDERS"
    NOT_SELECTED_BY_HEURISTIC = "NOT_SELECTED_BY_HEURISTIC"
    OTHER_CAPACITY_LIMIT = "OTHER_CAPACITY_LIMIT"

