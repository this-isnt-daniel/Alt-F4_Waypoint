"""
Waypoint Optimizer — Command Line Interface
============================================
Provides easy commands for running the optimizer from the terminal.

Commands:
  demo       — run a demo with synthetic data (no real data needed)
  benchmark  — compare Greedy vs Hybrid vs Full CP-SAT Cold
  validate   — validate a plan from a JSON or CSV file
  optimize   — run optimization on CSV input files

Usage:
  python -m waypoint_optimizer.cli demo
  python -m waypoint_optimizer.cli benchmark
  python -m waypoint_optimizer.cli benchmark --orders 200 --vehicles 30
  python -m waypoint_optimizer.cli validate plan.csv
  python -m waypoint_optimizer.cli optimize --input-dir ./data/
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional


def cmd_demo(args: argparse.Namespace) -> None:
    """Run a demo allocation on synthetic data and print a summary."""
    from waypoint_optimizer.mock_data import generate_scenario
    from waypoint_optimizer.engine import optimize
    from waypoint_optimizer.config import OptimizerConfig

    n_orders = getattr(args, "orders", 50)
    n_vehicles = getattr(args, "vehicles", 10)
    seed = getattr(args, "seed", 42)

    print(f"\n{'='*60}")
    print(f"  WAYPOINT OPTIMIZER - DEMO")
    print(f"  Synthetic data: {n_orders} orders, {n_vehicles} vehicles")
    print(f"  Seed: {seed} (deterministic)")
    print(f"{'='*60}\n")
    print("  Note: all data is SYNTHETIC. Not official competition data.\n")

    orders, vehicles, travel, allowances = generate_scenario(
        n_orders=n_orders, n_vehicles=n_vehicles, seed=seed
    )

    cfg = OptimizerConfig(
        enable_targeted_cpsat=True,
        targeted_cpsat_time_limit_s=2.0,
    )

    t0 = time.perf_counter()
    result = optimize(orders, vehicles, travel, allowances, config=cfg)
    elapsed = time.perf_counter() - t0

    print(f"  Engine:     {result.engine_name}")
    print(f"  Status:     {result.status.value}")
    print(f"  Runtime:    {elapsed:.2f}s")
    print(f"  Validation: {'PASS [OK]' if result.validation.valid else 'FAIL [X]'}")
    print()
    print(f"  Orders total:   {result.metrics.total_orders}")
    print(f"  Served:         {result.metrics.served_count}")
    print(f"  Deferred:       {result.metrics.deferred_count}")
    print(f"  Penalty total:  {result.metrics.total_deferral_penalty:.1f}")
    print(f"  Trips created:  {result.metrics.trips_created}")
    print(f"  Vehicles used:  {result.metrics.vehicles_used}")
    print(f"  Reefer used:    {result.metrics.reefer_vehicles_used}")
    print(f"  Vans used:      {result.metrics.van_vehicles_used}")
    print()

    if result.validation.valid:
        print("  VALIDATION: PASS")
        print("  (FEASIBLE - satisfies all hard constraints)")
        print("  (NOT claimed to be globally optimal)")
    else:
        print("  VALIDATION: FAIL")
        for err in result.validation.errors[:5]:
            print(f"    [X] [{err.rule}] {err.detail}")
        if len(result.validation.errors) > 5:
            print(f"    ... and {len(result.validation.errors)-5} more errors")

    print()
    print("  TOP TRIPS:")
    for tr in result.trips[:5]:
        print(
            f"    {tr.vehicle_id} trip-{tr.trip_number} "
            f"({tr.brand.value}, {tr.district}): "
            f"{len(tr.order_refs)} orders, "
            f"{tr.total_weight_kg:.0f}kg, "
            f"{tr.total_volume_m3:.2f}m3, "
            f"{tr.trip_minutes:.0f}min"
        )
    if len(result.trips) > 5:
        print(f"    ... and {len(result.trips)-5} more trips")

    print()
    print("  TOP DEFERRED ORDERS:")
    from waypoint_optimizer.objective import defer_penalty
    from waypoint_optimizer.config import OptimizerConfig as Cfg
    order_by_ref = {o.order_ref: o for o in orders}
    deferred_with_penalty = [
        (d, defer_penalty(order_by_ref[d.order_ref]))
        for d in result.deferred_orders
        if d.order_ref in order_by_ref
    ]
    deferred_with_penalty.sort(key=lambda x: -x[1])
    for d, pen in deferred_with_penalty[:5]:
        print(f"    {d.order_ref}: [{d.reason.value}] penalty={pen:.0f}")
    if len(deferred_with_penalty) > 5:
        print(f"    ... and {len(deferred_with_penalty)-5} more deferred")
    print()


def cmd_plan_daily(args: argparse.Namespace) -> None:
    """Run Hackathon daily delivery draft planning and export strict JSON."""
    from waypoint_optimizer.adapters.csv_adapter import (
        load_orders_with_outlets,
        load_reference_data,
        load_fleet_state_from_csv,
        vehicles_from_csv,
    )
    from waypoint_optimizer.hackathon_planner import generate_daily_draft_plan
    from waypoint_optimizer.operational.models import (
        OperationalContext,
        TravelPolicy,
        WindowPolicy,
    )

    ref_dir = Path(args.ref_dir or "./data").resolve()
    if not ref_dir.exists():
        print(f"Error: Reference directory not found at {ref_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*70}")
    print("  WAYPOINT OPTIMIZER — HACKATHON DAILY DISPATCH PLANNER")
    print(f"{'='*70}\n")
    print(f"  Reference directory: {ref_dir}")
    print(f"  Target date:         {args.date}")
    print(f"  Travel policy:       {args.travel_policy}")
    print(f"  Window policy:       {args.window_policy}")

    # 1. Load Reference Data
    ref_data = load_reference_data(ref_dir)
    print(f"  Authoritative outlets:   {len(ref_data.outlets)}")
    print(f"  Districts covered:       {len(ref_data.travel)}")

    # 2. Load Confirmed Orders
    if not args.orders_file:
        print("Error: --orders-file is required for daily planning.", file=sys.stderr)
        sys.exit(1)
    orders_path = Path(args.orders_file).resolve()
    if not orders_path.exists():
        print(f"Error: Orders file not found at {orders_path}", file=sys.stderr)
        sys.exit(1)

    orders = load_orders_with_outlets(orders_path, outlets=ref_data.outlets)
    if args.depot:
        orders = [o for o in orders if o.depot.lower() == args.depot.lower()]
    print(f"  Confirmed orders loaded: {len(orders)}")

    # 3. Load Fleet State
    if not args.fleet_file:
        print(
            "Error: --fleet-file is required for daily operational planning.\n"
            "Production dispatch planning requires explicit fleet state (mechanical availability,\n"
            "dispatcher selection, remaining trips, fuel used, and external reservations).\n"
            "To run the example with test fleet state, supply: --fleet-file examples/fleet_state_test.csv",
            file=sys.stderr,
        )
        sys.exit(1)

    fleet_path = Path(args.fleet_file).resolve()
    if not fleet_path.exists():
        print(f"Error: Fleet state file not found at {fleet_path}", file=sys.stderr)
        sys.exit(1)
    fleet = load_fleet_state_from_csv(fleet_path, vehicle_reference=ref_data.vehicles)
    if args.depot:
        fleet = [v for v in fleet if v.depot.lower() == args.depot.lower()]
    print(f"  Fleet vehicles:          {len(fleet)}")

    # 4. Context Setup
    context = OperationalContext(
        planning_date=args.date,
        timezone=args.timezone,
        depot_turnaround_duration_min=args.turnaround,
        travel_policy=TravelPolicy(args.travel_policy),
        window_policy=WindowPolicy(args.window_policy),
    )

    # 5. Generate Daily Draft Plan
    from waypoint_optimizer.input_validation import InputValidationError
    t0 = time.perf_counter()
    try:
        draft = generate_daily_draft_plan(
            orders=orders,
            fleet=fleet,
            reference_data=ref_data,
            context=context,
        )
    except InputValidationError as e:
        print(f"Error: Missing required operational reference data:\n{e}", file=sys.stderr)
        sys.exit(1)
    elapsed = time.perf_counter() - t0

    # 6. Save Strict JSON Plan
    out_path = Path(args.output_file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, allow_nan=False)

    print(f"\n  Plan ID:        {draft['plan_id']}")
    print(f"  Status:         {draft['status']}")
    print(f"  Runtime:        {elapsed:.2f}s")
    val = draft["validation"]
    print(f"  Validation:     {'PASS [DRAFT — REQUIRES DISPATCHER APPROVAL]' if val.get('valid') else 'FAIL [INVALID]'}")
    counts = draft["order_counts"]
    print(f"  Fully served:   {counts['fully_served_orders']} / {counts['total_orders']}")
    print(f"  Partially:      {counts['partially_served_orders']}")
    print(f"  Deferred:       {counts['fully_deferred_orders']}")
    metrics = draft["metrics"]
    print(f"  Trips created:  {metrics['trips_created']}")
    print(f"  Vehicles used:  {metrics['vehicles_used']}")
    print(f"  Total distance: {metrics['total_distance_km']:.1f} km")
    print(f"  Total fuel:     {metrics['total_fuel_litres']:.2f} L")
    cpsat = draft.get("targeted_cpsat_stage")
    if isinstance(cpsat, dict):
        if cpsat.get("executed"):
            print(f"  Targeted CP-SAT: {cpsat.get('outcome')} (Accepted: {cpsat.get('improvement_accepted')}, Status: {cpsat.get('raw_solver_status')})")
        else:
            print(f"  Targeted CP-SAT: SKIPPED ({cpsat.get('rejection_or_skip_reason')})")
    print(f"\n  Strict plan saved to: {out_path}\n")

    if not val.get("valid"):
        print("  WARNING: Produced draft plan has validation errors or missing data!", file=sys.stderr)
        sys.exit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate a plan from a JSON file against input data."""
    plan_file = Path(args.plan_file)
    if not plan_file.exists():
        print(f"Error: plan file {plan_file} not found.", file=sys.stderr)
        sys.exit(1)

    with open(plan_file, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    from waypoint_optimizer.domain import OrderAssignment, DeferredOrder, TripResult
    from waypoint_optimizer.enums import Brand, DeferralReason
    from waypoint_optimizer.trip_math import build_allowance_index, build_travel_index
    from waypoint_optimizer.validator import validate

    ref_dir = getattr(args, "ref_dir", None)
    orders_file = getattr(args, "orders_file", None)
    input_dir = getattr(args, "input_dir", None)

    orders = None
    vehicles = None
    travel = None
    allowances = None

    if ref_dir and orders_file:
        from waypoint_optimizer.adapters.csv_adapter import load_reference_data, load_orders_with_outlets
        ref = load_reference_data(ref_dir)
        orders = load_orders_with_outlets(orders_file, outlets=ref.outlets)
        vehicles = ref.vehicles
        travel = ref.travel
        allowances = ref.allowances
        print(f"Loaded validation inputs: reference from {ref_dir}, orders from {orders_file}")
    elif input_dir and Path(input_dir).exists():
        from waypoint_optimizer.adapters.csv_adapter import (
            load_reference_data, load_orders_with_outlets,
            orders_from_csv, vehicles_from_csv, travel_from_csv, allowances_from_csv,
        )
        p = Path(input_dir)
        if (p / "outlets.csv").exists():
            ref = load_reference_data(p)
            orders = load_orders_with_outlets(p / "orders.csv", outlets=ref.outlets)
            vehicles = ref.vehicles
            travel = ref.travel
            allowances = ref.allowances
        else:
            orders = orders_from_csv(p / "orders.csv")
            vehicles = vehicles_from_csv(p / "fleet_availability.csv", p / "vehicle_reference.csv")
            travel = travel_from_csv(p / "district_travel.csv")
            sa_file = p / "service_allowance.csv" if (p / "service_allowance.csv").exists() else p / "service_allowances.csv"
            allowances = allowances_from_csv(sa_file)
        print(f"Loaded input scenario from: {input_dir}")
    else:
        from waypoint_optimizer.mock_data import generate_scenario
        orders, vehicles, travel, allowances = generate_scenario()
        print("Note: using default synthetic scenario - specify --ref-dir and --orders-file for production datasets.")

    vehicles_by_id = {v.vehicle_id: v for v in vehicles}
    travel_index = build_travel_index(travel)
    allowance_index = build_allowance_index(allowances)

    served_assignments = [
        OrderAssignment(
            order_ref=a["order_ref"],
            vehicle_id=a["vehicle_id"],
            trip_number=a["trip_number"],
        )
        for a in plan_data.get("served_assignments", [])
    ]

    # If served_assignments was omitted, infer from trips
    if not served_assignments and "trips" in plan_data:
        for tr in plan_data["trips"]:
            v_id = tr["vehicle_id"]
            t_num = tr["trip_number"]
            for o_ref in tr["order_refs"]:
                served_assignments.append(OrderAssignment(order_ref=o_ref, vehicle_id=v_id, trip_number=t_num))

    deferred_orders = [
        DeferredOrder(
            order_ref=d["order_ref"],
            reason=DeferralReason(d.get("reason", DeferralReason.OTHER_CAPACITY_LIMIT.value)),
            detail=d.get("detail", ""),
        )
        for d in plan_data.get("deferred_orders", [])
    ]

    trip_results = [
        TripResult(
            vehicle_id=tr["vehicle_id"],
            trip_number=tr["trip_number"],
            brand=Brand(tr["brand"]),
            district=tr["district"],
            order_refs=tuple(tr["order_refs"]),
            stop_sequence=tuple(tr.get("stop_sequence", tr["order_refs"])),
            total_weight_kg=float(tr.get("total_weight_kg", tr.get("weight_kg", 0.0))),
            total_volume_m3=float(tr.get("total_volume_m3", tr.get("volume_m3", 0.0))),
            trip_minutes=float(tr.get("trip_minutes", tr.get("minutes", 0.0))),
            remaining_weight_kg=float(tr.get("remaining_weight_kg", 0.0)),
            remaining_volume_m3=float(tr.get("remaining_volume_m3", 0.0)),
        )
        for tr in plan_data.get("trips", [])
    ]

    val_res = validate(
        orders=orders,
        vehicles_by_id=vehicles_by_id,
        travel_index=travel_index,
        allowance_index=allowance_index,
        served_assignments=served_assignments,
        deferred_orders=deferred_orders,
        trip_results=trip_results,
    )

    print(f"Validation: {'PASS [OK]' if val_res.valid else 'FAIL [X]'}")
    if val_res.valid:
        print("  All hard constraints verified successfully.")
    else:
        print(f"  Found {len(val_res.errors)} validation errors:")
        for err in val_res.errors[:10]:
            print(f"    [X] [{err.rule}] {err.detail}")
        if len(val_res.errors) > 10:
            print(f"    ... and {len(val_res.errors)-10} more errors")
        sys.exit(1)


def cmd_optimize(args: argparse.Namespace) -> None:
    """
    Run production optimization using supplied reference CSVs and explicit orders.

    Guarantees:
      - Never silently falls back to synthetic or mock data.
      - Requires explicit orders transaction file.
      - Never overwrites source CSVs.
      - Validates all inputs and independently revalidates the final plan.
    """
    # 1. Discover reference data directory
    ref_dir = None
    if getattr(args, "ref_dir", None):
        ref_dir = Path(args.ref_dir)
    elif getattr(args, "input_dir", None):
        ref_dir = Path(args.input_dir)
    elif Path("../data").exists():
        ref_dir = Path("../data")
    elif Path("./data").exists():
        ref_dir = Path("./data")

    if not ref_dir or not ref_dir.exists():
        print(
            "Error: Reference data directory not found.\n"
            "Specify --ref-dir <path_to_reference_directory> containing "
            "outlets.csv, district_travel.csv, service_allowance.csv, and vehicles.csv.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Discover orders file
    orders_file = None
    if getattr(args, "orders_file", None):
        orders_file = Path(args.orders_file)
    elif getattr(args, "input_dir", None) and (Path(args.input_dir) / "orders.csv").exists():
        orders_file = Path(args.input_dir) / "orders.csv"

    if not orders_file or not orders_file.exists():
        print(
            "Error: Production optimization requires an explicit orders file.\n"
            "None of the reference CSV files contains order transactions.\n"
            "Specify --orders-file <path_to_orders.csv> to optimize.\n"
            "(Use 'waypoint-optimizer demo' to test synthetic scenarios).",
            file=sys.stderr,
        )
        sys.exit(1)

    # 3. Output path check
    out_arg = getattr(args, "output_file", "plan_output.json")
    output_path = Path(out_arg)
    if output_path.suffix.lower() == ".csv":
        print(
            f"Error: Output file {output_path} cannot be a CSV file. "
            "Specify a .json output path (preventing source CSV overwrite).",
            file=sys.stderr,
        )
        sys.exit(1)

    from waypoint_optimizer.adapters.csv_adapter import (
        load_reference_data,
        load_orders_with_outlets,
        export_plan_json,
    )
    from waypoint_optimizer.engine import optimize
    from waypoint_optimizer.config import OptimizerConfig
    from waypoint_optimizer.input_validation import InputValidationError

    fleet_avail = getattr(args, "fleet_availability", None)
    scenario = getattr(args, "scenario", None)

    try:
        ref = load_reference_data(ref_dir, fleet_availability_source=fleet_avail, scenario=scenario)
        orders = load_orders_with_outlets(orders_file, outlets=ref.outlets, scenario_filter=scenario)
    except (FileNotFoundError, InputValidationError, ValueError) as e:
        print(f"Error loading inputs: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  WAYPOINT OPTIMIZER - PRODUCTION RUN")
    print(f"  Reference dir: {ref.ref_dir}")
    print(f"  Orders file:   {orders_file.resolve()}")
    print(f"  Total orders:  {len(orders)}")
    print(f"  Fleet size:    {len(ref.vehicles)} vehicles")
    print(f"{'='*60}\n")

    cfg = OptimizerConfig(
        enable_targeted_cpsat=True,
        targeted_cpsat_time_limit_s=5.0,
    )

    t0 = time.perf_counter()
    try:
        result = optimize(orders, ref.vehicles, ref.travel, ref.allowances, config=cfg)
    except InputValidationError as e:
        print(f"Input validation error: {e}", file=sys.stderr)
        sys.exit(1)
    elapsed = time.perf_counter() - t0

    # Save output plan
    provenance = {
        "orders_source": str(orders_file.resolve()),
        "ref_dir": str(ref_dir.resolve()),
        "scenario": scenario or "default",
        "orders_count": len(orders),
        "fleet_count": len(ref.vehicles),
    }
    saved_path = export_plan_json(result, output_path, provenance=provenance)

    print(f"  Status:         {result.status.value}")
    print(f"  Runtime:        {elapsed:.2f}s")
    print(f"  Validation:     {'PASS [OK]' if result.validation.valid else 'FAIL [X]'}")
    print(f"  Served orders:  {result.metrics.served_count} / {result.metrics.total_orders}")
    print(f"  Deferred:       {result.metrics.deferred_count}")
    print(f"  Trips created:  {result.metrics.trips_created}")
    print(f"  Vehicles used:  {result.metrics.vehicles_used}")
    print(f"  Total penalty:  {result.metrics.total_deferral_penalty:.1f}")
    if result.diagnostic_message:
        print(f"  Diagnostic:     {result.diagnostic_message}")
    print(f"\n  Plan saved strictly to: {saved_path}\n")

    if not result.validation.valid:
        print("  WARNING: Produced plan failed independent validation!", file=sys.stderr)
        sys.exit(1)


def main(argv: Optional[list[str]] = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="waypoint-optimizer",
        description="Waypoint fleet allocation optimization engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # demo
    p_demo = sub.add_parser("demo", help="Run demo with synthetic data")
    p_demo.add_argument("--orders", type=int, default=50, help="Number of orders")
    p_demo.add_argument("--vehicles", type=int, default=10, help="Number of vehicles")
    p_demo.add_argument("--seed", type=int, default=42, help="Random seed")

    # plan-daily (Hackathon operational dispatch workflow)
    p_plan = sub.add_parser("plan-daily", help="Generate Hackathon daily delivery draft plan")
    p_plan.add_argument("--orders-file", "-orders", dest="orders_file", required=True,
                        help="Path to confirmed orders CSV file")
    p_plan.add_argument("--fleet-file", "-fleet", dest="fleet_file", required=True,
                        help="Path to daily fleet state CSV file (required)")
    p_plan.add_argument("--ref-dir", dest="ref_dir", default="./data",
                        help="Directory containing reference CSVs (default: ./data)")
    p_plan.add_argument("--date", dest="date", default="2026-10-03",
                        help="Target planning date in YYYY-MM-DD format (default: 2026-10-03)")
    p_plan.add_argument("--timezone", dest="timezone", default="Asia/Colombo",
                        help="Authoritative timezone (default: Asia/Colombo)")
    p_plan.add_argument("--depot", dest="depot", default=None,
                        help="Optional depot filter (e.g. Peliyagoda or Kandy)")
    p_plan.add_argument("--travel-policy", dest="travel_policy", default="static_freeflow",
                        choices=["static_freeflow", "dynamic_conditions"],
                        help="Travel evaluation policy (default: static_freeflow)")
    p_plan.add_argument("--window-policy", dest="window_policy", default="arrival_before_close",
                        choices=["arrival_before_close", "service_start_before_close", "service_end_before_close"],
                        help="Delivery window compliance rule (default: arrival_before_close)")
    p_plan.add_argument("--turnaround", dest="turnaround", type=float, default=30.0,
                        help="Depot turnaround duration in minutes (default: 30.0)")
    p_plan.add_argument("--output", "-o", dest="output_file", default="draft_plan.json",
                        help="Path to output JSON file (default: draft_plan.json)")

    # validate
    p_val = sub.add_parser("validate", help="Validate a plan JSON file")
    p_val.add_argument("plan_file", help="Path to plan JSON file")
    p_val.add_argument("--ref-dir", dest="ref_dir", default=None,
                       help="Path to directory containing reference CSVs")
    p_val.add_argument("--orders-file", dest="orders_file", default=None,
                       help="Path to orders CSV file")
    p_val.add_argument("--input-dir", dest="input_dir", default=None,
                       help="Optional directory containing orders.csv and reference data")

    # optimize
    p_opt = sub.add_parser("optimize", help="Run production optimization from CSV reference and orders")
    p_opt.add_argument("--ref-dir", dest="ref_dir", default=None,
                       help="Directory containing reference CSVs (outlets.csv, district_travel.csv, etc.)")
    p_opt.add_argument("--orders-file", dest="orders_file", default=None,
                       help="Path to orders CSV file (required)")
    p_opt.add_argument("--output", "-o", dest="output_file", default="plan_output.json",
                       help="Path to output JSON file (default: plan_output.json)")
    p_opt.add_argument("--fleet-availability", dest="fleet_availability", default=None,
                       help="Optional path to fleet_availability.csv to override status")
    p_opt.add_argument("--scenario", dest="scenario", default=None,
                       help="Optional scenario name filter")
    p_opt.add_argument("--input-dir", dest="input_dir", default=None,
                       help="Legacy directory containing orders.csv and reference CSVs")

    args = parser.parse_args(argv)

    if args.command == "demo":
        cmd_demo(args)
    elif args.command == "plan-daily":
        cmd_plan_daily(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "optimize":
        cmd_optimize(args)


if __name__ == "__main__":
    main()

