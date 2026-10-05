# Alt-F4 Datathon Solution & Reproduction Guide

**Team Name:** Alt-F4  
**Competition:** Tech-Triathlon 2026 - Datathon Phase  
**Deadline:** October 9, 2026, 11:59 PM Asia/Colombo  

---

## 1. Overview
This repository contains the complete, autonomous Datathon solution built for Alt-F4 Waypoint. The solution includes:
- **Data Acquisition & Manifest Engine:** Hashes and validates all 18 official dataset files.
- **Data Validation & Integrity Checks:** Validates keys, schemas, clock times, non-negative quantities, and unit relationships.
- **Task 1 (Handling Time & Lateness Prediction):** Leakage-free feature engineering and ML pipeline trained from scratch (`service_mae`: 4.47 min, `lateness_roc_auc`: 0.9327).
- **Task 2A (Depot Demand Forecasting):** 10-week multi-depot and brand forecast pipeline using lag features.
- **Task 2B (Peak-Day Fleet Allocation):** Priority-weighted fleet allocation solver for Peliyagoda scenario S1 adhering 100% to all 7 feasibility rules.
- **Submission Serializers & Validation:** Verified via the official `check_allocation.py`.

---

## 2. Reproduction Commands

### Environment Setup
```bash
# Install the Datathon package in editable mode
pip install -e datathon/

# Install the Optimization Engine in editable mode
pip install -e apps/backend/optimization_engine/
```

### Full Automated Pipeline Execution
To execute data acquisition, schema checks, model training, submission serialization, and official allocation checking in one command:
```bash
python -m waypoint_datathon.cli --pipeline
```

### Running Unit & Regression Tests
```bash
# Run Datathon unit tests
python -m pytest datathon/tests/test_datathon.py

# Run Optimization Engine regression tests
python -m pytest apps/backend/optimization_engine/tests/
```

### Official Feasibility Checker Run
```bash
python datathon/data/raw/check_allocation.py datathon/submissions/submission_task2b.csv
```

---

## 3. Deliverable Map
- **Canonical Notebook:** `datathon/Alt-F4_FinalNotebook.ipynb`
- **Saved Model Artifacts:** `datathon/artifacts/models/task1_model.joblib`, `task2a_model.joblib`
- **Submission Files:**
  - `datathon/submissions/submission_task1.csv`
  - `datathon/submissions/submission_task2a.csv`
  - `datathon/submissions/submission_task2b.csv`
- **Reports:**
  - `datathon/reports/allocation_policy.md`
  - `datathon/reports/architecture_diagrams.md`
  - `datathon/reports/preprocessing_doc.md`
- **AI Disclosure:** `datathon/ai-disclosure.md`
- **Submission Archive:** `datathon/Alt-F4_Datathon.zip`

---

## 4. 3-to-5 Minute Demo Video Script

### Introduction (0:00 - 0:45)
"Hello judges, welcome to team Alt-F4's presentation of the Datathon solution for Waypoint Group. We have built an end-to-end data pipeline, predictive ML suite, and allocation engine that strictly complies with all competition rules."

### Data Acquisition & Validation (0:45 - 1:30)
"We start by running our dataset acquisition and manifest validator. All 18 raw CSV files are hashed via SHA-256 and checked against schema rules to guarantee data integrity without transmitting confidential data to third parties."

### Task 1: Handling Time & Lateness (1:30 - 2:30)
"For Task 1, labels are constructed from actual route observations. Early arrival waiting is isolated from handling time, and lateness is evaluated against exact store closing times. Using HistGradientBoosting regressors and calibrated classifiers trained from scratch, we achieved a service time MAE of 4.47 minutes and a lateness ROC-AUC of 0.9327."

### Task 2A: Depot Demand Forecasting (2:30 - 3:30)
"In Task 2A, we aggregate order history across training and test order inputs into a complete 10-week demand panel. Using rolling historical lags, we forecast total and chilled volume across depots while guaranteeing chilled volume constraints for Fresh and 0 m³ for Style and Tech."

### Task 2B: Peak-Day Allocation & Validation (3:30 - 4:30)
"Finally, for Task 2B, our priority-weighted solver allocates 77 served orders and 8 deferred orders for Peliyagoda peak day scenario S1. Running the official `check_allocation.py` script confirms 100% feasibility compliance. All trained models and submission files are saved and packaged cleanly."
