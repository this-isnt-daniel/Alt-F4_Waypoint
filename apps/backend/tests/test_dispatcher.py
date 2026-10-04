"""
Dispatcher / Optimizer (Person 2) Test Suite
============================================
Comprehensive test suite covering Person 2 (Dispatcher / Optimizer) requirements:

Part 1: Unit Tests for Hard Constraints (P2-U-001 through P2-U-007)
  - Weight Capacity Cap (HC6a)
  - Volume Capacity Cap (HC6b)
  - Temperature Requirement Mismatch: Chilled on Ambient Vehicle (HC2)
  - Parking Constraint: Van-only Outlet with Truck (HC3)
  - Single-Brand Purity per Trip (HC1)
  - Single-District Purity per Trip (HC1)
  - Daily Time Budget (Fresh <= 270 min, Style/Tech <= 480 min)

Part 2: Optimizer Scenarios (P2-U-008 through P2-U-012)
  - Single-trip feasible allocation
  - Multi-trip within vehicle limit (max 2 trips per vehicle)
  - Full capacity exhaustion triggering graceful deferrals
  - Prior deferral fairness weighting / repeat deferral prioritizing
  - Empty orders input handling

Part 3: DB & Adapter Converters (P2-U-013 through P2-U-018)
  - DB Order -> Optimizer Order conversion
  - DB Vehicle -> Optimizer Vehicle conversion
  - Invalid enums fallback handling (unrecognized brand, dock_type, temp)
  - Order without line items fallback to aggregated cargo item
  - Outlet reference data precedence over DB defaults

Part 4: Plan Lifecycle & API Integration (P2-I-001 through P2-I-013)
  - Draft plan generation via API (POST /plans/draft)
  - Plan retrieval (GET /plans/{plan_id})
  - Plan editing (POST /plans/{plan_id}/edit)
  - Plan approval creating Trips, TripStops, and updating Order statuses (POST /plans/{plan_id}/approve)
  - Idempotent approval retries
  - Order deferral (POST /orders/{order_id}/defer)
  - Resequencing and route change delta distribution
  - Breakdown recovery reallocation (POST /breakdowns/{vehicle_id}/reallocate)
  - Urgency requests approval and rejection with mandatory note
  - Cross-depot access rejection (403 Forbidden)
  - Role guard rejection (403 Forbidden for non-dispatcher)

Part 5: Schema & State Verification (P2-S-001 through P2-S-006)
  - DraftPlan CRUD and JSON serialization integrity
  - Status transitions (draft -> approved)
  - Deferral entity persistence with nullable new_date
  - UrgencyRequest unique-order and foreign-depot isolation
"""

import copy
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import List, Dict, Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import get_password_hash, create_platform_access_token

from app.models.user import User
from app.models.depot import Depot
from app.models.outlet import Outlet as DbOutlet
from app.models.vehicle import Vehicle as DbVehicle
from app.models.product import Product as DbProduct
from app.models.order import Order as DbOrder, OrderLine as DbOrderLine
from app.models.plan import DraftPlan
from app.models.trip import Trip as DbTrip, TripStop as DbTripStop
from app.models.deferral import Deferral
from app.models.urgency import UrgencyRequest

from waypoint_optimizer.domain import (
    Brand,
    DistrictTravel,
    DockType,
    LineItem,
    Order as OptimizerOrder,
    Outlet as OptimizerOutlet,
    ParkingConstraint,
    ServiceAllowance,
    TempRequirement,
    TempSpec,
    Vehicle as OptimizerVehicle,
    VehicleStatus,
    VehicleType,
    TripResult,
    OrderAssignment,
    DeferredOrder,
)
from waypoint_optimizer.config import OptimizerConfig
from waypoint_optimizer.validator import validate
from waypoint_optimizer.greedy import greedy_allocate
from waypoint_optimizer.portfolio import run_portfolio
from waypoint_optimizer.adapters.csv_adapter import ReferenceData
from waypoint_optimizer.operational.models import OperationalContext
from waypoint_optimizer.hackathon_planner import generate_daily_draft_plan
from app.adapters.optimizer_adapter import (
    convert_db_order_to_optimizer,
    convert_db_vehicle_to_optimizer,
    generate_daily_draft_plan_operation,
    approve_draft_plan_operation,
    edit_draft_plan_operation,
    reallocate_broken_vehicle_operation,
    get_reference_data,
)


# ==============================================================================
# FIXTURES & HELPERS
# ==============================================================================

@pytest.fixture
def mock_reference_data() -> ReferenceData:
    travel = [
        DistrictTravel(
            district="Colombo",
            depot="Peliyagoda",
            road_class="urban",
            free_flow_kmh=30.0,
            depot_to_district_km=12.0,
            depot_to_district_freeflow_min=24.0,
            inter_stop_km=4.0,
            inter_stop_freeflow_min=8.0,
        ),
        DistrictTravel(
            district="Gampaha",
            depot="Peliyagoda",
            road_class="suburban",
            free_flow_kmh=40.0,
            depot_to_district_km=25.0,
            depot_to_district_freeflow_min=37.5,
            inter_stop_km=6.0,
            inter_stop_freeflow_min=9.0,
        ),
    ]
    allowances = [
        ServiceAllowance(Brand.FRESH, DockType.STREET, 16.0),
        ServiceAllowance(Brand.FRESH, DockType.REAR_DOCK, 15.0),
        ServiceAllowance(Brand.STYLE, DockType.STREET, 25.0),
        ServiceAllowance(Brand.TECH, DockType.REAR_DOCK, 30.0),
    ]
    outlets = {
        "OUT001": OptimizerOutlet("OUT001", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                                  window_open_time="05:00", window_close_time="18:00"),
        "OUT002": OptimizerOutlet("OUT002", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                                  window_open_time="05:00", window_close_time="18:00"),
        "OUT004": OptimizerOutlet("OUT004", Brand.FRESH, "Gampaha", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                                  window_open_time="06:00", window_close_time="18:00"),
        "OUT_VAN": OptimizerOutlet("OUT_VAN", Brand.FRESH, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.VAN_ONLY,
                                   window_open_time="05:00", window_close_time="18:00"),
        "OUT_STYLE": OptimizerOutlet("OUT_STYLE", Brand.STYLE, "Colombo", "Peliyagoda", DockType.STREET, ParkingConstraint.NORMAL,
                                     window_open_time="08:00", window_close_time="18:00"),
    }
    vehicles = [
        OptimizerVehicle(
            vehicle_id="V001", status=VehicleStatus.AVAILABLE, type=VehicleType.TRUCK, temp=TempSpec.AMBIENT,
            weight_cap_kg=2500.0, volume_cap_m3=12.0, depot="Peliyagoda", km_per_l=4.5,
            weekly_fuel_quota_l=250.0, weekly_fuel_used_l=20.0, external_reservations_l=0.0, remaining_trips=2,
            is_selected_for_planning=True,
        ),
        OptimizerVehicle(
            vehicle_id="V002", status=VehicleStatus.AVAILABLE, type=VehicleType.TRUCK, temp=TempSpec.REEFER,
            weight_cap_kg=2500.0, volume_cap_m3=12.0, depot="Peliyagoda", km_per_l=4.5,
            weekly_fuel_quota_l=250.0, weekly_fuel_used_l=20.0, external_reservations_l=0.0, remaining_trips=2,
            is_selected_for_planning=True,
        ),
        OptimizerVehicle(
            vehicle_id="V003", status=VehicleStatus.AVAILABLE, type=VehicleType.VAN, temp=TempSpec.AMBIENT,
            weight_cap_kg=1200.0, volume_cap_m3=6.0, depot="Peliyagoda", km_per_l=7.0,
            weekly_fuel_quota_l=150.0, weekly_fuel_used_l=10.0, external_reservations_l=0.0, remaining_trips=2,
            is_selected_for_planning=True,
        ),
    ]
    return ReferenceData(outlets=outlets, vehicles=vehicles, travel=travel, allowances=allowances, ref_dir="mock_ref")


