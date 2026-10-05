"""Schema definitions and validation utilities for Datathon datasets."""
import pandas as pd

ID_COLUMNS = [
    "delivery_id", "route_id", "outlet_id", "vehicle_id", "leg_id",
    "order_ref", "row_id", "depot", "brand", "district", "to_outlet", "from_point"
]

NON_NEGATIVE_COLUMNS = [
    "order_weight_kg", "order_volume_m3", "order_units", "distance_km",
    "planned_travel_duration_min", "actual_travel_duration_min",
    "service_allowance_min", "depot_to_district_freeflow_min", "inter_stop_freeflow_min"
]

def enforce_schema_types(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce string types on all ID columns present in df."""
    df_out = df.copy()
    for col in ID_COLUMNS:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype(str).str.strip()
    return df_out

def check_non_negative(df: pd.DataFrame, df_name: str = "DataFrame") -> list[str]:
    issues = []
    for col in NON_NEGATIVE_COLUMNS:
        if col in df.columns:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                issues.append(f"{df_name}: Column '{col}' has {neg_count} negative values.")
    return issues

def validate_join(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    on_keys: list[str],
    left_name: str = "left",
    right_name: str = "right"
) -> dict:
    """Validate key uniqueness and report unmatched records prior to join."""
    left_keys = left_df[on_keys].drop_duplicates()
    right_keys = right_df[on_keys].drop_duplicates()

    left_total = len(left_df)
    right_total = len(right_df)

    # Check duplicates on keys if expected 1-to-1 or 1-to-many
    left_dupes = left_df.duplicated(subset=on_keys).sum()
    right_dupes = right_df.duplicated(subset=on_keys).sum()

    unmatched_left = left_df.merge(right_keys, on=on_keys, how="left", indicator=True)
    unmatched_left_count = (unmatched_left["_merge"] == "left_only").sum()

    unmatched_right = right_df.merge(left_keys, on=on_keys, how="left", indicator=True)
    unmatched_right_count = (unmatched_right["_merge"] == "left_only").sum()

    return {
        "left_total": left_total,
        "right_total": right_total,
        "left_dupes": int(left_dupes),
        "right_dupes": int(right_dupes),
        "unmatched_left_count": int(unmatched_left_count),
        "unmatched_right_count": int(unmatched_right_count),
        "on_keys": on_keys,
    }
