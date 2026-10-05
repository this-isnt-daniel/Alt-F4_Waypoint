import os
import argparse
import pandas as pd
from pathlib import Path

from waypoint_datathon.acquisition import acquire_datasets
from waypoint_datathon.validation import run_all_checks, enforce_schema_types
from waypoint_datathon.task1 import construct_task1_labels, build_task1_features, Task1Pipeline
from waypoint_datathon.task2a import build_demand_panel, build_task2a_features, Task2APipeline
from waypoint_datathon.task2b import adapt_task2b_scenario, solve_task2b_allocation
from waypoint_datathon.submissions import (
    serialize_task1_submission, serialize_task2a_submission, serialize_task2b_submission,
    validate_all_submissions
)

def run_full_pipeline(base_dir: Path):
    raw_dir = base_dir / "data" / "raw"
    data_dir = raw_dir / "data" if (raw_dir / "data").exists() else raw_dir
    artifacts_dir = base_dir / "artifacts" / "models"
    submissions_dir = base_dir / "submissions"

    # 1. Acquisition & Manifest
    print("\n--- STAGE 1: Data Acquisition & Manifest ---")
    manifest = acquire_datasets(str(raw_dir))
    print(f"Manifest completeness check: {manifest['completeness_check']}")

    # 2. Data Validation
    print("\n--- STAGE 2: Data Validation & Schema Checks ---")
    val_res = run_all_checks(str(raw_dir))
    print(f"Validation status: {val_res['passed']} (Warnings: {len(val_res['warnings'])}, Errors: {len(val_res['errors'])})")

    # Load shared datasets
    outlets = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "outlets.csv"))
    vehicles = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "vehicles.csv"))
    calendar = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "calendar.csv"))
    district_travel = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "district_travel.csv"))
    service_allowance = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "service_allowance.csv"))
    traffic_speed = pd.read_csv(data_dir / "General Data" / "traffic_speed.csv")
    road_conditions = pd.read_csv(data_dir / "General Data" / "road_conditions.csv")

    # 3. Task 1: Handling time & lateness model training & inference
    print("\n--- STAGE 3: Task 1 Model Training & Inference ---")
    deliveries_train = enforce_schema_types(pd.read_csv(data_dir / "Training Data" / "deliveries_train.csv"))
    route_legs_train = enforce_schema_types(pd.read_csv(data_dir / "Training Data" / "route_legs_train.csv"))

    task1_train_labeled = construct_task1_labels(deliveries_train, route_legs_train)
    X_train_t1, y_service_train, y_late_train = build_task1_features(
        task1_train_labeled, outlets, vehicles, calendar, traffic_speed, road_conditions, is_training=True
    )

    t1_pipeline = Task1Pipeline()
    t1_pipeline.fit(X_train_t1, y_service_train, y_late_train)

    metrics_t1 = t1_pipeline.evaluate(X_train_t1, y_service_train, y_late_train)
    print(f"Task 1 Evaluation Metrics: {metrics_t1}")

    t1_model_path = artifacts_dir / "task1_model.joblib"
    t1_pipeline.save(str(t1_model_path))

    # Inference for Task 1 test inputs
    task1_test_inputs = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task1_test_inputs.csv"))
    route_legs_test = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "route_legs_test.csv"))
    task1_test_merged = task1_test_inputs.merge(
        route_legs_test,
        left_on=["route_id", "seq_in_route"],
        right_on=["route_id", "seq"],
        how="left",
        suffixes=("_deliv", "_leg")
    )

    X_test_t1, _, _ = build_task1_features(
        task1_test_merged, outlets, vehicles, calendar, traffic_speed, road_conditions, is_training=False
    )
    pred_service, pred_late = t1_pipeline.predict(X_test_t1)

    t1_sub_path = submissions_dir / "submission_task1.csv"
    t1_template_path = data_dir / "Submission Templates" / "submission_task1.csv"
    serialize_task1_submission(
        str(t1_template_path),
        task1_test_inputs["delivery_id"].tolist(),
        pred_service,
        pred_late,
        str(t1_sub_path)
    )

    # Also sync copy to datathon root submissions folder and datathon/submission_task1.csv
    serialize_task1_submission(str(t1_template_path), task1_test_inputs["delivery_id"].tolist(), pred_service, pred_late, str(base_dir / "submission_task1.csv"))

    # 4. Task 2A: Depot Demand Forecasting
    print("\n--- STAGE 4: Task 2A Forecasting Model Training & Inference ---")
    task2a_test_inputs = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task2a_test_inputs.csv"))
    panel = build_demand_panel(deliveries_train, task1_test_inputs, calendar, task2a_test_inputs)

    train_feat_2a, test_feat_2a = build_task2a_features(panel, calendar, task2a_test_inputs)

    t2a_pipeline = Task2APipeline()
    t2a_pipeline.fit(train_feat_2a)

    t2a_model_path = artifacts_dir / "task2a_model.joblib"
    t2a_pipeline.save(str(t2a_model_path))

    pred_tot_vol, pred_chl_vol = t2a_pipeline.predict(test_feat_2a)

    t2a_sub_path = submissions_dir / "submission_task2a.csv"
    t2a_template_path = data_dir / "Submission Templates" / "submission_task2a.csv"
    serialize_task2a_submission(
        str(t2a_template_path),
        test_feat_2a["row_id"].tolist(),
        pred_tot_vol,
        pred_chl_vol,
        str(t2a_sub_path)
    )
    serialize_task2a_submission(str(t2a_template_path), test_feat_2a["row_id"].tolist(), pred_tot_vol, pred_chl_vol, str(base_dir / "submission_task2a.csv"))

    # 5. Task 2B: Peak-Day Fleet Allocation
    print("\n--- STAGE 5: Task 2B Fleet Allocation ---")
    task2b_scenarios = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task2b_peak_day_scenarios.csv"))
    task2b_fleet = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task2b_peak_day_fleet.csv"))

    adapted_scen = adapt_task2b_scenario(task2b_scenarios, task2b_fleet, vehicles, district_travel, service_allowance)
    alloc_res = solve_task2b_allocation(adapted_scen)

    t2b_sub_path = submissions_dir / "submission_task2b.csv"
    t2b_template_path = data_dir / "Submission Templates" / "submission_task2b.csv"
    serialize_task2b_submission(str(t2b_template_path), alloc_res, str(t2b_sub_path))
    serialize_task2b_submission(str(t2b_template_path), alloc_res, str(base_dir / "submission_task2b.csv"))

    # 6. Submission Validation
    print("\n--- STAGE 6: Official Submission Validation ---")
    checker_script = raw_dir / "check_allocation.py"
    sub_val = validate_all_submissions(str(t1_sub_path), str(t2a_sub_path), str(t2b_sub_path), str(checker_script))
    print(f"Final Submission Validation Passed: {sub_val['passed']}")
    if "checker_output" in sub_val:
        print(f"Official Allocation Checker Output:\n{sub_val['checker_output']}")

def main():
    parser = argparse.ArgumentParser(description="Waypoint Datathon CLI")
    parser.add_argument("--pipeline", action="store_true", help="Run full pipeline")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[2]
    run_full_pipeline(base_dir)

if __name__ == "__main__":
    main()