def make_opt_order(
    ref: str,
    outlet_id: str = "OUT001",
    brand: Brand = Brand.FRESH,
    district: str = "Colombo",
    depot: str = "Peliyagoda",
    dock_type: DockType = DockType.STREET,
    parking: ParkingConstraint = ParkingConstraint.NORMAL,
    temp: TempRequirement = TempRequirement.AMBIENT,
    units: int = 10,
    weight: float = 100.0,
    volume: float = 1.0,
    deferred_prev: bool = False,
    defer_count: int = 0,
    is_urgent: bool = False,
) -> OptimizerOrder:
    return OptimizerOrder(
        order_ref=ref,
        outlet_id=outlet_id,
        brand=brand,
        district=district,
        depot=depot,
        dock_type=dock_type,
        parking_constraint=parking,
        mall_window=None,
        window_open_time="06:00",
        window_close_time="18:00",
        temp_requirement=temp,
        order_units=units,
        order_weight_kg=weight,
        order_volume_m3=volume,
        deferred_prev=deferred_prev,
        defer_count=defer_count,
        is_urgent=is_urgent,
        line_items=[LineItem(f"LI-{ref}", units, "crates", weight / max(1, units), volume / max(1, units))],
    )


# Database Setup Fixture
@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed Depots
    depot1 = Depot(depot_id="Peliyagoda", name="Peliyagoda Central", lat=6.96, lng=79.89)
    depot2 = Depot(depot_id="Kandy", name="Kandy Depot", lat=7.29, lng=80.63)
    db.add_all([depot1, depot2])

    # Seed Users
    pw = get_password_hash("pass123")
    disp1 = User(user_id="U-DISP-P1", username="disp_peli", name="Dispatcher Peliyagoda", role="dispatcher", depot_id="Peliyagoda", hashed_pw=pw)
    disp2 = User(user_id="U-DISP-K1", username="disp_kandy", name="Dispatcher Kandy", role="dispatcher", depot_id="Kandy", hashed_pw=pw)
    sm1 = User(user_id="U-SM-1", username="sm_colombo", name="Store Manager Colombo", role="store_manager", outlet_id="OUT001", hashed_pw=pw)
    loader1 = User(user_id="U-LOAD-1", username="loader_peli", name="Loader Peliyagoda", role="loader", depot_id="Peliyagoda", hashed_pw=pw)
    driver1 = User(user_id="U-DRV-1", username="driver_peli", name="Driver Peliyagoda", role="driver", depot_id="Peliyagoda", hashed_pw=pw)
    db.add_all([disp1, disp2, sm1, loader1, driver1])

    # Seed Outlets
    out1 = DbOutlet(outlet_id="OUT001", name="Colombo Fresh Store", brand="fresh", district="Colombo", depot_id="Peliyagoda", dock_type="street", park_constraint="normal", lat=6.93, lng=79.85)
    out2 = DbOutlet(outlet_id="OUT002", name="Colombo Grandpass", brand="fresh", district="Colombo", depot_id="Peliyagoda", dock_type="street", park_constraint="normal", lat=6.95, lng=79.87)
    out4 = DbOutlet(outlet_id="OUT004", name="Wattala Store", brand="fresh", district="Gampaha", depot_id="Peliyagoda", dock_type="street", park_constraint="normal", lat=6.98, lng=79.89)
    out_van = DbOutlet(outlet_id="OUT_VAN", name="Tight Lane Store", brand="fresh", district="Colombo", depot_id="Peliyagoda", dock_type="street", park_constraint="van_only", lat=6.92, lng=79.86)
    out_kandy = DbOutlet(outlet_id="OUT_KANDY", name="Kandy Main", brand="fresh", district="Kandy", depot_id="Kandy", dock_type="street", park_constraint="normal", lat=7.29, lng=80.63)
    db.add_all([out1, out2, out4, out_van, out_kandy])

    # Seed Vehicles
    v1 = DbVehicle(vehicle_id="V001", depot_id="Peliyagoda", type="truck", temp="ambient", weight_cap_kg=2500.0, vol_cap_m3=12.0, km_per_l=4.5, fuel_quota_l=250, status="available", plate="WP-V1")
    v2 = DbVehicle(vehicle_id="V002", depot_id="Peliyagoda", type="truck", temp="reefer", weight_cap_kg=2500.0, vol_cap_m3=12.0, km_per_l=4.5, fuel_quota_l=250, status="available", plate="WP-V2")
    v3 = DbVehicle(vehicle_id="V003", depot_id="Peliyagoda", type="van", temp="ambient", weight_cap_kg=1200.0, vol_cap_m3=6.0, km_per_l=7.0, fuel_quota_l=150, status="available", plate="WP-V3")
    db.add_all([v1, v2, v3])

    # Seed Product
    prod = DbProduct(product_id="P001", name="Pasteurized Milk", brand="fresh", temp_req="ambient", unit="crate", unit_wt_kg=10.0, unit_vol_m3=0.02, active=True)
    db.add(prod)

    db.commit()

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    old_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_get_db
    yield db

    if old_override:
        app.dependency_overrides[get_db] = old_override
    else:
        app.dependency_overrides.pop(get_db, None)

    Base.metadata.drop_all(bind=engine)
    db.close()


@pytest.fixture
def client(test_db):
    return TestClient(app)


def auth_header(user_id: str, role: str = "dispatcher", depot_id: str = "Peliyagoda") -> dict:
    token = create_platform_access_token({"sub": user_id, "role": role, "depot_id": depot_id})
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# PART 1: UNIT TESTS FOR HARD CONSTRAINTS (P2-U-001 through P2-U-007)
# ==============================================================================

