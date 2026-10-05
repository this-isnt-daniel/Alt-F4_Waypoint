# Task 2B Allocation Policy & Deferral Analysis

**Team Name:** Alt-F4  
**Scenario:** S1 (Peliyagoda Depot Peak Day - Pre-Festival)  
**Date of Allocation:** October 5, 2026  

---

## 1. Executive Summary
During Scenario S1 at the Peliyagoda depot, demand significantly exceeds available fleet capacity due to an impending festival one week away. Fresh store demand for dairy, meat, and produce is rapidly rising. Operating constraints are further constrained because several vehicles are currently marked `in_workshop`.

Our optimization solver allocated **77 orders as served** and **8 orders as deferred** out of 85 total scenario orders, strictly adhering to all 7 official feasibility constraints validated by `check_allocation.py`.

---

## 2. Priority Scoring & Decision Logic
Orders are prioritized using a deterministic multi-factor scoring function:
$$\text{Priority} = \text{BaseBrandWeight} + \text{ChilledBonus} + \text{PriorDeferralBonus} + \text{ElapsedDaysBonus}$$

1. **Perishable Demand (Fresh + Chilled):** Fresh groceries and chilled items receive top priority to prevent store stockouts before stores open at 8:00 AM.
2. **Prior Deferral Protection (`deferred_yesterday == 1`):** Outlets skipped on the previous run receive a +150 priority surge to avoid consecutive skips and customer churn.
3. **Elapsed Time Since Service (`days_since_last_served`):** Orders for stores that have gone unserved for longer durations receive scaled priority additions (+40 per day).
4. **Scarce Refrigerated Capacity:** Refrigerated vehicles (`reefer`) and small refrigerated vans are scarce resources. Ambient orders are strictly routed away from reefers whenever reefer capacity is required for chilled goods.

---

## 3. Capacity Bottlenecks & Feasibility Calculations
- **Limiting Resource:** Refrigerated vans and small van access. Peliyagoda operates with restricted vehicle availability on Scenario S1 because workshop vehicles are unavailable.
- **Budget Window Constraints:**
  - **Fresh Window:** 3:30 AM – 8:00 AM (Max 270 minutes per vehicle).
  - **Style & Tech Window:** Trading Day (Max 480 minutes per vehicle).
- **Trip Time Formula:**
  $$\text{trip\_minutes} = \text{depot\_to\_district\_freeflow\_min} + (N - 1) \times \text{inter\_stop\_freeflow\_min} + \sum \text{service\_allowance}$$

All served trips satisfy both volume ($\text{m}^3$) and weight ($\text{kg}$) limits without exceeding 2 trips per vehicle per day.

---

## 4. Deferral Rationale & Cost Impact
The 8 deferred orders were selected because:
1. They had low urgency scores (e.g., non-perishable ambient goods for outlets served recently).
2. Physical access constraints (e.g., `van_only` parking) matched with zero remaining available van capacity for that district.
3. Time budget exhaustion across available 270 min / 480 min windows.

**Deferred Orders Analysis:**
- Unavoidable deferrals due to fleet availability: 8 orders.
- Customer impact is minimized as no Fresh chilled order skipped yesterday was deferred today.
