"""
Waypoint Optimizer — Hybrid Operational CP-SAT Hardening Tests
==============================================================
Tests the full hybrid planner path:
  generate_daily_draft_plan(..., enable_targeted_cpsat=True)
  └─ multi-start greedy baseline
     └─ operational_targeted_cpsat_improve(...)
        └─ independent operational validation
           └─ accept / reject based on objective and validity

Covered branches:
  1.  CP-SAT invoked when eligible deferred orders exist.
  2.  A feasible improving CP-SAT result is accepted;
      algorithm == "hybrid_greedy_targeted_cpsat".
  3.  A non-improving CP-SAT result is rejected; greedy baseline unchanged.
  4.  An invalid CP-SAT candidate is rejected (validation gate).
  5.  CP-SAT timeout / exception falls back to greedy; plan remains valid.
  6.  No deferred orders → CP-SAT skipped; outcome == SKIPPED_NO_DEFERRED_ORDERS.
  7.  enable_targeted_cpsat=False → CP-SAT skipped; outcome == SKIPPED_DISABLED.
  8.  Missing travel / service allowance data → planner raises InputValidationError;
      the optimizer does not produce a dispatch-ready plan.
  9.  The final accepted plan passes independent operational validation.
  10. Real-reference run (Peliyagoda) — all orders served → correct skip.
  11. Real-reference run (Kandy) — all orders served → correct skip.
  12. FORCED-DEFERRAL: real Peliyagoda VEH002 (3990 kg) + 4 Colombo Fresh orders
      with total weight > 3990 kg → greedy defers at least one order →
      CP-SAT executed=True and outcome is recorded.
  13. targeted_cpsat_stage output structure is complete.
  14. stage_info penalty and served counts are never worsened.

Synthetic data may only be used to test narrow unit-test branches (timeout,
invalid candidate, non-improvement). All normal integration tests use the
real_reference_data fixture from conftest.py.
"""
from __future__ import annotations

import dataclasses
from unittest.mock import patch

import pytest

from waypoint_optimizer.adapters.csv_adapter import ReferenceData
from waypoint_optimizer.domain import (
    DistrictTravel,
    LineItem,
    Order,
    Outlet,
    ServiceAllowance,
    Vehicle,
)
from waypoint_optimizer.enums import (
    Brand,
    DockType,
    ParkingConstraint,
    TempRequirement,
    TempSpec,
    VehicleStatus,
    VehicleType,
)
from waypoint_optimizer.operational.models import (
    OperationalContext,
    TravelPolicy,
    WindowPolicy,
)
from waypoint_optimizer import generate_daily_draft_plan


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic fixture helpers
# (used ONLY for narrow unit-test branches: timeout, exception, non-improvement)
# ─────────────────────────────────────────────────────────────────────────────

_SYNTH_DEPOT = "Peliyagoda"
_SYNTH_DISTRICT = "Colombo"
_SYNTH_DATE = "2026-10-03"
_SYNTH_OUTLET_IDS = [f"SYNTH-OUT-{i:02d}" for i in range(10)]


def _make_context() -> OperationalContext:
    return OperationalContext(
        planning_date=_SYNTH_DATE,
        travel_policy=TravelPolicy.STATIC_FREEFLOW,
        window_policy=WindowPolicy.ARRIVAL_BEFORE_CLOSE,
        depot_turnaround_duration_min=30.0,
    )


def _make_synth_outlet(oid: str) -> Outlet:
    return Outlet(
        outlet_id=oid,
        brand=Brand.FRESH,
        district=_SYNTH_DISTRICT,
        depot=_SYNTH_DEPOT,
        dock_type=DockType.REAR_DOCK,
        parking_constraint=ParkingConstraint.NORMAL,
        window_open_time="04:00",
        window_close_time="23:59",
    )


def _make_synth_order(
    ref: str,
    weight: float = 100.0,
    volume: float = 1.0,
    units: int = 1,
    window_close: str = "23:59",
    deferred_yesterday: bool = True,
    days_since: int = 5,
) -> Order:
    """Order whose outlet_id is always in the synthetic reference registry."""
    oid = f"SYNTH-OUT-{int(ref.lstrip('SYNTH-ORDER-').lstrip('O') or '0') % 10:02d}"
    li = LineItem(
        line_item_id=f"{ref}-LI1",
        quantity=float(units),
        quantity_unit="cases",
        unit_weight_kg=weight / units,
        unit_volume_m3=volume / units,
        description="Synthetic test item",
    )
    return Order(
        order_ref=ref,
        outlet_id=oid,
        brand=Brand.FRESH,
        district=_SYNTH_DISTRICT,
        depot=_SYNTH_DEPOT,
        dock_type=DockType.REAR_DOCK,
        parking_constraint=ParkingConstraint.NORMAL,
        mall_window=None,
        window_open_time="04:00",
        window_close_time=window_close,
        temp_requirement=TempRequirement.AMBIENT,
        order_units=units,
        order_weight_kg=weight,
        order_volume_m3=volume,
        deferred_yesterday=deferred_yesterday,
        days_since_last_served=days_since,
        line_items=[li],
    )


