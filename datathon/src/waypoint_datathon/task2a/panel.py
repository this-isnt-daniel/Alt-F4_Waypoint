import pandas as pd
import numpy as np

def build_demand_panel(
    deliveries_train_df: pd.DataFrame,
    task1_test_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
    task2a_test_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Builds the historical and test demand panel aggregated by (depot, brand, iso_year, iso_week).
    """
    # Combine deliveries from train and task1 test inputs without duplication
    dt_cols = ["delivery_id", "order_date", "depot", "brand", "temp_requirement", "order_volume_m3"]

    train_sub = deliveries_train_df[dt_cols].copy()
    test_sub = task1_test_df[dt_cols].copy()

    combined = pd.concat([train_sub, test_sub], ignore_index=True)
    combined.drop_duplicates(subset=["delivery_id"], inplace=True)

    # Clean order_date and join with calendar to get iso_year, iso_week
    combined["date_clean"] = combined["order_date"].astype(str).str.split().str[0]

    cal_clean = calendar_df.copy()
    cal_clean["date_clean"] = cal_clean["date"].astype(str).str.split().str[0]
    date_to_isoweek = cal_clean[["date_clean", "iso_year", "iso_week"]].drop_duplicates("date_clean")

    combined = combined.merge(date_to_isoweek, on="date_clean", how="left")

    # Flag chilled orders
    combined["chilled_volume_m3"] = np.where(
        (combined["brand"] == "Fresh") & (combined["temp_requirement"] == "chilled"),
        combined["order_volume_m3"],
        0.0
    )

    # Aggregate by depot, brand, iso_year, iso_week
    agg = combined.groupby(["depot", "brand", "iso_year", "iso_week"], as_index=False).agg(
        total_volume_m3=("order_volume_m3", "sum"),
        chilled_volume_m3=("chilled_volume_m3", "sum")
    )

    # Force Style and Tech chilled volume to 0.0
    agg.loc[agg["brand"].isin(["Style", "Tech"]), "chilled_volume_m3"] = 0.0

    print(f"Demand Panel Built: {len(agg)} historical (depot, brand, iso_year, iso_week) rows.")
    return agg
