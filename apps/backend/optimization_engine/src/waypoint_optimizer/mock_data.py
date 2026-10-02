"""
Waypoint Optimizer — Synthetic Mock Data Generator
====================================================
Generates deterministic synthetic data for testing and benchmarking.

IMPORTANT: This data is NOT official competition data. All values are
synthetically generated for development and testing purposes only.

The generator produces:
  - Orders: Fresh/Style/Tech, various districts, brands, dock types, weights,
    volumes, chilled/ambient, van_only/normal constraints.
  - Vehicles: trucks/vans, reefer/ambient, various capacities,
    available/in_workshop status.
  - DistrictTravel: synthetic travel times and distances.
  - ServiceAllowances: synthetic handling times per (brand, dock_type).

Usage:
    from waypoint_optimizer.mock_data import generate_scenario
    orders, vehicles, travel, allowances = generate_scenario(n_orders=50, n_vehicles=10)
"""
from __future__ import annotations

import math
import random
from typing import Sequence

from waypoint_optimizer.config import OFFICIAL_DEPOT
from waypoint_optimizer.domain import (
    DistrictTravel, Order, ServiceAllowance, Vehicle,
)
from waypoint_optimizer.enums import (
    Brand, DockType, ParkingConstraint, TempRequirement,
    TempSpec, VehicleStatus, VehicleType,
)


# ──────────────────────────────────────────────────────────────────────────────
# Synthetic reference data (NOT official competition data)
# ──────────────────────────────────────────────────────────────────────────────

SYNTHETIC_DISTRICTS = [
    "Colombo", "Gampaha", "Kalutara", "Kandy", "Galle",
    "Matara", "Kurunegala", "Ratnapura", "Negombo", "Kegalle",
]

# Synthetic travel data: (district, outbound_min, inter_stop_min, outbound_km, inter_km)
# These are plausible but NOT real competition values.
_DISTRICT_TRAVEL_DATA = {
    "Colombo":    (24, 8, 12.0, 3.0),
    "Gampaha":    (37, 9, 37.0, 4.5),
    "Kalutara":   (55, 10, 60.0, 5.0),
    "Kandy":      (90, 12, 110.0, 6.0),
    "Galle":      (105, 11, 120.0, 5.5),
    "Matara":     (130, 12, 155.0, 6.0),
    "Kurunegala": (80, 11, 95.0, 5.5),
    "Ratnapura":  (100, 13, 115.0, 6.5),
    "Negombo":    (30, 8, 25.0, 4.0),
    "Kegalle":    (75, 11, 85.0, 5.0),
}

# Synthetic service allowances: (brand, dock_type) → minutes
# ASSUMPTION: Values are illustrative. Not official competition values.
_SERVICE_ALLOWANCES = [
    (Brand.FRESH, DockType.REAR_DOCK, 15.0),
    (Brand.FRESH, DockType.STREET,    16.0),
    (Brand.FRESH, DockType.MALL_BAY,  20.0),
    (Brand.STYLE, DockType.REAR_DOCK, 20.0),
    (Brand.STYLE, DockType.STREET,    22.0),
    (Brand.STYLE, DockType.MALL_BAY,  28.0),
    (Brand.TECH,  DockType.REAR_DOCK, 25.0),
    (Brand.TECH,  DockType.STREET,    27.0),
    (Brand.TECH,  DockType.MALL_BAY,  35.0),
]


def generate_travel_data(depot: str = OFFICIAL_DEPOT) -> list[DistrictTravel]:
    """
    Generate synthetic DistrictTravel records for all districts.

    ASSUMPTION: Road class, free-flow speed, and distance values are
    illustrative. They are NOT official competition data.
    """
    records = []
    for district, (out_min, inter_min, out_km, inter_km) in _DISTRICT_TRAVEL_DATA.items():
        records.append(DistrictTravel(
            district=district,
            depot=depot,
            road_class="A" if out_km < 50 else "B",
            free_flow_kmh=60.0,
            depot_to_district_km=float(out_km),
            depot_to_district_freeflow_min=float(out_min),
            inter_stop_km=float(inter_km),
            inter_stop_freeflow_min=float(inter_min),
        ))
    return records


