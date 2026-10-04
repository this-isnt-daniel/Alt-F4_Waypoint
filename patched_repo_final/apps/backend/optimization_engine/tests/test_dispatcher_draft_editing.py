"""
Tests for Dispatcher Draft Editing and Revalidation
===================================================
Covers the 10 required test scenarios:
  1. Moving a valid whole order
  2. Moving an order that violates capacity
  3. Moving an order that violates brand or district policy
  4. Deferring and reinstating an order
  5. Valid line-item split
  6. Rejected line-item action on an aggregated order
  7. Quantity conservation failure
  8. Edited trip with a delivery window violation
  9. Edited plan with fuel quota exhaustion
  10. Proof that the original base plan is unchanged
"""
import copy
import json
import pytest

from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, Outlet,
    ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleStatus, VehicleType,
)
from waypoint_optimizer.adapters.csv_adapter import ReferenceData
from waypoint_optimizer.hackathon_planner import generate_daily_draft_plan
from waypoint_optimizer.operational import (
    OperationalContext, TravelPolicy, WindowPolicy,
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


@pytest.fixture
def editing_references() -> ReferenceData:
    travel = [
        DistrictTravel(
            district="Colombo",
            depot="Peliyagoda",
            road_class="urban",
            free_flow_kmh=30.0,
            depot_to_district_km=15.0,
            depot_to_district_freeflow_min=30.0,
            inter_stop_km=5.0,
            inter_stop_freeflow_min=10.0,
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
        ServiceAllowance(Brand.FRESH, DockType.STREET, 15.0),
        ServiceAllowance(Brand.FRESH, DockType.REAR_DOCK, 20.0),
        ServiceAllowance(Brand.TECH, DockType.REAR_DOCK, 30.0),
        ServiceAllowance(Brand.STYLE, DockType.STREET, 25.0),
    ]
    outlets = {
        "OUT_COL_1": Outlet(
            outlet_id="OUT_COL_1",
            brand=Brand.FRESH,
            district="Colombo",
            depot="Peliyagoda",
            dock_type=DockType.STREET,
            parking_constraint=ParkingConstraint.NORMAL,
            window_open_time="05:00",
            window_close_time="09:00",
        ),
        "OUT_COL_2": Outlet(
            outlet_id="OUT_COL_2",
            brand=Brand.FRESH,
            district="Colombo",
            depot="Peliyagoda",
            dock_type=DockType.STREET,
            parking_constraint=ParkingConstraint.NORMAL,
            window_open_time="05:00",
            window_close_time="09:00",
        ),
        "OUT_COL_TIGHT": Outlet(
            outlet_id="OUT_COL_TIGHT",
            brand=Brand.FRESH,
            district="Colombo",
            depot="Peliyagoda",
            dock_type=DockType.STREET,
            parking_constraint=ParkingConstraint.NORMAL,
            window_open_time="05:00",
            window_close_time="05:15",  # Very tight: second stop arrives at 05:25, violating close!
        ),
        "OUT_GAM_TECH": Outlet(
            outlet_id="OUT_GAM_TECH",
            brand=Brand.TECH,
            district="Gampaha",
            depot="Peliyagoda",
            dock_type=DockType.REAR_DOCK,
            parking_constraint=ParkingConstraint.NORMAL,
            window_open_time="07:00",
            window_close_time="12:00",
        ),
    }
    vehicles = [
        Vehicle(
            vehicle_id="V_VAN_1",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=20.0,
            external_reservations_l=10.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="V_VAN_2",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=20.0,
            external_reservations_l=10.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="V_TINY",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=80.0,  # Tiny capacity: will fail on 100 kg order
            volume_cap_m3=0.5,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=20.0,
            external_reservations_l=10.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="V_TIGHT_FUEL",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=32.0,  # 30 km round trip consumes 6.0 L. 20 + 10 + 6 = 36 > 32 L quota!
            weekly_fuel_used_l=20.0,
            external_reservations_l=10.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
    ]
    return ReferenceData(
        outlets=outlets,
        vehicles=vehicles,
        travel=travel,
        allowances=allowances,
        ref_dir="mock_ref",
    )


def test_moving_valid_whole_order(editing_references):
    """
    Moving a valid whole order from one vehicle to another must succeed,
    recompute itineraries, track changed references, and pass validation.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    o2 = Order(
        order_ref="O2", outlet_id="OUT_COL_2", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )

    base_plan = generate_daily_draft_plan([o1, o2], [editing_references.vehicles[0]], editing_references, context)
    assert base_plan["validation"]["valid"]

    # Move O2 to V_VAN_2 Trip 1
    edit_action = MoveWholeOrderAction(order_ref="O2", target_vehicle_id="V_VAN_2", target_trip_number=1)
    edited_res = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[edit_action],
        authoritative_orders=[o1, o2],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert edited_res.valid
    assert not edited_res.is_dispatch_ready  # Draft requires approval
    assert "O2" in edited_res.changed_order_refs

    # Verify O2 is on V_VAN_2
    v2_trips = [t for t in edited_res.trips if t["vehicle_id"] == "V_VAN_2"]
    assert len(v2_trips) == 1
    v2_orders = [oref for stop in v2_trips[0]["driver_itinerary"] for oref in stop["order_refs"]]
    assert "O2" in v2_orders

    # Verify O1 remains on V_VAN_1
    v1_trips = [t for t in edited_res.trips if t["vehicle_id"] == "V_VAN_1"]
    assert len(v1_trips) == 1
    v1_orders = [oref for stop in v1_trips[0]["driver_itinerary"] for oref in stop["order_refs"]]
    assert "O1" in v1_orders
    assert "O2" not in v1_orders


def test_moving_order_violates_capacity(editing_references):
    """
    Moving an order to a vehicle with insufficient weight capacity must produce
    WEIGHT_OVERLOAD and valid=False.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O_HEAVY", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=120.0, order_volume_m3=1.0,  # 120 kg > V_TINY 80 kg cap
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    base_plan = generate_daily_draft_plan([o1], [editing_references.vehicles[0]], editing_references, context)

    # Move O_HEAVY to V_TINY (capacity = 80 kg)
    edit_action = MoveWholeOrderAction(order_ref="O_HEAVY", target_vehicle_id="V_TINY", target_trip_number=1)
    edited_res = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[edit_action],
        authoritative_orders=[o1],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert not edited_res.valid
    assert not edited_res.is_dispatch_ready
    rules = [v.rule for v in edited_res.violations]
    assert "WEIGHT_OVERLOAD" in rules


def test_moving_order_violates_brand_or_district_policy(editing_references):
    """
    Moving an order into a trip with a different brand or district violates homogeneity policy
    and must be rejected by independent validation.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o_fresh = Order(
        order_ref="O_FRESH", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    o_tech = Order(
        order_ref="O_TECH", outlet_id="OUT_GAM_TECH", brand=Brand.TECH, district="Gampaha", depot="Peliyagoda",
        dock_type=DockType.REAR_DOCK, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="07:00", window_close_time="12:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )

    # Start with base plan containing O_TECH on V_VAN_1
    base_plan = generate_daily_draft_plan([o_tech], [editing_references.vehicles[0]], editing_references, context)

    # Force O_FRESH (Fresh / Colombo) into the same trip as O_TECH (Tech / Gampaha)
    edit_action = MoveWholeOrderAction(order_ref="O_FRESH", target_vehicle_id="V_VAN_1", target_trip_number=1)
    edited_res = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[edit_action],
        authoritative_orders=[o_fresh, o_tech],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert not edited_res.valid
    rules = [v.rule for v in edited_res.violations]
    assert "MIXED_BRAND_TRIP" in rules or "MIXED_DISTRICT_TRIP" in rules


def test_deferring_and_reinstating_order(editing_references):
    """
    Deferring an assigned order moves it to deferred_orders with reason and detail.
    Reinstating moves it back to an assigned trip.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    base_plan = generate_daily_draft_plan([o1], [editing_references.vehicles[0]], editing_references, context)
    assert len(base_plan["trips"]) == 1

    # 1. Defer O1
    defer_action = DeferWholeOrderAction(order_ref="O1", reason="CLIENT_CANCELLED", detail="Client requested cancellation.")
    res_def = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[defer_action],
        authoritative_orders=[o1],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert res_def.valid
    assert len(res_def.trips) == 0  # Trip was emptied
    assert len(res_def.deferred_orders) == 1
    assert res_def.deferred_orders[0]["order_ref"] == "O1"
    assert res_def.deferred_orders[0]["reason"] == "CLIENT_CANCELLED"

    # 2. Reinstate O1 into V_VAN_2 Trip 1
    reinstate_action = ReinstateWholeOrderAction(order_ref="O1", target_vehicle_id="V_VAN_2", target_trip_number=1)
    res_reinstate = evaluate_edited_draft(
        base_plan=res_def,
        edit_actions=[reinstate_action],
        authoritative_orders=[o1],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert res_reinstate.valid
    assert len(res_reinstate.deferred_orders) == 0
    assert len(res_reinstate.trips) == 1
    assert res_reinstate.trips[0]["vehicle_id"] == "V_VAN_2"


def test_valid_line_item_split(editing_references):
    """
    Moving a discrete line item to another trip is permitted and conserves total demand.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o_split = Order(
        order_ref="O_SPLIT", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=15, order_weight_kg=150.0, order_volume_m3=1.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
        line_items=[
            LineItem(line_item_id="LI_1", quantity=10.0, quantity_unit="crates", unit_weight_kg=10.0, unit_volume_m3=0.1, description="Milk"),
            LineItem(line_item_id="LI_2", quantity=5.0, quantity_unit="crates", unit_weight_kg=10.0, unit_volume_m3=0.1, description="Cheese"),
        ],
    )

    base_plan = generate_daily_draft_plan([o_split], [editing_references.vehicles[0]], editing_references, context)
    assert base_plan["validation"]["valid"]

    # Move LI_2 to V_VAN_2 Trip 1
    split_action = MoveLineItemAction(
        order_ref="O_SPLIT",
        line_item_id="LI_2",
        quantity=5.0,
        target_vehicle_id="V_VAN_2",
        target_trip_number=1,
    )

    edited_res = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[split_action],
        authoritative_orders=[o_split],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert edited_res.valid
    assert len(edited_res.trips) == 2

    # Check V_VAN_1 has LI_1
    t1 = next(t for t in edited_res.trips if t["vehicle_id"] == "V_VAN_1")
    delivered_1 = [it["line_item_id"] for s in t1["driver_itinerary"] for it in s["line_items_delivered"]]
    assert delivered_1 == ["LI_1"]

    # Check V_VAN_2 has LI_2
    t2 = next(t for t in edited_res.trips if t["vehicle_id"] == "V_VAN_2")
    delivered_2 = [it["line_item_id"] for s in t2["driver_itinerary"] for it in s["line_items_delivered"]]
    assert delivered_2 == ["LI_2"]

    # Check exact unit conservation
    assert edited_res.quantity_totals_by_unit["crates"]["requested"] == 15.0
    assert edited_res.quantity_totals_by_unit["crates"]["assigned"] == 15.0
    assert edited_res.quantity_totals_by_unit["crates"]["deferred"] == 0.0


def test_rejected_line_item_action_on_aggregated_order(editing_references):
    """
    Attempting an item-level edit on an aggregated order without line items must be rejected
    with ITEM_LEVEL_EDITS_UNSUPPORTED.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o_agg = Order(
        order_ref="O_AGG", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
        line_items=None,  # Aggregated order!
    )
    base_plan = generate_daily_draft_plan([o_agg], [editing_references.vehicles[0]], editing_references, context)

    # Attempt line item action on aggregated order
    bad_action = MoveLineItemAction(
        order_ref="O_AGG",
        line_item_id="LI_FAKE",
        quantity=5.0,
        target_vehicle_id="V_VAN_2",
        target_trip_number=1,
    )
    edited_res = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[bad_action],
        authoritative_orders=[o_agg],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert not edited_res.valid
    rules = [v.rule for v in edited_res.violations]
    assert "ITEM_LEVEL_EDITS_UNSUPPORTED" in rules


def test_quantity_conservation_failure(editing_references):
    """
    An edit action corrupting or leaking quantity must fail quantity conservation.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=100.0, order_volume_m3=1.0,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    base_plan = generate_daily_draft_plan([o1], [editing_references.vehicles[0]], editing_references, context)

    # Corrupt action leaks quantity
    corrupt_action = {"action_type": "corrupt_quantity", "order_ref": "O1"}
    edited_res = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[corrupt_action],
        authoritative_orders=[o1],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert not edited_res.valid
    rules = [v.rule for v in edited_res.violations]
    assert "DEMAND_CONSERVATION_VIOLATION" in rules


def test_edited_trip_with_window_violation(editing_references):
    """
    Moving an order into a trip that causes arrival after window close must produce
    DELIVERY_WINDOW_VIOLATION.
    """
    context = OperationalContext(planning_date="2026-10-03", window_policy=WindowPolicy.ARRIVAL_BEFORE_CLOSE)
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    # OUT_COL_TIGHT closes at 05:35.
    # Departs 05:00 -> OUT_COL_1 arr 05:30, svc until 05:45 -> arr OUT_COL_TIGHT at 05:55 (> 05:35 close!)
    o_tight = Order(
        order_ref="O_TIGHT", outlet_id="OUT_COL_TIGHT", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="05:15", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    base_plan = generate_daily_draft_plan([o1, o_tight], [editing_references.vehicles[0]], editing_references, context)

    # Base plan deferred O_TIGHT due to window conflict. Dispatcher forces O_TIGHT into V_VAN_1 Trip 1
    force_action = MoveWholeOrderAction(order_ref="O_TIGHT", target_vehicle_id="V_VAN_1", target_trip_number=1)
    edited_res = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[force_action],
        authoritative_orders=[o1, o_tight],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert not edited_res.valid
    rules = [v.rule for v in edited_res.violations]
    assert "DELIVERY_WINDOW_VIOLATION" in rules


def test_edited_plan_with_fuel_quota_exhaustion(editing_references):
    """
    Moving an order to a vehicle whose fuel quota will be exceeded must produce
    FUEL_QUOTA_EXCEEDED.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    base_plan = generate_daily_draft_plan([o1], [editing_references.vehicles[0]], editing_references, context)

    # Move order to V_TIGHT_FUEL (weekly quota = 32 L, prior + res = 30 L, trip consumes 6.0 L -> 36 L > 32 L)
    fuel_action = MoveWholeOrderAction(order_ref="O1", target_vehicle_id="V_TIGHT_FUEL", target_trip_number=1)
    edited_res = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[fuel_action],
        authoritative_orders=[o1],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    assert not edited_res.valid
    rules = [v.rule for v in edited_res.violations]
    assert "FUEL_QUOTA_EXCEEDED" in rules


def test_proof_original_base_plan_is_unchanged(editing_references):
    """
    Proof of purity: The original base plan dictionary, trips, deferred orders,
    and authoritative inputs are strictly unmodified across multiple edits.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    o2 = Order(
        order_ref="O2", outlet_id="OUT_COL_2", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )

    base_plan = generate_daily_draft_plan([o1, o2], [editing_references.vehicles[0]], editing_references, context)

    # Snapshot of base_plan before edits
    base_plan_serialized_before = json.dumps(base_plan, sort_keys=True)
    o1_units_before = o1.order_units
    v0_fuel_before = editing_references.vehicles[0].weekly_fuel_used_l

    # Execute multiple edits (including invalid and deferral edits)
    evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[
            DeferWholeOrderAction(order_ref="O1"),
            MoveWholeOrderAction(order_ref="O2", target_vehicle_id="V_TINY", target_trip_number=1),
        ],
        authoritative_orders=[o1, o2],
        authoritative_fleet=editing_references.vehicles,
        reference_data=editing_references,
        operational_context=context,
    )

    # Verify base_plan is identical byte-for-byte
    base_plan_serialized_after = json.dumps(base_plan, sort_keys=True)
    assert base_plan_serialized_before == base_plan_serialized_after
    assert o1.order_units == o1_units_before
    assert editing_references.vehicles[0].weekly_fuel_used_l == v0_fuel_before


def test_missing_fuel_state_returns_invalid_and_preserves_none(editing_references):
    """
    Regression test:
    evaluate_edited_draft with missing live fleet fuel state
    (weekly_fuel_used_l or external_reservations_l is None) must return
    validation.valid=False, emit structured missing-data diagnostics,
    and NOT report missing fuel fields as numeric zero.
    """
    import dataclasses

    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_prev=False, defer_count=1, is_urgent=False,
    )
    # Generate a valid base plan with fully known fleet state
    base_plan = generate_daily_draft_plan([o1], [editing_references.vehicles[0]], editing_references, context)
    assert base_plan["validation"]["valid"]

    # Provide authoritative fleet where fuel state is missing (None)
    v_missing_fuel = dataclasses.replace(
        editing_references.vehicles[0],
        weekly_fuel_used_l=None,
        external_reservations_l=None,
    )
    fleet_missing = [v_missing_fuel]

    edited_resp = evaluate_edited_draft(
        base_plan=base_plan,
        edit_actions=[],
        authoritative_orders=[o1],
        authoritative_fleet=fleet_missing,
        reference_data=editing_references,
        operational_context=context,
    )

    # 1. Validation must fail and draft must not be dispatch-ready
    assert not edited_resp.valid
    assert edited_resp["validation"]["valid"] is False
    assert edited_resp["approval_status"] == "INVALID"
    assert edited_resp.is_dispatch_ready is False

    # 2. Must emit structured missing-data diagnostics for both fields
    missing_fields = [m["field"] for m in edited_resp["missing_data"]]
    assert "weekly_fuel_used_l" in missing_fields
    assert "external_reservations_l" in missing_fields

    # 3. Serialized output trips must preserve None and NOT report missing fuel as numeric 0.0
    assert len(edited_resp["trips"]) == 1
    fuel_info = edited_resp["trips"][0]["fuel"]
    assert fuel_info["prior_used_l"] is None
    assert fuel_info["prior_used_l"] != 0.0
    assert fuel_info["external_reservations_l"] is None
    assert fuel_info["external_reservations_l"] != 0.0
    assert fuel_info["cumulative_fuel_used_l"] is None
    assert fuel_info["fuel_compliant"] is False
