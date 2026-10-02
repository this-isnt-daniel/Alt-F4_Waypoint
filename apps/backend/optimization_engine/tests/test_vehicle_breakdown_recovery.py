"""
Tests for Vehicle Breakdown Recovery
====================================
Covers the 12 required test scenarios:
  1. One broken vehicle with all remaining stops reassigned
  2. Unaffected trips remaining unchanged
  3. Partial quantity already delivered
  4. Line-item quantity conservation
  5. Broken vehicle excluded from reassignment
  6. Vehicle capacity rejection
  7. Fuel quota rejection
  8. Vehicle unavailable at current time
  9. Unsupported roadside transfer
  10. Missing travel data
  11. Recovery plan never marked dispatch-ready
  12. Original active plan remaining unchanged
"""
import copy
import dataclasses
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
from waypoint_optimizer.operational.breakdown_recovery import (
    BreakdownRecoveryError,
    RecoveryDraftResponse,
    UndeliveredQuantity,
    reallocate_broken_vehicle,
)


# ==============================================================================
# SYNTHETIC UNIT-TEST FIXTURES (For Isolated Component Testing)
# ==============================================================================
# These synthetic fixtures provide controlled, deterministic domain models
# specifically for isolated unit tests of breakdown recovery edge cases.

@pytest.fixture
def recovery_references() -> ReferenceData:
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
        "OUT_COL_EARLY": Outlet(
            outlet_id="OUT_COL_EARLY",
            brand=Brand.FRESH,
            district="Colombo",
            depot="Peliyagoda",
            dock_type=DockType.STREET,
            parking_constraint=ParkingConstraint.NORMAL,
            window_open_time="05:00",
            window_close_time="08:00",
        ),
        "OUT_GAM_1": Outlet(
            outlet_id="OUT_GAM_1",
            brand=Brand.FRESH,
            district="Gampaha",
            depot="Peliyagoda",
            dock_type=DockType.STREET,
            parking_constraint=ParkingConstraint.NORMAL,
            window_open_time="06:00",
            window_close_time="11:00",
        ),
    }
    vehicles = [
        Vehicle(
            vehicle_id="V_BROKEN",
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
            vehicle_id="V_SPARE",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=10.0,
            external_reservations_l=5.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="V_OTHER",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=15.0,
            external_reservations_l=5.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="V_TINY",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=100.0,  # Only 100 kg!
            volume_cap_m3=0.8,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=10.0,
            external_reservations_l=5.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="V_LOW_FUEL",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=32.0,
            weekly_fuel_used_l=20.0,
            external_reservations_l=10.0,  # 30 L used out of 32 L quota -> only 2 L remaining!
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="V_LATE",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Peliyagoda",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=10.0,
            external_reservations_l=5.0,
            remaining_trips=2,
            earliest_availability_iso="2026-10-03T11:00:00+05:30",  # Unavailable until 11:00!
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


def test_one_broken_vehicle_all_remaining_stops_reassigned(recovery_references):
    """
    Scenario 1: One broken vehicle with all remaining stops reassigned.
    V_BROKEN breaks down at 07:30. Candidate vehicle V_SPARE takes over all undelivered stops.
    Plan is FEASIBLE, valid=True, is_dispatch_ready=False.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    o2 = Order(
        order_ref="O2", outlet_id="OUT_COL_2", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    fleet = [
        next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN"),
        next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE"),
    ]
    base_plan = generate_daily_draft_plan([o1, o2], [fleet[0]], recovery_references, context)
    assert base_plan["validation"]["valid"]

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
        {"order_ref": "O2", "line_item_id": "O2-ALL", "quantity": 5, "quantity_unit": "units"},
    ]

    recovery_resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=fleet,
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T06:30:00+05:30",
        authoritative_orders=[o1, o2],
    )

    assert recovery_resp.valid
    assert recovery_resp["validation"]["valid"] is True
    assert recovery_resp.is_dispatch_ready is False
    assert recovery_resp["approval_status"] == "DRAFT_REQUIRES_DISPATCHER_APPROVAL"
    assert len(recovery_resp.replacement_trips) == 1
    assert recovery_resp.replacement_trips[0]["vehicle_id"] == "V_SPARE"
    assert len(recovery_resp.reassigned_quantities) == 2
    assert len(recovery_resp.deferred_quantities) == 0


def test_unaffected_trips_remaining_unchanged(recovery_references):
    """
    Scenario 2: Unaffected trips remaining unchanged.
    V_OTHER is running an unaffected trip. When V_BROKEN fails, V_OTHER's trip
    is preserved byte-for-byte in frozen_trips.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    o_other = Order(
        order_ref="O_OTHER", outlet_id="OUT_GAM_1", brand=Brand.FRESH, district="Gampaha", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="06:00", window_close_time="11:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=4, order_weight_kg=40.0, order_volume_m3=0.4,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = dataclasses.replace(
        next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN"),
        remaining_trips=1,
    )
    v_other = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_OTHER")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")

    # Generate plan where V_BROKEN serves O1 and V_OTHER serves O_OTHER
    base_plan = generate_daily_draft_plan([o1, o_other], [v_broken, v_other], recovery_references, context)
    other_trip_before = next(t for t in base_plan["trips"] if t["vehicle_id"] == "V_OTHER")

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]

    recovery_resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_other, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T06:30:00+05:30",
        authoritative_orders=[o1, o_other],
    )

    assert recovery_resp.valid
    other_trip_after = next(t for t in recovery_resp.frozen_trips if t["vehicle_id"] == "V_OTHER")
    assert json.dumps(other_trip_before, sort_keys=True) == json.dumps(other_trip_after, sort_keys=True)


