"""
Tests for Real Reference CSV Integration and Public Workflows
=============================================================
Uses the real reference CSV data supplied in the project data directory:
  - outlets.csv
  - vehicles.csv
  - district_travel.csv
  - service_allowance.csv
  - calendar.csv
  - traffic_speed.csv
  - road_conditions.csv

Audits and eliminates depot and reference bias by explicitly testing both
Peliyagoda and Kandy depots across all supported dimensions:
  - Brands: Fresh, Style, Tech
  - Vehicle types: Truck and Van
  - Temperature specs: Reefer and Ambient
  - Access constraints: Street, Rear Dock, Mall Bay, Normal, Van-Only, Mall Dock
  - Multiple districts: Colombo, Gampaha, Kandy, Matale, Nuwara Eliya, etc.

Covers the public workflows:
  1. generate_daily_draft_plan() with real records from both Peliyagoda and Kandy
  2. evaluate_edited_draft() with real records across depots
  3. reallocate_broken_vehicle() with real records across depots
  4. Reference coverage tests (calendar, traffic, road, static travel model)
  5. Real-data validation tests (allowances, travel, fuel efficiency)
  6. Audit test documenting all real entities and unavailable combinations
"""
from __future__ import annotations

import copy
import dataclasses
import math
from typing import Any
import pytest

from waypoint_optimizer.adapters.csv_adapter import ReferenceData
from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, Outlet,
    ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleStatus, VehicleType,
)
from waypoint_optimizer.hackathon_planner import generate_daily_draft_plan
from waypoint_optimizer.operational import (
    OperationalContext, TravelPolicy, WindowPolicy,
)
from waypoint_optimizer.operational.draft_editor import (
    DeferWholeOrderAction,
    MoveWholeOrderAction,
    evaluate_edited_draft,
)
from waypoint_optimizer.operational.breakdown_recovery import (
    UndeliveredQuantity,
    reallocate_broken_vehicle,
)
from waypoint_optimizer.operational.validator import validate_operational_plan
from waypoint_optimizer.trip_math import (
    build_allowance_index,
    build_travel_index,
    handling_minutes,
    inter_stop_minutes,
    outbound_minutes,
)


# ==============================================================================
# Helpers for Constructing Authoritative Records from Real Reference Data
# ==============================================================================

def make_order_from_real_outlet(
    outlet: Outlet,
    order_ref: str,
    units: int = 10,
    weight_kg: float = 100.0,
    volume_m3: float = 1.0,
    temp: TempRequirement = TempRequirement.AMBIENT,
    line_items: list[LineItem] | None = None,
    deferred_prev: bool = False,
    defer_count: int = 1,
    is_urgent: bool = False,
) -> Order:
    """
    Creates an authoritative backend-shaped order by strictly copying
    outlet attributes from the real reference Outlet record.
    """
    return Order(
        order_ref=order_ref,
        outlet_id=outlet.outlet_id,
        brand=outlet.brand,
        district=outlet.district,
        depot=outlet.depot,
        dock_type=outlet.dock_type,
        parking_constraint=outlet.parking_constraint,
        mall_window=outlet.mall_window,
        window_open_time=outlet.window_open_time,
        window_close_time=outlet.window_close_time,
        temp_requirement=temp,
        order_units=units,
        order_weight_kg=weight_kg,
        order_volume_m3=volume_m3,
        deferred_prev=deferred_prev,
        defer_count=defer_count,
        is_urgent=is_urgent,
        line_items=line_items or [],
    )


def with_live_fleet_state(
    vehicle: Vehicle,
    weekly_fuel_used_l: float = 45.0,
    external_reservations_l: float = 15.0,
    remaining_trips: int = 2,
    is_selected_for_planning: bool = True,
    status: VehicleStatus = VehicleStatus.AVAILABLE,
    earliest_availability_iso: str | None = "2026-10-03T04:00:00+05:30",
) -> Vehicle:
    """
    Augments a real reference Vehicle with explicit live fleet state
    as expected from backend/dispatcher live fleet state.
    """
    return dataclasses.replace(
        vehicle,
        weekly_fuel_used_l=weekly_fuel_used_l,
        external_reservations_l=external_reservations_l,
        remaining_trips=remaining_trips,
        is_selected_for_planning=is_selected_for_planning,
        status=status,
        earliest_availability_iso=earliest_availability_iso,
    )


# ==============================================================================
# 1. generate_daily_draft_plan() with Real Reference Data Across Depots
# ==============================================================================

