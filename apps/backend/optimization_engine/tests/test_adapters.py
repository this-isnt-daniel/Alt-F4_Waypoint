"""
Tests for CSV adapter (read, write, roundtrip, and optimize).
"""
import pytest
from pathlib import Path
from waypoint_optimizer.adapters.csv_adapter import (
    orders_from_csv,
    vehicles_from_csv,
    travel_from_csv,
    allowances_from_csv,
    scenario_to_csv_dir,
    assignments_to_csv,
)
from waypoint_optimizer.mock_data import generate_scenario
from waypoint_optimizer.engine import optimize
from waypoint_optimizer.config import OptimizerConfig


def test_csv_export_and_roundtrip(tmp_path: Path):
    orders, vehicles, travel, allowances = generate_scenario(n_orders=30, n_vehicles=8, seed=123)

    out_dir = tmp_path / "csv_data"
    scenario_to_csv_dir(orders, vehicles, travel, allowances, out_dir, scenario_name="test_run")

    assert (out_dir / "orders.csv").exists()
    assert (out_dir / "fleet_availability.csv").exists()
    assert (out_dir / "vehicle_reference.csv").exists()
    assert (out_dir / "district_travel.csv").exists()
    assert (out_dir / "service_allowances.csv").exists()

    loaded_orders = orders_from_csv(out_dir / "orders.csv")
    loaded_vehicles = vehicles_from_csv(
        out_dir / "fleet_availability.csv",
        out_dir / "vehicle_reference.csv",
    )
    loaded_travel = travel_from_csv(out_dir / "district_travel.csv")
    loaded_allowances = allowances_from_csv(out_dir / "service_allowances.csv")

    assert len(loaded_orders) == len(orders)
    assert len(loaded_vehicles) == len(vehicles)
    assert len(loaded_travel) == len(travel)
    assert len(loaded_allowances) == len(allowances)

    for orig, loaded in zip(orders, loaded_orders):
        assert orig.order_ref == loaded.order_ref
        assert orig.brand == loaded.brand
        assert orig.district == loaded.district
        assert orig.dock_type == loaded.dock_type
        assert orig.order_weight_kg == loaded.order_weight_kg
        assert orig.order_volume_m3 == loaded.order_volume_m3


def test_optimize_from_csv_data(tmp_path: Path):
    orders, vehicles, travel, allowances = generate_scenario(n_orders=25, n_vehicles=6, seed=99)
    out_dir = tmp_path / "scenario_csv"
    scenario_to_csv_dir(orders, vehicles, travel, allowances, out_dir)

    l_orders = orders_from_csv(out_dir / "orders.csv")
    l_vehicles = vehicles_from_csv(
        out_dir / "fleet_availability.csv",
        out_dir / "vehicle_reference.csv",
    )
    l_travel = travel_from_csv(out_dir / "district_travel.csv")
    l_allowances = allowances_from_csv(out_dir / "service_allowances.csv")

    res = optimize(l_orders, l_vehicles, l_travel, l_allowances, config=OptimizerConfig(enable_targeted_cpsat=False))
    assert res.validation.valid is True
    assert res.metrics.served_count + res.metrics.deferred_count == 25

    # Test export assignments
    csv_plan = out_dir / "assignments.csv"
    assignments_to_csv(res.served_assignments, res.deferred_orders, csv_plan)
    assert csv_plan.exists()
    assert csv_plan.stat().st_size > 0