def test_partial_quantity_already_delivered(recovery_references):
    """
    Scenario 3: Partial quantity already delivered.
    V_BROKEN had 10 crates total. 4 crates of O1 were delivered before breakdown at 07:30.
    6 crates remain undelivered and are reassigned.
    Delivered (4) is recorded and undelivered (6) is reassigned.
    """
    context = OperationalContext(planning_date="2026-10-03")
    li1 = LineItem(line_item_id="LI-DELIV", quantity=4, quantity_unit="crates", unit_weight_kg=10.0, unit_volume_m3=0.1, description="Delivered Crates")
    li2 = LineItem(line_item_id="LI-UNDELIV", quantity=6, quantity_unit="crates", unit_weight_kg=10.0, unit_volume_m3=0.1, description="Remaining Crates")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=100.0, order_volume_m3=1.0,
        line_items=[li1, li2],
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")

    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    # 4 crates (LI-DELIV) were already delivered; 6 crates (LI-UNDELIV) remain undelivered on broken vehicle
    undelivered = [
        {"order_ref": "O1", "line_item_id": "LI-UNDELIV", "quantity": 6, "quantity_unit": "crates"},
    ]

    recovery_resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T06:30:00+05:30",
        authoritative_orders=[o1],
    )

    assert recovery_resp.valid
    assert len(recovery_resp.delivered_quantities) == 1
    assert recovery_resp.delivered_quantities[0]["quantity"] == 4.0

    assert len(recovery_resp.reassigned_quantities) == 1
    assert recovery_resp.reassigned_quantities[0]["quantity"] == 6.0
    assert recovery_resp.reassigned_quantities[0]["target_vehicle_id"] == "V_SPARE"


def test_line_item_quantity_conservation(recovery_references):
    """
    Scenario 4: Line-item quantity conservation.
    Enforces that delivered + reassigned + deferred strictly equals requested demand.
    Tampered / excess undelivered quantities are rejected.
    """
    context = OperationalContext(planning_date="2026-10-03")
    li1 = LineItem(line_item_id="LI-A", quantity=4, quantity_unit="crates", unit_weight_kg=10.0, unit_volume_m3=0.1, description="Crates A")
    li2 = LineItem(line_item_id="LI-B", quantity=6, quantity_unit="crates", unit_weight_kg=10.0, unit_volume_m3=0.1, description="Crates B")
    o_split = Order(
        order_ref="O_SPLIT", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=10, order_weight_kg=100.0, order_volume_m3=1.0,
        line_items=[li1, li2],
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")

    base_plan = generate_daily_draft_plan([o_split], [v_broken], recovery_references, context)

    # Valid undelivered quantities: LI-A = 4, LI-B = 6
    valid_undelivered = [
        {"order_ref": "O_SPLIT", "line_item_id": "LI-A", "quantity": 4, "quantity_unit": "crates"},
        {"order_ref": "O_SPLIT", "line_item_id": "LI-B", "quantity": 6, "quantity_unit": "crates"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=valid_undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o_split],
    )
    assert resp.valid
    tot_reassigned = sum(q["quantity"] for q in resp.reassigned_quantities)
    assert tot_reassigned == 10.0

    # Reject excess quantity (> planned 4 crates for LI-A)
    invalid_excess = [
        {"order_ref": "O_SPLIT", "line_item_id": "LI-A", "quantity": 99, "quantity_unit": "crates"},
    ]
    resp_excess = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=invalid_excess,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o_split],
    )
    assert not resp_excess.valid
    rules = [v.rule for v in resp_excess.violations]
    assert "EXCESS_UNDELIVERED_QUANTITY" in rules