def test_real_data_generate_daily_draft_plan_peliyagoda_fresh_reefer_truck(real_reference_data: ReferenceData):
    """
    Peliyagoda Depot: Fresh brand, Chilled orders, Reefer Truck (VEH001).
    Outlets: OUT004 (Street, Normal) and OUT006 (Street, Normal).
    """
    ref = real_reference_data
    outlet_004 = ref.outlets["OUT004"]
    outlet_006 = ref.outlets["OUT006"]

    raw_v1 = next(v for v in ref.vehicles if v.vehicle_id == "VEH001")
    v1_live = with_live_fleet_state(raw_v1, weekly_fuel_used_l=40.0, external_reservations_l=10.0)

    items_1 = [
        LineItem("LI01", 15.0, "crates", 10.0, 0.06, "Fresh Milk"),
        LineItem("LI02", 10.0, "crates", 10.0, 0.06, "Fresh Yogurt"),
    ]
    order_1 = make_order_from_real_outlet(
        outlet_004, "ORD_P_001", units=25, weight_kg=250.0, volume_m3=1.5,
        temp=TempRequirement.CHILLED, line_items=items_1,
    )

    items_2 = [
        LineItem("LI03", 20.0, "crates", 15.0, 0.09, "Fresh Cheese"),
    ]
    order_2 = make_order_from_real_outlet(
        outlet_006, "ORD_P_002", units=20, weight_kg=300.0, volume_m3=1.8,
        temp=TempRequirement.CHILLED, line_items=items_2,
    )

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
        window_policy=WindowPolicy.ARRIVAL_BEFORE_CLOSE,
        depot_turnaround_duration_min=30.0,
    )

    plan = generate_daily_draft_plan(
        orders=[order_1, order_2],
        fleet=[v1_live],
        reference_data=ref,
        context=context,
    )

    assert plan["status"] in ("OPTIMAL", "FEASIBLE")
    assert plan["validation"]["valid"] is True
    assert len(plan["trips"]) == 1

    trip = plan["trips"][0]
    assert trip["vehicle_id"] == "VEH001"
    assert trip["depot"] == "Peliyagoda"
    assert trip["district"] == "Colombo"
    assert trip["brand"] == "fresh"

    # Colombo travel: 12 km outbound, 4 km inter-stop, 12 km return = 28 km
    assert trip["fuel"]["distance_km"] == 28.0
    assert math.isclose(trip["fuel"]["fuel_consumed_l"], 28.0 / 4.7, rel_tol=1e-2)

    val_res = validate_operational_plan(
        orders=[order_1, order_2],
        timelines=plan,
        context=context,
        fleet=[v1_live],
        reference_data=ref,
    )
    assert val_res.valid is True


def test_real_data_generate_daily_draft_plan_peliyagoda_tech_ambient_truck_mall(real_reference_data: ReferenceData):
    """
    Peliyagoda Depot: Tech brand, Ambient orders, Ambient Truck (VEH008).
    Outlets: OUT021 and OUT022 (Mall Bay dock, Mall Dock parking constraint).
    """
    ref = real_reference_data
    outlet_021 = ref.outlets["OUT021"]
    outlet_022 = ref.outlets["OUT022"]

    assert outlet_021.dock_type == DockType.MALL_BAY
    assert outlet_021.parking_constraint == ParkingConstraint.MALL_DOCK
    assert outlet_021.brand == Brand.TECH

    raw_v8 = next(v for v in ref.vehicles if v.vehicle_id == "VEH008")
    assert raw_v8.type == VehicleType.TRUCK
    assert raw_v8.temp == TempSpec.AMBIENT
    v8_live = with_live_fleet_state(
        raw_v8,
        weekly_fuel_used_l=30.0,
        external_reservations_l=10.0,
        earliest_availability_iso="2026-10-03T08:30:00+05:30",
    )

    items_1 = [LineItem("LI_T1", 5.0, "boxes", 20.0, 0.2, "Laptops")]
    items_2 = [LineItem("LI_T2", 8.0, "boxes", 15.0, 0.15, "Peripherals")]
    order_1 = make_order_from_real_outlet(
        outlet_021, "ORD_TECH_001", units=5, weight_kg=100.0, volume_m3=1.0,
        temp=TempRequirement.AMBIENT, line_items=items_1,
    )
    order_2 = make_order_from_real_outlet(
        outlet_022, "ORD_TECH_002", units=8, weight_kg=120.0, volume_m3=1.2,
        temp=TempRequirement.AMBIENT, line_items=items_2,
    )

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
        window_policy=WindowPolicy.ARRIVAL_BEFORE_CLOSE,
        depot_turnaround_duration_min=30.0,
    )

    plan = generate_daily_draft_plan(
        orders=[order_1, order_2],
        fleet=[v8_live],
        reference_data=ref,
        context=context,
    )

    assert plan["status"] in ("OPTIMAL", "FEASIBLE")
    assert plan["validation"]["valid"] is True
    assert len(plan["trips"]) == 1
    assert plan["trips"][0]["vehicle_id"] == "VEH008"
    assert plan["trips"][0]["brand"] == "tech"
    # Tech mall_bay service allowance is 55.0 min per stop
    for stop in plan["trips"][0]["driver_itinerary"]:
        assert stop["service_duration_min"] == 55.0


def test_real_data_generate_daily_draft_plan_peliyagoda_fresh_reefer_van_van_only(real_reference_data: ReferenceData):
    """
    Peliyagoda Depot: Fresh brand, Chilled orders, Reefer Van (VEH036).
    Outlets: OUT001 and OUT002 (Van-Only parking constraint).
    """
    ref = real_reference_data
    outlet_001 = ref.outlets["OUT001"]
    outlet_002 = ref.outlets["OUT002"]

    assert outlet_001.parking_constraint == ParkingConstraint.VAN_ONLY
    assert outlet_002.parking_constraint == ParkingConstraint.VAN_ONLY

    raw_van = next(v for v in ref.vehicles if v.vehicle_id == "VEH036")
    assert raw_van.type == VehicleType.VAN
    assert raw_van.temp == TempSpec.REEFER
    van_live = with_live_fleet_state(raw_van, weekly_fuel_used_l=25.0, external_reservations_l=5.0)

    items_1 = [LineItem("LI_V1", 10.0, "crates", 10.0, 0.05, "Milk")]
    items_2 = [LineItem("LI_V2", 10.0, "crates", 10.0, 0.05, "Butter")]
    order_1 = make_order_from_real_outlet(
        outlet_001, "ORD_VAN_001", units=10, weight_kg=100.0, volume_m3=0.5,
        temp=TempRequirement.CHILLED, line_items=items_1,
    )
    order_2 = make_order_from_real_outlet(
        outlet_002, "ORD_VAN_002", units=10, weight_kg=100.0, volume_m3=0.5,
        temp=TempRequirement.CHILLED, line_items=items_2,
    )

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    plan = generate_daily_draft_plan(
        orders=[order_1, order_2],
        fleet=[van_live],
        reference_data=ref,
        context=context,
    )

    assert plan["status"] in ("OPTIMAL", "FEASIBLE")
    assert plan["validation"]["valid"] is True
    assert plan["trips"][0]["vehicle_id"] == "VEH036"
    assert math.isclose(plan["trips"][0]["fuel"]["fuel_consumed_l"], 28.0 / 10.3, rel_tol=1e-2)


