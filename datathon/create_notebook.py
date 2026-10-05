import json
from pathlib import Path

cells = [
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            '# Alt-F4 Datathon Final Notebook\n',
            '\n',
            '**Team Name:** Alt-F4  \n',
            '**Project:** Waypoint Datathon 2026 Solution  \n',
            '**Description:** End-to-end execution notebook covering Data Acquisition, Validation, Task 1 (Service Time & Lateness Prediction), Task 2A (10-Week Depot Demand Forecasting), and Task 2B (Peak-Day Fleet Allocation).'
        ]
    },
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': ['## Section 1: Environment Setup & Imports']
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            'import os\n',
            'import sys\n',
            'import pandas as pd\n',
            'import numpy as np\n',
            'from pathlib import Path\n',
            '\n',
            '# Ensure local packages are on path\n',
            'base_dir = Path.cwd()\n',
            'if (base_dir / "src").exists():\n',
            '    sys.path.insert(0, str(base_dir / "src"))\n',
            '\n',
            'from waypoint_datathon.acquisition import acquire_datasets\n',
            'from waypoint_datathon.validation import run_all_checks, enforce_schema_types\n',
            'from waypoint_datathon.task1 import construct_task1_labels, build_task1_features, Task1Pipeline\n',
            'from waypoint_datathon.task2a import build_demand_panel, build_task2a_features, Task2APipeline\n',
            'from waypoint_datathon.task2b import adapt_task2b_scenario, solve_task2b_allocation\n',
            'from waypoint_datathon.submissions import serialize_task1_submission, serialize_task2a_submission, serialize_task2b_submission, validate_all_submissions\n',
            '\n',
            'print("Environment initialized successfully.")'
        ]
    },
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': ['## Section 2: Data Acquisition & Manifest']
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            'raw_dir = base_dir / "data" / "raw"\n',
            'manifest = acquire_datasets(str(raw_dir))\n',
            'print(f"Manifest Completeness Check: {manifest[\'completeness_check\']}")\n',
            'print(f"Total Files Tracked: {len(manifest[\'files\'])}")'
        ]
    },
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': ['## Section 3: Data Integrity & Schema Validation']
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            'val_results = run_all_checks(str(raw_dir))\n',
            'print(f"Data Validation Status: {val_results[\'passed\']}\")\n',
            'print(f"Warnings: {len(val_results[\'warnings\'])}, Errors: {len(val_results[\'errors\'])}")'
        ]
    },
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': ['## Section 4: Task 1 - Service Time & Lateness Prediction']
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            'data_dir = raw_dir / "data" if (raw_dir / "data").exists() else raw_dir\n',
            'outlets = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "outlets.csv"))\n',
            'vehicles = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "vehicles.csv"))\n',
            'calendar = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "calendar.csv"))\n',
            'traffic_speed = pd.read_csv(data_dir / "General Data" / "traffic_speed.csv")\n',
            'road_conditions = pd.read_csv(data_dir / "General Data" / "road_conditions.csv")\n',
            '\n',
            'deliveries_train = enforce_schema_types(pd.read_csv(data_dir / "Training Data" / "deliveries_train.csv"))\n',
            'route_legs_train = enforce_schema_types(pd.read_csv(data_dir / "Training Data" / "route_legs_train.csv"))\n',
            '\n',
            'task1_train_labeled = construct_task1_labels(deliveries_train, route_legs_train)\n',
            'X_train_t1, y_service_train, y_late_train = build_task1_features(task1_train_labeled, outlets, vehicles, calendar, traffic_speed, road_conditions, is_training=True)\n',
            '\n',
            't1_pipeline = Task1Pipeline()\n',
            't1_pipeline.fit(X_train_t1, y_service_train, y_late_train)\n',
            '\n',
            'metrics_t1 = t1_pipeline.evaluate(X_train_t1, y_service_train, y_late_train)\n',
            'print(f"Task 1 Training Metrics: {metrics_t1}")\n',
            '\n',
            'artifacts_dir = base_dir / "artifacts" / "models"\n',
            'artifacts_dir.mkdir(parents=True, exist_ok=True)\n',
            't1_model_path = artifacts_dir / "task1_model.joblib"\n',
            't1_pipeline.save(str(t1_model_path))'
        ]
    },
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': ['## Section 5: Task 2A - 10-Week Depot Demand Forecasting']
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            'task1_test_inputs = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task1_test_inputs.csv"))\n',
            'task2a_test_inputs = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task2a_test_inputs.csv"))\n',
            '\n',
            'panel = build_demand_panel(deliveries_train, task1_test_inputs, calendar, task2a_test_inputs)\n',
            'train_feat_2a, test_feat_2a = build_task2a_features(panel, calendar, task2a_test_inputs)\n',
            '\n',
            't2a_pipeline = Task2APipeline()\n',
            't2a_pipeline.fit(train_feat_2a)\n',
            '\n',
            't2a_model_path = artifacts_dir / "task2a_model.joblib"\n',
            't2a_pipeline.save(str(t2a_model_path))'
        ]
    },
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': ['## Section 6: Task 2B - Peak-Day Fleet Allocation']
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            'district_travel = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "district_travel.csv"))\n',
            'service_allowance = enforce_schema_types(pd.read_csv(data_dir / "General Data" / "service_allowance.csv"))\n',
            'task2b_scenarios = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task2b_peak_day_scenarios.csv"))\n',
            'task2b_fleet = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "task2b_peak_day_fleet.csv"))\n',
            '\n',
            'adapted_scen = adapt_task2b_scenario(task2b_scenarios, task2b_fleet, vehicles, district_travel, service_allowance)\n',
            'alloc_res = solve_task2b_allocation(adapted_scen)'
        ]
    },
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': ['## Section 7: Submission Serializers & Official Verification']
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            'submissions_dir = base_dir / "submissions"\n',
            'submissions_dir.mkdir(parents=True, exist_ok=True)\n',
            '\n',
            '# Task 1 Inference\n',
            'route_legs_test = enforce_schema_types(pd.read_csv(data_dir / "Test Data" / "route_legs_test.csv"))\n',
            'task1_test_merged = task1_test_inputs.merge(route_legs_test, left_on=["route_id", "seq_in_route"], right_on=["route_id", "seq"], how="left")\n',
            'X_test_t1, _, _ = build_task1_features(task1_test_merged, outlets, vehicles, calendar, traffic_speed, road_conditions, is_training=False)\n',
            'pred_service, pred_late = t1_pipeline.predict(X_test_t1)\n',
            'serialize_task1_submission(str(data_dir / "Submission Templates" / "submission_task1.csv"), task1_test_inputs["delivery_id"].tolist(), pred_service, pred_late, str(submissions_dir / "submission_task1.csv"))\n',
            'serialize_task1_submission(str(data_dir / "Submission Templates" / "submission_task1.csv"), task1_test_inputs["delivery_id"].tolist(), pred_service, pred_late, str(base_dir / "submission_task1.csv"))\n',
            '\n',
            '# Task 2A Inference\n',
            'pred_tot_vol, pred_chl_vol = t2a_pipeline.predict(test_feat_2a)\n',
            'serialize_task2a_submission(str(data_dir / "Submission Templates" / "submission_task2a.csv"), test_feat_2a["row_id"].tolist(), pred_tot_vol, pred_chl_vol, str(submissions_dir / "submission_task2a.csv"))\n',
            'serialize_task2a_submission(str(data_dir / "Submission Templates" / "submission_task2a.csv"), test_feat_2a["row_id"].tolist(), pred_tot_vol, pred_chl_vol, str(base_dir / "submission_task2a.csv"))\n',
            '\n',
            '# Task 2B Serializing\n',
            'serialize_task2b_submission(str(data_dir / "Submission Templates" / "submission_task2b.csv"), alloc_res, str(submissions_dir / "submission_task2b.csv"))\n',
            'serialize_task2b_submission(str(data_dir / "Submission Templates" / "submission_task2b.csv"), alloc_res, str(base_dir / "submission_task2b.csv"))\n',
            '\n',
            '# Official Checker Run\n',
            'checker_script = raw_dir / "check_allocation.py"\n',
            'sub_val = validate_all_submissions(str(submissions_dir / "submission_task1.csv"), str(submissions_dir / "submission_task2a.csv"), str(submissions_dir / "submission_task2b.csv"), str(checker_script))\n',
            'print(f"Final Official Submission Checker Result: {sub_val[\'passed\']}\")\n',
            'if "checker_output" in sub_val:\n',
            '    print(f"Official Checker Output:\\n{sub_val[\'checker_output\']}")'
        ]
    },
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': ['## Mandatory Final Cell: Inference Demonstration from Saved Models']
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            '# Mandatory final cell loading saved model joblib files and demonstrating Task 1 and Task 2A inference\n',
            'import joblib\n',
            'import pandas as pd\n',
            'import numpy as np\n',
            'from pathlib import Path\n',
            '\n',
            'base_path = Path.cwd()\n',
            'models_dir = base_path / "artifacts" / "models"\n',
            '\n',
            '# 1. Load Saved Models\n',
            'loaded_t1_model = joblib.load(models_dir / "task1_model.joblib")\n',
            'loaded_t2a_model = joblib.load(models_dir / "task2a_model.joblib")\n',
            'print("SUCCESS: Loaded task1_model.joblib and task2a_model.joblib")\n',
            '\n',
            '# 2. Demonstrate Task 1 Inference\n',
            'sample_t1_inputs = pd.DataFrame([\n',
            '    {\n',
            '        "brand": "Fresh", "depot": "Peliyagoda", "district": "Colombo", "dock_type": "rear_dock",\n',
            '        "parking_constraint": "normal", "temp_requirement": "chilled", "vehicle_type": "truck", "vehicle_temp": "reefer",\n',
            '        "order_units": 50, "order_weight_kg": 600.0, "order_volume_m3": 4.5, "distance_km": 18.5,\n',
            '        "planned_travel_duration_min": 25.0, "seq_in_route": 1, "planned_depart_hour": 4.5, "planned_arrival_hour": 5.0,\n',
            '        "window_duration_min": 150.0, "arrival_slack_min": 180.0, "dow": 1, "is_weekend": 0,\n',
            '        "is_payday": 1, "is_holiday": 0, "monsoon": 0, "festival_ramp": 0.5, "traffic_speed_index": 95.0, "road_disruption_index": 100.0\n',
            '    },\n',
            '    {\n',
            '        "brand": "Style", "depot": "Peliyagoda", "district": "Gampaha", "dock_type": "street",\n',
            '        "parking_constraint": "van_only", "temp_requirement": "ambient", "vehicle_type": "van", "vehicle_temp": "ambient",\n',
            '        "order_units": 120, "order_weight_kg": 300.0, "order_volume_m3": 8.0, "distance_km": 37.0,\n',
            '        "planned_travel_duration_min": 45.0, "seq_in_route": 2, "planned_depart_hour": 9.0, "planned_arrival_hour": 10.0,\n',
            '        "window_duration_min": 240.0, "arrival_slack_min": 120.0, "dow": 3, "is_weekend": 0,\n',
            '        "is_payday": 0, "is_holiday": 0, "monsoon": 1, "festival_ramp": 0.0, "traffic_speed_index": 80.0, "road_disruption_index": 85.0\n',
            '    }\n',
            '])\n',
            '\n',
            'demo_service, demo_late = loaded_t1_model.predict(sample_t1_inputs)\n',
            'print("\\n--- TASK 1 INFERENCE DEMO ---")\n',
            'for i in range(len(sample_t1_inputs)):\n',
            '    b = sample_t1_inputs.loc[i, "brand"]\n',
            '    d = sample_t1_inputs.loc[i, "district"]\n',
            '    print(f"Sample {i+1} [{b} -> {d}]: Predicted Handling Time = {demo_service[i]:.2f} min, Predicted Lateness Prob = {demo_late[i]:.4f}")\n',
            '\n',
            '# 3. Demonstrate Task 2A Inference\n',
            'sample_t2a_inputs = pd.DataFrame([\n',
            '    {\n',
            '        "depot": "Peliyagoda", "brand": "Fresh", "iso_week": 42,\n',
            '        "operating_days": 6, "payday_count": 1, "festival_ramp_max": 0.8, "monsoon_mode": 0,\n',
            '        "lag_tot_10": 420.0, "lag_tot_11": 410.0, "lag_tot_12": 390.0, "lag_tot_13": 405.0, "lag_tot_14": 400.0,\n',
            '        "lag_chl_10": 150.0, "lag_chl_11": 145.0, "lag_chl_12": 140.0, "lag_chl_13": 148.0, "lag_chl_14": 142.0\n',
            '    },\n',
            '    {\n',
            '        "depot": "Kandy", "brand": "Style", "iso_week": 42,\n',
            '        "operating_days": 6, "payday_count": 0, "festival_ramp_max": 0.0, "monsoon_mode": 1,\n',
            '        "lag_tot_10": 110.0, "lag_tot_11": 105.0, "lag_tot_12": 115.0, "lag_tot_13": 108.0, "lag_tot_14": 112.0,\n',
            '        "lag_chl_10": 0.0, "lag_chl_11": 0.0, "lag_chl_12": 0.0, "lag_chl_13": 0.0, "lag_chl_14": 0.0\n',
            '    }\n',
            '])\n',
            '\n',
            'demo_tot, demo_chl = loaded_t2a_model.predict(sample_t2a_inputs)\n',
            'print("\\n--- TASK 2A INFERENCE DEMO ---")\n',
            'for i in range(len(sample_t2a_inputs)):\n',
            '    dep = sample_t2a_inputs.loc[i, "depot"]\n',
            '    b = sample_t2a_inputs.loc[i, "brand"]\n',
            '    print(f"Sample {i+1} [{dep} - {b}]: Predicted Total Volume = {demo_tot[i]:.2f} m3, Predicted Chilled Volume = {demo_chl[i]:.2f} m3")\n'
        ]
    }
]

nb_dict = {
    'cells': cells,
    'metadata': {'language_info': {'name': 'python'}},
    'nbformat': 4,
    'nbformat_minor': 4
}

out_path = Path('datathon/Alt-F4_FinalNotebook.ipynb')
out_path.write_text(json.dumps(nb_dict, indent=2), encoding='utf-8')
print("Canonical Notebook Alt-F4_FinalNotebook.ipynb created successfully.")

alias_cells = [
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            '# Canonical Notebook Redirect\n',
            '\n',
            'Please refer to `Alt-F4_FinalNotebook.ipynb` for our team\'s complete Datathon implementation notebook.'
        ]
    }
]
alias_nb = {'cells': alias_cells, 'metadata': {'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 4}
Path('datathon/TeamName_FinalNotebook.ipynb').write_text(json.dumps(alias_nb, indent=2), encoding='utf-8')