def test_broken_vehicle_excluded_from_reassignment(recovery_references):
    """
    Scenario 5: Broken vehicle excluded from reassignment.
    The broken vehicle must never be selected to perform replacement trips.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")

    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o1],
    )
    assert resp.valid
    assert all(t["vehicle_id"] != "V_BROKEN" for t in resp.replacement_trips)


def test_vehicle_capacity_rejection(recovery_references):
    """
    Scenario 6: Vehicle capacity rejection.
    If the only candidate vehicle (V_TINY, 100 kg) cannot hold remaining cargo (500 kg),
    the order is deferred due to insufficient capacity.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o_heavy = Order(
        order_ref="O_HEAVY", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=50, order_weight_kg=500.0, order_volume_m3=3.0,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_tiny = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_TINY")

    base_plan = generate_daily_draft_plan([o_heavy], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O_HEAVY", "line_item_id": "O_HEAVY-ALL", "quantity": 50, "quantity_unit": "units"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_tiny],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o_heavy],
    )
    assert len(resp.replacement_trips) == 0
    assert len(resp.deferred_quantities) == 1
    assert resp.deferred_quantities[0]["reason"] == "INSUFFICIENT_FLEET_CAPACITY_AT_BREAKDOWN"


def test_fuel_quota_rejection(recovery_references):
    """
    Scenario 7: Fuel quota rejection.
    Candidate vehicle V_LOW_FUEL has only 2 L remaining weekly quota, but replacement trip
    requires ~6 L. Reallocation is rejected and order deferred.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_low_fuel = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_LOW_FUEL")

    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_low_fuel],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o1],
    )
    assert len(resp.replacement_trips) == 0
    assert len(resp.deferred_quantities) == 1


def test_vehicle_unavailable_at_current_time(recovery_references):
    """
    Scenario 8: Vehicle unavailable at current time.
    Candidate vehicle V_LATE earliest availability is 11:00. Outlet delivery window closes
    at 09:00. Candidate cannot deliver on time -> deferred.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o_early = Order(
        order_ref="O_EARLY", outlet_id="OUT_COL_EARLY", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="08:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_late = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_LATE")

    base_plan = generate_daily_draft_plan([o_early], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O_EARLY", "line_item_id": "O_EARLY-ALL", "quantity": 5, "quantity_unit": "units"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_late],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o_early],
    )
    assert len(resp.replacement_trips) == 0
    assert len(resp.deferred_quantities) == 1


def test_unsupported_roadside_transfer(recovery_references):
    """
    Scenario 9: Unsupported roadside transfer.
    Passing a roadside outlet pickup location without supported transfer travel returns
    UNSUPPORTED_TRANSFER_GEOMETRY and valid=False.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")

    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        pickup_location="OUT_COL_1",  # Roadside location!
        authoritative_orders=[o1],
    )

    assert not resp.valid
    assert resp.is_dispatch_ready is False
    rules = [v.rule for v in resp.violations]
    assert "UNSUPPORTED_TRANSFER_GEOMETRY" in rules


def test_missing_travel_data(recovery_references):
    """
    Scenario 10: Missing travel data.
    When travel reference data for target district is missing, emits structured
    missing-data diagnostic and valid=False.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")

    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    # Empty travel data
    ref_no_travel = dataclasses.replace(recovery_references, travel=[])

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=ref_no_travel,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o1],
    )

    assert not resp.valid
    assert len(resp.missing_data) > 0


