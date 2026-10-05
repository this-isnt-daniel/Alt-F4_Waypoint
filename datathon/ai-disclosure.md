# AI Tool Disclosure Statement

**Team Name:** Alt-F4  
**Project:** Waypoint Datathon 2026  

---

## 1. Compliance with Competition Rules
In accordance with the Tech-Triathlon 2026 Challenge Booklet rules:
- **No Pre-trained Prediction Models:** All machine learning models (HistGradientBoosting regressors and classifiers) were initialized and trained strictly from scratch on the competition dataset.
- **No Low-code / AutoML / Remote APIs:** No automated end-to-end AutoML frameworks (e.g. DataRobot, H2O AutoML) or proprietary cloud prediction APIs were used for modelling or data preprocessing.
- **Data Privacy & Confidentiality:** Competition datasets, raw order records, model artifacts, and generated outputs were processed locally on the development machine. No dataset records were transmitted to external cloud services or third-party web platforms.

---

## 2. Scope of AI Assistance
AI assistance was utilized exclusively for:
1. **Code Scaffolding & Module Structure:** Drafting boilerplate Python functions for dataset acquisition, manifest generation, schema validation, and CLI commands.
2. **Synthetic Unit Test Creation:** Writing unit test fixtures in `datathon/tests/test_datathon.py` to verify edge cases (e.g., midnight rollover, exact delivery window closing time).
3. **Documentation Assistance:** Formatting markdown reports, architecture diagrams (Mermaid syntax), and setup instructions.

---

## 3. Human Control & Independent Verification
All feature engineering logic, label construction formulas, priority scoring functions, and Task 2B optimization constraints were designed, audited, and verified by team members against the official Challenge Booklet specifications.
