"""
Tests for the compatibility module.
Covers all official hard constraints (HC1–HC7) as pure function tests.
"""
import pytest
from waypoint_optimizer.domain import Order, Trip, Vehicle
from waypoint_optimizer.enums import (
    Brand, DockType, ParkingConstraint, TempRequirement,
    TempSpec, VehicleStatus, VehicleType,
)
from waypoint_optimizer.compatibility import (
    check_temperature_compatibility,
    check_access_compatibility,
    check_depot_compatibility,
    check_vehicle_available,
    is_vehicle_compatible,
    can_add_order_to_trip,
    can_open_new_trip,
)
from waypoint_optimizer.domain import DistrictTravel, ServiceAllowance
from waypoint_optimizer.trip_math import build_allowance_index, build_travel_index


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def depot() -> str:
    return "Peliyagoda"


@pytest.fixture
def travel_data(depot) -> list[DistrictTravel]:
    return [
        DistrictTravel(
            district="Colombo", depot=depot, road_class="A",
            free_flow_kmh=50.0, depot_to_district_km=12.0,
            depot_to_district_freeflow_min=24.0,
            inter_stop_km=3.0, inter_stop_freeflow_min=8.0,
        )
    ]


@pytest.fixture
def allowances() -> list[ServiceAllowance]:
    return [
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.REAR_DOCK, service_allowance_min=15.0),
        ServiceAllowance(brand=Brand.FRESH, dock_type=DockType.STREET, service_allowance_min=16.0),
        ServiceAllowance(brand=Brand.STYLE, dock_type=DockType.REAR_DOCK, service_allowance_min=20.0),
    ]


@pytest.fixture
def travel_index(travel_data) -> dict:
    return build_travel_index(travel_data)


@pytest.fixture
def allowance_index(allowances) -> dict:
    return build_allowance_index(allowances)


def make_order(
    ref: str = "O1",
    brand: Brand = Brand.FRESH,
    district: str = "Colombo",
    depot: str = "Peliyagoda",
    temp: TempRequirement = TempRequirement.AMBIENT,
    parking: ParkingConstraint = ParkingConstraint.NORMAL,
    weight: float = 100.0,
    volume: float = 1.0,
    dock: DockType = DockType.REAR_DOCK,
) -> Order:
    return Order(
        order_ref=ref, outlet_id="OUT001",
        brand=brand, district=district, depot=depot,
        dock_type=dock, parking_constraint=parking,
        mall_window=None, window_open_time=None, window_close_time=None,
        temp_requirement=temp, order_units=10,
        order_weight_kg=weight, order_volume_m3=volume,
        deferred_prev=False, defer_count=0, is_urgent=False,
    )


def make_vehicle(
    vid: str = "VH001",
    status: VehicleStatus = VehicleStatus.AVAILABLE,
    vtype: VehicleType = VehicleType.TRUCK,
    temp: TempSpec = TempSpec.AMBIENT,
    depot: str = "Peliyagoda",
    weight_cap: float = 5000.0,
    volume_cap: float = 30.0,
) -> Vehicle:
    return Vehicle(
        vehicle_id=vid, status=status, type=vtype, temp=temp,
        weight_cap_kg=weight_cap, volume_cap_m3=volume_cap, depot=depot,
    )


# ──────────────────────────────────────────────────────────────────────────────
# HC2: Temperature
# ──────────────────────────────────────────────────────────────────────────────

class TestTemperatureCompatibility:
    def test_chilled_ambient_vehicle_rejected(self):
        """HC2: chilled order + ambient vehicle → incompatible."""
        order = make_order(temp=TempRequirement.CHILLED)
        vehicle = make_vehicle(temp=TempSpec.AMBIENT)
        err = check_temperature_compatibility(order, vehicle)
        assert err is not None
        assert "chilled" in err.lower() or "reefer" in err.lower()

    def test_chilled_reefer_vehicle_accepted(self):
        """HC2: chilled order + reefer vehicle → compatible."""
        order = make_order(temp=TempRequirement.CHILLED)
        vehicle = make_vehicle(temp=TempSpec.REEFER)
        err = check_temperature_compatibility(order, vehicle)
        assert err is None

    def test_ambient_reefer_vehicle_accepted(self):
        """HC2: reefer vehicle MAY carry ambient orders."""
        order = make_order(temp=TempRequirement.AMBIENT)
        vehicle = make_vehicle(temp=TempSpec.REEFER)
        err = check_temperature_compatibility(order, vehicle)
        assert err is None

    def test_ambient_ambient_vehicle_accepted(self):
        """HC2: ambient order + ambient vehicle → compatible."""
        order = make_order(temp=TempRequirement.AMBIENT)
        vehicle = make_vehicle(temp=TempSpec.AMBIENT)
        err = check_temperature_compatibility(order, vehicle)
        assert err is None