def test_recovery_plan_never_marked_dispatch_ready(recovery_references):
    """
    Scenario 11: Recovery plan never marked dispatch-ready.
    Confirms is_dispatch_ready is False on both successful and rejected recovery attempts.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")

    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o1],
    )
    assert resp.is_dispatch_ready is False
    assert resp["is_dispatch_ready"] is False
    assert resp["validation"]["is_dispatch_ready"] is False


def test_original_active_plan_remaining_unchanged(recovery_references):
    """
    Scenario 12: Original active plan remaining unchanged.
    Proof of purity: active_plan is byte-for-byte identical before and after recovery.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")

    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)
    plan_json_before = json.dumps(base_plan, sort_keys=True)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]
    reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o1],
    )
    plan_json_after = json.dumps(base_plan, sort_keys=True)
    assert plan_json_before == plan_json_after


# ==============================================================================
# AUTHORITATIVE DATA VALIDATION & REJECTION TESTS
# ==============================================================================

def test_missing_or_empty_authoritative_orders(recovery_references):
    """
    Requirement 1: Make authoritative_orders mandatory for reallocate_broken_vehicle.
    If it is missing or empty, return:
    - status="INVALID"
    - validation.valid=False
    - structured missing-data diagnostic:
      field="authoritative_orders", entity_id="all", detail="Backend-confirmed orders are required for breakdown recovery."
    - no replacement trips.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")
    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]

    # Test with authoritative_orders=None
    resp_none = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=None,
    )
    assert not resp_none.valid
    assert resp_none["status"] == "INVALID"
    assert resp_none["approval_status"] == "INVALID"
    assert len(resp_none.replacement_trips) == 0
    assert any(
        m.field == "authoritative_orders" and m.entity_id == "all"
        for m in resp_none.missing_data
    )

    # Test with authoritative_orders=[]
    resp_empty = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[],
    )
    assert not resp_empty.valid
    assert resp_empty["status"] == "INVALID"
    assert resp_empty["approval_status"] == "INVALID"
    assert len(resp_empty.replacement_trips) == 0
    assert any(
        m.field == "authoritative_orders" and m.entity_id == "all"
        for m in resp_empty.missing_data
    )


def test_unknown_order_and_line_item_references_rejected(recovery_references):
    """
    Requirement 5: Validate that every undelivered order_ref and line_item_id exists
    in authoritative_orders. Reject unknown references.
    """
    context = OperationalContext(planning_date="2026-10-03")
    li1 = LineItem("LI-CONFIRMED", 5, "units", 10.0, 0.1, "Confirmed item")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        line_items=[li1], deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")
    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    # 1. Unknown order_ref
    resp_bad_oref = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=[
            {"order_ref": "UNKNOWN_ORDER", "line_item_id": "LI-CONFIRMED", "quantity": 5, "quantity_unit": "units"}
        ],
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o1],
    )
    assert not resp_bad_oref.valid
    assert any(v.rule == "UNKNOWN_ORDER_REF" for v in resp_bad_oref.violations)
    assert len(resp_bad_oref.replacement_trips) == 0

    # 2. Unknown line_item_id
    resp_bad_lid = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=[
            {"order_ref": "O1", "line_item_id": "UNKNOWN_LINE_ITEM", "quantity": 5, "quantity_unit": "units"}
        ],
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o1],
    )
    assert not resp_bad_lid.valid
    assert any(v.rule == "UNKNOWN_LINE_ITEM_ID" for v in resp_bad_lid.violations)
    assert len(resp_bad_lid.replacement_trips) == 0


def test_missing_required_attributes_emits_diagnostics_and_aborts_recovery(recovery_references):
    """
    Requirements 2 & 3:
    Remove every invented fallback value for:
    brand, district, depot, dock type, parking constraint, delivery windows,
    temperature requirement, unit weight, unit volume, service allowance.
    If any required order or outlet attribute is missing, return structured
    missing-data diagnostics and do not attempt recovery.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")
    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]

    # 1. Missing temp_requirement (No invented fallback)
    o_no_temp = dataclasses.replace(o1, temp_requirement=None)
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o_no_temp],
    )
    assert not resp.valid
    assert resp["status"] == "INVALID"
    assert len(resp.replacement_trips) == 0
    assert any(m.field == "temp_requirement" for m in resp.missing_data)

    # 2. Missing delivery windows (No invented fallback)
    o_no_win = dataclasses.replace(o1, window_open_time=None)
    # Also remove windows from outlet to verify no silent fallback
    outlets_no_win = dict(recovery_references.outlets)
    outlets_no_win["OUT_COL_1"] = dataclasses.replace(outlets_no_win["OUT_COL_1"], window_open_time=None)
    ref_no_win = dataclasses.replace(recovery_references, outlets=outlets_no_win)
    resp_win = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=ref_no_win,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o_no_win],
    )
    assert not resp_win.valid
    assert resp_win["status"] == "INVALID"
    assert len(resp_win.replacement_trips) == 0
    assert any(m.field == "delivery_windows" for m in resp_win.missing_data)

    # 3. Missing service allowance (No invented fallback)
    ref_no_allow = dataclasses.replace(recovery_references, allowances=[])
    resp_allow = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=ref_no_allow,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        authoritative_orders=[o1],
    )
    assert not resp_allow.valid
    assert resp_allow["status"] == "INVALID"
    assert len(resp_allow.replacement_trips) == 0
    assert any(m.field == "service_allowance" for m in resp_allow.missing_data)


