"""
Waypoint Optimizer — Operational Package (Hackathon H1)
=======================================================
Pure operational scheduling, delivery windows, fuel quotas, vehicle timelines,
and independent constraint validation for the Waypoint Web Application.
"""

from waypoint_optimizer.operational.models import (
    DEFAULT_FRESH_DEPARTURE_TIME,
    DEFAULT_STYLE_TECH_DEPARTURE_TIME,
    DEFAULT_TIMEZONE,
    ESTIMATED_DEPOT_TURNAROUND_MIN,
    FRESH_DEADLINE_TIME,
    REFERENCE_DATA_MAX_DATE,
    REFERENCE_DATA_MIN_DATE,
    EvaluatedTripSchedule,
    OperationalContext,
    OperationalMissingData,
    OperationalStop,
    OperationalViolation,
    TravelPolicy,
    TurnaroundPolicy,
    VehicleScheduleTimeline,
    WindowPolicy,
)
from waypoint_optimizer.operational.schedule_evaluator import (
    consolidate_orders_to_stops,
    evaluate_trip_schedule,
    parse_iso_or_time_str,
)
from waypoint_optimizer.operational.timeline import evaluate_vehicle_timeline
from waypoint_optimizer.operational.validator import (
    OperationalValidationResult,
    validate_operational_plan,
)
from waypoint_optimizer.operational.draft_editor import (
    DispatcherEditError,
    EditedDraftResponse,
    MoveWholeOrderAction,
    DeferWholeOrderAction,
    ReinstateWholeOrderAction,
    MoveLineItemAction,
    DeferLineItemAction,
    SplitLineItemAction,
    evaluate_edited_draft,
)
from waypoint_optimizer.operational.breakdown_recovery import (
    BreakdownRecoveryError,
    RecoveryDraftResponse,
    UndeliveredQuantity,
    reallocate_broken_vehicle,
)

__all__ = [
    "TravelPolicy",
    "WindowPolicy",
    "TurnaroundPolicy",
    "ESTIMATED_DEPOT_TURNAROUND_MIN",
    "DEFAULT_TIMEZONE",
    "REFERENCE_DATA_MIN_DATE",
    "REFERENCE_DATA_MAX_DATE",
    "DEFAULT_FRESH_DEPARTURE_TIME",
    "DEFAULT_STYLE_TECH_DEPARTURE_TIME",
    "FRESH_DEADLINE_TIME",
    "OperationalViolation",
    "OperationalMissingData",
    "OperationalContext",
    "OperationalStop",
    "EvaluatedTripSchedule",
    "VehicleScheduleTimeline",
    "parse_iso_or_time_str",
    "consolidate_orders_to_stops",
    "evaluate_trip_schedule",
    "evaluate_vehicle_timeline",
    "OperationalValidationResult",
    "validate_operational_plan",
    "DispatcherEditError",
    "EditedDraftResponse",
    "MoveWholeOrderAction",
    "DeferWholeOrderAction",
    "ReinstateWholeOrderAction",
    "MoveLineItemAction",
    "DeferLineItemAction",
    "SplitLineItemAction",
    "evaluate_edited_draft",
    "BreakdownRecoveryError",
    "RecoveryDraftResponse",
    "UndeliveredQuantity",
    "reallocate_broken_vehicle",
]
