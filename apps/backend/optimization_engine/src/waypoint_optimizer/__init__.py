"""Waypoint Optimizer — package init."""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("waypoint-optimizer")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.domain import (
    DeferredOrder,
    DistrictTravel,
    OptimizationResult,
    Order,
    OrderAssignment,
    PlanMetrics,
    ServiceAllowance,
    TripResult,
    ValidationError,
    ValidationResult,
    Vehicle,
)
from waypoint_optimizer.engine import benchmark, optimize
from waypoint_optimizer.hackathon_planner import generate_daily_draft_plan
from waypoint_optimizer.enums import (
    Brand,
    DeferralReason,
    DockType,
    EngineMode,
    ParkingConstraint,
    SolverStatus,
    TempRequirement,
    TempSpec,
    VehicleStatus,
    VehicleType,
)
from waypoint_optimizer.input_validation import (
    InputErrorDetail,
    InputValidationError,
    validate_inputs,
)
from waypoint_optimizer.validator import validate

__all__ = [
    "__version__",
    "optimize",
    "benchmark",
    "generate_daily_draft_plan",
    "validate",
    "validate_inputs",
    "InputValidationError",
    "InputErrorDetail",
    "OptimizerConfig",
    "EngineMode",
    "SolverStatus",
    "Order",
    "Vehicle",
    "DistrictTravel",
    "ServiceAllowance",
    "TripResult",
    "OrderAssignment",
    "DeferredOrder",
    "PlanMetrics",
    "ValidationError",
    "ValidationResult",
    "Brand",
    "DockType",
    "ParkingConstraint",
    "TempRequirement",
    "VehicleStatus",
    "VehicleType",
    "DeferralReason",
    "evaluate_edited_draft",
    "EditedDraftResponse",
    "DispatcherEditError",
    "MoveWholeOrderAction",
    "DeferWholeOrderAction",
    "ReinstateWholeOrderAction",
    "MoveLineItemAction",
    "DeferLineItemAction",
    "SplitLineItemAction",
    "BreakdownRecoveryError",
    "RecoveryDraftResponse",
    "UndeliveredQuantity",
    "reallocate_broken_vehicle",
]

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

