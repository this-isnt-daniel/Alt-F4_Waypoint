import pandas as pd
import numpy as np

CATEGORICAL_COLS = [
    "brand", "depot", "district", "dock_type", "parking_constraint",
    "temp_requirement", "vehicle_type", "vehicle_temp"
]

NUMERICAL_COLS = [
    "order_units", "order_weight_kg", "order_volume_m3", "distance_km",
    "planned_travel_duration_min", "seq_in_route", "planned_depart_hour",
    "planned_arrival_hour", "window_duration_min", "arrival_slack_min",
    "dow", "is_weekend", "is_payday", "is_holiday", "monsoon", "festival_ramp",
    "traffic_speed_index", "road_disruption_index"
]

def hhmm_to_minutes(hhmm_str: str) -> float:
    if pd.isna(hhmm_str):
        return 0.0
    try:
        parts = str(hhmm_str).strip().split(":")
        return float(int(parts[0]) * 60 + int(parts[1]))
    except Exception:
        return 0.0

def resolve_col(df: pd.DataFrame, target_name: str) -> pd.Series:
    """Helper to resolve column name if suffixes like _deliv or _leg were attached."""
    if target_name in df.columns:
        return df[target_name]
    for suf in ["_deliv", "_leg", "_x", "_y"]:
        if f"{target_name}{suf}" in df.columns:
            return df[f"{target_name}{suf}"]
    return pd.Series(np.nan, index=df.index)

def build_task1_features(
    df: pd.DataFrame,
    outlets_df: pd.DataFrame,
    vehicles_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
    traffic_speed_df: pd.DataFrame,
    road_conditions_df: pd.DataFrame,
    is_training: bool = True
) -> tuple[pd.DataFrame, pd.Series | None, pd.Series | None]:
    """
    Builds prediction-time features for Task 1, preventing data leakage.
    """
    data = df.copy()

    # Ensure outlet metadata is merged if not present
    if "dock_type" not in data.columns and "outlet_id" in data.columns:
        data = data.merge(outlets_df[["outlet_id", "dock_type", "parking_constraint"]], on="outlet_id", how="left")

    planned_depart = resolve_col(data, "planned_depart_time")
    planned_arrival = resolve_col(data, "planned_arrival_time")
    window_open = resolve_col(data, "window_open_time")
    window_close = resolve_col(data, "window_close_time")

    # Parse clock times to minutes from midnight
    data["planned_depart_min"] = planned_depart.apply(hhmm_to_minutes)
    data["planned_arrival_min"] = planned_arrival.apply(hhmm_to_minutes)
    data["window_open_min"] = window_open.apply(hhmm_to_minutes)
    data["window_close_min"] = window_close.apply(hhmm_to_minutes)

    data["planned_depart_hour"] = data["planned_depart_min"] / 60.0
    data["planned_arrival_hour"] = data["planned_arrival_min"] / 60.0

    # Calculate window duration and slack
    w_close = np.where(data["window_close_min"] < data["window_open_min"], data["window_close_min"] + 1440, data["window_close_min"])
    data["window_duration_min"] = w_close - data["window_open_min"]
    data["arrival_slack_min"] = w_close - data["planned_arrival_min"]

    # Resolve numerical columns if suffixed
    for col_name in ["distance_km", "planned_travel_duration_min", "seq_in_route", "order_units", "order_weight_kg", "order_volume_m3"]:
        data[col_name] = resolve_col(data, col_name)

    # Merge calendar features
    date_col = "order_date" if "order_date" in data.columns else ("dispatch_date" if "dispatch_date" in data.columns else "date")
    if date_col in data.columns:
        data["date_clean"] = data[date_col].astype(str).str.split().str[0]
        cal_clean = calendar_df.copy()
        cal_clean["date_clean"] = cal_clean["date"].astype(str).str.split().str[0]
        cal_cols = ["date_clean", "dow", "is_weekend", "is_payday", "is_holiday", "monsoon", "festival_ramp"]
        data = data.merge(cal_clean[cal_cols].drop_duplicates("date_clean"), on="date_clean", how="left")
    else:
        for c in ["dow", "is_weekend", "is_payday", "is_holiday", "monsoon", "festival_ramp"]:
            if c not in data.columns:
                data[c] = 0

    # Traffic speed index lookup by monsoon & hour
    if "monsoon" in data.columns and not traffic_speed_df.empty:
        traffic_map = traffic_speed_df.groupby(["monsoon"])["speed_index"].mean().to_dict()
        data["traffic_speed_index"] = data["monsoon"].map(traffic_map).fillna(100.0)
    else:
        data["traffic_speed_index"] = 100.0

    # Road disruption index lookup
    if "date_clean" in data.columns and "district" in data.columns and not road_conditions_df.empty:
        rc_clean = road_conditions_df.copy()
        rc_clean["date_clean"] = rc_clean["date"].astype(str).str.split().str[0]
        data = data.merge(rc_clean[["date_clean", "district", "disruption_index"]], on=["date_clean", "district"], how="left")
        data["road_disruption_index"] = data["disruption_index"].fillna(100.0)
        data.drop(columns=["disruption_index"], inplace=True, errors="ignore")
    else:
        data["road_disruption_index"] = 100.0

    # Fill numerical missing values
    for col in NUMERICAL_COLS:
        if col not in data.columns:
            data[col] = 0.0
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0.0)

    # One-hot / Category encoding for categoricals
    for col in CATEGORICAL_COLS:
        val = resolve_col(data, col)
        data[col] = val.fillna("unknown").astype(str)

    feature_cols = CATEGORICAL_COLS + NUMERICAL_COLS
    X = data[feature_cols].copy()

    y_service = data["target_service_min"] if "target_service_min" in data.columns else None
    y_late = data["target_late_prob"] if "target_late_prob" in data.columns else None

    return X, y_service, y_late
