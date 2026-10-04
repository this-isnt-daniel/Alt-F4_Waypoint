"""
Waypoint Optimizer — Configuration
====================================
All named constants that encode official competition rules or team-defined
policy defaults live here. Raw numbers are NOT scattered through the codebase.

Sections:
  OFFICIAL_RULES   — from the Task 2B specification. Must never be changed
                     without a corresponding official rule update.
  TEAM_POLICY      — team-defined heuristics and tuning. Clearly labelled.
  ENGINE_DEFAULTS  — runtime defaults for the optimization engine.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# OFFICIAL COMPETITION RULES
# Source: Tech-Triathlon 2026 Waypoint Task 2B specification.
# ──────────────────────────────────────────────────────────────────────────────

# Maximum minutes a vehicle may spend on Fresh trips per day.
FRESH_DAILY_BUDGET_MIN: int = 270

# Maximum minutes a vehicle may spend on Style + Tech trips per day (combined).
STYLE_TECH_DAILY_BUDGET_MIN: int = 480

# Maximum number of trips a single vehicle may perform in a day.
MAX_TRIPS_PER_VEHICLE: int = 2

# Valid trip numbers.
VALID_TRIP_NUMBERS: frozenset[int] = frozenset({1, 2})

# Official scenario identifier for Task 2B.
OFFICIAL_SCENARIO: str = "S1"

# Official depot for Task 2B.
OFFICIAL_DEPOT: str = "Peliyagoda"


# ──────────────────────────────────────────────────────────────────────────────
# TEAM-DEFINED POLICY DEFAULTS
# These are heuristics chosen by the team. They are NOT official formulas.
# They are configurable and replaceable.
# ──────────────────────────────────────────────────────────────────────────────

# TEAM-DEFINED: Base deferral penalty for any order.
DEFER_PENALTY_BASE: int = 100

# TEAM-DEFINED: Extra penalty when the order was deferred in previous planning cycle.
DEFER_PENALTY_DEFERRED_PREV: int = 2500

# TEAM-DEFINED: Per-deferral penalty for repeat deferrals (capped at DEFER_COUNT_CAP).
DEFER_PENALTY_PER_DEFERRAL: int = 100
DEFER_COUNT_CAP: int = 30

# TEAM-DEFINED: Priority bonus for Dispatcher-approved urgency requests.
URGENCY_PRIORITY_BONUS: int = 1000

# TEAM-DEFINED: Per unit of order volume (m³ × 10, ceiling).
DEFER_PENALTY_VOLUME_FACTOR: float = 10.0

# Deprecated aliases for backwards compatibility
DEFER_PENALTY_DEFERRED_YESTERDAY: int = DEFER_PENALTY_DEFERRED_PREV
DEFER_PENALTY_PER_DAY: int = DEFER_PENALTY_PER_DEFERRAL
DEFER_PENALTY_DAYS_CAP: int = DEFER_COUNT_CAP


# ──────────────────────────────────────────────────────────────────────────────
# ENGINE RUNTIME DEFAULTS
# ──────────────────────────────────────────────────────────────────────────────

# Default random seed for reproducibility.
DEFAULT_RANDOM_SEED: int = 42

# Default time limit for Targeted CP-SAT improvement (seconds).
TARGETED_CPSAT_TIME_LIMIT_S: float = 2.0

# Default time limit for Full CP-SAT Cold benchmark (seconds).
FULL_CPSAT_TIME_LIMIT_S: float = 10.0

# Default number of CP-SAT workers (1 = deterministic single-threaded).
CPSAT_NUM_WORKERS: int = 1


@dataclass(frozen=True)
class OptimizerConfig:
    """
    Runtime configuration for the optimization engine.

    All fields have defaults matching the engine runtime defaults above.
    Downstream callers (e.g., a Dispatcher backend) may override any field.
    """
    # ── Official rule references ──────────────────────────────────────────
    fresh_daily_budget_min: int = FRESH_DAILY_BUDGET_MIN
    style_tech_daily_budget_min: int = STYLE_TECH_DAILY_BUDGET_MIN
    max_trips_per_vehicle: int = MAX_TRIPS_PER_VEHICLE
    valid_trip_numbers: frozenset[int] = VALID_TRIP_NUMBERS

    # ── TEAM-DEFINED: Penalty weights ────────────────────────────────────
    # NOTE: These are team heuristics. Changing them does not violate any
    # official rule; it shifts which orders are prioritized.
    defer_penalty_base: int = DEFER_PENALTY_BASE
    defer_penalty_deferred_prev: int = DEFER_PENALTY_DEFERRED_PREV
    defer_penalty_per_deferral: int = DEFER_PENALTY_PER_DEFERRAL
    defer_count_cap: int = DEFER_COUNT_CAP
    urgency_priority_bonus: int = URGENCY_PRIORITY_BONUS
    defer_penalty_volume_factor: float = DEFER_PENALTY_VOLUME_FACTOR

    # Deprecated compatibility accessors
    @property
    def defer_penalty_deferred_yesterday(self) -> int:
        return self.defer_penalty_deferred_prev

    @property
    def defer_penalty_per_day(self) -> int:
        return self.defer_penalty_per_deferral

    @property
    def defer_penalty_days_cap(self) -> int:
        return self.defer_count_cap

    # ── Solver settings ───────────────────────────────────────────────────
    random_seed: int = DEFAULT_RANDOM_SEED
    targeted_cpsat_time_limit_s: float = TARGETED_CPSAT_TIME_LIMIT_S
    full_cpsat_time_limit_s: float = FULL_CPSAT_TIME_LIMIT_S
    cpsat_num_workers: int = CPSAT_NUM_WORKERS

    # ── Engine switches ───────────────────────────────────────────────────
    enable_targeted_cpsat: bool = True
    enable_full_cpsat_benchmark: bool = False

    # ── Greedy portfolio: how many random restarts to add ─────────────────
    greedy_random_restarts: int = 5
