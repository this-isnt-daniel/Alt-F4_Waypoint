import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

CAT_COLS = ["depot", "brand"]
NUM_COLS = [
    "iso_week", "operating_days", "payday_count", "festival_ramp_max", "monsoon_mode",
    "lag_tot_10", "lag_tot_11", "lag_tot_12", "lag_tot_13", "lag_tot_14",
    "lag_chl_10", "lag_chl_11", "lag_chl_12", "lag_chl_13", "lag_chl_14"
]

class Task2APipeline:
    """End-to-end forecasting pipeline for Task 2A depot demand."""

    def __init__(self):
        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS),
                ("num", StandardScaler(), NUM_COLS)
            ]
        )

        self.tot_model = Pipeline([
            ("prep", preprocessor),
            ("reg", HistGradientBoostingRegressor(max_iter=150, random_state=42))
        ])

        self.chl_model = Pipeline([
            ("prep", preprocessor),
            ("reg", HistGradientBoostingRegressor(max_iter=150, random_state=42))
        ])

    def fit(self, train_df: pd.DataFrame):
        X = train_df[CAT_COLS + NUM_COLS].copy()
        y_tot = train_df["total_volume_m3"]
        y_chl = train_df["chilled_volume_m3"]

        print("Fitting Task 2A Total Volume Forecaster...")
        self.tot_model.fit(X, y_tot)

        print("Fitting Task 2A Chilled Volume Forecaster...")
        self.chl_model.fit(X, y_chl)

    def predict(self, test_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        X_test = test_df[CAT_COLS + NUM_COLS].copy()

        pred_tot = self.tot_model.predict(X_test)
        pred_tot = np.maximum(0.0, pred_tot)

        pred_chl = self.chl_model.predict(X_test)
        pred_chl = np.maximum(0.0, pred_chl)

        # Enforce chilled <= total constraint
        pred_chl = np.minimum(pred_chl, pred_tot)

        # Force Style and Tech chilled predictions to 0.0 exactly
        is_fresh = test_df["brand"] == "Fresh"
        pred_chl = np.where(is_fresh, pred_chl, 0.0)

        return pred_tot, pred_chl

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)
        print(f"Task 2A model saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "Task2APipeline":
        return joblib.load(filepath)