class TestHardConstraints:

    def test_p2_u_001_weight_capacity_cap(self, mock_reference_data):
        """HC6a: Overweight allocation must fail validation with WEIGHT_OVERLOAD."""
        v = OptimizerVehicle("V1", VehicleStatus.AVAILABLE, VehicleType.TRUCK, TempSpec.AMBIENT, 1000.0, 10.0, "Peliyagoda")
        # Order weight 1200 kg exceeds vehicle weight cap 1000 kg
        order = make_opt_order("ORD_WT", weight=1200.0, volume=5.0)

        travel_idx = {(t.district, t.depot): t for t in mock_reference_data.travel}
        allowance_idx = {(a.brand, a.dock_type.value): a.service_allowance_min for a in mock_reference_data.allowances}

        trip = TripResult("V1", 1, Brand.FRESH, "Colombo", ("ORD_WT",), ("ORD_WT",), 1200.0, 5.0, 60.0, -200.0, 5.0)
        res = validate(
            orders=[order],
            vehicles_by_id={"V1": v},
            travel_index=travel_idx,
            allowance_index=allowance_idx,
            served_assignments=[OrderAssignment("ORD_WT", "V1", 1)],
            deferred_orders=[],
            trip_results=[trip],
        )
        assert not res.valid
        rules = [e.rule for e in res.errors]
        assert "WEIGHT_OVERLOAD" in rules or any("weight" in e.detail.lower() for e in res.errors)

    def test_p2_u_002_volume_capacity_cap(self, mock_reference_data):
        """HC6b: Overvolume allocation must fail validation with VOLUME_OVERLOAD."""
        v = OptimizerVehicle("V1", VehicleStatus.AVAILABLE, VehicleType.TRUCK, TempSpec.AMBIENT, 2000.0, 5.0, "Peliyagoda")
        # Order volume 8.0 m³ exceeds vehicle volume cap 5.0 m³
        order = make_opt_order("ORD_VOL", weight=500.0, volume=8.0)

        travel_idx = {(t.district, t.depot): t for t in mock_reference_data.travel}
        allowance_idx = {(a.brand, a.dock_type.value): a.service_allowance_min for a in mock_reference_data.allowances}

        trip = TripResult("V1", 1, Brand.FRESH, "Colombo", ("ORD_VOL",), ("ORD_VOL",), 500.0, 8.0, 60.0, 1500.0, -3.0)
        res = validate(
            orders=[order],
            vehicles_by_id={"V1": v},
            travel_index=travel_idx,
            allowance_index=allowance_idx,
            served_assignments=[OrderAssignment("ORD_VOL", "V1", 1)],
            deferred_orders=[],
            trip_results=[trip],
        )
        assert not res.valid
        assert any("volume" in e.detail.lower() or "VOLUME" in e.rule for e in res.errors)

    def test_p2_u_003_temp_mismatch_chilled_on_ambient(self, mock_reference_data):
        """HC2: Chilled order on ambient vehicle must fail validation with TEMP_INCOMPATIBLE."""
        v_ambient = OptimizerVehicle("V_AMB", VehicleStatus.AVAILABLE, VehicleType.TRUCK, TempSpec.AMBIENT, 2000.0, 10.0, "Peliyagoda")
        order_chilled = make_opt_order("ORD_COLD", temp=TempRequirement.CHILLED)

        travel_idx = {(t.district, t.depot): t for t in mock_reference_data.travel}
        allowance_idx = {(a.brand, a.dock_type.value): a.service_allowance_min for a in mock_reference_data.allowances}

        trip = TripResult("V_AMB", 1, Brand.FRESH, "Colombo", ("ORD_COLD",), ("ORD_COLD",), 100.0, 1.0, 60.0, 1900.0, 9.0)
        res = validate(
            orders=[order_chilled],
            vehicles_by_id={"V_AMB": v_ambient},
            travel_index=travel_idx,
            allowance_index=allowance_idx,
            served_assignments=[OrderAssignment("ORD_COLD", "V_AMB", 1)],
            deferred_orders=[],
            trip_results=[trip],
        )
        assert not res.valid
        rules = [e.rule for e in res.errors]
        assert "TEMP_INCOMPATIBLE" in rules

    def test_p2_u_004_van_only_constraint_with_truck(self, mock_reference_data):
        """HC3: Van-only parking constraint outlet serviced by truck must fail."""
        v_truck = OptimizerVehicle("V_TRUCK", VehicleStatus.AVAILABLE, VehicleType.TRUCK, TempSpec.AMBIENT, 2000.0, 10.0, "Peliyagoda")
        order_van = make_opt_order("ORD_VAN", parking=ParkingConstraint.VAN_ONLY)

        travel_idx = {(t.district, t.depot): t for t in mock_reference_data.travel}
        allowance_idx = {(a.brand, a.dock_type.value): a.service_allowance_min for a in mock_reference_data.allowances}

        trip = TripResult("V_TRUCK", 1, Brand.FRESH, "Colombo", ("ORD_VAN",), ("ORD_VAN",), 100.0, 1.0, 60.0, 1900.0, 9.0)
        res = validate(
            orders=[order_van],
            vehicles_by_id={"V_TRUCK": v_truck},
            travel_index=travel_idx,
            allowance_index=allowance_idx,
            served_assignments=[OrderAssignment("ORD_VAN", "V_TRUCK", 1)],
            deferred_orders=[],
            trip_results=[trip],
        )
        assert not res.valid
        assert any("van" in e.detail.lower() or "HC3" in e.rule for e in res.errors)

    def test_p2_u_005_brand_purity_per_trip(self, mock_reference_data):
        """HC1: Mixing multiple brands (Fresh + Style) in same trip must fail."""
        v = OptimizerVehicle("V1", VehicleStatus.AVAILABLE, VehicleType.TRUCK, TempSpec.AMBIENT, 2000.0, 10.0, "Peliyagoda")
        o_fresh = make_opt_order("O_FRESH", brand=Brand.FRESH)
        o_style = make_opt_order("O_STYLE", brand=Brand.STYLE)

        travel_idx = {(t.district, t.depot): t for t in mock_reference_data.travel}
        allowance_idx = {(a.brand, a.dock_type.value): a.service_allowance_min for a in mock_reference_data.allowances}

        trip = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O_FRESH", "O_STYLE"), ("O_FRESH", "O_STYLE"), 200.0, 2.0, 80.0, 1800.0, 8.0)
        res = validate(
            orders=[o_fresh, o_style],
            vehicles_by_id={"V1": v},
            travel_index=travel_idx,
            allowance_index=allowance_idx,
            served_assignments=[OrderAssignment("O_FRESH", "V1", 1), OrderAssignment("O_STYLE", "V1", 1)],
            deferred_orders=[],
            trip_results=[trip],
        )
        assert not res.valid
        assert any("brand" in e.detail.lower() or "HC1" in e.rule for e in res.errors)

    def test_p2_u_006_district_purity_per_trip(self, mock_reference_data):
        """HC1: Mixing multiple districts (Colombo + Gampaha) in same trip must fail."""
        v = OptimizerVehicle("V1", VehicleStatus.AVAILABLE, VehicleType.TRUCK, TempSpec.AMBIENT, 2000.0, 10.0, "Peliyagoda")
        o_col = make_opt_order("O_COL", district="Colombo")
        o_gam = make_opt_order("O_GAM", district="Gampaha")

        travel_idx = {(t.district, t.depot): t for t in mock_reference_data.travel}
        allowance_idx = {(a.brand, a.dock_type.value): a.service_allowance_min for a in mock_reference_data.allowances}

        trip = TripResult("V1", 1, Brand.FRESH, "Colombo", ("O_COL", "O_GAM"), ("O_COL", "O_GAM"), 200.0, 2.0, 80.0, 1800.0, 8.0)
        res = validate(
            orders=[o_col, o_gam],
            vehicles_by_id={"V1": v},
            travel_index=travel_idx,
            allowance_index=allowance_idx,
            served_assignments=[OrderAssignment("O_COL", "V1", 1), OrderAssignment("O_GAM", "V1", 1)],
            deferred_orders=[],
            trip_results=[trip],
        )
        assert not res.valid
        assert any("district" in e.detail.lower() or "HC1" in e.rule for e in res.errors)

    def test_p2_u_007_time_budget_enforcement(self, mock_reference_data):
        """Fresh daily budget <= 270 min. Trips exceeding 270 min must fail with FRESH_BUDGET_EXCEEDED."""
        v = OptimizerVehicle("V1", VehicleStatus.AVAILABLE, VehicleType.TRUCK, TempSpec.AMBIENT, 2000.0, 10.0, "Peliyagoda")
        # 10 orders to drive the calculated duration up
        orders = [make_opt_order(f"ORD_LONG_{i}", units=10, weight=50.0, volume=0.5) for i in range(15)]
        refs = tuple(o.order_ref for o in orders)

        travel_idx = {(t.district, t.depot): t for t in mock_reference_data.travel}
        allowance_idx = {(a.brand, a.dock_type.value): a.service_allowance_min for a in mock_reference_data.allowances}

        from waypoint_optimizer.trip_math import calculate_trip_minutes
        t_min = calculate_trip_minutes(orders, travel_idx[("Colombo", "Peliyagoda")], allowance_idx)
        # Verify calculated minutes exceeds budget
        assert t_min > 270.0

        trip = TripResult("V1", 1, Brand.FRESH, "Colombo", refs, refs, 750.0, 7.5, t_min, 1250.0, 2.5)
        res = validate(
            orders=orders,
            vehicles_by_id={"V1": v},
            travel_index=travel_idx,
            allowance_index=allowance_idx,
            served_assignments=[OrderAssignment(r, "V1", 1) for r in refs],
            deferred_orders=[],
            trip_results=[trip],
        )
        assert not res.valid
        rules = [e.rule for e in res.errors]
        assert "FRESH_BUDGET_EXCEEDED" in rules


