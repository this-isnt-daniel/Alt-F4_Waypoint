import pandas as pd

def calculate_order_priority(order: pd.Series) -> float:
    """
    Computes a transparent priority score for Task 2B order allocation:
    - Base priority by brand (Fresh > Style > Tech)
    - Perishable chilled requirement bonus
    - Deferral urgency bonus (deferred_yesterday == 1)
    - Days since last served multiplier
    """
    brand = order["brand"]
    temp = order["temp_requirement"]
    deferred_yesterday = order.get("deferred_yesterday", 0)
    days_since_served = order.get("days_since_last_served", 1)

    # Base brand priority
    brand_weights = {"Fresh": 100.0, "Style": 50.0, "Tech": 30.0}
    score = brand_weights.get(brand, 20.0)

    # Chilled perishable bonus
    if temp == "chilled":
        score += 80.0

    # Prior deferral penalty avoidance bonus
    if deferred_yesterday == 1:
        score += 150.0

    # Days since last served weight
    score += (days_since_served - 1) * 40.0

    return score
