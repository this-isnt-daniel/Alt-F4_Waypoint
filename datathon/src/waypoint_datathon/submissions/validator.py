import os
import subprocess
import pandas as pd
import numpy as np

def validate_all_submissions(
    sub_task1_path: str,
    sub_task2a_path: str,
    sub_task2b_path: str,
    checker_script_path: str
) -> dict:
    results = {"passed": True, "errors": [], "warnings": []}

    # 1. Validate Task 1 submission
    try:
        t1 = pd.read_csv(sub_task1_path)
        req_cols_1 = ["delivery_id", "pred_service_min", "pred_late_prob"]
        if list(t1.columns) != req_cols_1:
            results["passed"] = False
            results["errors"].append(f"Task 1 submission columns mismatch: got {list(t1.columns)}, expected {req_cols_1}")
        if t1["pred_service_min"].isna().any() or (t1["pred_service_min"] < 0).any():
            results["passed"] = False
            results["errors"].append("Task 1 pred_service_min contains missing or negative values.")
        if t1["pred_late_prob"].isna().any() or ((t1["pred_late_prob"] < 0) | (t1["pred_late_prob"] > 1)).any():
            results["passed"] = False
            results["errors"].append("Task 1 pred_late_prob contains missing or out-of-bound probabilities [0, 1].")
    except Exception as e:
        results["passed"] = False
        results["errors"].append(f"Failed to read/validate Task 1 submission file: {e}")

    # 2. Validate Task 2A submission
    try:
        t2a = pd.read_csv(sub_task2a_path)
        req_cols_2a = ["row_id", "pred_total_volume_m3", "pred_chilled_volume_m3"]
        if list(t2a.columns) != req_cols_2a:
            results["passed"] = False
            results["errors"].append(f"Task 2A submission columns mismatch: got {list(t2a.columns)}, expected {req_cols_2a}")
        if t2a["pred_total_volume_m3"].isna().any() or (t2a["pred_total_volume_m3"] < 0).any():
            results["passed"] = False
            results["errors"].append("Task 2A pred_total_volume_m3 contains missing or negative values.")
        if t2a["pred_chilled_volume_m3"].isna().any() or (t2a["pred_chilled_volume_m3"] < 0).any():
            results["passed"] = False
            results["errors"].append("Task 2A pred_chilled_volume_m3 contains missing or negative values.")
        if (t2a["pred_chilled_volume_m3"] > t2a["pred_total_volume_m3"] + 1e-6).any():
            results["passed"] = False
            results["errors"].append("Task 2A contains rows where pred_chilled_volume_m3 > pred_total_volume_m3.")
    except Exception as e:
        results["passed"] = False
        results["errors"].append(f"Failed to read/validate Task 2A submission file: {e}")

    # 3. Validate Task 2B submission with check_allocation.py
    if os.path.exists(checker_script_path):
        try:
            cmd = ["python", checker_script_path, sub_task2b_path]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            results["checker_output"] = proc.stdout + "\n" + proc.stderr
            if proc.returncode != 0 or "FEASIBILITY: PASSED" not in proc.stdout:
                results["passed"] = False
                results["errors"].append(f"check_allocation.py failed on Task 2B submission.\n{proc.stdout}\n{proc.stderr}")
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Failed to run check_allocation.py: {e}")
    else:
        results["warnings"].append(f"check_allocation.py script not found at {checker_script_path}")

    return results