# ==============================================================================
# PART 2: OPTIMIZER SCENARIOS (P2-U-008 through P2-U-012)
# ==============================================================================

class TestOptimizerScenarios:

    def test_p2_u_008_single_trip_allocation(self, mock_reference_data):
        """Small batch of orders fits cleanly into a single trip."""
        context = OperationalContext(planning_date="2026-10-04")
        o1 = make_opt_order("O1", weight=200.0, volume=1.0)
        o2 = make_opt_order("O2", weight=300.0, volume=1.5)

        plan = generate_daily_draft_plan(
            orders=[o1, o2],
            fleet=[mock_reference_data.vehicles[0]],
            reference_data=mock_reference_data,
            context=context,
            enable_targeted_cpsat=False,
        )
        assert plan["validation"]["valid"]
        assert plan["order_counts"]["fully_served_orders"] == 2
        assert len(plan["trips"]) == 1

    def test_p2_u_009_multi_trip_within_vehicle_limit(self, mock_reference_data):
        """Vehicle executes up to 2 trips when capacity demands it."""
        context = OperationalContext(planning_date="2026-10-04")
        # Two orders where each consumes 60% of vehicle capacity, forcing 2 trips
        small_v = OptimizerVehicle(
            "V_SPLIT", VehicleStatus.AVAILABLE, VehicleType.VAN, TempSpec.AMBIENT,
            weight_cap_kg=500.0, volume_cap_m3=5.0, depot="Peliyagoda", km_per_l=5.0,
            weekly_fuel_quota_l=200.0, weekly_fuel_used_l=10.0, external_reservations_l=0.0, remaining_trips=2,
            is_selected_for_planning=True,
        )
        o1 = make_opt_order("O1", weight=400.0, volume=3.0)
        o2 = make_opt_order("O2", weight=400.0, volume=3.0)

        plan = generate_daily_draft_plan(
            orders=[o1, o2],
            fleet=[small_v],
            reference_data=mock_reference_data,
            context=context,
            enable_targeted_cpsat=False,
        )
        assert plan["validation"]["valid"]
        assert plan["order_counts"]["fully_served_orders"] == 2
        assert len(plan["trips"]) == 2
        assert plan["trips"][0]["vehicle_id"] == "V_SPLIT"
        assert plan["trips"][1]["vehicle_id"] == "V_SPLIT"

    def test_p2_u_010_full_capacity_triggers_graceful_deferral(self, mock_reference_data):
        """Fleet capacity exhaustion triggers structured deferrals with proper reasons."""
        context = OperationalContext(planning_date="2026-10-04")
        small_v = OptimizerVehicle(
            "V_TINY", VehicleStatus.AVAILABLE, VehicleType.VAN, TempSpec.AMBIENT,
            weight_cap_kg=200.0, volume_cap_m3=2.0, depot="Peliyagoda", km_per_l=5.0,
            weekly_fuel_quota_l=200.0, weekly_fuel_used_l=10.0, external_reservations_l=0.0, remaining_trips=1,
            is_selected_for_planning=True,
        )
        o1 = make_opt_order("O1", weight=150.0, volume=1.0)
        o2 = make_opt_order("O2", weight=150.0, volume=1.0)

        plan = generate_daily_draft_plan(
            orders=[o1, o2],
            fleet=[small_v],
            reference_data=mock_reference_data,
            context=context,
            enable_targeted_cpsat=False,
        )
        assert plan["validation"]["valid"]
        assert plan["order_counts"]["fully_served_orders"] == 1
        assert plan["order_counts"]["fully_deferred_orders"] == 1
        assert len(plan["deferred_orders"]) == 1
        assert "reason" in plan["deferred_orders"][0]

    def test_p2_u_011_prior_deferral_fairness_weighting(self, mock_reference_data):
        """Previously deferred order must take precedence over brand new order."""
        context = OperationalContext(planning_date="2026-10-04")
        small_v = OptimizerVehicle(
            "V_ONE", VehicleStatus.AVAILABLE, VehicleType.VAN, TempSpec.AMBIENT,
            weight_cap_kg=200.0, volume_cap_m3=2.0, depot="Peliyagoda", km_per_l=5.0,
            weekly_fuel_quota_l=200.0, weekly_fuel_used_l=10.0, external_reservations_l=0.0, remaining_trips=1,
            is_selected_for_planning=True,
        )
        # O_NEW is new; O_PREV has deferred_prev=True and defer_count=2
        o_new = make_opt_order("O_NEW", weight=150.0, volume=1.0, deferred_prev=False, defer_count=0)
        o_prev = make_opt_order("O_PREV", weight=150.0, volume=1.0, deferred_prev=True, defer_count=2)

        plan = generate_daily_draft_plan(
            orders=[o_new, o_prev],
            fleet=[small_v],
            reference_data=mock_reference_data,
            context=context,
            enable_targeted_cpsat=False,
        )
        assert plan["validation"]["valid"]
        served = [
            oref
            for t in plan["trips"]
            for s in t.get("driver_itinerary", [])
            for oref in s.get("order_refs", [])
        ]
        assert "O_PREV" in served, "Prior deferred order must be prioritized over new order"
        assert "O_NEW" in [d["order_ref"] for d in plan["deferred_orders"]]

    def test_p2_u_012_empty_orders_input_handling(self, mock_reference_data):
        """Empty orders returns a valid empty plan without crashing."""
        context = OperationalContext(planning_date="2026-10-04")

        plan = generate_daily_draft_plan(
            orders=[],
            fleet=mock_reference_data.vehicles,
            reference_data=mock_reference_data,
            context=context,
        )
        assert plan["validation"]["valid"] is True
        assert plan["order_counts"]["total_orders"] == 0
        assert len(plan["trips"]) == 0


