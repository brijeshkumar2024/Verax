from __future__ import annotations

from app.engine.types import TriggerMeaning


TRIGGER_MAP: dict[str, TriggerMeaning] = {
    "spike": TriggerMeaning(
        semantic_label="high-intent demand surge",
        urgency_phrase="right now",
        priority_weight=20,
    ),
    "drop": TriggerMeaning(
        semantic_label="conversion erosion detected",
        urgency_phrase="today",
        priority_weight=18,
    ),
    "high_cart_abandon": TriggerMeaning(
        semantic_label="checkout friction spike",
        urgency_phrase="now",
        priority_weight=19,
    ),
    "low_repeat_rate": TriggerMeaning(
        semantic_label="retention decay",
        urgency_phrase="this week",
        priority_weight=17,
    ),
    "new_competitor": TriggerMeaning(
        semantic_label="competitive pressure rise",
        urgency_phrase="today",
        priority_weight=16,
    ),
    "rating_dip": TriggerMeaning(
        semantic_label="trust risk event",
        urgency_phrase="now",
        priority_weight=17,
    ),
    "inventory_expiry": TriggerMeaning(
        semantic_label="inventory value-at-risk",
        urgency_phrase="today",
        priority_weight=20,
    ),
    "weekend_opportunity": TriggerMeaning(
        semantic_label="peak window opportunity",
        urgency_phrase="today",
        priority_weight=15,
    ),
}


def infer_trigger(trigger_type: str) -> TriggerMeaning:
    return TRIGGER_MAP.get(trigger_type, TRIGGER_MAP["spike"])
