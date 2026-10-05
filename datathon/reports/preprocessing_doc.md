# Data Preprocessing, Cleaning, & Label Construction Document

## 1. Task 1 Label Construction
Neither handling time nor lateness is directly provided in the input CSV files. Training labels were constructed from actual route observations using the following rules:

### A. Outlet Handling Time (`target_service_min`)
- **Formula:**
  $$\text{service\_start} = \max(\text{actual\_arrival}, \text{window\_open\_time})$$
  $$\text{service\_minutes} = \frac{\text{leave\_outlet\_time} - \text{service\_start}}{60\text{ seconds}}$$
- **Waiting Time Isolation:** Early arrival waiting is strictly excluded from handling time.
- **Midnight Rollover:** Handled for timestamps spanning past midnight.

### B. Arrival Lateness (`target_late_prob`)
- **Formula:**
  $$\text{late\_label} = \mathbb{I}(\text{actual\_arrival} > \text{window\_close\_time})$$
- **Boundary Condition:** Arrival exactly at `window_close_time` is **on-time** ($\text{late\_label} = 0$).
- **Definition:** Lateness refers to arrival time, not completion time.

---

## 2. Feature Engineering & Data Leakage Prevention
- **Allowed Prediction-Time Features:**
  - Brand, Depot, District, Dock Type, Parking Constraints, Temperature Requirements.
  - Vehicle attributes (type, temp capability, weight and volume caps).
  - Order units, weight ($\text{kg}$), volume ($\text{m}^3$).
  - Planned departure hour, planned arrival hour, window duration, planned arrival slack.
  - Calendar context (Day of week, weekend, payday, monsoon, festival ramp).
  - Contextual traffic speed index and road condition disruption index.
- **Strict Leakage Prevention:** Actual arrival times, actual travel durations, and actual leave outlet times were **never** used as input features.

---

## 3. Task 2A Demand Panel Construction
- Every order in `deliveries_train.csv` and `task1_test_inputs.csv` was counted exactly once.
- Orders were assigned to `order_date` and grouped by `(depot, brand, iso_year, iso_week)`.
- Chilled demand was isolated for `Fresh` brand. `Style` and `Tech` chilled volumes were explicitly locked to $0.0\,\text{m}^3$.
- Missing weeks were filled with zero volume.
