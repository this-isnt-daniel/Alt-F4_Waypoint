import pandas as pd

def adapt_task2b_scenario(
    scenarios_df: pd.DataFrame,
    fleet_df: pd.DataFrame,
    vehicles_df: pd.DataFrame,
    district_travel_df: pd.DataFrame,
    service_allowance_df: pd.DataFrame
) -> dict:
    """
    Adapts Datathon Task 2B scenario files into standardized structures for priority scoring and solving.
    Preserves days_since_last_served and deferred_yesterday without modifying column semantics.
    """
    scenarios = scenarios_df.copy()

    # Filter available fleet (exclude in_workshop)
    available_fleet_ids = set(fleet_df[fleet_df["status"] == "available"]["vehicle_id"])
    avail_vehicles = vehicles_df[vehicles_df["vehicle_id"].isin(available_fleet_ids)].copy()

    # Build lookup dicts
    dtravel = district_travel_df.set_index("district").to_dict("index")
    allowance = {(r.brand, r.dock_type): r.service_allowance_min for r in service_allowance_df.itertuples()}

    return {
        "orders": scenarios,
        "available_vehicles": avail_vehicles,
        "district_travel": dtravel,
        "service_allowance": allowance
    }