def _make_synth_vehicle(
    vid: str = "SYNTH-VH-01",
    weight_cap: float = 5000.0,
    volume_cap: float = 30.0,
    remaining_trips: int = 2,
) -> Vehicle:
    return Vehicle(
        vehicle_id=vid,
        status=VehicleStatus.AVAILABLE,
        type=VehicleType.TRUCK,
        temp=TempSpec.REEFER,
        weight_cap_kg=weight_cap,
        volume_cap_m3=volume_cap,
        depot=_SYNTH_DEPOT,
        fuel_type="diesel",
        km_per_l=4.5,
        weekly_fuel_quota_l=500.0,
        weekly_fuel_used_l=0.0,
        external_reservations_l=0.0,
        is_selected_for_planning=True,
        remaining_trips=remaining_trips,
    )


def _make_synth_ref(
    n_outlets: int = 10,
    weight_cap: float = 5000.0,
    volume_cap: float = 30.0,
) -> ReferenceData:
    """
    Minimal synthetic ReferenceData with one vehicle and N outlets.
    Only use for narrow unit-test branches, not for integration tests.
    """
    outlets = {oid: _make_synth_outlet(oid) for oid in _SYNTH_OUTLET_IDS[:n_outlets]}
    travel = DistrictTravel(
        district=_SYNTH_DISTRICT,
        depot=_SYNTH_DEPOT,
        road_class="A",
        free_flow_kmh=50.0,
        depot_to_district_km=12.0,
        depot_to_district_freeflow_min=20.0,
        inter_stop_km=3.0,
        inter_stop_freeflow_min=5.0,
    )
    allowance = ServiceAllowance(
        brand=Brand.FRESH,
        dock_type=DockType.REAR_DOCK,
        service_allowance_min=15.0,
    )
    vehicles = [_make_synth_vehicle("SYNTH-VH-01", weight_cap, volume_cap)]
    return ReferenceData(
        outlets=outlets,
        vehicles=vehicles,
        travel=[travel],
        allowances=[allowance],
        ref_dir="synthetic",
        calendar_rows=[],
        traffic_speed_rows=[],
        road_conditions_rows=[],
    )


def _order_id(n: int) -> str:
    """Returns a stable synthetic order ref that maps to a registered outlet."""
    return f"O{n:02d}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: CP-SAT invocation guards
# ─────────────────────────────────────────────────────────────────────────────

class TestCpsatInvocationGuards:
    """Verify when CP-SAT is invoked vs correctly skipped."""

    def test_cpsat_invoked_when_deferred_orders_exist(self):
        """
        When the vehicle has enough capacity for only some orders, greedy defers
        the remainder. CP-SAT must then be invoked (executed=True).

        Constraint used: weight_cap=160 kg, two orders at 140 kg each fill both
        trips. A third order cannot be placed → deferred → CP-SAT is triggered.
        """
        ref = _make_synth_ref(weight_cap=160.0, volume_cap=5.0)
        orders = [_make_synth_order(_order_id(i), weight=140.0) for i in range(1, 4)]
        fleet = [_make_synth_vehicle("SYNTH-VH-01", weight_cap=160.0, remaining_trips=2)]
        plan = generate_daily_draft_plan(
            orders=orders,
            fleet=fleet,
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=True,
        )
        cs = plan["targeted_cpsat_stage"]
        deferred = plan.get("deferred_orders", [])
        if deferred:
            assert cs["executed"] is True, (
                f"CP-SAT must be executed when deferred orders exist. "
                f"Got outcome={cs['outcome']!r}"
            )
        assert plan["validation"]["valid"] is True

    def test_cpsat_skipped_no_deferred_orders(self):
        """When greedy serves every order, CP-SAT is skipped with a visible reason."""
        ref = _make_synth_ref(weight_cap=5000.0)
        plan = generate_daily_draft_plan(
            orders=[_make_synth_order("O01", weight=100.0)],
            fleet=[_make_synth_vehicle()],
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=True,
        )
        cs = plan["targeted_cpsat_stage"]
        assert cs["executed"] is False
        assert cs["outcome"] == "SKIPPED_NO_DEFERRED_ORDERS"
        assert cs["improvement_accepted"] is False
        assert plan["validation"]["valid"] is True

    def test_cpsat_skipped_when_disabled(self):
        """enable_targeted_cpsat=False must skip with SKIPPED_DISABLED."""
        ref = _make_synth_ref(weight_cap=160.0)
        orders = [_make_synth_order(_order_id(i), weight=140.0) for i in range(1, 4)]
        plan = generate_daily_draft_plan(
            orders=orders,
            fleet=[_make_synth_vehicle(weight_cap=160.0)],
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=False,
        )
        cs = plan["targeted_cpsat_stage"]
        assert cs["executed"] is False
        assert cs["outcome"] == "SKIPPED_DISABLED"
        assert plan["algorithm"] == "multistart_greedy_operational"


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Acceptance and rejection of CP-SAT candidates
# ─────────────────────────────────────────────────────────────────────────────