# ==============================================================================
# REAL-DATA INTEGRATION TEST (Production Reference CSVs)
# ==============================================================================

def test_integration_real_reference_breakdown_recovery():
    """
    Requirement 6: Integration test that loads:
    - outlets.csv
    - vehicles.csv
    - district_travel.csv
    - service_allowance.csv
    from the real data directory, then creates small test orders using real
    outlet IDs and real district/depot combinations.
    """
    from pathlib import Path
    from waypoint_optimizer.adapters.csv_adapter import load_reference_data

    # Resolve real data directory from workspace layout
    repo_root = Path(__file__).resolve().parent.parent.parent
    real_data_dir = repo_root / "data"
    if not real_data_dir.exists():
        real_data_dir = Path("data")
    assert real_data_dir.exists(), f"Real data directory not found at {real_data_dir}"

    real_ref = load_reference_data(real_data_dir)
    assert len(real_ref.outlets) >= 100, "outlets.csv not loaded"
    assert len(real_ref.vehicles) >= 50, "vehicles.csv not loaded"
    assert len(real_ref.travel) >= 10, "district_travel.csv not loaded"
    assert len(real_ref.allowances) >= 8, "service_allowance.csv not loaded"

    # Select real outlets: OUT004 and OUT006 (Colombo, Peliyagoda, Fresh, Normal parking)
    out4 = real_ref.outlets["OUT004"]
    out6 = real_ref.outlets["OUT006"]

    li1 = LineItem("LI-OUT004-1", 10, "units", 5.0, 0.05, "Fresh Dairy Crate")
    li2 = LineItem("LI-OUT006-1", 10, "units", 5.0, 0.05, "Fresh Bakery Crate")

    o1 = Order(
        order_ref="ORD-REAL-1",
        outlet_id="OUT004",
        brand=out4.brand,
        district=out4.district,
        depot=out4.depot,
        dock_type=out4.dock_type,
        parking_constraint=out4.parking_constraint,
        mall_window=out4.mall_window,
        window_open_time=out4.window_open_time,
        window_close_time=out4.window_close_time,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=50.0,
        order_volume_m3=0.5,
        line_items=[li1],
        deferred_yesterday=False,
        days_since_last_served=1,
    )

    o2 = Order(
        order_ref="ORD-REAL-2",
        outlet_id="OUT006",
        brand=out6.brand,
        district=out6.district,
        depot=out6.depot,
        dock_type=out6.dock_type,
        parking_constraint=out6.parking_constraint,
        mall_window=out6.mall_window,
        window_open_time=out6.window_open_time,
        window_close_time=out6.window_close_time,
        temp_requirement=TempRequirement.CHILLED,
        order_units=10,
        order_weight_kg=50.0,
        order_volume_m3=0.5,
        line_items=[li2],
        deferred_yesterday=False,
        days_since_last_served=1,
    )

    # Configure real vehicles from vehicles.csv with live fleet state
    v1 = dataclasses.replace(
        real_ref.vehicles[0],
        vehicle_id="VEH001",
        status=VehicleStatus.AVAILABLE,
        is_selected_for_planning=True,
        weekly_fuel_used_l=50.0,
        external_reservations_l=10.0,
        remaining_trips=2,
    )
    v2 = dataclasses.replace(
        real_ref.vehicles[1],
        vehicle_id="VEH002",
        status=VehicleStatus.AVAILABLE,
        is_selected_for_planning=True,
        weekly_fuel_used_l=30.0,
        external_reservations_l=10.0,
        remaining_trips=2,
    )

    ctx = OperationalContext(planning_date="2026-10-03")
    base_plan = generate_daily_draft_plan([o1, o2], [v1], real_ref, ctx)
    assert base_plan["validation"]["valid"] is True
    assert len(base_plan["trips"]) == 1

    # Simulate breakdown at 06:00:00+05:30 with both stops undelivered
    undelivered = [
        {"order_ref": "ORD-REAL-1", "line_item_id": "LI-OUT004-1", "quantity": 10, "quantity_unit": "units"},
        {"order_ref": "ORD-REAL-2", "line_item_id": "LI-OUT006-1", "quantity": 10, "quantity_unit": "units"},
    ]

    recovery_resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="VEH001",
        undelivered_quantities=undelivered,
        available_fleet=[v1, v2],
        reference_data=real_ref,
        operational_context=ctx,
        current_time_iso="2026-10-03T06:00:00+05:30",
        authoritative_orders=[o1, o2],
    )

    assert recovery_resp.valid is True
    assert recovery_resp["status"] == "FEASIBLE"
    assert recovery_resp["approval_status"] == "DRAFT_REQUIRES_DISPATCHER_APPROVAL"
    assert recovery_resp.is_dispatch_ready is False
    assert len(recovery_resp.replacement_trips) == 1
    assert recovery_resp.replacement_trips[0]["vehicle_id"] == "VEH002"
    assert len(recovery_resp.reassigned_quantities) == 2
    assert len(recovery_resp.deferred_quantities) == 0
    assert len(recovery_resp.violations) == 0
    assert len(recovery_resp.missing_data) == 0


