"""
Unit and integration tests for Phase 4 reference data loading and production contracts.
"""
from __future__ import annotations

import io
import json
import math
from pathlib import Path
import pytest

from waypoint_optimizer.adapters.csv_adapter import (
    ReferenceData,
    export_plan_json,
    load_fleet_state_from_csv,
    load_orders_with_outlets,
    load_plan_json,
    load_reference_data,
    outlets_from_csv,
    vehicles_from_csv,
)
from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.domain import Brand, DockType, ParkingConstraint, TempRequirement
from waypoint_optimizer.engine import optimize
from waypoint_optimizer.input_validation import InputValidationError
from waypoint_optimizer.validator import validate
from waypoint_optimizer.trip_math import build_allowance_index, build_travel_index
try:
    from tests.conftest import resolve_real_data_dir
except ImportError:
    from .conftest import resolve_real_data_dir

REAL_DATA_DIR = resolve_real_data_dir()


# ── 1. Actual supplied CSV schemas and relations ──────────────────────────────

def test_load_real_reference_csvs():
    """Verify loading directly from the real data/ directory."""
    assert REAL_DATA_DIR.exists(), f"Reference data directory not found at {REAL_DATA_DIR}"

    ref = load_reference_data(REAL_DATA_DIR)

    # 1. Outlets
    assert len(ref.outlets) == 120
    assert "OUT001" in ref.outlets
    assert "OUT120" in ref.outlets
    assert ref.outlets["OUT001"].outlet_id == "OUT001"  # leading zeros preserved
    assert ref.outlets["OUT001"].brand == Brand.FRESH
    assert ref.outlets["OUT001"].district == "Colombo"
    assert ref.outlets["OUT001"].depot == "Peliyagoda"
    assert ref.outlets["OUT001"].dock_type == DockType.STREET
    assert ref.outlets["OUT001"].parking_constraint == ParkingConstraint.VAN_ONLY

    # 2. Vehicles
    assert len(ref.vehicles) == 60
    assert ref.vehicles[0].vehicle_id == "VEH001"  # leading zeros preserved
    assert ref.vehicles[0].is_available  # default status is available

    # 3. District travel
    assert len(ref.travel) == 12
    travel_keys = {(t.district, t.depot) for t in ref.travel}
    assert ("Colombo", "Peliyagoda") in travel_keys
    assert ("Kandy", "Kandy") in travel_keys

    # 4. Service allowance
    assert len(ref.allowances) == 9
    allowance_keys = {(a.brand, a.dock_type) for a in ref.allowances}
    for b in (Brand.FRESH, Brand.STYLE, Brand.TECH):
        for dt in (DockType.REAR_DOCK, DockType.STREET, DockType.MALL_BAY):
            assert (b, dt) in allowance_keys

    # 5. Operational context files
    assert ref.calendar_rows is not None
    assert len(ref.calendar_rows) == 910
    assert ref.traffic_speed_rows is not None
    assert len(ref.traffic_speed_rows) == 576
    assert ref.road_conditions_rows is not None
    assert len(ref.road_conditions_rows) == 10920


# ── 2. Order-to-outlet joins and identifier preservation ───────────────────────