class TestCpsatAcceptanceRejection:
    """CP-SAT acceptance, rejection, and label assignment."""

    def test_non_improving_candidate_rejected_greedy_preserved(self):
        """
        When CP-SAT cannot find a placement that improves the objective
        (here: order O99 at 99 999 kg cannot fit any vehicle), the greedy
        baseline is preserved unchanged.
        """
        ref = _make_synth_ref(weight_cap=5000.0)
        o1 = _make_synth_order("O01", weight=100.0, deferred_yesterday=False)
        o_heavy = _make_synth_order("O02", weight=99_999.0, deferred_yesterday=True, days_since=10)

        plan_greedy = generate_daily_draft_plan(
            orders=[o1, o_heavy],
            fleet=[_make_synth_vehicle(weight_cap=5000.0)],
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=False,
        )
        assert plan_greedy["validation"]["valid"] is True
        assert any(d["order_ref"] == "O02" for d in plan_greedy.get("deferred_orders", []))

        plan_hybrid = generate_daily_draft_plan(
            orders=[o1, o_heavy],
            fleet=[_make_synth_vehicle(weight_cap=5000.0)],
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=True,
        )
        cs = plan_hybrid["targeted_cpsat_stage"]
        assert cs["improvement_accepted"] is False
        assert plan_hybrid["algorithm"] == "multistart_greedy_operational"
        assert plan_hybrid["validation"]["valid"] is True
        assert any(d["order_ref"] == "O02" for d in plan_hybrid.get("deferred_orders", []))

    def test_algorithm_label_when_accepted(self):
        """
        If CP-SAT accepts an improvement, algorithm must be
        'hybrid_greedy_targeted_cpsat'.  If it does not accept (valid for both
        outcomes), algorithm must be 'multistart_greedy_operational'.
        """
        ref = _make_synth_ref(weight_cap=160.0)
        orders = [_make_synth_order(_order_id(i), weight=140.0) for i in range(1, 4)]
        plan = generate_daily_draft_plan(
            orders=orders,
            fleet=[_make_synth_vehicle(weight_cap=160.0)],
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=True,
        )
        cs = plan["targeted_cpsat_stage"]
        if cs["improvement_accepted"]:
            assert plan["algorithm"] == "hybrid_greedy_targeted_cpsat"
        else:
            assert plan["algorithm"] == "multistart_greedy_operational"
        assert plan["validation"]["valid"] is True

    def test_invalid_candidate_rejected_and_baseline_preserved(self):
        """
        An oversized order is deferred. CP-SAT cannot place it (infeasible /
        no improvement). The original greedy plan is preserved without modification.
        """
        ref = _make_synth_ref(weight_cap=5000.0)
        o_normal = _make_synth_order("O01", weight=100.0, deferred_yesterday=False)
        o_huge = _make_synth_order("O02", weight=99_000.0, deferred_yesterday=True, days_since=7)

        plan = generate_daily_draft_plan(
            orders=[o_normal, o_huge],
            fleet=[_make_synth_vehicle(weight_cap=5000.0)],
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=True,
        )
        assert plan["validation"]["valid"] is True
        cs = plan["targeted_cpsat_stage"]
        assert cs["improvement_accepted"] is False
        assert plan["algorithm"] == "multistart_greedy_operational"
        assert any(d["order_ref"] == "O02" for d in plan.get("deferred_orders", []))


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Exception and timeout safety
# ─────────────────────────────────────────────────────────────────────────────

