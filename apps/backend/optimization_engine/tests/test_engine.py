"""
Tests for the Greedy allocator and end-to-end engine integration.
Covers:
  - Determinism: same input → same output
  - Workshop vehicles are never allocated
  - All orders accounted for (served or deferred)
  - All results pass Validator
  - Hybrid never returns a worse accepted solution than its base plan
"""
import pytest
from waypoint_optimizer.mock_data import generate_scenario
from waypoint_optimizer.engine import optimize
from waypoint_optimizer.greedy import greedy_allocate
from waypoint_optimizer.portfolio import run_portfolio, _sort_priority_first
from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.enums import VehicleStatus, EngineMode


@pytest.fixture
def small_scenario():
    return generate_scenario(n_orders=30, n_vehicles=8, seed=42)


@pytest.fixture
def medium_scenario():
    return generate_scenario(n_orders=100, n_vehicles=20, seed=99)


class TestGreedyDeterminism:
    def test_same_input_same_output(self, small_scenario):
        """Same seed + same inputs must produce identical results."""
        orders, vehicles, travel, allowances = small_scenario
        cfg = OptimizerConfig(enable_targeted_cpsat=False)

        result1 = greedy_allocate(orders, vehicles, travel, allowances, cfg=cfg)
        result2 = greedy_allocate(orders, vehicles, travel, allowances, cfg=cfg)

        assert result1.objective_value == result2.objective_value
        assert result1.metrics.served_count == result2.metrics.served_count
        # Same assignments (sets, since list order may differ)
        refs1 = {(a.order_ref, a.vehicle_id, a.trip_number) for a in result1.served_assignments}
        refs2 = {(a.order_ref, a.vehicle_id, a.trip_number) for a in result2.served_assignments}
        assert refs1 == refs2

    def test_portfolio_determinism(self, small_scenario):
        """Multi-start portfolio must be deterministic with same seed."""
        orders, vehicles, travel, allowances = small_scenario
        cfg = OptimizerConfig(enable_targeted_cpsat=False, random_seed=42)

        best1, _ = run_portfolio(orders, vehicles, travel, allowances, cfg=cfg)
        best2, _ = run_portfolio(orders, vehicles, travel, allowances, cfg=cfg)

        assert best1 is not None and best2 is not None
        assert best1.objective_value == best2.objective_value


class TestGreedyCorrectness:
    def test_all_orders_accounted_for(self, small_scenario):
        """Every input order must appear exactly once (served or deferred)."""
        orders, vehicles, travel, allowances = small_scenario
        result = greedy_allocate(orders, vehicles, travel, allowances)

        input_refs = {o.order_ref for o in orders}
        served_refs = {a.order_ref for a in result.served_assignments}
        deferred_refs = {d.order_ref for d in result.deferred_orders}

        assert served_refs | deferred_refs == input_refs
        assert served_refs & deferred_refs == set()

    def test_workshop_vehicles_never_allocated(self, small_scenario):
        """Vehicles in workshop must never appear in the result."""
        orders, vehicles, travel, allowances = small_scenario
        workshop_ids = {v.vehicle_id for v in vehicles if v.status == VehicleStatus.IN_WORKSHOP}

        result = greedy_allocate(orders, vehicles, travel, allowances)

        allocated_ids = {a.vehicle_id for a in result.served_assignments}
        assert not (workshop_ids & allocated_ids), (
            f"Workshop vehicles allocated: {workshop_ids & allocated_ids}"
        )

    def test_all_greedy_results_pass_validator(self, small_scenario):
        """Every Greedy result must pass independent validation."""
        orders, vehicles, travel, allowances = small_scenario
        result = greedy_allocate(orders, vehicles, travel, allowances)
        assert result.validation.valid, (
            f"Greedy result failed validation: "
            f"{[e.detail for e in result.validation.errors[:3]]}"
        )

    def test_portfolio_best_passes_validator(self, small_scenario):
        """Portfolio best result must pass independent validation."""
        orders, vehicles, travel, allowances = small_scenario
        best, _ = run_portfolio(orders, vehicles, travel, allowances)
        if best is not None:
            assert best.validation.valid, (
                f"Portfolio best failed validation: "
                f"{[e.detail for e in best.validation.errors[:3]]}"
            )


class TestHybridEngineQuality:
    def test_hybrid_never_worse_than_base(self, small_scenario):
        """
        Hybrid (portfolio + targeted CP-SAT) must never return a plan
        with a higher penalty than the best Greedy base plan.
        """
        orders, vehicles, travel, allowances = small_scenario
        cfg = OptimizerConfig(
            enable_targeted_cpsat=True,
            targeted_cpsat_time_limit_s=1.0,
        )

        best_greedy, _ = run_portfolio(orders, vehicles, travel, allowances, cfg=cfg)
        hybrid = optimize(orders, vehicles, travel, allowances, config=cfg)

        if best_greedy is not None and hybrid is not None:
            if hybrid.validation.valid:
                assert hybrid.objective_value <= best_greedy.objective_value, (
                    f"Hybrid ({hybrid.objective_value}) is worse than "
                    f"base greedy ({best_greedy.objective_value})"
                )

    def test_optimize_result_passes_validator(self, small_scenario):
        """The main optimize() function result must always pass validation."""
        orders, vehicles, travel, allowances = small_scenario
        cfg = OptimizerConfig(enable_targeted_cpsat=False)
        result = optimize(orders, vehicles, travel, allowances, config=cfg)
        assert result.validation.valid, (
            f"optimize() result failed validation: "
            f"{[e.detail for e in result.validation.errors[:3]]}"
        )

    def test_optimize_with_cpsat_passes_validator(self, medium_scenario):
        """optimize() with CP-SAT enabled must still pass validation."""
        orders, vehicles, travel, allowances = medium_scenario
        cfg = OptimizerConfig(
            enable_targeted_cpsat=True,
            targeted_cpsat_time_limit_s=2.0,
        )
        result = optimize(orders, vehicles, travel, allowances, config=cfg)
        assert result.validation.valid, (
            f"optimize() with CP-SAT failed validation: "
            f"{[e.detail for e in result.validation.errors[:3]]}"
        )


class TestEngineContract:
    def test_no_split_orders(self, small_scenario):
        """No order should be split across multiple vehicles or trips."""
        orders, vehicles, travel, allowances = small_scenario
        result = greedy_allocate(orders, vehicles, travel, allowances)

        seen = {}
        for a in result.served_assignments:
            if a.order_ref in seen:
                prev = seen[a.order_ref]
                assert False, (
                    f"Order {a.order_ref} split: "
                    f"appears in ({prev}) and ({a.vehicle_id}, {a.trip_number})"
                )
            seen[a.order_ref] = (a.vehicle_id, a.trip_number)

    def test_trip_numbers_valid(self, small_scenario):
        """All trip numbers in the result must be 1 or 2."""
        from waypoint_optimizer.config import VALID_TRIP_NUMBERS
        orders, vehicles, travel, allowances = small_scenario
        result = greedy_allocate(orders, vehicles, travel, allowances)
        for a in result.served_assignments:
            assert a.trip_number in VALID_TRIP_NUMBERS, (
                f"Invalid trip number {a.trip_number} for order {a.order_ref}"
            )