def test_real_data_generate_daily_draft_plan_kandy_fresh_reefer_truck(real_reference_data: ReferenceData):
    """
    Kandy Depot: Fresh brand, Chilled orders, Reefer Truck (VEH040).
    Outlets: OUT084 and OUT085 (Kandy district, Rear Dock, Normal parking).
    """
    ref = real_reference_data
    outlet_084 = ref.outlets["OUT084"]
    outlet_085 = ref.outlets["OUT085"]

    assert outlet_084.depot == "Kandy"
    assert outlet_084.district == "Kandy"
    assert outlet_084.dock_type == DockType.REAR_DOCK
    assert outlet_084.parking_constraint == ParkingConstraint.NORMAL

    raw_v40 = next(v for v in ref.vehicles if v.vehicle_id == "VEH040")
    assert raw_v40.depot == "Kandy"
    assert raw_v40.temp == TempSpec.REEFER
    v40_live = with_live_fleet_state(raw_v40, weekly_fuel_used_l=35.0, external_reservations_l=10.0)

    items_1 = [LineItem("LI_K1", 12.0, "crates", 10.0, 0.08, "Hill Milk")]
    items_2 = [LineItem("LI_K2", 15.0, "crates", 10.0, 0.08, "Hill Cheese")]
    order_1 = make_order_from_real_outlet(
        outlet_085, "ORD_K_001", units=12, weight_kg=120.0, volume_m3=0.96,
        temp=TempRequirement.CHILLED, line_items=items_1,
    )
    order_2 = make_order_from_real_outlet(
        outlet_084, "ORD_K_002", units=15, weight_kg=150.0, volume_m3=1.2,
        temp=TempRequirement.CHILLED, line_items=items_2,
    )

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    plan = generate_daily_draft_plan(
        orders=[order_1, order_2],
        fleet=[v40_live],
        reference_data=ref,
        context=context,
    )

    assert plan["status"] in ("OPTIMAL", "FEASIBLE")
    assert plan["validation"]["valid"] is True
    trip = plan["trips"][0]
    assert trip["vehicle_id"] == "VEH040"
    assert trip["depot"] == "Kandy"
    assert trip["district"] == "Kandy"
    # Kandy travel: outbound 8 km (16 min), inter-stop 3 km (6 min), return 8 km (16 min) = 19 km
    assert trip["fuel"]["distance_km"] == 19.0
    assert math.isclose(trip["fuel"]["fuel_consumed_l"], 19.0 / 4.7, rel_tol=1e-2)


def test_real_data_generate_daily_draft_plan_kandy_style_ambient_truck_mall(real_reference_data: ReferenceData):
    """
    Kandy Depot: Style brand, Ambient orders, Ambient Truck (VEH044).
    Outlets: OUT089 and OUT090 (Kandy district, Mall Bay dock, Mall Dock parking).
    """
    ref = real_reference_data
    outlet_089 = ref.outlets["OUT089"]
    outlet_090 = ref.outlets["OUT090"]

    assert outlet_089.depot == "Kandy"
    assert outlet_089.brand == Brand.STYLE
    assert outlet_089.dock_type == DockType.MALL_BAY
    assert outlet_089.parking_constraint == ParkingConstraint.MALL_DOCK

    raw_v44 = next(v for v in ref.vehicles if v.vehicle_id == "VEH044")
    assert raw_v44.depot == "Kandy"
    assert raw_v44.temp == TempSpec.AMBIENT
    v44_live = with_live_fleet_state(
        raw_v44,
        weekly_fuel_used_l=30.0,
        external_reservations_l=5.0,
        earliest_availability_iso="2026-10-03T08:30:00+05:30",
    )

    items_1 = [LineItem("LI_S1", 10.0, "garments", 8.0, 0.1, "Silk Shirts")]
    items_2 = [LineItem("LI_S2", 12.0, "garments", 8.0, 0.1, "Linen Trousers")]
    order_1 = make_order_from_real_outlet(
        outlet_089, "ORD_KS_001", units=10, weight_kg=80.0, volume_m3=1.0,
        temp=TempRequirement.AMBIENT, line_items=items_1,
    )
    order_2 = make_order_from_real_outlet(
        outlet_090, "ORD_KS_002", units=12, weight_kg=96.0, volume_m3=1.2,
        temp=TempRequirement.AMBIENT, line_items=items_2,
    )

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    plan = generate_daily_draft_plan(
        orders=[order_1, order_2],
        fleet=[v44_live],
        reference_data=ref,
        context=context,
    )

    assert plan["status"] in ("OPTIMAL", "FEASIBLE")
    assert plan["validation"]["valid"] is True
    trip = plan["trips"][0]
    assert trip["vehicle_id"] == "VEH044"
    assert trip["brand"] == "style"
    # Style mall_bay service allowance is 59.0 min per stop
    for stop in trip["driver_itinerary"]:
        assert stop["service_duration_min"] == 59.0