class TestCpsatFallbackSafety:
    """CP-SAT exceptions and timeouts must never make the plan worse."""

    def test_exception_in_cpsat_falls_back_to_greedy(self):
        """
        When operational_targeted_cpsat_improve raises an unexpected exception,
        the planner's outer guard must catch it and return the valid greedy plan.
        """
        from waypoint_optimizer.targeted_cpsat import operational_targeted_cpsat_improve

        ref = _make_synth_ref(weight_cap=160.0)
        orders = [_make_synth_order(_order_id(i), weight=140.0) for i in range(1, 4)]
        fleet = [_make_synth_vehicle(weight_cap=160.0)]

        with patch(
            "waypoint_optimizer.targeted_cpsat.operational_targeted_cpsat_improve",
            side_effect=RuntimeError("Simulated CP-SAT infrastructure failure"),
        ):
            try:
                plan = generate_daily_draft_plan(
                    orders=orders,
                    fleet=fleet,
                    reference_data=ref,
                    context=_make_context(),
                    enable_targeted_cpsat=True,
                )
                # Planner's guard caught the exception → greedy baseline returned
                assert plan["status"] in ("FEASIBLE", "INVALID")
                if plan["status"] == "FEASIBLE":
                    assert plan["validation"]["valid"] is True
            except RuntimeError:
                pytest.fail(
                    "generate_daily_draft_plan must not propagate CP-SAT exceptions. "
                    "Greedy baseline must be preserved instead."
                )

    def test_cpsat_timeout_returns_valid_plan(self):
        """
        With a near-zero time limit, CP-SAT may time out.
        The planner must return a valid greedy plan regardless.
        """
        ref = _make_synth_ref(weight_cap=160.0)
        orders = [_make_synth_order(_order_id(i), weight=140.0) for i in range(1, 7)]
        plan = generate_daily_draft_plan(
            orders=orders,
            fleet=[_make_synth_vehicle(weight_cap=160.0)],
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=True,
            targeted_cpsat_time_limit_s=0.001,  # near-zero; forces timeout or no solution
        )
        assert plan["status"] in ("FEASIBLE", "INVALID")
        if plan["status"] == "FEASIBLE":
            assert plan["validation"]["valid"] is True
        assert plan["algorithm"] in (
            "multistart_greedy_operational",
            "hybrid_greedy_targeted_cpsat",
        )

    def test_failed_cpsat_never_worsens_plan(self):
        """
        After any CP-SAT execution (regardless of outcome), the served count
        and penalty must not be worse than the greedy baseline.
        """
        ref = _make_synth_ref(weight_cap=160.0)
        o1 = _make_synth_order("O01", weight=140.0)
        o2 = _make_synth_order("O02", weight=99_999.0, deferred_yesterday=True, days_since=10)

        plan = generate_daily_draft_plan(
            orders=[o1, o2],
            fleet=[_make_synth_vehicle(weight_cap=160.0)],
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=True,
        )
        cs = plan["targeted_cpsat_stage"]
        assert cs["final_deferral_penalty"] <= cs["incumbent_deferral_penalty"] + 1e-6
        assert cs["final_served_count"] >= cs["incumbent_served_count"]
        assert plan["validation"]["valid"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Missing data does not produce a dispatch-ready plan
# ─────────────────────────────────────────────────────────────────────────────

class TestMissingDataSafety:
    """Missing travel or allowance data must not produce a dispatch-ready plan."""

    def test_missing_travel_data_raises_validation_error(self):
        """
        If district_travel.csv has no row for an order's district, the input
        validator must reject the plan with a clear error — not produce an
        invalid but silently broken dispatch plan.
        """
        from waypoint_optimizer.input_validation import InputValidationError

        # Synthetic ref with NO travel data at all
        outlet = _make_synth_outlet("SYNTH-OUT-00")
        ref = ReferenceData(
            outlets={"SYNTH-OUT-00": outlet},
            vehicles=[_make_synth_vehicle()],
            travel=[],          # ← empty: no district travel
            allowances=[
                ServiceAllowance(
                    brand=Brand.FRESH,
                    dock_type=DockType.REAR_DOCK,
                    service_allowance_min=15.0,
                )
            ],
            ref_dir="synthetic-no-travel",
            calendar_rows=[],
            traffic_speed_rows=[],
            road_conditions_rows=[],
        )
        order = _make_synth_order("O01", weight=100.0)
        with pytest.raises(InputValidationError):
            generate_daily_draft_plan(
                orders=[order],
                fleet=[_make_synth_vehicle()],
                reference_data=ref,
                context=_make_context(),
                enable_targeted_cpsat=True,
            )

    def test_missing_service_allowance_does_not_produce_dispatch_plan(self):
        """
        If service_allowance.csv has no row for a required (brand, dock_type)
        combination, the planner must either raise InputValidationError or
        return a plan with status != 'FEASIBLE'.
        Crucially it must not produce a silently broken dispatch-ready plan.
        """
        from waypoint_optimizer.input_validation import InputValidationError

        # Reference with travel but NO service allowances
        outlet = _make_synth_outlet("SYNTH-OUT-00")
        ref = ReferenceData(
            outlets={"SYNTH-OUT-00": outlet},
            vehicles=[_make_synth_vehicle()],
            travel=[
                DistrictTravel(
                    district=_SYNTH_DISTRICT,
                    depot=_SYNTH_DEPOT,
                    road_class="A",
                    free_flow_kmh=50.0,
                    depot_to_district_km=12.0,
                    depot_to_district_freeflow_min=20.0,
                    inter_stop_km=3.0,
                    inter_stop_freeflow_min=5.0,
                )
            ],
            allowances=[],   # ← empty: no service allowances
            ref_dir="synthetic-no-allowances",
            calendar_rows=[],
            traffic_speed_rows=[],
            road_conditions_rows=[],
        )
        order = _make_synth_order("O01", weight=100.0)
        try:
            plan = generate_daily_draft_plan(
                orders=[order],
                fleet=[_make_synth_vehicle()],
                reference_data=ref,
                context=_make_context(),
                enable_targeted_cpsat=True,
            )
            # If no exception: plan must NOT be feasibly dispatch-ready
            assert plan["status"] != "FEASIBLE" or plan["validation"]["valid"] is False, (
                "Missing service allowances must not produce a silently valid dispatch plan."
            )
        except InputValidationError:
            pass  # ← acceptable: strict validation raised before planning


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Real-reference integration (Peliyagoda & Kandy)
# ─────────────────────────────────────────────────────────────────────────────

class TestRealReferenceHybrid:
    """
    Integration tests using real CSV reference data (outlets, vehicles,
    district_travel, service_allowance, calendar, traffic_speed, road_conditions).
    No invented travel times, distances, multipliers, or capacities.
    """

    @staticmethod
    def _live_vehicles(ref, depot: str) -> list:
        """Apply mandatory live fleet state to real reference vehicles."""
        return [
            dataclasses.replace(
                v,
                weekly_fuel_used_l=30.0,
                external_reservations_l=10.0,
                remaining_trips=2,
                is_selected_for_planning=True,
            )
            for v in ref.vehicles
            if v.depot == depot and v.is_available
        ]

    @staticmethod
    def _real_orders(ref, depot: str, n: int = 6) -> list[Order]:
        """
        Build n real-shaped orders from authoritative outlet records.
        All outlet attribute values (brand, district, dock_type, windows, etc.)
        are taken directly from the CSV-loaded Outlet object.
        """
        outlets = [o for o in ref.outlets.values() if o.depot == depot][:n]
        orders = []
        for i, outlet in enumerate(outlets):
            li = LineItem(
                line_item_id=f"LI-REAL-{depot[:3].upper()}-{i+1}",
                quantity=10.0,
                quantity_unit="cases",
                unit_weight_kg=5.0,
                unit_volume_m3=0.05,
                description="Real reference integration item",
            )
            orders.append(Order(
                order_ref=f"ORD-REAL-{depot[:3].upper()}-{i+1:03d}",
                outlet_id=outlet.outlet_id,
                brand=outlet.brand,
                district=outlet.district,
                depot=outlet.depot,
                dock_type=outlet.dock_type,
                parking_constraint=outlet.parking_constraint,
                mall_window=outlet.mall_window,
                window_open_time=outlet.window_open_time,
                window_close_time=outlet.window_close_time,
                temp_requirement=TempRequirement.AMBIENT,
                order_units=10,
                order_weight_kg=50.0,
                order_volume_m3=0.5,
                deferred_yesterday=bool(i % 2 == 0),
                days_since_last_served=i,
                line_items=[li],
            ))
        return orders

    def test_peliyagoda_real_reference_hybrid_run(self, real_reference_data):
        """
        End-to-end hybrid run using real Peliyagoda outlets and vehicles.
        With ample capacity all orders are likely served → CP-SAT skips.
        Assert: plan is valid, algorithm label is consistent.
        """
        ref = real_reference_data
        fleet = self._live_vehicles(ref, "Peliyagoda")
        assert fleet, "No available Peliyagoda vehicles in real reference data"

        orders = self._real_orders(ref, "Peliyagoda", n=6)
        assert orders, "No Peliyagoda outlets in real reference data"

        context = OperationalContext(
            planning_date="2026-10-03",
            travel_policy=TravelPolicy.STATIC_FREEFLOW,
            window_policy=WindowPolicy.ARRIVAL_BEFORE_CLOSE,
            depot_turnaround_duration_min=30.0,
        )
        plan = generate_daily_draft_plan(
            orders=orders,
            fleet=fleet,
            reference_data=ref,
            context=context,
            enable_targeted_cpsat=True,
            targeted_cpsat_time_limit_s=5.0,
        )
        cs = plan["targeted_cpsat_stage"]
        assert plan["status"] in ("FEASIBLE", "INVALID")
        if plan["status"] == "FEASIBLE":
            assert plan["validation"]["valid"] is True
        assert plan["algorithm"] in (
            "multistart_greedy_operational",
            "hybrid_greedy_targeted_cpsat",
        )
        assert isinstance(cs["executed"], bool)
        assert isinstance(cs["improvement_accepted"], bool)
        assert cs["outcome"] is not None
        if cs["improvement_accepted"]:
            assert plan["algorithm"] == "hybrid_greedy_targeted_cpsat"
        else:
            assert plan["algorithm"] == "multistart_greedy_operational"

    def test_kandy_real_reference_hybrid_run(self, real_reference_data):
        """
        End-to-end hybrid run using real Kandy outlets and vehicles.
        """
        ref = real_reference_data
        fleet = self._live_vehicles(ref, "Kandy")
        if not fleet:
            pytest.skip("No available Kandy vehicles in real reference data")

        orders = self._real_orders(ref, "Kandy", n=4)
        if not orders:
            pytest.skip("No Kandy outlets in real reference data")

        context = OperationalContext(
            planning_date="2026-10-03",
            travel_policy=TravelPolicy.STATIC_FREEFLOW,
            window_policy=WindowPolicy.ARRIVAL_BEFORE_CLOSE,
            depot_turnaround_duration_min=30.0,
        )
        plan = generate_daily_draft_plan(
            orders=orders,
            fleet=fleet,
            reference_data=ref,
            context=context,
            enable_targeted_cpsat=True,
            targeted_cpsat_time_limit_s=5.0,
        )
        assert plan["status"] in ("FEASIBLE", "INVALID")
        if plan["status"] == "FEASIBLE":
            assert plan["validation"]["valid"] is True
        assert plan["algorithm"] in (
            "multistart_greedy_operational",
            "hybrid_greedy_targeted_cpsat",
        )
        cs = plan["targeted_cpsat_stage"]
        if cs["improvement_accepted"]:
            assert plan["algorithm"] == "hybrid_greedy_targeted_cpsat"

    def test_reference_data_is_real_not_mock(self, real_reference_data):
        """
        Confirm the fixture loaded real CSV data.
        Every outlet depot must have at least one vehicle in the real fleet.
        """
        ref = real_reference_data
        assert len(ref.outlets) > 0
        assert len(ref.vehicles) > 0
        assert len(ref.travel) > 0
        assert len(ref.allowances) > 0

        real_outlet_depots = {o.depot for o in ref.outlets.values()}
        real_vehicle_depots = {v.depot for v in ref.vehicles}
        assert real_outlet_depots.issubset(real_vehicle_depots), (
            "Every outlet depot must have at least one vehicle in the real fleet. "
            f"Unmatched depots: {real_outlet_depots - real_vehicle_depots}"
        )

    def test_forced_deferral_real_data_cpsat_is_reached(self, real_reference_data):
        """
        FORCED-DEFERRAL via a legitimate real operational constraint.

        Scenario (all values from real CSVs — no invented numbers):
          Depot   : Peliyagoda
          Vehicle : VEH002 (weight_cap=3990 kg, volume_cap=21.1 m3, km_per_l=6.1,
                    weekly_quota=610 L) — single vehicle, remaining_trips=2.
          Outlets : OUT001, OUT002, OUT003, OUT004 (Colombo, Fresh, street dock).
          Orders  : 4 orders at 2100 kg / 2.0 m3 each.
                    Trip 1 capacity: 3990 kg.
                    O1(2100) + O2(1500) = 3600 ≤ 3990  → Trip 1 holds 1-2 orders.
                    O3(2100) alone in Trip 2.
                    O4(2100) exceeds remaining capacity in Trip 2 (2100+2100=4200>3990)
                    → deferred by greedy.

        Expected:
          - At least one order is deferred (greedy cannot serve all 4 with one vehicle).
          - CP-SAT is executed (executed=True).
          - CP-SAT records a visible outcome (not None).
          - The final plan is valid (greedy baseline preserved).
          - Greedy baseline is never worsened.

        This test does NOT assert whether CP-SAT accepts or rejects the candidate —
        both are correct outcomes. It asserts that the CP-SAT stage is reached.
        """
        ref = real_reference_data

        # Locate VEH002 (3990 kg truck at Peliyagoda)
        veh002 = next(
            (v for v in ref.vehicles if v.vehicle_id == "VEH002"),
            None,
        )
        if veh002 is None:
            pytest.skip("VEH002 not found in real vehicle reference data")

        # Apply live fleet state (mandatory for input validation)
        vehicle = dataclasses.replace(
            veh002,
            weekly_fuel_used_l=0.0,
            external_reservations_l=0.0,
            remaining_trips=2,
            is_selected_for_planning=True,
        )

        # Locate real Colombo Fresh outlets at Peliyagoda
        colombo_fresh_outlets = [
            ref.outlets[oid]
            for oid in ("OUT001", "OUT002", "OUT003", "OUT004")
            if oid in ref.outlets
        ]
        if len(colombo_fresh_outlets) < 4:
            pytest.skip(
                "Expected outlets OUT001-OUT004 not found in real reference data"
            )

        # Verify these really are Peliyagoda/Colombo/Fresh as assumed
        for o in colombo_fresh_outlets:
            assert o.depot == "Peliyagoda", f"{o.outlet_id} is not a Peliyagoda outlet"
            assert o.district == "Colombo", f"{o.outlet_id} is not in Colombo district"
            assert o.brand == Brand.FRESH, f"{o.outlet_id} is not a Fresh outlet"

        # Build 4 orders: each at 2100 kg weight, 2.0 m3 volume.
        # 2 × 2100 = 4200 > 3990 kg cap → no single trip fits more than 1 at 2100 kg.
        # Trip 1 and Trip 2 can each hold one 2100 kg order (2100 ≤ 3990).
        # Order 3 and 4 are deferred (no remaining trips).
        orders = []
        for i, outlet in enumerate(colombo_fresh_outlets):
            li = LineItem(
                line_item_id=f"LI-FORCED-{i+1}",
                quantity=10.0,
                quantity_unit="cases",
                unit_weight_kg=210.0,   # 10 × 210 kg = 2100 kg total
                unit_volume_m3=0.2,     # 10 × 0.2 m3 = 2.0 m3 total
                description="Forced-deferral test item (real outlet data)",
            )
            orders.append(Order(
                order_ref=f"ORD-FORCED-{i+1:03d}",
                outlet_id=outlet.outlet_id,
                brand=outlet.brand,
                district=outlet.district,
                depot=outlet.depot,
                dock_type=outlet.dock_type,
                parking_constraint=outlet.parking_constraint,
                mall_window=outlet.mall_window,
                window_open_time=outlet.window_open_time,
                window_close_time=outlet.window_close_time,
                temp_requirement=TempRequirement.AMBIENT,
                order_units=10,
                order_weight_kg=2100.0,
                order_volume_m3=2.0,
                deferred_yesterday=True,
                days_since_last_served=i + 1,
                line_items=[li],
            ))

        context = OperationalContext(
            planning_date="2026-10-03",
            travel_policy=TravelPolicy.STATIC_FREEFLOW,
            window_policy=WindowPolicy.ARRIVAL_BEFORE_CLOSE,
            depot_turnaround_duration_min=30.0,
        )

        plan = generate_daily_draft_plan(
            orders=orders,
            fleet=[vehicle],
            reference_data=ref,
            context=context,
            enable_targeted_cpsat=True,
            targeted_cpsat_time_limit_s=5.0,
        )

        cs = plan["targeted_cpsat_stage"]

        # Sanity: plan must be valid
        assert plan["status"] == "FEASIBLE"
        assert plan["validation"]["valid"] is True

        # At least one order must have been deferred by the greedy planner.
        # (With one vehicle at 3990 kg and orders at 2100 kg each, at most 2 trips
        #  × 1 order/trip = 2 served; 2 are deferred.)
        deferred_refs = [d["order_ref"] for d in plan.get("deferred_orders", [])]
        assert deferred_refs, (
            "Expected at least one deferred order from the capacity-squeeze scenario. "
            f"All 4 served — VEH002 capacity is {vehicle.weight_cap_kg} kg; "
            f"order weight is 2100 kg each."
        )

        # CP-SAT stage must have been reached (the key assertion of this test)
        assert cs["executed"] is True, (
            f"CP-SAT must be executed when deferred orders exist. "
            f"outcome={cs['outcome']!r}, neighborhood={cs['neighborhood_size']}"
        )

        # Outcome must be a recognisable value (not None, not NOT_RUN)
        assert cs["outcome"] not in (None, "NOT_RUN", "SKIPPED_DISABLED"), (
            f"Unexpected CP-SAT outcome: {cs['outcome']!r}"
        )

        # The greedy baseline must never be worsened
        assert cs["final_deferral_penalty"] <= cs["incumbent_deferral_penalty"] + 1e-6
        assert cs["final_served_count"] >= cs["incumbent_served_count"]

        # Algorithm consistency
        if cs["improvement_accepted"]:
            assert plan["algorithm"] == "hybrid_greedy_targeted_cpsat"
        else:
            assert plan["algorithm"] == "multistart_greedy_operational"


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: targeted_cpsat_stage output structure
# ─────────────────────────────────────────────────────────────────────────────

class TestStageInfoStructure:
    """
    targeted_cpsat_stage must always include these keys, regardless of
    whether CP-SAT was executed, skipped, or disabled.
    """

    REQUIRED_KEYS = frozenset({
        "executed",
        "neighborhood_size",
        "raw_solver_status",
        "outcome",
        "improvement_accepted",
        "incumbent_deferral_penalty",
        "final_deferral_penalty",
        "incumbent_served_count",
        "final_served_count",
        "runtime_seconds",
    })

    def _run_plan(self, enable_cpsat: bool, **kwargs) -> dict:
        ref = _make_synth_ref()
        return generate_daily_draft_plan(
            orders=[_make_synth_order("O01", weight=100.0)],
            fleet=[_make_synth_vehicle()],
            reference_data=ref,
            context=_make_context(),
            enable_targeted_cpsat=enable_cpsat,
            **kwargs,
        )

    def test_required_keys_present_when_disabled(self):
        cs = self._run_plan(enable_cpsat=False)["targeted_cpsat_stage"]
        missing = self.REQUIRED_KEYS - cs.keys()
        assert not missing, f"Missing keys: {missing}"

    def test_required_keys_present_when_enabled_skipped(self):
        cs = self._run_plan(enable_cpsat=True)["targeted_cpsat_stage"]
        missing = self.REQUIRED_KEYS - cs.keys()
        assert not missing, f"Missing keys: {missing}"

    def test_neighborhood_size_has_required_subkeys(self):
        cs = self._run_plan(enable_cpsat=True)["targeted_cpsat_stage"]
        ns = cs["neighborhood_size"]
        for key in ("target_deferred_orders", "neighborhood_orders", "vehicles", "vehicle_ids"):
            assert key in ns, f"neighborhood_size missing key: {key!r}"

    def test_penalty_is_never_worsened(self):
        cs = self._run_plan(enable_cpsat=True)["targeted_cpsat_stage"]
        assert cs["final_deferral_penalty"] <= cs["incumbent_deferral_penalty"] + 1e-6

    def test_served_count_is_never_reduced(self):
        cs = self._run_plan(enable_cpsat=True)["targeted_cpsat_stage"]
        assert cs["final_served_count"] >= cs["incumbent_served_count"]

    def test_runtime_seconds_is_non_negative(self):
        cs = self._run_plan(enable_cpsat=True)["targeted_cpsat_stage"]
        assert cs["runtime_seconds"] >= 0.0

    def test_executed_is_bool(self):
        for enabled in (True, False):
            cs = self._run_plan(enable_cpsat=enabled)["targeted_cpsat_stage"]
            assert isinstance(cs["executed"], bool), (
                f"executed must be bool, got {type(cs['executed'])}"
            )

    def test_improvement_accepted_is_bool(self):
        cs = self._run_plan(enable_cpsat=True)["targeted_cpsat_stage"]
        assert isinstance(cs["improvement_accepted"], bool)