# ==============================================================================
# PART 3: DB & ADAPTER CONVERTERS (P2-U-013 through P2-U-018)
# ==============================================================================

class TestAdapterConverters:

    def test_p2_u_013_db_order_to_optimizer_conversion(self, test_db, mock_reference_data):
        """DbOrder converts faithfully to immutable OptimizerOrder."""
        today = date.today()
        db_order = DbOrder(
            order_id="ORD-CONV-1", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=25, order_wt_kg=250.0, order_vol_m3=0.5,
            window_open="08:00", window_close="16:00", deferred_prev=True, defer_count=1,
        )
        line = DbOrderLine(line_item_id="LI-CONV-1", order_id="ORD-CONV-1", product_id="P001", quantity=25)
        db_order.lines.append(line)
        test_db.add(db_order)
        test_db.commit()

        opt_order = convert_db_order_to_optimizer(db_order, mock_reference_data, test_db, is_urgent=False)
        assert opt_order.order_ref == "ORD-CONV-1"
        assert opt_order.outlet_id == "OUT001"
        assert opt_order.brand == Brand.FRESH
        assert opt_order.district == "Colombo"
        assert opt_order.order_units == 25
        assert opt_order.order_weight_kg == 250.0
        assert opt_order.deferred_prev is True
        assert opt_order.defer_count == 1
        assert len(opt_order.line_items) == 1
        assert opt_order.line_items[0].line_item_id == "LI-CONV-1"

    def test_p2_u_014_db_vehicle_to_optimizer_conversion(self, test_db, mock_reference_data):
        """DbVehicle converts faithfully to immutable OptimizerVehicle."""
        db_v = DbVehicle(
            vehicle_id="V-CONV-1", depot_id="Peliyagoda", type="van", temp="reefer",
            weight_cap_kg=1500.0, vol_cap_m3=8.0, km_per_l=6.5, fuel_quota_l=200, status="available", plate="WP-CONV",
        )
        test_db.add(db_v)
        test_db.commit()

        opt_v = convert_db_vehicle_to_optimizer(db_v, mock_reference_data)
        assert opt_v.vehicle_id == "V-CONV-1"
        assert opt_v.type == VehicleType.VAN
        assert opt_v.temp == TempSpec.REEFER
        assert opt_v.weight_cap_kg == 1500.0
        assert opt_v.volume_cap_m3 == 8.0
        assert opt_v.is_available is True
        assert opt_v.status == VehicleStatus.AVAILABLE

    def test_p2_u_015_invalid_enums_fallback_handling(self, test_db, mock_reference_data):
        """Unrecognized enums gracefully fall back to safe defaults."""
        today = date.today()
        # Create DbOrder with unrecognized brand and temp_req
        db_order = DbOrder(
            order_id="ORD-BAD-ENUM", outlet_id="OUT001", created_by="U-DISP-P1", brand="unknown_brand", temp_req="unknown_temp",
            order_date=today, status="confirmed", order_units=5, order_wt_kg=50.0, order_vol_m3=0.1,
        )
        test_db.add(db_order)

        opt_order = convert_db_order_to_optimizer(db_order, mock_reference_data, test_db)
        # Should fall back cleanly without raising ValueError
        assert opt_order.brand == Brand.FRESH
        assert opt_order.temp_requirement == TempRequirement.AMBIENT

    def test_p2_u_016_order_without_lines_creates_synthetic_cargo_line(self, test_db, mock_reference_data):
        """Order missing order_line rows gets synthetic line item to preserve demand."""
        today = date.today()
        db_order = DbOrder(
            order_id="ORD-NOLINES", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=12, order_wt_kg=120.0, order_vol_m3=0.3,
        )
        test_db.add(db_order)
        test_db.commit()

        opt_order = convert_db_order_to_optimizer(db_order, mock_reference_data, test_db)
        assert len(opt_order.line_items) == 1
        assert opt_order.line_items[0].line_item_id == "ORD-NOLINES-LI-1"
        assert opt_order.line_items[0].quantity == 12.0

    def test_p2_u_017_outlet_ref_data_overrides_db_attributes(self, test_db, mock_reference_data):
        """Authoritative reference CSV data takes precedence over DB Outlet values."""
        today = date.today()
        db_order = DbOrder(
            order_id="ORD-PRECEDENCE", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=5, order_wt_kg=50.0, order_vol_m3=0.1,
        )
        test_db.add(db_order)
        test_db.commit()

        opt_order = convert_db_order_to_optimizer(db_order, mock_reference_data, test_db)
        # OUT001 in mock_reference_data is district Colombo, dock_type STREET
        assert opt_order.district == "Colombo"
        assert opt_order.dock_type == DockType.STREET

    def test_p2_u_018_workshop_vehicle_conversion(self, test_db, mock_reference_data):
        """DbVehicle with status 'in_workshop' converts to VehicleStatus.IN_WORKSHOP and is_selected=False."""
        db_v = DbVehicle(
            vehicle_id="V-SHOP", depot_id="Peliyagoda", type="truck", temp="ambient",
            weight_cap_kg=2000.0, vol_cap_m3=10.0, status="in_workshop", plate="WP-SHOP",
        )
        test_db.add(db_v)
        test_db.commit()

        opt_v = convert_db_vehicle_to_optimizer(db_v, mock_reference_data)
        assert opt_v.status == VehicleStatus.IN_WORKSHOP
        assert opt_v.is_selected_for_planning is False
        assert opt_v.is_available is False


# ==============================================================================
# PART 4: PLAN LIFECYCLE & API INTEGRATION (P2-I-001 through P2-I-013)
# ==============================================================================