def generate_service_allowances() -> list[ServiceAllowance]:
    """
    Generate synthetic ServiceAllowance records for all (brand, dock_type) pairs.

    ASSUMPTION: All values are illustrative. Not official competition data.
    """
    return [
        ServiceAllowance(brand=brand, dock_type=dock, service_allowance_min=minutes)
        for brand, dock, minutes in _SERVICE_ALLOWANCES
    ]


def generate_vehicles(
    n_vehicles: int = 10,
    depot: str = OFFICIAL_DEPOT,
    workshop_fraction: float = 0.15,
    reefer_fraction: float = 0.35,
    van_fraction: float = 0.40,
    seed: int = 42,
) -> list[Vehicle]:
    """
    Generate a synthetic fleet.

    Args:
        n_vehicles:        Number of vehicles to generate.
        depot:             Home depot for all vehicles.
        workshop_fraction: Fraction of vehicles in workshop (unavailable).
        reefer_fraction:   Fraction of vehicles with reefer capability.
        van_fraction:      Fraction of vehicles that are vans.
        seed:              Random seed for reproducibility.

    ASSUMPTION: Capacities and fuel profiles are synthetic. Not competition data.
    """
    rng = random.Random(seed)
    vehicles = []

    for i in range(n_vehicles):
        is_workshop = rng.random() < workshop_fraction
        is_reefer = rng.random() < reefer_fraction
        is_van = rng.random() < van_fraction

        # Vans have smaller capacities; trucks have larger
        if is_van:
            weight_cap = rng.uniform(800, 2000)
            volume_cap = rng.uniform(6, 15)
        else:
            weight_cap = rng.uniform(3000, 8000)
            volume_cap = rng.uniform(20, 50)

        v_id = f"VH{i+1:03d}"
        vehicles.append(Vehicle(
            vehicle_id=v_id,
            status=VehicleStatus.IN_WORKSHOP if is_workshop else VehicleStatus.AVAILABLE,
            type=VehicleType.VAN if is_van else VehicleType.TRUCK,
            temp=TempSpec.REEFER if is_reefer else TempSpec.AMBIENT,
            weight_cap_kg=round(weight_cap, 1),
            volume_cap_m3=round(volume_cap, 2),
            depot=depot,
            fuel_type="diesel",
            km_per_l=rng.uniform(6.0, 12.0),
            weekly_fuel_quota_l=rng.uniform(200, 500),
            weekly_fuel_used_l=rng.uniform(0, 150),
        ))

    return vehicles