def test_real_data_generate_daily_draft_plan_kandy_fresh_reefer_van_van_only(real_reference_data: ReferenceData):
    """
    Kandy Depot: Fresh brand, Chilled orders, Reefer Van (VEH057).
    Outlets: OUT076 and OUT077 (Kandy district, Street dock, Van-Only parking).
    """
    ref = real_reference_data
    outlet_076 = ref.outlets["OUT076"]
    outlet_077 = ref.outlets["OUT077"]

    assert outlet_076.depot == "Kandy"
    assert outlet_076.parking_constraint == ParkingConstraint.VAN_ONLY

    raw_van = next(v for v in ref.vehicles if v.vehicle_id == "VEH057")
    assert raw_van.depot == "Kandy"
    assert raw_van.type == VehicleType.VAN
    assert raw_van.temp == TempSpec.REEFER
    van_live = with_live_fleet_state(raw_van, weekly_fuel_used_l=15.0, external_reservations_l=5.0)

    items_1 = [LineItem("LI_KV1", 8.0, "crates", 10.0, 0.05, "Yogurt")]
    items_2 = [LineItem("LI_KV2", 10.0, "crates", 10.0, 0.05, "Milk")]
    order_1 = make_order_from_real_outlet(
        outlet_076, "ORD_KVAN_001", units=8, weight_kg=80.0, volume_m3=0.4,
        temp=TempRequirement.CHILLED, line_items=items_1,
    )
    order_2 = make_order_from_real_outlet(
        outlet_077, "ORD_KVAN_002", units=10, weight_kg=100.0, volume_m3=0.5,
        temp=TempRequirement.CHILLED, line_items=items_2,
    )

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    plan = generate_daily_draft_plan(
        orders=[order_1, order_2],
        fleet=[van_live],
        reference_data=ref,
        context=context,
    )

    assert plan["status"] in ("OPTIMAL", "FEASIBLE")
    assert plan["validation"]["valid"] is True
    assert plan["trips"][0]["vehicle_id"] == "VEH057"
    assert math.isclose(plan["trips"][0]["fuel"]["fuel_consumed_l"], 19.0 / 10.3, rel_tol=1e-2)


def test_real_data_generate_daily_draft_plan_kandy_matale_district(real_reference_data: ReferenceData):
    """
    Kandy Depot serving Matale District:
    Outlet: OUT096 (Fresh, Matale district, Kandy depot, Rear Dock).
    Vehicle: VEH039 (Reefer Truck at Kandy, km_per_l=5.0).
    """
    ref = real_reference_data
    outlet_matale = ref.outlets["OUT096"]
    assert outlet_matale.depot == "Kandy"
    assert outlet_matale.district == "Matale"

    raw_v39 = next(v for v in ref.vehicles if v.vehicle_id == "VEH039")
    v39_live = with_live_fleet_state(raw_v39, weekly_fuel_used_l=50.0, external_reservations_l=10.0)

    items = [LineItem("LI_M1", 20.0, "crates", 12.0, 0.08, "Matale Curd")]
    order = make_order_from_real_outlet(
        outlet_matale, "ORD_MATALE_001", units=20, weight_kg=240.0, volume_m3=1.6,
        temp=TempRequirement.CHILLED, line_items=items,
    )

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    plan = generate_daily_draft_plan(
        orders=[order],
        fleet=[v39_live],
        reference_data=ref,
        context=context,
    )

    assert plan["status"] in ("OPTIMAL", "FEASIBLE")
    assert plan["validation"]["valid"] is True
    trip = plan["trips"][0]
    assert trip["depot"] == "Kandy"
    assert trip["district"] == "Matale"
    # Matale travel: 26 km outbound, 26 km return = 52.0 km
    assert trip["fuel"]["distance_km"] == 52.0
    assert math.isclose(trip["fuel"]["fuel_consumed_l"], 52.0 / 5.0, rel_tol=1e-2)


# ==============================================================================
# 2. evaluate_edited_draft() Across Depots
# ==============================================================================