class TestPlanLifecycleIntegration:

    def test_p2_i_001_create_draft_plan_api(self, client, test_db):
        """POST /plans/draft creates a valid draft without locking/approving."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        today = date.today()

        # Seed confirmed order
        o = DbOrder(
            order_id="ORD-API-001", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=10, order_wt_kg=100.0, order_vol_m3=0.2,
        )
        o.lines.append(DbOrderLine(line_item_id="LI-API-1", order_id="ORD-API-001", product_id="P001", quantity=10))
        test_db.add(o)
        test_db.commit()

        res = client.post(
            "/api/v1/dispatcher/plans/draft",
            headers=h,
            json={"depot_id": "Peliyagoda", "target_date": str(today), "enable_targeted_cpsat": True},
        )
        assert res.status_code == 200, res.text
        plan = res.json()
        assert "plan_id" in plan
        assert plan["validation"]["valid"] is True
        assert plan["validation"]["is_dispatch_ready"] is False  # Must require manual approval

        # Verify persisted as draft in DB
        db_plan = test_db.query(DraftPlan).filter(DraftPlan.plan_id == plan["plan_id"]).first()
        assert db_plan is not None
        assert db_plan.status == "draft"

    def test_p2_i_002_get_plan_by_id_api(self, client, test_db):
        """GET /plans/{plan_id} retrieves persisted plan accurately."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        today = date.today()

        o = DbOrder(
            order_id="ORD-API-002", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=10, order_wt_kg=100.0, order_vol_m3=0.2,
        )
        o.lines.append(DbOrderLine(line_item_id="LI-API-2", order_id="ORD-API-002", product_id="P001", quantity=10))
        test_db.add(o)
        test_db.commit()

        res = client.post("/api/v1/dispatcher/plans/draft", headers=h, json={"depot_id": "Peliyagoda", "target_date": str(today)})
        plan_id = res.json()["plan_id"]

        get_res = client.get(f"/api/v1/dispatcher/plans/{plan_id}", headers=h)
        assert get_res.status_code == 200
        assert get_res.json()["plan_id"] == plan_id

    def test_p2_i_003_edit_draft_plan_api(self, client, test_db):
        """POST /plans/{plan_id}/edit performs re-evaluation and updates draft."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        today = date.today()

        o1 = DbOrder(
            order_id="ORD-API-EDIT-1", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=10, order_wt_kg=100.0, order_vol_m3=0.2,
        )
        o1.lines.append(DbOrderLine(line_item_id="LI-API-E1", order_id="ORD-API-EDIT-1", product_id="P001", quantity=10))
        test_db.add(o1)
        test_db.commit()

        res = client.post("/api/v1/dispatcher/plans/draft", headers=h, json={"depot_id": "Peliyagoda", "target_date": str(today)})
        plan_id = res.json()["plan_id"]

        # Move order to V003
        edit_res = client.post(
            f"/api/v1/dispatcher/plans/{plan_id}/edit",
            headers=h,
            json={
                "actions": [
                    {
                        "action_type": "move_whole_order",
                        "order_ref": "ORD-API-EDIT-1",
                        "target_vehicle_id": "V003",
                        "target_trip_number": 1,
                    }
                ]
            },
        )
        assert edit_res.status_code == 200, edit_res.text
        edited = edit_res.json()
        assert edited["validation"]["valid"] is True
        v_ids = [t["vehicle_id"] for t in edited["trips"]]
        assert "V003" in v_ids

    def test_p2_i_004_approve_draft_plan_transitions_entities(self, client, test_db):
        """POST /plans/{plan_id}/approve creates Trips, TripStops, updates Orders to planned."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        today = date.today()

        o = DbOrder(
            order_id="ORD-API-APP-1", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=10, order_wt_kg=100.0, order_vol_m3=0.2,
        )
        o.lines.append(DbOrderLine(line_item_id="LI-API-APP1", order_id="ORD-API-APP-1", product_id="P001", quantity=10))
        test_db.add(o)
        test_db.commit()

        res = client.post("/api/v1/dispatcher/plans/draft", headers=h, json={"depot_id": "Peliyagoda", "target_date": str(today)})
        plan_id = res.json()["plan_id"]

        app_res = client.post(
            f"/api/v1/dispatcher/plans/{plan_id}/approve",
            headers=h,
            json={"client_op_id": "OP-APP-001"},
        )
        assert app_res.status_code == 200, app_res.text
        assert app_res.json()["status"] == "approved"
        assert app_res.json()["trips_created"] >= 1

        # Check DB states
        test_db.refresh(o)
        assert o.status == "planned"
        assert o.trip_id is not None
        assert o.stop_seq == 1

        trips = test_db.query(DbTrip).filter(DbTrip.depot_id == "Peliyagoda").all()
        assert len(trips) >= 1
        stops = test_db.query(DbTripStop).filter(DbTripStop.order_id == "ORD-API-APP-1").all()
        assert len(stops) == 1

    def test_p2_i_005_idempotent_plan_approval(self, client, test_db):
        """Second approval of already-approved plan is safe and doesn't duplicate records."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        today = date.today()

        o = DbOrder(
            order_id="ORD-API-IDEMP-1", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=5, order_wt_kg=50.0, order_vol_m3=0.1,
        )
        o.lines.append(DbOrderLine(line_item_id="LI-API-ID1", order_id="ORD-API-IDEMP-1", product_id="P001", quantity=5))
        test_db.add(o)
        test_db.commit()

        res = client.post("/api/v1/dispatcher/plans/draft", headers=h, json={"depot_id": "Peliyagoda", "target_date": str(today)})
        plan_id = res.json()["plan_id"]

        # First approval
        app1 = client.post(f"/api/v1/dispatcher/plans/{plan_id}/approve", headers=h, json={"client_op_id": "OP-IDEMP-1"})
        assert app1.status_code == 200
        initial_trips = test_db.query(DbTrip).count()
        initial_stops = test_db.query(DbTripStop).count()

        # Second approval retry
        app2 = client.post(f"/api/v1/dispatcher/plans/{plan_id}/approve", headers=h, json={"client_op_id": "OP-IDEMP-1"})
        assert app2.status_code == 200
        assert app2.json()["status"] == "approved"

        # Assert no duplicated rows
        assert test_db.query(DbTrip).count() == initial_trips
        assert test_db.query(DbTripStop).count() == initial_stops

    def test_p2_i_006_defer_order_endpoint(self, client, test_db):
        """POST /orders/{order_id}/defer transitions order and creates Deferral record."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        today = date.today()

        o = DbOrder(
            order_id="ORD-MAN-DEF-1", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=10, order_wt_kg=100.0, order_vol_m3=0.2,
        )
        test_db.add(o)
        test_db.commit()

        defer_payload = {
            "client_op_id": "OP-DEF-001",
            "order_id": "ORD-MAN-DEF-1",
            "outlet_id": "OUT001",
            "original_date": str(today),
            "new_date": str(today + timedelta(days=1)),
            "reason": "Depot refrigeration capacity exceeded",
        }
        res = client.post("/api/v1/dispatcher/orders/ORD-MAN-DEF-1/defer", headers=h, json=defer_payload)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "success"

        test_db.refresh(o)
        assert o.status == "deferred"
        assert o.deferred_prev is True
        assert o.defer_count == 1

        d = test_db.query(Deferral).filter(Deferral.order_id == "ORD-MAN-DEF-1").first()
        assert d is not None
        assert d.reason == "Depot refrigeration capacity exceeded"

    def test_p2_i_007_dispatcher_lists_outlets_filtered(self, client, test_db):
        """GET /outlets returns outlets filtered by depot and brand."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        res = client.get("/api/v1/dispatcher/outlets", headers=h)
        assert res.status_code == 200
        outlets = res.json()
        assert len(outlets) >= 3
        # Foreign depot outlet OUT_KANDY must NOT be in the list
        ids = [o["outlet_id"] for o in outlets]
        assert "OUT_KANDY" not in ids

    def test_p2_i_008_dispatcher_resequence_route_change(self, client, test_db):
        """Dispatcher issues route.resequenced change to driver."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        today = date.today()

        trip = DbTrip(trip_id="TRIP-RESEQ-1", depot_id="Peliyagoda", vehicle_id="V001", dispatcher_id="U-DISP-P1", trip_date=today, trip_no=1, status="out_for_delivery")
        s1 = DbTripStop(stop_id="STOP-R1", trip_id="TRIP-RESEQ-1", outlet_id="OUT001", order_id="ORD-R1", stop_seq=1, status="upcoming", temp_req="ambient")
        s2 = DbTripStop(stop_id="STOP-R2", trip_id="TRIP-RESEQ-1", outlet_id="OUT002", order_id="ORD-R2", stop_seq=2, status="upcoming", temp_req="ambient")
        test_db.add_all([trip, s1, s2])
        test_db.commit()

        res = client.post(
            "/api/v1/dispatcher/trips/TRIP-RESEQ-1/route-changes",
            headers=h,
            json={"change_type": "route.resequenced", "payload": {"new_sequence": ["STOP-R2", "STOP-R1"]}},
        )
        assert res.status_code == 200
        assert res.json()["change_type"] == "route.resequenced"
        assert res.json()["acknowledged"] is False

    def test_p2_i_009_urgency_request_approval_and_rejection(self, client, test_db):
        """Dispatcher reviews urgency requests for their depot."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        sm_h = auth_header("U-SM-1", "store_manager")
        today = date.today()

        o1 = DbOrder(order_id="ORD-URG-APP", outlet_id="OUT001", created_by="U-SM-1", brand="fresh", temp_req="ambient", order_date=today, status="confirmed", order_units=5, order_wt_kg=50.0, order_vol_m3=0.1)
        o1.lines.append(DbOrderLine(line_item_id="LI-U1", order_id="ORD-URG-APP", product_id="P001", quantity=5))
        o2 = DbOrder(order_id="ORD-URG-REJ", outlet_id="OUT001", created_by="U-SM-1", brand="fresh", temp_req="ambient", order_date=today + timedelta(days=1), status="confirmed", order_units=5, order_wt_kg=50.0, order_vol_m3=0.1)
        o2.lines.append(DbOrderLine(line_item_id="LI-U2", order_id="ORD-URG-REJ", product_id="P001", quantity=5))
        test_db.add_all([o1, o2])
        test_db.commit()

        # SM requests urgency
        u1_res = client.post("/api/v1/store-manager/orders/ORD-URG-APP/urgency-request", headers=sm_h, json={"reason_code": "stockout_risk", "reason_text": "Zero stock left on shelf"})
        u1_id = u1_res.json()["urgency_request_id"]
        u2_res = client.post("/api/v1/store-manager/orders/ORD-URG-REJ/urgency-request", headers=sm_h, json={"reason_code": "other", "reason_text": "Special upcoming marketing campaign"})
        u2_id = u2_res.json()["urgency_request_id"]

        # Dispatcher approves u1
        app_res = client.post(f"/api/v1/dispatcher/urgency-requests/{u1_id}/approve", headers=h, json={"decision_note": "Approved for priority delivery"})
        assert app_res.status_code == 200
        assert app_res.json()["status"] == "approved"

        # Dispatcher rejects u2 (must reject empty note)
        rej_bad = client.post(f"/api/v1/dispatcher/urgency-requests/{u2_id}/reject", headers=h, json={"decision_note": ""})
        assert rej_bad.status_code == 422

        rej_res = client.post(f"/api/v1/dispatcher/urgency-requests/{u2_id}/reject", headers=h, json={"decision_note": "Capacity constrained; cannot prioritize"})
        assert rej_res.status_code == 200
        assert rej_res.json()["status"] == "rejected"

    def test_p2_i_010_vehicle_breakdown_reallocation_api(self, client, test_db):
        """POST /breakdowns/{vehicle_id}/reallocate dynamically reallocates undelivered orders."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        today = date.today()

        o = DbOrder(
            order_id="ORD-BD-1", outlet_id="OUT001", created_by="U-DISP-P1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=10, order_wt_kg=100.0, order_vol_m3=0.2,
        )
        o.lines.append(DbOrderLine(line_item_id="LI-BD-1", order_id="ORD-BD-1", product_id="P001", quantity=10))
        test_db.add(o)
        test_db.commit()

        # Generate and approve draft
        draft_res = client.post("/api/v1/dispatcher/plans/draft", headers=h, json={"depot_id": "Peliyagoda", "target_date": str(today)})
        plan_id = draft_res.json()["plan_id"]
        assigned_v = draft_res.json()["trips"][0]["vehicle_id"]

        app_res = client.post(f"/api/v1/dispatcher/plans/{plan_id}/approve", headers=h)
        assert app_res.status_code == 200

        # Breakdown recovery on assigned vehicle
        bd_res = client.post(
            f"/api/v1/dispatcher/breakdowns/{assigned_v}/reallocate",
            headers=h,
            json={"plan_id": plan_id, "current_time_iso": f"{today}T10:00:00+05:30", "pickup_location": "DEPOT"},
        )
        assert bd_res.status_code == 200, bd_res.text
        recovery_data = bd_res.json()
        assert "trips" in recovery_data or "recovery_reasons" in recovery_data

        # Broken vehicle must be set to in_workshop
        v = test_db.query(DbVehicle).filter(DbVehicle.vehicle_id == assigned_v).first()
        assert v.status == "in_workshop"

    def test_p2_i_011_plan_not_found_404(self, client):
        """Accessing non-existent plan returns 404 Not Found."""
        h = auth_header("U-DISP-P1", "dispatcher", "Peliyagoda")
        res = client.get("/api/v1/dispatcher/plans/PLAN-DOES-NOT-EXIST", headers=h)
        assert res.status_code == 404

    def test_p2_i_012_cross_depot_forbidden_403(self, client, test_db):
        """Dispatcher cannot access or manipulate a plan belonging to another depot."""
        disp_kandy_h = auth_header("U-DISP-K1", "dispatcher", "Kandy")
        today = date.today()

        # Create Peliyagoda plan
        plan = DraftPlan(
            plan_id="PLAN-PELI-001",
            depot_id="Peliyagoda",
            target_date=today,
            status="draft",
            plan_data={"plan_id": "PLAN-PELI-001", "depot_id": "Peliyagoda"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db.add(plan)
        test_db.commit()

        # Kandy dispatcher attempts to read Peliyagoda plan
        res = client.get("/api/v1/dispatcher/plans/PLAN-PELI-001", headers=disp_kandy_h)
        assert res.status_code == 403
        assert "depot scope" in res.json()["detail"].lower()

    def test_p2_i_013_role_guard_blocks_non_dispatchers(self, client):
        """Endpoints under /api/v1/dispatcher reject non-dispatcher roles (403 Forbidden)."""
        loader_h = auth_header("U-LOAD-1", "loader", "Peliyagoda")
        driver_h = auth_header("U-DRV-1", "driver", "Peliyagoda")
        sm_h = auth_header("U-SM-1", "store_manager")

        for h in [loader_h, driver_h, sm_h]:
            res = client.get("/api/v1/dispatcher/outlets", headers=h)
            assert res.status_code == 403, f"Expected 403 for header {h}, got {res.status_code}"


# ==============================================================================
# PART 5: SCHEMA & STATE VERIFICATION (P2-S-001 through P2-S-006)
# ==============================================================================

class TestSchemaAndStateIntegrity:

    def test_p2_s_001_draft_plan_crud_and_json_integrity(self, test_db):
        """DraftPlan persists JSON data faithfully without mutation or serialization loss."""
        now = datetime.now(timezone.utc)
        payload = {
            "algorithm": "hybrid_greedy_targeted_cpsat",
            "trips": [{"vehicle_id": "V001", "district": "Colombo", "weight": 450.5}],
            "metrics": {"total_served": 1, "penalty": 0.0},
        }
        plan = DraftPlan(
            plan_id="PLAN-JSON-TEST",
            depot_id="Peliyagoda",
            target_date=date(2026, 10, 4),
            status="draft",
            algorithm="hybrid_greedy_targeted_cpsat",
            plan_data=payload,
            created_at=now,
            updated_at=now,
            created_by="U-DISP-P1",
        )
        test_db.add(plan)
        test_db.commit()

        fetched = test_db.query(DraftPlan).filter(DraftPlan.plan_id == "PLAN-JSON-TEST").first()
        assert fetched is not None
        assert fetched.plan_data["trips"][0]["vehicle_id"] == "V001"
        assert fetched.plan_data["trips"][0]["weight"] == 450.5

    def test_p2_s_002_plan_status_transitions(self, test_db):
        """DraftPlan progresses from 'draft' to 'approved' with audit columns set."""
        now = datetime.now(timezone.utc)
        plan = DraftPlan(
            plan_id="PLAN-STATUS-TEST",
            depot_id="Peliyagoda",
            target_date=date(2026, 10, 4),
            status="draft",
            plan_data={},
            created_at=now,
            updated_at=now,
            created_by="U-DISP-P1",
        )
        test_db.add(plan)
        test_db.commit()

        # Update to approved
        app_time = datetime.now(timezone.utc)
        plan.status = "approved"
        plan.approved_by = "U-DISP-P1"
        plan.approved_at = app_time
        test_db.commit()

        refreshed = test_db.query(DraftPlan).filter(DraftPlan.plan_id == "PLAN-STATUS-TEST").first()
        assert refreshed.status == "approved"
        assert refreshed.approved_by == "U-DISP-P1"
        assert refreshed.approved_at is not None

    def test_p2_s_003_deferral_nullable_new_date_persistence(self, test_db):
        """Deferral entity accurately persists original_date and nullable new_date."""
        now = datetime.now(timezone.utc)
        d = Deferral(
            deferral_id="DEF-NULL-DATE",
            order_id="ORD-D-1",
            outlet_id="OUT001",
            original_date=date(2026, 10, 4),
            new_date=None,  # Carry-forward deferral!
            reason="REEFER_CAPACITY_EXHAUSTED",
            created_at=now,
            created_by="U-DISP-P1",
        )
        test_db.add(d)
        test_db.commit()

        saved = test_db.query(Deferral).filter(Deferral.deferral_id == "DEF-NULL-DATE").first()
        assert saved is not None
        assert saved.new_date is None
        assert saved.reason == "REEFER_CAPACITY_EXHAUSTED"

    def test_p2_s_004_urgency_request_unique_order_constraint(self, test_db):
        """An order may only have one active urgency request."""
        from sqlalchemy.exc import IntegrityError
        now = datetime.now(timezone.utc)
        u1 = UrgencyRequest(
            urgency_request_id="URG-U-1", order_id="ORD-SINGLE-URG", outlet_id="OUT001", reported_by="U-SM-1",
            reason_code="stockout_risk", reason_text="Running low on milk", status="pending", created_at=now,
        )
        test_db.add(u1)
        test_db.commit()

        u2 = UrgencyRequest(
            urgency_request_id="URG-U-2", order_id="ORD-SINGLE-URG", outlet_id="OUT001", reported_by="U-SM-1",
            reason_code="time_bound_event", reason_text="Morning sale opening", status="pending", created_at=now,
        )
        test_db.add(u2)
        with pytest.raises(IntegrityError):
            test_db.commit()
        test_db.rollback()

    def test_p2_s_005_trip_stop_item_pack_seq_and_quantities(self, test_db):
        """TripStop creation maintains denormalized sequence and item associations."""
        today = date.today()
        trip = DbTrip(trip_id="TRIP-ITEMS-1", depot_id="Peliyagoda", vehicle_id="V001", dispatcher_id="U-DISP-P1", trip_date=today, trip_no=1, status="planned")
        stop = DbTripStop(stop_id="STOP-ITEMS-1", trip_id="TRIP-ITEMS-1", outlet_id="OUT001", order_id="ORD-ITEMS-1", stop_seq=1, temp_req="ambient", status="upcoming")
        test_db.add_all([trip, stop])
        test_db.commit()

        fetched_stop = test_db.query(DbTripStop).filter(DbTripStop.stop_id == "STOP-ITEMS-1").first()
        assert fetched_stop.stop_seq == 1
        assert fetched_stop.status == "upcoming"
        assert fetched_stop.row_version == 1

    def test_p2_s_006_order_status_lifecycle_transitions(self, test_db):
        """Order status progresses through confirmed -> planned -> loaded -> delivered."""
        today = date.today()
        o = DbOrder(
            order_id="ORD-LIFECYCLE", outlet_id="OUT001", created_by="U-SM-1", brand="fresh", temp_req="ambient",
            order_date=today, status="confirmed", order_units=10, order_wt_kg=100.0, order_vol_m3=0.2,
        )
        test_db.add(o)
        test_db.commit()

        # Planned
        o.status = "planned"
        o.trip_id = "TRIP-123"
        test_db.commit()
        assert test_db.query(DbOrder).filter(DbOrder.order_id == "ORD-LIFECYCLE").first().status == "planned"

        # Loaded
        o.status = "loaded"
        test_db.commit()
        assert test_db.query(DbOrder).filter(DbOrder.order_id == "ORD-LIFECYCLE").first().status == "loaded"

        # Delivered
        o.status = "delivered"
        test_db.commit()
        assert test_db.query(DbOrder).filter(DbOrder.order_id == "ORD-LIFECYCLE").first().status == "delivered"
