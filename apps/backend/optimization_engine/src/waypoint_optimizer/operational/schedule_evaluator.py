"""
Waypoint Optimizer — Pure Schedule Evaluator (Hackathon H1)
===========================================================
Calculates deterministic stop-by-stop timelines, delivery window compliance,
inter-stop travel, depot return arrival, vehicle next-availability times,
and cumulative fuel quotas.

Guarantees:
  - Completely pure and side-effect free: no database calls, no network, no mutations.
  - Timezone-aware ISO-8601 formatting using ZoneInfo.
  - Distinguishes physical stop visits from order counts.
  - Supports configurable window semantics (arrival, service start, service completion).
  - Explicitly flags district-average travel as an estimation model.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo

from waypoint_optimizer.domain import (
    Brand, DistrictTravel, DockType, LineItem, Order, Outlet,
    ParkingConstraint, ServiceAllowance, TempRequirement, TempSpec,
    Vehicle, VehicleType,
)
from waypoint_optimizer.input_validation import InputValidationError
from waypoint_optimizer.operational.models import (
    DEFAULT_FRESH_DEPARTURE_TIME, DEFAULT_STYLE_TECH_DEPARTURE_TIME,
    DEFAULT_TIMEZONE, ESTIMATED_DEPOT_TURNAROUND_MIN, FRESH_DEADLINE_TIME,
    REFERENCE_DATA_MAX_DATE, REFERENCE_DATA_MIN_DATE,
    EvaluatedTripSchedule, OperationalContext, OperationalMissingData,
    OperationalStop, OperationalViolation, TravelPolicy, WindowPolicy,
)


def parse_iso_or_time_str(
    time_val: Optional[str],
    date_str: str,
    tz_str: str = DEFAULT_TIMEZONE,
) -> Optional[datetime]:
    """
    Parse a time string into a timezone-aware datetime.

    Accepts:
      - Full ISO-8601 string: '2026-10-03T04:00:00+05:30'
      - Time string 'HH:MM' or 'HH:MM:SS': combined with date_str in timezone tz_str.
    """
    if not time_val or not time_val.strip():
        return None
    val = time_val.strip()
    tz = ZoneInfo(tz_str)

    # 1. Try ISO datetime with optional timezone
    try:
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tz)
        return dt.astimezone(tz)
    except ValueError:
        pass

    # 2. Try parsing HH:MM or HH:MM:SS
    parts = val.split(":")
    if len(parts) >= 2:
        try:
            h = int(parts[0])
            m = int(parts[1])
            s = int(parts[2]) if len(parts) > 2 else 0
            d_parts = [int(p) for p in date_str.split("-")]
            return datetime(d_parts[0], d_parts[1], d_parts[2], h, m, s, tzinfo=tz)
        except (ValueError, IndexError):
            pass

    return None


def consolidate_orders_to_stops(
    orders: list[Order],
    outlets: dict[str, Outlet],
    allowances: dict[tuple[Brand, DockType], float],
    stop_sequence: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """
    Consolidate orders into physical outlet stop visits.

    Physical stop visit rule:
      Multiple orders delivered to the same outlet are handled during a single
      docking/unloading visit.
      Handling allowance is determined by (brand, outlet.dock_type).

    Stop ordering:
      Preserved according to explicit stop_sequence if provided;
      otherwise according to first order appearance in the list.
    """
    # Group orders by outlet_id
    orders_by_outlet: dict[str, list[Order]] = {}
    outlet_order_list: list[str] = []

    for order in orders:
        oid = order.outlet_id
        if oid not in orders_by_outlet:
            orders_by_outlet[oid] = []
            outlet_order_list.append(oid)
        orders_by_outlet[oid].append(order)

    # Determine sequence of physical outlet visits
    if stop_sequence:
        ordered_outlet_ids = [oid for oid in stop_sequence if oid in orders_by_outlet]
        # Append any remaining outlets not in stop_sequence
        for oid in outlet_order_list:
            if oid not in ordered_outlet_ids:
                ordered_outlet_ids.append(oid)
    else:
        ordered_outlet_ids = outlet_order_list

    stops: list[dict[str, Any]] = []
    for oid in ordered_outlet_ids:
        outlet_orders = orders_by_outlet[oid]
        first_order = outlet_orders[0]
        outlet = outlets.get(oid)

        brand = first_order.brand
        dock_type = outlet.dock_type if outlet else first_order.dock_type
        parking = outlet.parking_constraint if outlet else first_order.parking_constraint

        # Window times: outlet takes precedence if present, else order
        w_open = (outlet.window_open_time if outlet and outlet.window_open_time
                  else first_order.window_open_time)
        w_close = (outlet.window_close_time if outlet and outlet.window_close_time
                   else first_order.window_close_time)

        # Handling duration in minutes
        allowance_key = (brand, dock_type)
        if allowance_key not in allowances:
            raise InputValidationError(
                f"Missing service allowance for brand {brand.value!r} and dock type {dock_type.value!r} at outlet {oid!r}."
            )
        service_min = allowances[allowance_key]

        # Build delivered line items & order refs
        order_refs = [o.order_ref for o in outlet_orders]
        line_items_delivered: list[dict[str, Any]] = []
        for o in outlet_orders:
            if o.line_items:
                for li in o.line_items:
                    line_items_delivered.append({
                        "order_ref": o.order_ref,
                        "line_item_id": li.line_item_id,
                        "description": li.description,
                        "quantity": li.quantity,
                        "quantity_unit": li.quantity_unit,
                        "unit_weight_kg": li.unit_weight_kg,
                        "unit_volume_m3": li.unit_volume_m3,
                    })
            else:
                line_items_delivered.append({
                    "order_ref": o.order_ref,
                    "line_item_id": f"{o.order_ref}-ALL",
                    "description": "Aggregated Order",
                    "quantity": o.order_units,
                    "quantity_unit": "units",
                    "unit_weight_kg": round(o.order_weight_kg / max(1, o.order_units), 3),
                    "unit_volume_m3": round(o.order_volume_m3 / max(1, o.order_units), 3),
                })

        stops.append({
            "outlet_id": oid,
            "order_refs": order_refs,
            "orders": outlet_orders,
            "dock_type": dock_type,
            "parking_constraint": parking,
            "window_open_time": w_open,
            "window_close_time": w_close,
            "service_duration_min": service_min,
            "line_items_delivered": line_items_delivered,
        })

    return stops


def evaluate_trip_schedule(
    vehicle: Vehicle,
    trip_number: int,
    orders: list[Order],
    brand: Brand,
    district: str,
    depot: str,
    departure_time_iso: Optional[str],
    travel_data: dict[tuple[str, str], DistrictTravel],
    outlets: dict[str, Outlet],
    allowances: dict[tuple[Brand, DockType], float],
    context: OperationalContext,
    trip_id: Optional[str] = None,
    stop_sequence: Optional[list[str]] = None,
) -> EvaluatedTripSchedule:
    """
    Pure schedule evaluator for a single trip.

    Evaluates:
      1. Travel time and distance (outbound, inter-stop, return to depot).
      2. Chronological stop schedule: arrival, waiting duration, service start/end.
      3. Delivery window compliance and lateness margin under chosen WindowPolicy.
      4. Return arrival at depot and vehicle next-availability time.
      5. Cumulative weekly fuel consumption against vehicle quota.
      6. Physical capacity constraints (weight, volume, reefer, van access, depot).
    """
    violations: list[OperationalViolation] = []
    missing_data: list[OperationalMissingData] = []
    tz = ZoneInfo(context.timezone)

    scoped_trip_id = trip_id or f"PLAN-{context.planning_date}-TRIP-{vehicle.vehicle_id}-{trip_number}"

    # 1. Travel Reference Lookup
    travel = travel_data.get((district, depot))
    if travel is None:
        missing_data.append(OperationalMissingData(
            field="district_travel",
            entity_id=f"{district}::{depot}",
            detail=f"No travel record found between depot {depot!r} and district {district!r}.",
        ))
        # Provide zero fallback travel object to allow diagnostic evaluation to proceed
        travel = DistrictTravel(
            district=district,
            depot=depot,
            road_class="unknown",
            free_flow_kmh=0.0,
            depot_to_district_km=0.0,
            depot_to_district_freeflow_min=0.0,
            inter_stop_km=0.0,
            inter_stop_freeflow_min=0.0,
        )

    # 2. Check Date Coverage and Provider for Dynamic Travel Policy (Strict: No silent fallback!)
    if context.travel_policy == TravelPolicy.DYNAMIC_CONDITIONS:
        if (context.planning_date < REFERENCE_DATA_MIN_DATE
                or context.planning_date > REFERENCE_DATA_MAX_DATE):
            missing_data.append(OperationalMissingData(
                field="planning_date",
                entity_id=context.planning_date,
                detail=(
                    f"Planning date {context.planning_date!r} is outside authoritative calendar and road "
                    f"conditions coverage ({REFERENCE_DATA_MIN_DATE} to {REFERENCE_DATA_MAX_DATE}). "
                    "Dynamic conditions travel policy cannot be evaluated without calendar/road reference data."
                ),
            ))
        if context.speed_factor_fn is None:
            missing_data.append(OperationalMissingData(
                field="speed_factor_fn",
                entity_id="dynamic_conditions",
                detail=(
                    "Dynamic conditions travel policy was requested, but no dynamic speed provider or "
                    "speed_factor_fn is configured. Never silently execute static travel under a dynamic label."
                ),
            ))

    # 3. Departure Time Evaluation
    if departure_time_iso:
        dep_dt = parse_iso_or_time_str(departure_time_iso, context.planning_date, context.timezone)
        if dep_dt is None:
            missing_data.append(OperationalMissingData(
                field="departure_time_iso",
                entity_id=departure_time_iso,
                detail=f"Invalid departure timestamp format: {departure_time_iso!r}",
            ))
            dep_dt = parse_iso_or_time_str(
                DEFAULT_FRESH_DEPARTURE_TIME if brand == Brand.FRESH else DEFAULT_STYLE_TECH_DEPARTURE_TIME,
                context.planning_date,
                context.timezone,
            )
    else:
        # Standard default dispatch release times
        default_time_str = (
            DEFAULT_FRESH_DEPARTURE_TIME if brand == Brand.FRESH else DEFAULT_STYLE_TECH_DEPARTURE_TIME
        )
        dep_dt = parse_iso_or_time_str(default_time_str, context.planning_date, context.timezone)

    assert dep_dt is not None

    # 4. Consolidate Orders into Physical Stops
    raw_stops = consolidate_orders_to_stops(orders, outlets, allowances, stop_sequence)
    num_stops = len(raw_stops)

    # 5. Travel Time Calculation
    outbound_min = travel.depot_to_district_freeflow_min
    inter_stop_min = travel.inter_stop_freeflow_min
    return_min = travel.depot_to_district_freeflow_min  # Documented estimation policy: mirrors outbound

    # Optional dynamic speed adjustment factor (if provided and valid)
    if (context.travel_policy == TravelPolicy.DYNAMIC_CONDITIONS
            and context.speed_factor_fn is not None
            and not missing_data):
        speed_factor = context.speed_factor_fn(district, dep_dt.hour, 0, context.planning_date)
        if speed_factor > 0:
            outbound_min /= speed_factor
            inter_stop_min /= speed_factor
            return_min /= speed_factor

    # 6. Stop-by-Stop Chronological Timeline Evaluation
    evaluated_stops: list[OperationalStop] = []
    current_time = dep_dt
    windows_compliant = True

    for idx, s in enumerate(raw_stops, start=1):
        # Leg travel: Stop 1 = outbound; subsequent stops = inter-stop
        leg_travel_min = outbound_min if idx == 1 else inter_stop_min
        arrival_dt = current_time + timedelta(minutes=leg_travel_min)

        # Parse Delivery Windows
        w_open_dt = parse_iso_or_time_str(s["window_open_time"], context.planning_date, context.timezone)
        w_close_dt = parse_iso_or_time_str(s["window_close_time"], context.planning_date, context.timezone)

        # For Fresh: Arrival must precede store opening at 08:00 AM
        if brand == Brand.FRESH:
            fresh_limit_dt = parse_iso_or_time_str(FRESH_DEADLINE_TIME, context.planning_date, context.timezone)
            if fresh_limit_dt:
                if w_close_dt is None or fresh_limit_dt < w_close_dt:
                    w_close_dt = fresh_limit_dt

        # Waiting & Service Start
        if w_open_dt and arrival_dt < w_open_dt:
            waiting_min = (w_open_dt - arrival_dt).total_seconds() / 60.0
            service_start_dt = w_open_dt
        else:
            waiting_min = 0.0
            service_start_dt = arrival_dt

        service_duration = s["service_duration_min"]
        departure_dt = service_start_dt + timedelta(minutes=service_duration)

        # Window Compliance Evaluation
        stop_compliant = True
        violation_detail: Optional[str] = None
        lateness_margin_min = 0.0

        if w_close_dt:
            if context.window_policy == WindowPolicy.ARRIVAL_BEFORE_CLOSE:
                stop_compliant = (arrival_dt <= w_close_dt)
                lateness_margin_min = (w_close_dt - arrival_dt).total_seconds() / 60.0
                if not stop_compliant:
                    violation_detail = (
                        f"Arrival {arrival_dt.strftime('%H:%M')} is after window close "
                        f"{w_close_dt.strftime('%H:%M')} (late by {-lateness_margin_min:.1f} min)."
                    )
            elif context.window_policy == WindowPolicy.SERVICE_START_BEFORE_CLOSE:
                stop_compliant = (service_start_dt <= w_close_dt)
                lateness_margin_min = (w_close_dt - service_start_dt).total_seconds() / 60.0
                if not stop_compliant:
                    violation_detail = (
                        f"Service start {service_start_dt.strftime('%H:%M')} is after window close "
                        f"{w_close_dt.strftime('%H:%M')} (late by {-lateness_margin_min:.1f} min)."
                    )
            elif context.window_policy == WindowPolicy.SERVICE_END_BEFORE_CLOSE:
                stop_compliant = (departure_dt <= w_close_dt)
                lateness_margin_min = (w_close_dt - departure_dt).total_seconds() / 60.0
                if not stop_compliant:
                    violation_detail = (
                        f"Service completion {departure_dt.strftime('%H:%M')} is after window close "
                        f"{w_close_dt.strftime('%H:%M')} (late by {-lateness_margin_min:.1f} min)."
                    )

        if not stop_compliant:
            windows_compliant = False
            violations.append(OperationalViolation(
                rule="DELIVERY_WINDOW_VIOLATION",
                detail=violation_detail or "Delivery window violated.",
                outlet_id=s["outlet_id"],
                vehicle_id=vehicle.vehicle_id,
                trip_number=trip_number,
            ))

        evaluated_stops.append(OperationalStop(
            stop_number=idx,
            outlet_id=s["outlet_id"],
            order_refs=s["order_refs"],
            dock_type=s["dock_type"],
            parking_constraint=s["parking_constraint"],
            window_open_iso=w_open_dt.isoformat() if w_open_dt else None,
            window_close_iso=w_close_dt.isoformat() if w_close_dt else None,
            arrival_time_iso=arrival_dt.isoformat(),
            waiting_duration_min=round(waiting_min, 2),
            service_start_time_iso=service_start_dt.isoformat(),
            service_duration_min=round(service_duration, 2),
            departure_time_iso=departure_dt.isoformat(),
            window_compliant=stop_compliant,
            lateness_margin_min=round(lateness_margin_min, 2),
            violation_detail=violation_detail,
            line_items_delivered=s["line_items_delivered"],
        ))

        # Advance timeline to this stop's departure
        current_time = departure_dt

    # 7. Depot Return & Vehicle Next Available Time
    if num_stops > 0:
        return_arrival_dt = current_time + timedelta(minutes=return_min)
    else:
        return_arrival_dt = dep_dt

    turnaround_min = context.depot_turnaround_duration_min
    next_available_dt = return_arrival_dt + timedelta(minutes=turnaround_min)

    # 8. Distance and Fuel Calculations
    outbound_km = travel.depot_to_district_km if num_stops > 0 else 0.0
    inter_stop_km = (num_stops - 1) * travel.inter_stop_km if num_stops > 1 else 0.0
    return_km = travel.depot_to_district_km if num_stops > 0 else 0.0  # Documented estimation policy
    total_distance_km = outbound_km + inter_stop_km + return_km

    total_trip_duration_min = (return_arrival_dt - dep_dt).total_seconds() / 60.0

    if vehicle.km_per_l is not None and vehicle.km_per_l > 0:
        fuel_consumed_l = total_distance_km / vehicle.km_per_l
    else:
        missing_data.append(OperationalMissingData(
            field="km_per_l",
            entity_id=vehicle.vehicle_id,
            detail=f"Vehicle {vehicle.vehicle_id!r} has missing or non-positive fuel efficiency rating km_per_l.",
        ))
        fuel_consumed_l = 0.0

    prior_used = vehicle.weekly_fuel_used_l or 0.0
    external_reservations = vehicle.external_reservations_l or 0.0
    cumulative_fuel_used_l = prior_used + external_reservations + fuel_consumed_l

    fuel_compliant = True
    if vehicle.weekly_fuel_quota_l is not None:
        if cumulative_fuel_used_l > vehicle.weekly_fuel_quota_l:
            fuel_compliant = False
            violations.append(OperationalViolation(
                rule="FUEL_QUOTA_EXCEEDED",
                detail=(
                    f"Trip requires ~{fuel_consumed_l:.2f} L, driving cumulative weekly fuel to "
                    f"{cumulative_fuel_used_l:.2f} L, which exceeds weekly quota of "
                    f"{vehicle.weekly_fuel_quota_l:.2f} L (prior used={prior_used:.2f} L, "
                    f"external reservations={external_reservations:.2f} L)."
                ),
                vehicle_id=vehicle.vehicle_id,
                trip_number=trip_number,
            ))

    # 9. Physical Capacity & Compatibility Checks
    total_weight = sum(o.order_weight_kg for o in orders)
    total_volume = sum(o.order_volume_m3 for o in orders)
    capacity_compliant = True

    if total_weight > vehicle.weight_cap_kg:
        capacity_compliant = False
        violations.append(OperationalViolation(
            rule="WEIGHT_CAPACITY_EXCEEDED",
            detail=f"Total weight {total_weight:.2f} kg exceeds vehicle capacity {vehicle.weight_cap_kg:.2f} kg.",
            vehicle_id=vehicle.vehicle_id,
            trip_number=trip_number,
        ))

    if total_volume > vehicle.volume_cap_m3:
        capacity_compliant = False
        violations.append(OperationalViolation(
            rule="VOLUME_CAPACITY_EXCEEDED",
            detail=f"Total volume {total_volume:.2f} m3 exceeds vehicle capacity {vehicle.volume_cap_m3:.2f} m3.",
            vehicle_id=vehicle.vehicle_id,
            trip_number=trip_number,
        ))

    # Refrigeration compatibility
    for o in orders:
        if o.temp_requirement == TempRequirement.CHILLED and vehicle.temp != TempSpec.REEFER:
            capacity_compliant = False
            violations.append(OperationalViolation(
                rule="TEMPERATURE_INCOMPATIBLE",
                detail=f"Chilled order {o.order_ref!r} assigned to ambient vehicle {vehicle.vehicle_id!r}.",
                order_ref=o.order_ref,
                vehicle_id=vehicle.vehicle_id,
                trip_number=trip_number,
            ))
            break

    # Van-only access compatibility
    for o in orders:
        if o.parking_constraint == ParkingConstraint.VAN_ONLY and vehicle.type != VehicleType.VAN:
            capacity_compliant = False
            violations.append(OperationalViolation(
                rule="ACCESS_RESTRICTION_VIOLATION",
                detail=f"van_only outlet order {o.order_ref!r} assigned to non-van vehicle {vehicle.vehicle_id!r}.",
                order_ref=o.order_ref,
                vehicle_id=vehicle.vehicle_id,
                trip_number=trip_number,
            ))
            break

    # Depot containment
    for o in orders:
        if o.depot != vehicle.depot:
            capacity_compliant = False
            violations.append(OperationalViolation(
                rule="DEPOT_MISMATCH",
                detail=f"Order depot {o.depot!r} does not match vehicle home depot {vehicle.depot!r}.",
                order_ref=o.order_ref,
                vehicle_id=vehicle.vehicle_id,
                trip_number=trip_number,
            ))
            break

    # Brand and District homogeneity policy
    for o in orders:
        if o.brand != brand:
            violations.append(OperationalViolation(
                rule="HETEROGENEOUS_BRAND",
                detail=f"Order brand {o.brand.value!r} does not match trip brand {brand.value!r}.",
                order_ref=o.order_ref,
                trip_number=trip_number,
            ))
            break
        if o.district != district:
            violations.append(OperationalViolation(
                rule="HETEROGENEOUS_DISTRICT",
                detail=f"Order district {o.district!r} does not match trip district {district!r}.",
                order_ref=o.order_ref,
                trip_number=trip_number,
            ))
            break

    return EvaluatedTripSchedule(
        trip_id=scoped_trip_id,
        vehicle_id=vehicle.vehicle_id,
        trip_number=trip_number,
        brand=brand,
        district=district,
        depot=depot,
        departure_time_iso=dep_dt.isoformat(),
        stops=evaluated_stops,
        depot_return_arrival_iso=return_arrival_dt.isoformat(),
        vehicle_next_available_iso=next_available_dt.isoformat(),
        outbound_distance_km=round(outbound_km, 2),
        inter_stop_distance_km=round(inter_stop_km, 2),
        return_distance_km=round(return_km, 2),
        total_distance_km=round(total_distance_km, 2),
        total_duration_min=round(total_trip_duration_min, 2),
        fuel_consumed_l=round(fuel_consumed_l, 2),
        cumulative_fuel_used_l=round(cumulative_fuel_used_l, 2),
        weekly_quota_l=vehicle.weekly_fuel_quota_l,
        fuel_compliant=fuel_compliant,
        windows_compliant=windows_compliant,
        capacity_compliant=capacity_compliant,
        total_weight_kg=round(total_weight, 2),
        weight_cap_kg=round(vehicle.weight_cap_kg, 2),
        total_volume_m3=round(total_volume, 2),
        volume_cap_m3=round(vehicle.volume_cap_m3, 2),
        violations=violations,
        missing_data=missing_data,
    )