def test_real_data_evaluate_edited_draft_peliyagoda(real_reference_data: ReferenceData):
    """
    Peliyagoda Depot Draft Editing:
      - Base plan with OUT004 & OUT006 on VEH001.
      - Dispatcher defers ORD_P_002.
      - Confirms recalculation, validation, base plan immutability.
    """
    ref = real_reference_data
    outlet_004 = ref.outlets["OUT004"]
    outlet_006 = ref.outlets["OUT006"]

    raw_v1 = next(v for v in ref.vehicles if v.vehicle_id == "VEH001")
    v1_live = with_live_fleet_state(raw_v1, weekly_fuel_used_l=30.0, external_reservations_l=10.0)

    order_1 = make_order_from_real_outlet(
        outlet_004, "ORD_P_001", units=15, weight_kg=150.0, volume_m3=1.0,
        temp=TempRequirement.CHILLED,
        line_items=[LineItem("LI01", 15.0, "crates", 10.0, 1.0 / 15.0, "Item 1")],
    )
    order_2 = make_order_from_real_outlet(
        outlet_006, "ORD_P_002", units=20, weight_kg=200.0, volume_m3=1.5,
        temp=TempRequirement.CHILLED,
        line_items=[LineItem("LI02", 20.0, "crates", 10.0, 1.5 / 20.0, "Item 2")],
    )
    orders = [order_1, order_2]
    fleet = [v1_live]

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    base_plan = generate_daily_draft_plan(
        orders=orders,
        fleet=fleet,
        reference_data=ref,
        context=context,
    )
    assert base_plan["validation"]["valid"] is True
    base_plan_copy = copy.deepcopy(base_plan)

    edited = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[DeferWholeOrderAction(order_ref="ORD_P_002", reason="Outlet deferred")],
        authoritative_orders=orders,
        authoritative_fleet=fleet,
        reference_data=ref,
        operational_context=context,
    )

    assert edited.valid is True
    assert len(edited.violations) == 0
    assert "ORD_P_002" in [d["order_ref"] for d in edited.deferred_orders]
    assert len(edited.trips) == 1
    assert len(edited.trips[0]["driver_itinerary"]) == 1
    assert edited.trips[0]["driver_itinerary"][0]["outlet_id"] == "OUT004"
    assert base_plan == base_plan_copy


def test_real_data_evaluate_edited_draft_kandy(real_reference_data: ReferenceData):
    """
    Kandy Depot Draft Editing:
      - Base plan with OUT084 and OUT085 on VEH040.
      - Spare reefer truck VEH041 at Kandy.
      - Dispatcher moves ORD_K_002 to VEH041 trip 1.
      - Confirms recalculation, validation, base plan immutability.
    """
    ref = real_reference_data
    outlet_084 = ref.outlets["OUT084"]
    outlet_085 = ref.outlets["OUT085"]

    raw_v40 = next(v for v in ref.vehicles if v.vehicle_id == "VEH040")
    raw_v41 = next(v for v in ref.vehicles if v.vehicle_id == "VEH041")

    v40_live = with_live_fleet_state(raw_v40, weekly_fuel_used_l=30.0, external_reservations_l=10.0)
    v41_live = with_live_fleet_state(
        raw_v41,
        weekly_fuel_used_l=20.0,
        external_reservations_l=5.0,
        earliest_availability_iso="2026-10-03T05:00:00+05:30",
    )

    order_1 = make_order_from_real_outlet(
        outlet_085, "ORD_K_001", units=12, weight_kg=120.0, volume_m3=0.96,
        temp=TempRequirement.CHILLED,
        line_items=[LineItem("LI_K1", 12.0, "crates", 10.0, 0.08, "Item 1")],
    )
    order_2 = make_order_from_real_outlet(
        outlet_084, "ORD_K_002", units=15, weight_kg=150.0, volume_m3=1.2,
        temp=TempRequirement.CHILLED,
        line_items=[LineItem("LI_K2", 15.0, "crates", 10.0, 0.08, "Item 2")],
    )
    orders = [order_1, order_2]
    fleet = [v40_live, v41_live]

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    base_plan = generate_daily_draft_plan(
        orders=orders,
        fleet=fleet,
        reference_data=ref,
        context=context,
    )
    assert base_plan["validation"]["valid"] is True
    base_plan_copy = copy.deepcopy(base_plan)

    # Move order 2 to spare Kandy vehicle VEH041 trip 1
    move_action = MoveWholeOrderAction(
        order_ref="ORD_K_002",
        target_vehicle_id="VEH041",
        target_trip_number=1,
    )

    edited = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[move_action],
        authoritative_orders=orders,
        authoritative_fleet=fleet,
        reference_data=ref,
        operational_context=context,
    )

    assert edited.valid is True
    assert len(edited.violations) == 0
    assert len(edited.trips) == 2
    trip_vehicles = {t["vehicle_id"] for t in edited.trips}
    assert trip_vehicles == {"VEH040", "VEH041"}
    assert base_plan == base_plan_copy


# ==============================================================================
# 3. reallocate_broken_vehicle() Across Depots
# ==============================================================================

