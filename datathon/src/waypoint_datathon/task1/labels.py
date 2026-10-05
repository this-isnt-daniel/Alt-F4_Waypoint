import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def parse_hhmm_to_datetime(date_str: str, hhmm_str: str) -> datetime | None:
    if pd.isna(date_str) or pd.isna(hhmm_str):
        return None
    try:
        parts = str(hhmm_str).strip().split(":")
        h, m = int(parts[0]), int(parts[1])
        base_dt = datetime.strptime(str(date_str).split()[0], "%Y-%m-%d")
        return base_dt + timedelta(hours=h, minutes=m)
    except Exception:
        return None

def construct_task1_labels(deliveries_df: pd.DataFrame, route_legs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs Task 1 training labels according to official rules:
    - service_start = max(actual_arrival, window_open)
    - service_minutes = (leave_outlet_time - service_start).total_seconds() / 60.0
    - late_label = int(actual_arrival > window_close)
    Quarantines invalid chronology.
    """
    deliv = deliveries_df.copy()
    legs = route_legs_df.copy()

    # Filter for dispatched orders with valid route legs
    deliv = deliv[deliv["route_id"].notna() & (deliv["route_id"] != "nan")].copy()
    deliv["seq_in_route"] = deliv["seq_in_route"].astype(int)
    legs["seq"] = legs["seq"].astype(int)

    # Join deliveries to route legs
    merged = deliv.merge(
        legs,
        left_on=["route_id", "seq_in_route"],
        right_on=["route_id", "seq"],
        how="inner",
        suffixes=("_deliv", "_leg")
    )

    # Use dispatch date if available, else date
    merged["event_date"] = merged["dispatch_date"].fillna(merged["date"])

    valid_rows = []
    quarantine_count = 0

    for idx, row in merged.iterrows():
        dt_str = str(row["event_date"]).split()[0]

        arr_dt = parse_hhmm_to_datetime(dt_str, row["arrival_time"])
        lv_dt = parse_hhmm_to_datetime(dt_str, row["leave_outlet_time"])
        w_open_dt = parse_hhmm_to_datetime(dt_str, row["window_open_time"])
        w_close_dt = parse_hhmm_to_datetime(dt_str, row["window_close_time"])

        if arr_dt is None or lv_dt is None or w_open_dt is None or w_close_dt is None:
            quarantine_count += 1
            continue

        # Handle midnight rollover if leave_outlet_time < arrival_time
        if lv_dt < arr_dt:
            lv_dt += timedelta(days=1)

        # Handle window open/close crossing midnight if window_close < window_open
        if w_close_dt < w_open_dt:
            w_close_dt += timedelta(days=1)

        # Early arrival waiting does NOT count towards service time
        service_start = max(arr_dt, w_open_dt)

        if lv_dt < service_start:
            quarantine_count += 1
            continue

        service_minutes = (lv_dt - service_start).total_seconds() / 60.0
        late_label = 1 if arr_dt > w_close_dt else 0

        # Sanity check: service time must be non-negative and reasonable (< 480 mins)
        if service_minutes < 0 or service_minutes > 480:
            quarantine_count += 1
            continue

        row_dict = row.to_dict()
        row_dict["target_service_min"] = service_minutes
        row_dict["target_late_prob"] = late_label
        valid_rows.append(row_dict)

    result_df = pd.DataFrame(valid_rows)
    print(f"Task 1 Label Construction: {len(result_df)} valid labeled rows generated. Quarantined {quarantine_count} rows.")
    return result_df
