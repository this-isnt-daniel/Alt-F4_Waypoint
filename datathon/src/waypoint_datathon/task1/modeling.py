import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, log_loss, brier_score_loss, roc_auc_score

from .features import CATEGORICAL_COLS, NUMERICAL_COLS

class Task1Pipeline:
    """End-to-end pipeline for Task 1 handling time and lateness prediction."""

    def __init__(self):
        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLS),
                ("num", StandardScaler(), NUMERICAL_COLS)
            ]
        )

        self.service_model = Pipeline([
            ("prep", preprocessor),
            ("reg", HistGradientBoostingRegressor(max_iter=150, random_state=42))
        ])

        base_clf = HistGradientBoostingClassifier(max_iter=150, random_state=42)
        self.lateness_model = Pipeline([
            ("prep", preprocessor),
            ("clf", CalibratedClassifierCV(estimator=base_clf, cv=3))
        ])

    def fit(self, X: pd.DataFrame, y_service: pd.Series, y_late: pd.Series):
        print("Fitting Task 1 Service Time Regressor...")
        self.service_model.fit(X, y_service)

        print("Fitting Task 1 Lateness Probability Classifier...")
        self.lateness_model.fit(X, y_late)

    def predict(self, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        pred_service = self.service_model.predict(X)
        pred_service = np.maximum(0.0, pred_service)  # Ensure non-negative handling time

        pred_late_prob = self.lateness_model.predict_proba(X)[:, 1]
        pred_late_prob = np.clip(pred_late_prob, 0.0, 1.0)  # Ensure probability bounds

        return pred_service, pred_late_prob

    def evaluate(self, X: pd.DataFrame, y_service: pd.Series, y_late: pd.Series) -> dict:
        pred_service, pred_late_prob = self.predict(X)

        mae = mean_absolute_error(y_service, pred_service)
        rmse = root_mean_squared_error(y_service, pred_service)

        ll = log_loss(y_late, pred_late_prob)
        brier = brier_score_loss(y_late, pred_late_prob)
        auc = roc_auc_score(y_late, pred_late_prob) if len(np.unique(y_late)) > 1 else 0.5

        metrics = {
            "service_mae": float(mae),
            "service_rmse": float(rmse),
            "lateness_log_loss": float(ll),
            "lateness_brier_score": float(brier),
            "lateness_roc_auc": float(auc)
        }
        return metrics

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)
        print(f"Task 1 model saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "Task1Pipeline":
        return joblib.load(filepath)