def test_order_to_outlet_join_success():
    """Verify orders correctly join to authoritative outlets and inherit attributes."""
    ref = load_reference_data(REAL_DATA_DIR)

    csv_data = """order_ref,outlet_id,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT001,15,250.5,3.2,ambient,0,2
ORD0002,OUT015,20,400.0,4.5,ambient,1,5
"""
    orders = load_orders_with_outlets(io.StringIO(csv_data), outlets=ref.outlets)
    assert len(orders) == 2

    # Check ORD0001 joined with OUT001
    o1 = orders[0]
    assert o1.order_ref == "ORD0001"
    assert o1.outlet_id == "OUT001"
    assert o1.brand == Brand.FRESH
    assert o1.district == "Colombo"
    assert o1.depot == "Peliyagoda"
    assert o1.dock_type == DockType.STREET
    assert o1.parking_constraint == ParkingConstraint.VAN_ONLY
    assert o1.order_units == 15
    assert o1.order_weight_kg == 250.5
    assert o1.order_volume_m3 == 3.2
    assert o1.temp_requirement == TempRequirement.AMBIENT
    assert o1.deferred_yesterday is False
    assert o1.days_since_last_served == 2

    # Check ORD0002 joined with OUT015
    o2 = orders[1]
    assert o2.order_ref == "ORD0002"
    assert o2.outlet_id == "OUT015"
    assert o2.brand == Brand.STYLE
    assert o2.dock_type == DockType.MALL_BAY
    assert o2.parking_constraint == ParkingConstraint.MALL_DOCK
    assert o2.mall_window == "09:00-11:00"
    assert o2.deferred_yesterday is True
    assert o2.days_since_last_served == 5


# ── 3. Unknown outlets and conflicting attributes ───────────────────────────────

def test_orders_unknown_outlet_rejected():
    """Verify unknown outlet IDs raise actionable InputValidationError."""
    ref = load_reference_data(REAL_DATA_DIR)

    csv_data = """order_ref,outlet_id,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT999,10,100.0,1.0,ambient,0,0
"""
    with pytest.raises(InputValidationError, match="references unknown outlet_id 'OUT999'"):
        load_orders_with_outlets(io.StringIO(csv_data), outlets=ref.outlets)


def test_orders_conflicting_attributes_rejected():
    """Verify conflicting attributes in orders CSV vs authoritative outlets raise errors."""
    ref = load_reference_data(REAL_DATA_DIR)

    # 1. Conflicting brand
    csv_brand = """order_ref,outlet_id,brand,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT001,style,10,100.0,1.0,ambient,0,0
"""
    with pytest.raises(InputValidationError, match="conflicts with authoritative outlet 'OUT001' brand 'fresh'"):
        load_orders_with_outlets(io.StringIO(csv_brand), outlets=ref.outlets)

    # 2. Conflicting district
    csv_district = """order_ref,outlet_id,district,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT001,Kandy,10,100.0,1.0,ambient,0,0
"""
    with pytest.raises(InputValidationError, match="conflicts with authoritative outlet 'OUT001' district 'Colombo'"):
        load_orders_with_outlets(io.StringIO(csv_district), outlets=ref.outlets)

    # 3. Conflicting dock_type
    csv_dock = """order_ref,outlet_id,dock_type,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT001,rear_dock,10,100.0,1.0,ambient,0,0
"""
    with pytest.raises(InputValidationError, match="conflicts with authoritative outlet 'OUT001' dock_type 'street'"):
        load_orders_with_outlets(io.StringIO(csv_dock), outlets=ref.outlets)


# ── 4. Duplicate keys and malformed values ─────────────────────────────────────

def test_duplicate_outlet_id_rejected():
    """Verify duplicate outlet IDs in outlets reference are rejected."""
    csv_outlets = """outlet_id,brand,district,depot,dock_type,parking_constraint,mall_window,window_open_time,window_close_time
OUT001,fresh,Colombo,Peliyagoda,street,van_only,,,
OUT001,fresh,Colombo,Peliyagoda,street,van_only,,,
"""
    with pytest.raises(InputValidationError, match="Duplicate outlet_id 'OUT001'"):
        outlets_from_csv(io.StringIO(csv_outlets))


def test_duplicate_order_ref_rejected():
    """Verify duplicate order_ref in orders CSV is rejected."""
    ref = load_reference_data(REAL_DATA_DIR)
    csv_data = """order_ref,outlet_id,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT001,10,100.0,1.0,ambient,0,0
ORD0001,OUT002,15,150.0,1.5,ambient,0,0
"""
    with pytest.raises(InputValidationError, match="Duplicate order_ref 'ORD0001'"):
        load_orders_with_outlets(io.StringIO(csv_data), outlets=ref.outlets)