# ==============================================================================
# PICKUP LOCATION VALIDATION TESTS (DEPOT, Peliyagoda, Kandy, Roadside)
# ==============================================================================

def test_pickup_location_depot_keyword(recovery_references):
    """
    Test that pickup_location='DEPOT' is treated as a valid depot pickup.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")
    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T06:30:00+05:30",
        pickup_location="DEPOT",
        authoritative_orders=[o1],
    )
    assert resp.valid is True
    assert resp["status"] == "FEASIBLE"
    assert len(resp.replacement_trips) == 1
    assert not any(v.rule == "UNSUPPORTED_TRANSFER_GEOMETRY" for v in resp.violations)


def test_pickup_location_peliyagoda(recovery_references):
    """
    Test that pickup_location='Peliyagoda' (matching the vehicle/reference depot) is
    treated as a valid depot pickup, not an unsupported roadside outlet.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")
    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T06:30:00+05:30",
        pickup_location="Peliyagoda",
        authoritative_orders=[o1],
    )
    assert resp.valid is True
    assert resp["status"] == "FEASIBLE"
    assert len(resp.replacement_trips) == 1
    assert not any(v.rule == "UNSUPPORTED_TRANSFER_GEOMETRY" for v in resp.violations)


def test_pickup_location_kandy():
    """
    Test that pickup_location='Kandy' is recognized as a depot pickup when Kandy is an
    authoritative depot in the fleet and reference data, avoiding hardcoded Peliyagoda bias.
    """
    travel_kandy = [
        DistrictTravel(
            district="Kandy",
            depot="Kandy",
            road_class="urban",
            free_flow_kmh=30.0,
            depot_to_district_km=10.0,
            depot_to_district_freeflow_min=20.0,
            inter_stop_km=4.0,
            inter_stop_freeflow_min=8.0,
        ),
    ]
    allowances = [
        ServiceAllowance(Brand.FRESH, DockType.STREET, 15.0),
    ]
    outlets_kandy = {
        "OUT_KAN_1": Outlet(
            outlet_id="OUT_KAN_1",
            brand=Brand.FRESH,
            district="Kandy",
            depot="Kandy",
            dock_type=DockType.STREET,
            parking_constraint=ParkingConstraint.NORMAL,
            window_open_time="05:00",
            window_close_time="09:00",
        ),
    }
    vehicles_kandy = [
        Vehicle(
            vehicle_id="V_KAN_BROKEN",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Kandy",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=20.0,
            external_reservations_l=10.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
        Vehicle(
            vehicle_id="V_KAN_SPARE",
            status=VehicleStatus.AVAILABLE,
            type=VehicleType.VAN,
            temp=TempSpec.AMBIENT,
            weight_cap_kg=1500.0,
            volume_cap_m3=10.0,
            depot="Kandy",
            km_per_l=5.0,
            weekly_fuel_quota_l=250.0,
            weekly_fuel_used_l=10.0,
            external_reservations_l=5.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        ),
    ]
    ref_kandy = ReferenceData(
        outlets=outlets_kandy,
        vehicles=vehicles_kandy,
        travel=travel_kandy,
        allowances=allowances,
        ref_dir="mock_kandy",
    )
    context = OperationalContext(planning_date="2026-10-03")
    o_kan = Order(
        order_ref="O_KAN_1", outlet_id="OUT_KAN_1", brand=Brand.FRESH, district="Kandy", depot="Kandy",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )

    base_plan = generate_daily_draft_plan([o_kan], [vehicles_kandy[0]], ref_kandy, context)
    assert base_plan["validation"]["valid"] is True

    undelivered = [
        {"order_ref": "O_KAN_1", "line_item_id": "O_KAN_1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]

    # Reallocate with pickup_location="Kandy"
    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_KAN_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=vehicles_kandy,
        reference_data=ref_kandy,
        operational_context=context,
        current_time_iso="2026-10-03T06:30:00+05:30",
        pickup_location="Kandy",
        authoritative_orders=[o_kan],
    )
    assert resp.valid is True
    assert resp["status"] == "FEASIBLE"
    assert len(resp.replacement_trips) == 1
    assert resp.replacement_trips[0]["vehicle_id"] == "V_KAN_SPARE"
    assert resp.replacement_trips[0]["depot"] == "Kandy"
    assert not any(v.rule == "UNSUPPORTED_TRANSFER_GEOMETRY" for v in resp.violations)


def test_pickup_location_unsupported_roadside(recovery_references):
    """
    Test that an outlet/location identifier that is not an authoritative depot
    (e.g., 'OUT_COL_2') is treated as roadside and rejected with UNSUPPORTED_TRANSFER_GEOMETRY.
    """
    context = OperationalContext(planning_date="2026-10-03")
    o1 = Order(
        order_ref="O1", outlet_id="OUT_COL_1", brand=Brand.FRESH, district="Colombo", depot="Peliyagoda",
        dock_type=DockType.STREET, parking_constraint=ParkingConstraint.NORMAL, mall_window=None,
        window_open_time="05:00", window_close_time="09:00", temp_requirement=TempRequirement.AMBIENT,
        order_units=5, order_weight_kg=50.0, order_volume_m3=0.5,
        deferred_yesterday=False, days_since_last_served=1,
    )
    v_broken = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_BROKEN")
    v_spare = next(v for v in recovery_references.vehicles if v.vehicle_id == "V_SPARE")
    base_plan = generate_daily_draft_plan([o1], [v_broken], recovery_references, context)

    undelivered = [
        {"order_ref": "O1", "line_item_id": "O1-ALL", "quantity": 5, "quantity_unit": "units"},
    ]

    resp = reallocate_broken_vehicle(
        active_plan=base_plan,
        broken_vehicle_id="V_BROKEN",
        undelivered_quantities=undelivered,
        available_fleet=[v_broken, v_spare],
        reference_data=recovery_references,
        operational_context=context,
        current_time_iso="2026-10-03T07:30:00+05:30",
        pickup_location="OUT_COL_2",  # Roadside outlet identifier, not a depot
        authoritative_orders=[o1],
    )
    assert not resp.valid
    assert resp["status"] == "INVALID"
    assert any(v.rule == "UNSUPPORTED_TRANSFER_GEOMETRY" for v in resp.violations)
    assert any(r["code"] == "UNSUPPORTED_TRANSFER_GEOMETRY" for r in resp.recovery_reasons)
    assert len(resp.replacement_trips) == 0


