import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from waypoint_datathon.validation import enforce_schema_types, check_non_negative, validate_join
from waypoint_datathon.task1 import construct_task1_labels, build_task1_features, Task1Pipeline
from waypoint_datathon.task2a import build_demand_panel, build_task2a_features
from waypoint_datathon.task2b import adapt_task2b_scenario, calculate_order_priority, solve_task2b_allocation
from waypoint_datathon.task2b.solver import calculate_trip_time

def test_task1_label_rules():
    # Synthetic test fixture for label rules:
    # 1. Early arrival waiting does not count as handling time
    # 2. Arrival exactly at window close is not late
    # 3. Arrival after window close is late
    deliv_data = pd.DataFrame([
        {
            "delivery_id": "ORD001", "route_id": "R001", "seq_in_route": 0, "dispatch_status": "attempted",
            "dispatch_date": "2026-10-01", "planned_arrival_time": "05:00", "window_open_time": "05:30", "window_close_time": "08:00"
        },
        {
            "delivery_id": "ORD002", "route_id": "R001", "seq_in_route": 1, "dispatch_status": "attempted",
            "dispatch_date": "2026-10-01", "planned_arrival_time": "08:00", "window_open_time": "05:30", "window_close_time": "08:00"
        },
        {
            "delivery_id": "ORD003", "route_id": "R001", "seq_in_route": 2, "dispatch_status": "attempted",
            "dispatch_date": "2026-10-01", "planned_arrival_time": "08:30", "window_open_time": "05:30", "window_close_time": "08:00"
        },
    ])

    legs_data = pd.DataFrame([
        # ORD001: Arrives early at 05:00, window opens 05:30, leaves 05:45 -> service_start=05:30, handling time=15 min, late=0
        {"route_id": "R001", "seq": 0, "arrival_time": "05:00", "leave_outlet_time": "05:45", "date": "2026-10-01"},
        # ORD002: Arrives exactly at closing time 08:00, leaves 08:20 -> handling time=20 min, late=0
        {"route_id": "R001", "seq": 1, "arrival_time": "08:00", "leave_outlet_time": "08:20", "date": "2026-10-01"},
        # ORD003: Arrives late at 08:05, leaves 08:25 -> handling time=20 min, late=1
        {"route_id": "R001", "seq": 2, "arrival_time": "08:05", "leave_outlet_time": "08:25", "date": "2026-10-01"},
    ])

    labeled = construct_task1_labels(deliv_data, legs_data)
    assert len(labeled) == 3

    ord1 = labeled[labeled["delivery_id"] == "ORD001"].iloc[0]
    assert ord1["target_service_min"] == 15.0
    assert ord1["target_late_prob"] == 0

    ord2 = labeled[labeled["delivery_id"] == "ORD002"].iloc[0]
    assert ord2["target_service_min"] == 20.0
    assert ord2["target_late_prob"] == 0

    ord3 = labeled[labeled["delivery_id"] == "ORD003"].iloc[0]
    assert ord3["target_service_min"] == 20.0
    assert ord3["target_late_prob"] == 1

def test_task2b_trip_time_calculation():
    dtravel = {"Gampaha": {"depot_to_district_freeflow_min": 37.0, "inter_stop_freeflow_min": 9.0}}
    allowance = {("Fresh", "rear_dock"): 15.0, ("Fresh", "street"): 16.0}

    # Trip to Gampaha with 3 Fresh stops: two rear_dock, one street
    tt = calculate_trip_time("Gampaha", "Fresh", ["rear_dock", "rear_dock", "street"], dtravel, allowance)
    # 37 + (3-1)*9 + 15 + 15 + 16 = 37 + 18 + 46 = 101.0
    assert tt == 101.0

def test_task2b_prioritization():
    ord_fresh_chilled = pd.Series({"brand": "Fresh", "temp_requirement": "chilled", "deferred_yesterday": 1, "days_since_last_served": 2})
    ord_style_ambient = pd.Series({"brand": "Style", "temp_requirement": "ambient", "deferred_yesterday": 0, "days_since_last_served": 1})

    p_fresh = calculate_order_priority(ord_fresh_chilled)
    p_style = calculate_order_priority(ord_style_ambient)

    assert p_fresh > p_style
