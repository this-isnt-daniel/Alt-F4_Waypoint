import pandas as pd
import numpy as np

def build_task2a_features(
    panel_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
    task2a_test_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Builds feature matrix for Task 2A forecasting, including lag features and calendar aggregations.
    """
    panel = panel_df.copy()

    # Create a unique year_week index for ordering
    panel["week_idx"] = panel["iso_year"] * 52 + panel["iso_week"]

    # Ensure complete grid of (depot, brand, week_idx)
    depots = panel["depot"].unique()
    brands = panel["brand"].unique()

    test = task2a_test_df.copy()
    test["week_idx"] = test["iso_year"] * 52 + test["iso_week"]

    min_week = panel["week_idx"].min()
    max_week = test["week_idx"].max()

    full_grid_rows = []
    for d in depots:
        for b in brands:
            for w in range(min_week, max_week + 1):
                # reconstruct year and week
                y = w // 52
                wk = w % 52
                if wk == 0:
                    y -= 1
                    wk = 52
                full_grid_rows.append({"depot": d, "brand": b, "iso_year": y, "iso_week": wk, "week_idx": w})

    full_grid = pd.DataFrame(full_grid_rows)
    merged = full_grid.merge(panel, on=["depot", "brand", "iso_year", "iso_week", "week_idx"], how="left")
    merged["total_volume_m3"] = merged["total_volume_m3"].fillna(0.0)
    merged["chilled_volume_m3"] = merged["chilled_volume_m3"].fillna(0.0)
    merged.sort_values(by=["depot", "brand", "week_idx"], inplace=True)

    # Calculate weekly calendar features
    cal = calendar_df.copy()
    cal_weekly = cal.groupby(["iso_year", "iso_week"], as_index=False).agg(
        operating_days=("is_operating", "sum"),
        payday_count=("is_payday", "sum"),
        festival_ramp_max=("festival_ramp", "max"),
        monsoon_mode=("monsoon", "max")
    )
    cal_weekly["week_idx"] = cal_weekly["iso_year"] * 52 + cal_weekly["iso_week"]

    merged = merged.merge(cal_weekly[["week_idx", "operating_days", "payday_count", "festival_ramp_max", "monsoon_mode"]], on="week_idx", how="left")
    merged["operating_days"] = merged["operating_days"].fillna(6)

    # Build lag features per (depot, brand) group (lags >= 10 to avoid future leakage across the 10-week test window)
    feature_rows = []
    test_week_idxs = set(test["week_idx"])

    for (d, b), g in merged.groupby(["depot", "brand"]):
        g = g.sort_values("week_idx").copy()
        for i in range(len(g)):
            row = g.iloc[i].to_dict()
            current_w = row["week_idx"]

            # Lags 10 to 14
            for lag in range(10, 15):
                past_val_tot = g.loc[g["week_idx"] == current_w - lag, "total_volume_m3"]
                past_val_chl = g.loc[g["week_idx"] == current_w - lag, "chilled_volume_m3"]
                row[f"lag_tot_{lag}"] = past_val_tot.values[0] if len(past_val_tot) > 0 else 0.0
                row[f"lag_chl_{lag}"] = past_val_chl.values[0] if len(past_val_chl) > 0 else 0.0

            feature_rows.append(row)

    feat_df = pd.DataFrame(feature_rows)

    # Split into historical training set (where target is known and week_idx < min(test_week_idxs))
    train_feat = feat_df[feat_df["week_idx"] < min(test_week_idxs)].copy()

    # Join test inputs to get exact test rows
    test_feat = test.merge(feat_df, on=["depot", "brand", "iso_year", "iso_week"], how="left")

    return train_feat, test_feat