def test_malformed_numeric_values_rejected():
    """Verify negative and non-finite numbers in orders are rejected."""
    ref = load_reference_data(REAL_DATA_DIR)

    # Negative weight
    csv_neg = """order_ref,outlet_id,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT001,10,-50.0,1.0,ambient,0,0
"""
    with pytest.raises(InputValidationError, match="invalid order_weight_kg"):
        load_orders_with_outlets(io.StringIO(csv_neg), outlets=ref.outlets)

    # Negative units
    csv_units = """order_ref,outlet_id,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT001,-5,50.0,1.0,ambient,0,0
"""
    with pytest.raises(InputValidationError, match="invalid order_units"):
        load_orders_with_outlets(io.StringIO(csv_units), outlets=ref.outlets)


# ── 5. Missing files and missing relationships ─────────────────────────────────

def test_missing_reference_file(tmp_path: Path):
    """Verify FileNotFoundError when required reference files are missing."""
    empty_dir = tmp_path / "empty_ref"
    empty_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="Required outlets reference file not found"):
        load_reference_data(empty_dir)


def test_missing_reference_relationships(tmp_path: Path):
    """Verify InputValidationError when reference files have dangling foreign keys."""
    ref_dir = tmp_path / "broken_ref"
    ref_dir.mkdir()

    # Outlets with unknown district "Atlantis"
    (ref_dir / "outlets.csv").write_text(
        "outlet_id,brand,district,depot,dock_type,parking_constraint,mall_window,window_open_time,window_close_time\n"
        "OUT001,fresh,Atlantis,Peliyagoda,street,van_only,,,\n",
        encoding="utf-8",
    )
    (ref_dir / "district_travel.csv").write_text(
        "district,depot,road_class,free_flow_kmh,depot_to_district_km,depot_to_district_freeflow_min,inter_stop_km,inter_stop_freeflow_min\n"
        "Colombo,Peliyagoda,urban,30.0,12,24,4.0,8\n",
        encoding="utf-8",
    )
    (ref_dir / "service_allowance.csv").write_text(
        "brand,dock_type,service_allowance_min\n"
        "fresh,street,16\n",
        encoding="utf-8",
    )
    (ref_dir / "vehicles.csv").write_text(
        "vehicle_id,type,temp,weight_cap_kg,volume_cap_m3,depot\n"
        "VEH001,truck,reefer,5000,20,Peliyagoda\n",
        encoding="utf-8",
    )

    with pytest.raises(InputValidationError, match="no matching record in district_travel reference"):
        load_reference_data(ref_dir)


# ── 6. Production CLI behavior: never fall back to mock data ──────────────────

def test_cli_missing_orders_exits_nonzero(capsys):
    """Verify production optimize exits with nonzero code if orders file is missing."""
    import argparse
    from waypoint_optimizer.cli import cmd_optimize

    args = argparse.Namespace(
        ref_dir=str(REAL_DATA_DIR),
        orders_file="nonexistent_orders.csv",
        output_file="plan_output.json",
        input_dir=None,
        fleet_availability=None,
        scenario=None,
    )

    with pytest.raises(SystemExit) as exc_info:
        cmd_optimize(args)
    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "Orders file not found" in captured.err or "requires an explicit orders file" in captured.err


# ── 7. Strict JSON export and round-trip revalidation ──────────────────────────

