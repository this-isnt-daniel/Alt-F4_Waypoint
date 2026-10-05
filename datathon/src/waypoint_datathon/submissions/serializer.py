import os
import pandas as pd
import numpy as np

def serialize_task1_submission(
    template_path: str,
    delivery_ids: list[str],
    pred_service_min: np.ndarray,
    pred_late_prob: np.ndarray,
    output_path: str
) -> pd.DataFrame:
    tpl = pd.read_csv(template_path)
    df_preds = pd.DataFrame({
        "delivery_id": [str(d).strip() for d in delivery_ids],
        "pred_service_min": np.round(pred_service_min, 4),
        "pred_late_prob": np.round(pred_late_prob, 4)
    })

    merged = tpl[["delivery_id"]].merge(df_preds, on="delivery_id", how="left")
    merged["pred_service_min"] = merged["pred_service_min"].fillna(15.0)
    merged["pred_late_prob"] = merged["pred_late_prob"].fillna(0.0)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged.to_csv(output_path, index=False)
    print(f"Serialized Task 1 submission to {output_path} ({len(merged)} rows).")
    return merged

def serialize_task2a_submission(
    template_path: str,
    row_ids: list[str],
    pred_total_volume_m3: np.ndarray,
    pred_chilled_volume_m3: np.ndarray,
    output_path: str
) -> pd.DataFrame:
    tpl = pd.read_csv(template_path)
    df_preds = pd.DataFrame({
        "row_id": [str(r).strip() for r in row_ids],
        "pred_total_volume_m3": np.round(pred_total_volume_m3, 4),
        "pred_chilled_volume_m3": np.round(pred_chilled_volume_m3, 4)
    })

    merged = tpl[["row_id"]].merge(df_preds, on="row_id", how="left")
    merged["pred_total_volume_m3"] = merged["pred_total_volume_m3"].fillna(0.0)
    merged["pred_chilled_volume_m3"] = merged["pred_chilled_volume_m3"].fillna(0.0)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged.to_csv(output_path, index=False)
    print(f"Serialized Task 2A submission to {output_path} ({len(merged)} rows).")
    return merged

def serialize_task2b_submission(
    template_path: str,
    allocation_df: pd.DataFrame,
    output_path: str
) -> pd.DataFrame:
    tpl = pd.read_csv(template_path)

    clean_alloc = allocation_df.copy()
    clean_alloc["vehicle_id"] = np.where(clean_alloc["decision"] == "deferred", "", clean_alloc["vehicle_id"].fillna(""))
    clean_alloc["trip_id"] = np.where(clean_alloc["decision"] == "deferred", "", clean_alloc["trip_id"].fillna(""))

    merged = tpl[["scenario", "order_ref", "outlet_id"]].merge(
        clean_alloc[["scenario", "order_ref", "decision", "vehicle_id", "trip_id"]],
        on=["scenario", "order_ref"],
        how="left"
    )

    merged["decision"] = merged["decision"].fillna("deferred")
    merged["vehicle_id"] = merged["vehicle_id"].fillna("")
    merged["trip_id"] = merged["trip_id"].fillna("")

    # Standardize trip_id formatting for served orders (integer 1 or 2 as string or numeric)
    def fmt_trip(val):
        if pd.isna(val) or str(val).strip() in ["", "nan", "None"]:
            return ""
        try:
            return str(int(float(val)))
        except Exception:
            return str(val)

    merged["trip_id"] = merged["trip_id"].apply(fmt_trip)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged.to_csv(output_path, index=False)
    print(f"Serialized Task 2B submission to {output_path} ({len(merged)} rows).")
    return merged