# ──────────────────────────────────────────────────────────────────────────────
# HC3: Access / parking
# ──────────────────────────────────────────────────────────────────────────────

class TestAccessCompatibility:
    def test_van_only_truck_rejected(self):
        """HC3: van_only order + truck → incompatible."""
        order = make_order(parking=ParkingConstraint.VAN_ONLY)
        vehicle = make_vehicle(vtype=VehicleType.TRUCK)
        err = check_access_compatibility(order, vehicle)
        assert err is not None
        assert "van" in err.lower()

    def test_van_only_van_accepted(self):
        """HC3: van_only order + van → compatible."""
        order = make_order(parking=ParkingConstraint.VAN_ONLY)
        vehicle = make_vehicle(vtype=VehicleType.VAN)
        err = check_access_compatibility(order, vehicle)
        assert err is None

    def test_normal_truck_accepted(self):
        """HC3: normal parking + truck → compatible."""
        order = make_order(parking=ParkingConstraint.NORMAL)
        vehicle = make_vehicle(vtype=VehicleType.TRUCK)
        err = check_access_compatibility(order, vehicle)
        assert err is None

    def test_mall_dock_constraint_not_confused_with_dock_type(self):
        """
        HC3: parking_constraint=mall_dock is a different concept from dock_type=mall_bay.
        A truck with normal parking can handle a mall_dock order (parking constraint)
        — the parking_constraint=mall_dock does not require a van.
        """
        order = make_order(parking=ParkingConstraint.MALL_DOCK, dock=DockType.MALL_BAY)
        vehicle = make_vehicle(vtype=VehicleType.TRUCK)
        err = check_access_compatibility(order, vehicle)
        assert err is None  # mall_dock does NOT require van


# ──────────────────────────────────────────────────────────────────────────────
# HC4: Home depot
# ──────────────────────────────────────────────────────────────────────────────

class TestDepotCompatibility:
    def test_depot_mismatch_rejected(self):
        """HC4: order.depot != vehicle.depot → incompatible."""
        order = make_order(depot="Peliyagoda")
        vehicle = make_vehicle(depot="Kandy")
        err = check_depot_compatibility(order, vehicle)
        assert err is not None
        assert "depot" in err.lower()

    def test_depot_match_accepted(self):
        """HC4: same depot → compatible."""
        order = make_order(depot="Peliyagoda")
        vehicle = make_vehicle(depot="Peliyagoda")
        err = check_depot_compatibility(order, vehicle)
        assert err is None


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle availability
# ──────────────────────────────────────────────────────────────────────────────

class TestVehicleAvailability:
    def test_workshop_vehicle_rejected(self):
        """Vehicles in workshop must NEVER be allocated."""
        vehicle = make_vehicle(status=VehicleStatus.IN_WORKSHOP)
        err = check_vehicle_available(vehicle)
        assert err is not None
        assert "workshop" in err.lower()

    def test_available_vehicle_accepted(self):
        vehicle = make_vehicle(status=VehicleStatus.AVAILABLE)
        err = check_vehicle_available(vehicle)
        assert err is None


# ──────────────────────────────────────────────────────────────────────────────
# Combined is_vehicle_compatible
# ──────────────────────────────────────────────────────────────────────────────

class TestIsVehicleCompatible:
    def test_all_compatible(self):
        order = make_order()
        vehicle = make_vehicle()
        ok, reasons = is_vehicle_compatible(order, vehicle)
        assert ok
        assert reasons == []

    def test_multiple_violations_all_reported(self):
        """All incompatibility reasons should be returned, not just the first."""
        order = make_order(
            temp=TempRequirement.CHILLED,
            parking=ParkingConstraint.VAN_ONLY,
            depot="Peliyagoda",
        )
        vehicle = make_vehicle(
            status=VehicleStatus.AVAILABLE,
            temp=TempSpec.AMBIENT,   # violates HC2
            vtype=VehicleType.TRUCK,  # violates HC3
            depot="Kandy",           # violates HC4
        )
        ok, reasons = is_vehicle_compatible(order, vehicle)
        assert not ok
        assert len(reasons) >= 3  # all three violations should be reported


# ──────────────────────────────────────────────────────────────────────────────
# HC1: Brand + district mixing
# ──────────────────────────────────────────────────────────────────────────────