def generate_orders(
    n_orders: int = 50,
    depot: str = OFFICIAL_DEPOT,
    chilled_fraction: float = 0.20,
    van_only_fraction: float = 0.15,
    mall_fraction: float = 0.10,
    deferred_yesterday_fraction: float = 0.12,
    seed: int = 42,
) -> list[Order]:
    """
    Generate synthetic orders across all brands, districts, and constraint types.

    Args:
        n_orders:                  Number of orders to generate.
        depot:                     Depot for all orders.
        chilled_fraction:          Fraction of orders requiring chilled transport.
        van_only_fraction:         Fraction of orders with van_only parking.
        mall_fraction:             Fraction of orders with mall bay dock/mall_dock parking.
        deferred_yesterday_fraction: Fraction of orders deferred from yesterday.
        seed:                      Random seed.

    ASSUMPTION: Weight/volume distributions, dock type mix, and all other
    values are synthetic. Not official competition data.
    """
    rng = random.Random(seed)

    brand_weights = {Brand.FRESH: 0.45, Brand.STYLE: 0.35, Brand.TECH: 0.20}
    brands = list(brand_weights.keys())
    brand_probs = list(brand_weights.values())

    orders = []
    for i in range(n_orders):
        brand = rng.choices(brands, weights=brand_probs)[0]
        district = rng.choice(SYNTHETIC_DISTRICTS)

        # Temp requirement: Fresh often chilled, Style/Tech rarely
        if brand == Brand.FRESH:
            is_chilled = rng.random() < chilled_fraction * 1.5
        else:
            is_chilled = rng.random() < chilled_fraction * 0.3

        # Parking constraint
        rand_p = rng.random()
        if rand_p < van_only_fraction:
            parking = ParkingConstraint.VAN_ONLY
        elif rand_p < van_only_fraction + mall_fraction:
            parking = ParkingConstraint.MALL_DOCK
        else:
            parking = ParkingConstraint.NORMAL

        # Dock type (independent of parking constraint)
        rand_d = rng.random()
        if rand_d < 0.50:
            dock = DockType.REAR_DOCK
        elif rand_d < 0.80:
            dock = DockType.STREET
        else:
            dock = DockType.MALL_BAY

        # Mall window (only for mall_bay dock types)
        mall_window = None
        win_open = None
        win_close = None
        if dock == DockType.MALL_BAY:
            hour_open = rng.choice([7, 8, 9])
            hour_close = hour_open + rng.randint(2, 4)
            win_open = f"{hour_open:02d}:00"
            win_close = f"{hour_close:02d}:00"
            mall_window = f"{win_open}-{win_close}"

        # Weight and volume by brand
        if brand == Brand.FRESH:
            weight = rng.uniform(30, 500)
            volume = rng.uniform(0.1, 4.0)
        elif brand == Brand.STYLE:
            weight = rng.uniform(50, 800)
            volume = rng.uniform(0.5, 8.0)
        else:  # TECH
            weight = rng.uniform(100, 1500)
            volume = rng.uniform(0.3, 5.0)

        # Repeat-deferral signals
        was_deferred = rng.random() < deferred_yesterday_fraction
        days_since = rng.randint(0, 14) if not was_deferred else rng.randint(1, 5)

        outlet_id = f"OUT{rng.randint(100, 999)}"
        order_ref = f"ORD{i+1:04d}"

        orders.append(Order(
            order_ref=order_ref,
            outlet_id=outlet_id,
            brand=brand,
            district=district,
            depot=depot,
            dock_type=dock,
            parking_constraint=parking,
            mall_window=mall_window,
            window_open_time=win_open,
            window_close_time=win_close,
            temp_requirement=TempRequirement.CHILLED if is_chilled else TempRequirement.AMBIENT,
            order_units=rng.randint(1, 50),
            order_weight_kg=round(weight, 1),
            order_volume_m3=round(volume, 3),
            deferred_yesterday=was_deferred,
            days_since_last_served=days_since,
        ))

    return orders


def generate_scenario(
    n_orders: int = 50,
    n_vehicles: int = 10,
    depot: str = OFFICIAL_DEPOT,
    seed: int = 42,
) -> tuple[list[Order], list[Vehicle], list[DistrictTravel], list[ServiceAllowance]]:
    """
    Generate a complete synthetic scenario for testing or benchmarking.

    Returns:
        (orders, vehicles, travel_data, service_allowances)

    All data is synthetic and NOT official competition data.
    Same seed + same inputs always produce the same output.

    Args:
        n_orders:   Number of orders to generate.
        n_vehicles: Number of vehicles to generate.
        depot:      Depot for all entities.
        seed:       Random seed for reproducibility.
    """
    orders = generate_orders(n_orders=n_orders, depot=depot, seed=seed)
    vehicles = generate_vehicles(n_vehicles=n_vehicles, depot=depot, seed=seed + 1)
    travel = generate_travel_data(depot=depot)
    allowances = generate_service_allowances()

    return orders, vehicles, travel, allowances