def test_real_data_reallocate_broken_vehicle_peliyagoda(real_reference_data: ReferenceData):
    """
    Peliyagoda Depot Breakdown Recovery:
      - Breakdown prior to departures.
      - Reallocates demand from broken VEH001 to spare real vehicle VEH002.
      - Confirms broken vehicle is excluded and quantities conserved.
    """
    ref = real_reference_data
    outlet_004 = ref.outlets["OUT004"]
    outlet_006 = ref.outlets["OUT006"]

    raw_v1 = next(v for v in ref.vehicles if v.vehicle_id == "VEH001")
    raw_v2 = next(v for v in ref.vehicles if v.vehicle_id == "VEH002")

    v1_live = with_live_fleet_state(raw_v1, weekly_fuel_used_l=40.0, external_reservations_l=10.0)
    v2_live = with_live_fleet_state(
        raw_v2,
        weekly_fuel_used_l=20.0,
        external_reservations_l=5.0,
        earliest_availability_iso="2026-10-03T04:30:00+05:30",
    )

    order_1 = make_order_from_real_outlet(
        outlet_004, "ORD_P_001", units=10, weight_kg=100.0, volume_m3=0.8,
        temp=TempRequirement.CHILLED,
        line_items=[LineItem("LI01", 10.0, "crates", 10.0, 0.08, "Item 1")],
    )
    order_2 = make_order_from_real_outlet(
        outlet_006, "ORD_P_002", units=20, weight_kg=250.0, volume_m3=1.6,
        temp=TempRequirement.CHILLED,
        line_items=[LineItem("LI02", 20.0, "crates", 12.5, 0.08, "Item 2")],
    )
    orders = [order_1, order_2]

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    base_plan = generate_daily_draft_plan(
        orders=orders,
        fleet=[v1_live],
        reference_data=ref,
        context=context,
    )
    assert base_plan["validation"]["valid"] is True

    current_time_iso = "2026-10-03T04:00:00+05:30"
    undelivered = [
        UndeliveredQuantity("ORD_P_001", "LI01", 10, "crates"),
        UndeliveredQuantity("ORD_P_002", "LI02", 20, "crates"),
    ]

    recovery = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="VEH001",
        undelivered_quantities=undelivered,
        available_fleet=[v1_live, v2_live],
        reference_data=ref,
        operational_context=context,
        current_time_iso=current_time_iso,
        authoritative_orders=orders,
        pickup_location="DEPOT",
    )

    assert recovery.valid is True, f"Violations: {recovery.violations}, missing: {recovery.missing_data}"
    assert recovery.is_dispatch_ready is False
    assert recovery["approval_status"] == "DRAFT_REQUIRES_DISPATCHER_APPROVAL"
    replacement_vids = [t["vehicle_id"] for t in recovery.replacement_trips]
    assert "VEH001" not in replacement_vids
    assert "VEH002" in replacement_vids

    reassigned_crates = sum(item["quantity"] for item in recovery.reassigned_quantities)
    assert reassigned_crates == 30.0


def test_real_data_reallocate_broken_vehicle_kandy(real_reference_data: ReferenceData):
    """
    Kandy Depot Breakdown Recovery:
      - Breakdown of Kandy reefer truck VEH040 prior to departure.
      - Reallocates demand to spare Kandy reefer truck VEH041.
      - Confirms broken vehicle is excluded and quantities conserved at Kandy depot.
    """
    ref = real_reference_data
    outlet_084 = ref.outlets["OUT084"]
    outlet_085 = ref.outlets["OUT085"]

    raw_v40 = next(v for v in ref.vehicles if v.vehicle_id == "VEH040")
    raw_v41 = next(v for v in ref.vehicles if v.vehicle_id == "VEH041")

    v40_live = with_live_fleet_state(raw_v40, weekly_fuel_used_l=30.0, external_reservations_l=10.0)
    v41_live = with_live_fleet_state(
        raw_v41,
        weekly_fuel_used_l=15.0,
        external_reservations_l=5.0,
        earliest_availability_iso="2026-10-03T04:30:00+05:30",
    )

    order_1 = make_order_from_real_outlet(
        outlet_085, "ORD_K_001", units=12, weight_kg=120.0, volume_m3=0.96,
        temp=TempRequirement.CHILLED,
        line_items=[LineItem("LI_K1", 12.0, "crates", 10.0, 0.08, "Item 1")],
    )
    order_2 = make_order_from_real_outlet(
        outlet_084, "ORD_K_002", units=15, weight_kg=150.0, volume_m3=1.2,
        temp=TempRequirement.CHILLED,
        line_items=[LineItem("LI_K2", 15.0, "crates", 10.0, 0.08, "Item 2")],
    )
    orders = [order_1, order_2]

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    base_plan = generate_daily_draft_plan(
        orders=orders,
        fleet=[v40_live],
        reference_data=ref,
        context=context,
    )
    assert base_plan["validation"]["valid"] is True

    current_time_iso = "2026-10-03T04:00:00+05:30"
    undelivered = [
        UndeliveredQuantity("ORD_K_001", "LI_K1", 12, "crates"),
        UndeliveredQuantity("ORD_K_002", "LI_K2", 15, "crates"),
    ]

    recovery = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="VEH040",
        undelivered_quantities=undelivered,
        available_fleet=[v40_live, v41_live],
        reference_data=ref,
        operational_context=context,
        current_time_iso=current_time_iso,
        authoritative_orders=orders,
        pickup_location="Kandy",  # Depot pickup using explicit depot name
    )

    assert recovery.valid is True, f"Violations: {recovery.violations}, missing: {recovery.missing_data}"
    assert recovery.is_dispatch_ready is False
    assert recovery["approval_status"] == "DRAFT_REQUIRES_DISPATCHER_APPROVAL"
    replacement_vids = [t["vehicle_id"] for t in recovery.replacement_trips]
    assert "VEH040" not in replacement_vids
    assert "VEH041" in replacement_vids

    reassigned_crates = sum(item["quantity"] for item in recovery.reassigned_quantities)
    assert reassigned_crates == 27.0