def test_strict_json_export_and_revalidation(tmp_path: Path):
    """Verify JSON export contains no NaN/inf, includes provenance, and revalidates."""
    ref = load_reference_data(REAL_DATA_DIR)

    csv_data = """order_ref,outlet_id,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT001,10,120.0,1.5,ambient,0,1
ORD0002,OUT002,15,180.0,2.0,ambient,1,3
ORD0003,OUT003,12,140.0,1.8,ambient,0,0
"""
    orders = load_orders_with_outlets(io.StringIO(csv_data), outlets=ref.outlets)
    cfg = OptimizerConfig(enable_targeted_cpsat=False)
    result = optimize(orders, ref.vehicles, ref.travel, ref.allowances, config=cfg)

    assert result.validation.valid is True

    json_file = tmp_path / "plan_strict.json"
    provenance = {"orders_source": "test_buffer", "ref_dir": str(REAL_DATA_DIR)}
    export_plan_json(result, json_file, provenance=provenance)

    assert json_file.exists()
    plan_dict = load_plan_json(json_file)

    # Strict JSON assertions
    assert plan_dict["status"] in ("FEASIBLE", "OPTIMAL")
    assert plan_dict["validation"]["valid"] is True
    assert plan_dict["provenance"]["orders_source"] == "test_buffer"
    assert len(plan_dict["trips"]) > 0

    # Reconstruct for independent validator
    vehicles_by_id = {v.vehicle_id: v for v in ref.vehicles}
    travel_index = build_travel_index(ref.travel)
    allowance_index = build_allowance_index(ref.allowances)

    val_res = validate(
        orders=orders,
        vehicles_by_id=vehicles_by_id,
        travel_index=travel_index,
        allowance_index=allowance_index,
        served_assignments=result.served_assignments,
        deferred_orders=result.deferred_orders,
        trip_results=result.trips,
    )
    assert val_res.valid is True


def test_csv_overwrite_prevention(tmp_path: Path):
    """Verify that export_plan_json prevents overwriting source CSV files."""
    ref = load_reference_data(REAL_DATA_DIR)
    csv_data = """order_ref,outlet_id,order_units,order_weight_kg,order_volume_m3,temp_requirement,deferred_yesterday,days_since_last_served
ORD0001,OUT001,10,120.0,1.5,ambient,0,1
"""
    orders = load_orders_with_outlets(io.StringIO(csv_data), outlets=ref.outlets)
    result = optimize(orders, ref.vehicles, ref.travel, ref.allowances, config=OptimizerConfig(enable_targeted_cpsat=False))

    csv_dest = tmp_path / "orders.csv"
    with pytest.raises(ValueError, match="must be a JSON file, not a CSV file"):
        export_plan_json(result, csv_dest)


def test_load_explicit_fleet_state_from_csv():
    """Verify loading explicit daily fleet state joined with master vehicle reference."""
    ref = load_reference_data(REAL_DATA_DIR)
    fleet_csv = """vehicle_id,status,is_selected_for_planning,remaining_trips,earliest_availability_iso,weekly_fuel_used_l,external_reservations_l,exclusion_reason
VEH001,available,1,2,2026-10-03T04:00:00+05:30,45.0,10.0,
VEH015,in_workshop,0,0,,140.0,0.0,Brake overhaul
VEH025,available,0,0,,85.0,30.0,Dispatcher reserve
"""
    fleet = load_fleet_state_from_csv(io.StringIO(fleet_csv), vehicle_reference=ref.vehicles)
    assert len(fleet) == 60  # All 60 vehicles accounted for

    v1 = next(v for v in fleet if v.vehicle_id == "VEH001")
    assert v1.is_available
    assert v1.is_selected_for_planning
    assert v1.remaining_trips == 2
    assert v1.weekly_fuel_used_l == 45.0
    assert v1.external_reservations_l == 10.0

    v15 = next(v for v in fleet if v.vehicle_id == "VEH015")
    assert not v15.is_available
    assert not v15.is_selected_for_planning
    assert v15.remaining_trips == 0
    assert v15.exclusion_reason == "Brake overhaul"

    v25 = next(v for v in fleet if v.vehicle_id == "VEH025")
    assert v25.is_available
    assert not v25.is_selected_for_planning
    assert v25.exclusion_reason == "Dispatcher reserve"

    # Vehicles not in fleet_csv must be marked unselected
    v50 = next(v for v in fleet if v.vehicle_id == "VEH050")
    assert not v50.is_selected_for_planning
    assert v50.exclusion_reason == "Not listed in daily fleet state input"