class TestBrandDistrictConsistency:
    def test_brand_mixing_rejected(self, travel_index, allowance_index):
        """HC1: cannot add Style order to Fresh trip."""
        vehicle = make_vehicle()
        fresh_trip = Trip(
            vehicle_id="VH001", trip_number=1,
            brand=Brand.FRESH, district="Colombo",
            orders=[make_order("O1", Brand.FRESH, "Colombo")],
        )
        style_order = make_order("O2", Brand.STYLE, "Colombo")
        can, reasons = can_add_order_to_trip(
            style_order, fresh_trip, vehicle, [fresh_trip], travel_index, allowance_index
        )
        assert not can
        assert any("brand" in r.lower() for r in reasons)

    def test_district_mixing_rejected(self, travel_index, allowance_index):
        """HC1: cannot mix districts within a trip."""
        vehicle = make_vehicle()
        trip = Trip(
            vehicle_id="VH001", trip_number=1,
            brand=Brand.FRESH, district="Colombo",
            orders=[make_order("O1", Brand.FRESH, "Colombo")],
        )
        gampaha_order = make_order("O2", Brand.FRESH, "Gampaha")
        can, reasons = can_add_order_to_trip(
            gampaha_order, trip, vehicle, [trip], travel_index, allowance_index
        )
        assert not can
        assert any("district" in r.lower() for r in reasons)


# ──────────────────────────────────────────────────────────────────────────────
# HC6: Weight and volume capacity
# ──────────────────────────────────────────────────────────────────────────────

class TestCapacityChecks:
    def test_overweight_trip_rejected(self, travel_index, allowance_index):
        """HC6a: exceeding weight capacity → rejected."""
        vehicle = make_vehicle(weight_cap=1000.0, volume_cap=50.0)
        trip = Trip(
            vehicle_id="VH001", trip_number=1,
            brand=Brand.FRESH, district="Colombo",
            orders=[make_order("O1", weight=800.0)],
        )
        heavy_order = make_order("O2", weight=500.0)  # would exceed 1000 cap
        can, reasons = can_add_order_to_trip(
            heavy_order, trip, vehicle, [trip], travel_index, allowance_index
        )
        assert not can
        assert any("weight" in r.lower() for r in reasons)

    def test_over_volume_trip_rejected(self, travel_index, allowance_index):
        """HC6b: exceeding volume capacity → rejected."""
        vehicle = make_vehicle(weight_cap=50000.0, volume_cap=5.0)
        trip = Trip(
            vehicle_id="VH001", trip_number=1,
            brand=Brand.FRESH, district="Colombo",
            orders=[make_order("O1", volume=4.0)],
        )
        bulky_order = make_order("O2", volume=2.0)  # would exceed 5.0 m³ cap
        can, reasons = can_add_order_to_trip(
            bulky_order, trip, vehicle, [trip], travel_index, allowance_index
        )
        assert not can
        assert any("volume" in r.lower() for r in reasons)

    def test_both_weight_and_volume_feasible(self, travel_index, allowance_index):
        """When both weight and volume fit, insertion should be allowed."""
        vehicle = make_vehicle(weight_cap=5000.0, volume_cap=30.0)
        trip = Trip(
            vehicle_id="VH001", trip_number=1,
            brand=Brand.FRESH, district="Colombo",
            orders=[make_order("O1", weight=100.0, volume=1.0)],
        )
        small_order = make_order("O2", weight=50.0, volume=0.5)
        can, _ = can_add_order_to_trip(
            small_order, trip, vehicle, [trip], travel_index, allowance_index
        )
        assert can


# ──────────────────────────────────────────────────────────────────────────────
# HC7: Max trips per vehicle
# ──────────────────────────────────────────────────────────────────────────────

class TestMaxTrips:
    def test_third_trip_rejected(self, travel_index, allowance_index):
        """HC7: vehicle with 2 trips cannot open a third."""
        vehicle = make_vehicle()
        existing = [
            Trip(vehicle_id="VH001", trip_number=1, brand=Brand.FRESH, district="Colombo",
                 orders=[make_order("O1")]),
            Trip(vehicle_id="VH001", trip_number=2, brand=Brand.STYLE, district="Colombo",
                 orders=[make_order("O2", Brand.STYLE)]),
        ]
        new_order = make_order("O3")
        can, reasons = can_open_new_trip(
            new_order, vehicle, existing, travel_index, allowance_index
        )
        assert not can
        assert any("trips" in r.lower() or "trip" in r.lower() for r in reasons)
