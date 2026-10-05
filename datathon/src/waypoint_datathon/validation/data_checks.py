"""Full dataset integrity checking routines."""
import pandas as pd
from pathlib import Path
from .schema import enforce_schema_types, check_non_negative, validate_join

def run_all_checks(data_raw_dir: str) -> dict:
    raw_path = Path(data_raw_dir)
    data_dir = raw_path / "data" if (raw_path / "data").exists() else raw_path

    results = {
        "passed": True,
        "warnings": [],
        "errors": [],
        "file_stats": {}
    }

    # Load datasets
    try:
        outlets = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "outlets.csv"))
        vehicles = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "vehicles.csv"))
        calendar = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "calendar.csv"))
        district_travel = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "district_travel.csv"))
        service_allowance = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "service_allowance.csv"))

        deliveries_train = enforce_schema_types(pd.read_csv(data_dir / "Training Data" / "deliveries_train.csv"))
        route_legs_train = enforce_schema_types(pd.read_csv(data_dir / "Training Data" / "route_legs_train.csv"))

        task1_test = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task1_test_inputs.csv"))
        route_legs_test = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "route_legs_test.csv"))
        task2a_test = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task2a_test_inputs.csv"))
        task2b_scenarios = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task2b_peak_day_scenarios.csv"))
        task2b_fleet = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task2b_peak_day_fleet.csv"))

        tpl_task1 = enforce_schema_types(pd.read_csv(data_dir / "Submission Templates" / "submission_task1.csv"))
        tpl_task2a = enforce_schema_types(pd.read_csv(data_dir / "Submission Templates" / "submission_task2a.csv"))
        tpl_task2b = enforce_schema_types(pd.read_csv(data_dir / "Submission Templates" / "submission_task2b.csv"))
    except Exception as e:
        results["passed"] = False
        results["errors"].append(f"Failed to load CSV files: {e}")
        return results

    # Record row counts
    dfs = {
        "outlets": outlets, "vehicles": vehicles, "calendar": calendar,
        "deliveries_train": deliveries_train, "route_legs_train": route_legs_train,
        "task1_test": task1_test, "route_legs_test": route_legs_test,
        "task2a_test": task2a_test, "task2b_scenarios": task2b_scenarios, "task2b_fleet": task2b_fleet,
        "tpl_task1": tpl_task1, "tpl_task2a": tpl_task2a, "tpl_task2b": tpl_task2b
    }
    for name, df in dfs.items():
        results["file_stats"][name] = {"rows": len(df), "cols": len(df.columns)}
        neg_issues = check_non_negative(df, name)
        if neg_issues:
            results["warnings"].extend(neg_issues)

    # Key uniqueness & join integrity
    # 1. Task 1 test inputs vs template
    if len(task1_test) != len(tpl_task1):
        results["passed"] = False
        results["errors"].append(f"Task 1 test row count ({len(task1_test)}) != template ({len(tpl_task1)})")

    if list(task1_test["delivery_id"]) != list(tpl_task1["delivery_id"]):
        results["passed"] = False
        results["errors"].append("Task 1 delivery_id order mismatch between test inputs and template")

    # 2. Join deliveries_train to route_legs_train on route_id + seq_in_route=seq
    dispatched_train = deliveries_train[deliveries_train["route_id"].notna() & (deliveries_train["route_id"] != "nan")].copy()
    dispatched_train["seq_in_route"] = dispatched_train["seq_in_route"].astype(int)
    route_legs_train["seq"] = route_legs_train["seq"].astype(int)

    join_res = validate_join(
        dispatched_train, route_legs_train,
        on_keys=["route_id"], left_name="dispatched_train", right_name="route_legs_train"
    )
    if join_res["unmatched_left_count"] > 0:
        results["warnings"].append(f"Training deliveries has {join_res['unmatched_left_count']} unmatched route_ids in route_legs_train.")

    # 3. Task 2a test inputs vs template
    if len(task2a_test) != len(tpl_task2a):
        results["passed"] = False
        results["errors"].append(f"Task 2A test row count ({len(task2a_test)}) != template ({len(tpl_task2a)})")

    # 4. Task 2b test inputs vs template
    if len(task2b_scenarios) != len(tpl_task2b):
        results["passed"] = False
        results["errors"].append(f"Task 2B scenario row count ({len(task2b_scenarios)}) != template ({len(tpl_task2b)})")

    return results

if __name__ == "__main__":
    from pathlib import Path
    base = Path(__file__).resolve().parents[3]
    raw_dir = base / "data" / "raw"
    res = run_all_checks(str(raw_dir))
    print(f"Data validation passed: {res['passed']}")
    print(f"Warnings: {len(res['warnings'])}, Errors: {len(res['errors'])}")