def test_real_data_reallocate_broken_vehicle_partial_delivery(real_reference_data: ReferenceData):
    """
    Workflow 3 (Partial Delivery):
      - Orders with line items served by real vehicle VEH001.
      - Partial delivery occurs (LI01 delivered, LI02 undelivered).
      - Undelivered quantity is reassigned to VEH002.
      - Conserves delivered (10) and undelivered (10) quantities.
      - Confirms recovery result is a draft requiring dispatcher approval.
    """
    ref = real_reference_data
    outlet_004 = ref.outlets["OUT004"]

    raw_v1 = next(v for v in ref.vehicles if v.vehicle_id == "VEH001")
    raw_v2 = next(v for v in ref.vehicles if v.vehicle_id == "VEH002")

    v1_live = with_live_fleet_state(raw_v1, weekly_fuel_used_l=40.0, external_reservations_l=10.0)
    v2_live = with_live_fleet_state(
        raw_v2,
        weekly_fuel_used_l=20.0,
        external_reservations_l=5.0,
        earliest_availability_iso="2026-10-03T06:00:00+05:30",
    )

    items = [
        LineItem("LI01_DELIV", 10.0, "crates", 10.0, 0.08, "Delivered Milk"),
        LineItem("LI02_REMAIN", 10.0, "crates", 10.0, 0.08, "Undelivered Yogurt"),
    ]
    order = make_order_from_real_outlet(
        outlet_004, "ORD_SPLIT_001", units=20, weight_kg=200.0, volume_m3=1.6,
        temp=TempRequirement.CHILLED, line_items=items,
    )

    context = OperationalContext(
        planning_date="2026-10-03",
        timezone="Asia/Colombo",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )

    base_plan = generate_daily_draft_plan(
        orders=[order],
        fleet=[v1_live],
        reference_data=ref,
        context=context,
    )
    assert base_plan["validation"]["valid"] is True

    # Breakdown happens at 06:15 (stop departure was 05:46, stop delivery completed for LI01_DELIV)
    current_time_iso = "2026-10-03T06:15:00+05:30"
    undelivered = [
        UndeliveredQuantity("ORD_SPLIT_001", "LI02_REMAIN", 10, "crates")
    ]

    recovery = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="VEH001",
        undelivered_quantities=undelivered,
        available_fleet=[v1_live, v2_live],
        reference_data=ref,
        operational_context=context,
        current_time_iso=current_time_iso,
        authoritative_orders=[order],
        pickup_location="DEPOT",
    )

    assert recovery.valid is True, f"Violations: {recovery.violations}, missing: {recovery.missing_data}"
    assert recovery.is_dispatch_ready is False
    assert recovery["approval_status"] == "DRAFT_REQUIRES_DISPATCHER_APPROVAL"

    delivered_crates = sum(item["quantity"] for item in recovery.delivered_quantities)
    reassigned_crates = sum(item["quantity"] for item in recovery.reassigned_quantities)
    assert delivered_crates == 10.0
    assert reassigned_crates == 10.0
    assert delivered_crates + reassigned_crates == 20.0


# ==============================================================================
# 4. Reference Coverage Tests
# ==============================================================================

def test_real_data_reference_coverage(real_reference_data: ReferenceData):
    """
    Workflow 4:
      - Confirms calendar.csv is loaded.
      - Confirms traffic_speed.csv is loaded.
      - Confirms road_conditions.csv is loaded.
      - Does not apply traffic or road multipliers unless dynamic travel policy is configured.
      - Confirms static policy uses supported district_travel.csv model.
    """
    ref = real_reference_data

    assert ref.calendar_rows is not None
    assert len(ref.calendar_rows) == 910
    assert ref.traffic_speed_rows is not None
    assert len(ref.traffic_speed_rows) == 576
    assert ref.road_conditions_rows is not None
    assert len(ref.road_conditions_rows) == 10920

    colombo_travel = next(t for t in ref.travel if t.district == "Colombo" and t.depot == "Peliyagoda")
    assert colombo_travel.depot_to_district_freeflow_min == 24.0
    assert colombo_travel.inter_stop_freeflow_min == 8.0
    assert colombo_travel.free_flow_kmh == 30.0

    travel_index = build_travel_index(ref.travel)
    allowance_index = build_allowance_index(ref.allowances)

    calc_outbound = outbound_minutes(colombo_travel)
    assert calc_outbound == 24.0

    calc_inter = inter_stop_minutes(colombo_travel, 2)
    assert calc_inter == 8.0

    sample_order = make_order_from_real_outlet(ref.outlets["OUT004"], "ORD_SAMPLE")
    calc_allowance = handling_minutes([sample_order], allowance_index)
    assert calc_allowance == 16.0

    context_static = OperationalContext(
        planning_date="2026-10-03",
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
    )
    assert context_static.travel_policy == TravelPolicy.STATIC_FREEFLOW
    assert context_static.speed_factor_fn is None


# ==============================================================================
# 5. Real-Data Validation Tests
# ==============================================================================

