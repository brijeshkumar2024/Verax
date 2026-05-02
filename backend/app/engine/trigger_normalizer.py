"""
Trigger normalization layer to handle real-world business terminology.
Maps user-friendly trigger names to canonical enum values.
"""

from __future__ import annotations

from typing import Literal


TriggerType = Literal[
    "spike",
    "drop",
    "high_cart_abandon",
    "low_repeat_rate",
    "new_competitor",
    "rating_dip",
    "inventory_expiry",
    "weekend_opportunity",
]

# Mapping of user-friendly aliases to canonical trigger types
TRIGGER_ALIASES: dict[str, TriggerType] = {
    # Demand signals
    "spike": "spike",
    "surge": "spike",
    "peak": "spike",
    "traffic_up": "spike",
    
    # Decline signals
    "drop": "drop",
    "dip": "drop",
    "decline": "drop",
    "traffic_down": "drop",
    
    # Cart abandonment
    "high_cart_abandon": "high_cart_abandon",
    "cart_abandon": "high_cart_abandon",
    "checkout_drop": "high_cart_abandon",
    "abandoned_carts": "high_cart_abandon",
    
    # Repeat rate
    "low_repeat_rate": "low_repeat_rate",
    "refill_reminder": "low_repeat_rate",
    "retention_risk": "low_repeat_rate",
    "low_repeat": "low_repeat_rate",
    "churn_risk": "low_repeat_rate",
    
    # Competitive pressure
    "new_competitor": "new_competitor",
    "competition": "new_competitor",
    "competitor_entry": "new_competitor",
    "market_threat": "new_competitor",
    
    # Rating/Review issues
    "rating_dip": "rating_dip",
    "rating_drop": "rating_dip",
    "review_crisis": "rating_dip",
    "negative_reviews": "rating_dip",
    
    # Inventory/Expiry
    "inventory_expiry": "inventory_expiry",
    "expiry": "inventory_expiry",
    "stock_expiry": "inventory_expiry",
    "fast_moving_inventory": "inventory_expiry",
    
    # Seasonal/Weekend
    "weekend_opportunity": "weekend_opportunity",
    "festival": "weekend_opportunity",
    "weekend": "weekend_opportunity",
    "seasonal_peak": "weekend_opportunity",
    "holiday": "weekend_opportunity",
}

def normalize_trigger(trigger_input: str) -> TriggerType:
    """
    Normalize a user-provided trigger name to its canonical enum value.
    
    Args:
        trigger_input: User-provided trigger name (case-insensitive)
        
    Returns:
        Canonical TriggerType enum value
        
    Raises:
        ValueError: If trigger cannot be normalized
    """
    normalized = trigger_input.lower().strip()
    
    if normalized in TRIGGER_ALIASES:
        return TRIGGER_ALIASES[normalized]
    
    # If not found, try to match against known triggers
    if normalized in ["spike", "drop", "high_cart_abandon", "low_repeat_rate", 
                       "new_competitor", "rating_dip", "inventory_expiry", "weekend_opportunity"]:
        return normalized  # type: ignore
    
    raise ValueError(
        f"Unknown trigger '{trigger_input}'. Valid aliases include: dip, festival, refill_reminder, "
        f"and the canonical triggers: spike, drop, high_cart_abandon, low_repeat_rate, new_competitor, "
        f"rating_dip, inventory_expiry, weekend_opportunity"
    )

def get_trigger_priority(trigger: TriggerType) -> int:
    """
    Get priority ranking for trigger triage (lower = higher priority).
    Used when multiple triggers are present to select the dominant one.
    
    Args:
        trigger: Trigger type
        
    Returns:
        Priority score (0 = highest priority)
    """
    priority_map: dict[TriggerType, int] = {
        "spike": 0,                    # Capture demand immediately
        "drop": 1,                     # Recover declining demand urgently
        "new_competitor": 2,           # Defend market share
        "rating_dip": 3,               # Repair trust
        "high_cart_abandon": 4,        # Recover abandoned revenue
        "low_repeat_rate": 5,          # Retain customers
        "inventory_expiry": 6,         # Protect margin
        "weekend_opportunity": 7,      # Capture seasonal peak
    }
    return priority_map.get(trigger, 999)

def select_dominant_trigger(triggers: list[TriggerType]) -> TriggerType:
    """
    Select the highest priority trigger from a list.
    
    Args:
        triggers: List of trigger types
        
    Returns:
        The highest priority trigger
    """
    if not triggers:
        raise ValueError("No triggers provided")
    
    return min(triggers, key=lambda t: get_trigger_priority(t))
