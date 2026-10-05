import pandas as pd
import numpy as np
from .prioritization import calculate_order_priority

TRIP_BUDGET_FRESH = 270.0
TRIP_BUDGET_DAYTIME = 480.0
MAX_TRIPS_PER_VEHICLE = 2

def calculate_trip_time(
    district: str,
    brand: str,
    dock_types: list[str],
    dtravel: dict,
    allowance: dict
) -> float:
    if len(dock_types) == 0:
        return 0.0
    d = dtravel[district]
    n = len(dock_types)
    return (
        d["depot_to_district_freeflow_min"]
        + (n - 1) * d["inter_stop_freeflow_min"]
        + sum(allowance.get((brand, dk), 15.0) for dk in dock_types)
    )

def solve_task2b_allocation(
    adapted_scenario: dict
) -> pd.DataFrame:
    """
    Solves Task 2B Peak-Day Fleet Allocation while strictly enforcing all 7 feasibility rules.
    """
    orders_df = adapted_scenario["orders"].copy()
    vehicles_df = adapted_scenario["available_vehicles"].copy()
    dtravel = adapted_scenario["district_travel"]
    allowance = adapted_scenario["service_allowance"]

    # Calculate priority scores for orders
    orders_df["priority"] = orders_df.apply(calculate_order_priority, axis=1)

    # Filter for Peliyagoda depot vehicles only
    vehicles = vehicles_df[vehicles_df["depot"] == "Peliyagoda"].copy()

    # Sort vehicles by capabilities to utilize specialized vehicles (reefer, van) efficiently
    vehicles["is_reefer"] = (vehicles["temp"] == "reefer").astype(int)
    vehicles["is_van"] = (vehicles["type"] == "van").astype(int)
    vehicles.sort_values(by=["is_reefer", "is_van", "volume_cap_m3"], ascending=[True, True, False], inplace=True)

    unassigned_orders = orders_df.sort_values(by="priority", ascending=False).to_dict("records")
    assigned_records = []

    # Map to store vehicle usage state: vehicle_id -> {"trips": 0, "fresh_min": 0.0, "daytime_min": 0.0}
    veh_state = {
        vid: {"trips": 0, "fresh_min": 0.0, "daytime_min": 0.0}
        for vid in vehicles["vehicle_id"]
    }

    # Group unassigned orders by (brand, district)
    # We will build candidate trips for (brand, district) combinations
    groups = {}
    for ord_item in unassigned_orders:
        key = (ord_item["brand"], ord_item["district"])
        groups.setdefault(key, []).append(ord_item)

    # Sort group keys by highest priority orders inside
    sorted_group_keys = sorted(
        groups.keys(),
        key=lambda k: sum(o["priority"] for o in groups[k]),
        reverse=True
    )

    for brand, district in sorted_group_keys:
        group_orders = groups[(brand, district)]
        if not group_orders:
            continue

        # Try assigning to suitable available vehicles
        for v_idx, v_row in vehicles.iterrows():
            vid = v_row["vehicle_id"]
            state = veh_state[vid]

            if state["trips"] >= MAX_TRIPS_PER_VEHICLE:
                continue

            # Check vehicle compatibility with remaining group orders
            req_reefer = any(o["temp_requirement"] == "chilled" for o in group_orders)
            req_van = any(o["parking_constraint"] == "van_only" for o in group_orders)

            if req_reefer and v_row["temp"] != "reefer":
                # Filter out chilled orders for non-reefer vehicle
                candidate_orders = [o for o in group_orders if o["temp_requirement"] != "chilled"]
            else:
                candidate_orders = list(group_orders)

            if req_van and v_row["type"] != "van":
                # Filter out van_only orders for truck
                candidate_orders = [o for o in candidate_orders if o["parking_constraint"] != "van_only"]

            if not candidate_orders:
                continue

            # Pack orders into trip up to volume and weight capacity
            curr_vol = 0.0
            curr_wt = 0.0
            trip_orders = []

            for o in candidate_orders:
                if (curr_vol + o["order_volume_m3"] <= v_row["volume_cap_m3"] + 1e-6) and \
                   (curr_wt + o["order_weight_kg"] <= v_row["weight_cap_kg"] + 1e-6):

                    # Check trip time budget
                    temp_docks = [o_t["dock_type"] for o_t in trip_orders] + [o["dock_type"]]
                    tt = calculate_trip_time(district, brand, temp_docks, dtravel, allowance)

                    if brand == "Fresh":
                        if state["fresh_min"] + tt > TRIP_BUDGET_FRESH + 1e-6:
                            continue
                    else:
                        if state["daytime_min"] + tt > TRIP_BUDGET_DAYTIME + 1e-6:
                            continue

                    trip_orders.append(o)
                    curr_vol += o["order_volume_m3"]
                    curr_wt += o["order_weight_kg"]

            if trip_orders:
                # Commit trip
                trip_id = state["trips"] + 1
                tt = calculate_trip_time(district, brand, [o["dock_type"] for o in trip_orders], dtravel, allowance)

                state["trips"] += 1
                if brand == "Fresh":
                    state["fresh_min"] += tt
                else:
                    state["daytime_min"] += tt

                for o in trip_orders:
                    assigned_records.append({
                        "scenario": o["scenario"],
                        "order_ref": o["order_ref"],
                        "outlet_id": o["outlet_id"],
                        "decision": "served",
                        "vehicle_id": vid,
                        "trip_id": trip_id
                    })
                    group_orders.remove(o)

    # Any remaining unassigned orders are marked deferred
    assigned_refs = {r["order_ref"] for r in assigned_records}
    for o in unassigned_orders:
        if o["order_ref"] not in assigned_refs:
            assigned_records.append({
                "scenario": o["scenario"],
                "order_ref": o["order_ref"],
                "outlet_id": o["outlet_id"],
                "decision": "deferred",
                "vehicle_id": "",
                "trip_id": ""
            })

    result_df = pd.DataFrame(assigned_records)

    # Ensure original template order_ref sequence is preserved
    result_df = orders_df[["scenario", "order_ref", "outlet_id"]].merge(
        result_df[["scenario", "order_ref", "decision", "vehicle_id", "trip_id"]],
        on=["scenario", "order_ref"],
        how="left"
    )

    served_cnt = (result_df["decision"] == "served").sum()
    deferred_cnt = (result_df["decision"] == "deferred").sum()
    print(f"Task 2B Allocation Complete: {served_cnt} served, {deferred_cnt} deferred.")
    return result_df