def test_real_data_multi_depot_validation(real_reference_data: ReferenceData):
    """
    Workflow 5:
      - Selects real outlets from different valid records.
      - Selects vehicles from both relevant depots (Peliyagoda and Kandy).
      - Verifies real brand, district, depot, dock, and parking combinations.
      - Verifies service allowances are looked up from service_allowance.csv.
      - Verifies travel is looked up from district_travel.csv.
      - Verifies fuel is calculated using authoritative vehicle km_per_l.
    """
    ref = real_reference_data

    outlet_peliyagoda = ref.outlets["OUT004"]
    outlet_kandy = ref.outlets["OUT084"]
    outlet_style_kandy = ref.outlets["OUT091"]

    assert outlet_peliyagoda.depot == "Peliyagoda"
    assert outlet_peliyagoda.district == "Colombo"
    assert outlet_peliyagoda.brand == Brand.FRESH

    assert outlet_kandy.depot == "Kandy"
    assert outlet_kandy.district == "Kandy"
    assert outlet_kandy.brand == Brand.FRESH
    assert outlet_kandy.dock_type == DockType.REAR_DOCK

    assert outlet_style_kandy.depot == "Kandy"
    assert outlet_style_kandy.brand == Brand.STYLE

    veh_peliyagoda = next(v for v in ref.vehicles if v.vehicle_id == "VEH001")
    veh_kandy = next(v for v in ref.vehicles if v.vehicle_id == "VEH040")

    assert veh_peliyagoda.depot == "Peliyagoda"
    assert veh_peliyagoda.km_per_l == 4.7
    assert veh_kandy.depot == "Kandy"
    assert veh_kandy.km_per_l == 4.7

    allowance_map = {(a.brand, a.dock_type): a.service_allowance_min for a in ref.allowances}
    assert allowance_map[(Brand.FRESH, DockType.REAR_DOCK)] == 15.0
    assert allowance_map[(Brand.FRESH, DockType.STREET)] == 16.0
    assert allowance_map[(Brand.FRESH, DockType.MALL_BAY)] == 18.0
    assert allowance_map[(Brand.STYLE, DockType.REAR_DOCK)] == 38.0
    assert allowance_map[(Brand.STYLE, DockType.STREET)] == 46.0
    assert allowance_map[(Brand.STYLE, DockType.MALL_BAY)] == 59.0
    assert allowance_map[(Brand.TECH, DockType.REAR_DOCK)] == 43.0
    assert allowance_map[(Brand.TECH, DockType.STREET)] == 55.0
    assert allowance_map[(Brand.TECH, DockType.MALL_BAY)] == 55.0

    travel_map = {(t.district, t.depot): t for t in ref.travel}
    colombo_dt = travel_map[("Colombo", "Peliyagoda")]
    assert colombo_dt.depot_to_district_km == 12.0
    assert colombo_dt.depot_to_district_freeflow_min == 24.0
    assert colombo_dt.inter_stop_km == 4.0
    assert colombo_dt.inter_stop_freeflow_min == 8.0

    kandy_dt = travel_map[("Kandy", "Kandy")]
    assert kandy_dt.depot_to_district_km == 8.0
    assert kandy_dt.depot_to_district_freeflow_min == 16.0
    assert kandy_dt.inter_stop_km == 3.0
    assert kandy_dt.inter_stop_freeflow_min == 6.0

    fuel_peliyagoda = 24.0 / veh_peliyagoda.km_per_l
    assert math.isclose(fuel_peliyagoda, 24.0 / 4.7, rel_tol=1e-5)

    veh_kandy_ambient = next(v for v in ref.vehicles if v.vehicle_id == "VEH044")
    assert veh_kandy_ambient.km_per_l == 6.8
    fuel_kandy = 20.0 / veh_kandy_ambient.km_per_l
    assert math.isclose(fuel_kandy, 20.0 / 6.8, rel_tol=1e-5)


# ==============================================================================
# 6. Real Reference Audit & Coverage Limitation Verification
# ==============================================================================

def test_real_data_reference_audit_and_coverage_report(real_reference_data: ReferenceData):
    """
    Audits the real reference dataset against production domain constraints:
      1. Confirms both Peliyagoda and Kandy depots are present.
      2. Asserts no unauthorized depots exist in reference CSVs.
      3. Verifies supported brands (Fresh, Style, Tech) and vehicle types (Truck, Van).
      4. Audits unavailable combinations:
         - No cross-district travel pairs in district_travel.csv
         - No Fresh brand outlets with mall_bay or mall_dock
         - No non-diesel vehicles
    """
    ref = real_reference_data

    # Depots
    outlet_depots = {o.depot for o in ref.outlets.values()}
    vehicle_depots = {v.depot for v in ref.vehicles}
    travel_depots = {t.depot for t in ref.travel}

    assert outlet_depots == {"Peliyagoda", "Kandy"}
    assert vehicle_depots == {"Peliyagoda", "Kandy"}
    assert travel_depots == {"Peliyagoda", "Kandy"}

    # Supported Districts
    peliyagoda_districts = {t.district for t in ref.travel if t.depot == "Peliyagoda"}
    kandy_districts = {t.district for t in ref.travel if t.depot == "Kandy"}

    assert peliyagoda_districts == {"Colombo", "Gampaha", "Kalutara", "Galle", "Matara", "Kurunegala", "Puttalam"}
    assert kandy_districts == {"Kandy", "Matale", "Nuwara Eliya", "Badulla", "Kegalle"}

    # Combinations UNAVAILABLE in the real CSV data:
    # 1. No other depots besides Peliyagoda and Kandy
    assert len(travel_depots) == 2

    # 2. No cross-district connections in district_travel.csv
    # Every district_travel row connects a single district to its home depot
    assert len(ref.travel) == 12

    # 3. No Fresh outlets with mall_bay or mall_dock
    fresh_outlets = [o for o in ref.outlets.values() if o.brand == Brand.FRESH]
    fresh_mall_bays = [o for o in fresh_outlets if o.dock_type == DockType.MALL_BAY]
    fresh_mall_docks = [o for o in fresh_outlets if o.parking_constraint == ParkingConstraint.MALL_DOCK]
    assert len(fresh_mall_bays) == 0, "Real CSV provides no Fresh outlets with mall_bay"
    assert len(fresh_mall_docks) == 0, "Real CSV provides no Fresh outlets with mall_dock"

    # 4. No electric or hybrid vehicles (all diesel in supplied CSV)
    fuel_types = {v.fuel_type for v in ref.vehicles if v.fuel_type}
    assert fuel_types == {"diesel"}, "Real CSV vehicles are all diesel"
