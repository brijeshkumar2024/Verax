from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from app.config import DETERMINISTIC_MODE


StrategyType = Literal["urgency", "discount", "info", "social_proof", "trust_recovery"]


def _target_for_trigger(trigger_type: str) -> StrategyType:
    if trigger_type in {"spike", "drop"}:
        return "urgency"
    if trigger_type in {"high_cart_abandon", "new_competitor", "weekend_opportunity"}:
        return "discount"
    return "info"


def _rotate_strategy(target: StrategyType) -> StrategyType:
    if target == "urgency":
        return "discount"
    if target == "discount":
        return "social_proof"
    return "urgency"


def _is_within_cooldown(last_sent_at: str, cooldown_minutes: int, now: datetime) -> bool:
    if not last_sent_at:
        return False
    try:
        sent_at = datetime.fromisoformat(last_sent_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    elapsed_min = (now - sent_at).total_seconds() / 60.0
    return elapsed_min < cooldown_minutes


def decide_strategy(memory: dict[str, str], current_context: dict[str, str]) -> StrategyType:
    trigger_type = current_context.get("trigger_type", "")
    last_response = memory.get("last_response", "ignored")
    last_message_type = memory.get("last_message_type", "info")
    cooldown_minutes = int(current_context.get("cooldown_minutes", "30"))
    rating = float(current_context.get("rating", "5.0"))

    if trigger_type == "rating_dip":
        return "trust_recovery"

    # Multi-signal rule: low rating overrides demand/discount strategy
    # A merchant with rating < 3.8 needs trust repair even during a spike
    if rating < 3.8:
        return "trust_recovery"

    # High-rated merchant facing competition: reinforce loyalty, not discount
    if trigger_type == "new_competitor" and rating >= 4.3:
        return "social_proof"

    if last_response == "ignored":
        return "social_proof"

    target = _target_for_trigger(trigger_type)

    if target == last_message_type:
        return _rotate_strategy(target)

    if DETERMINISTIC_MODE:
        return target  # type: ignore[return-value]

    now = datetime.now(timezone.utc)
    last_sent_at = memory.get("last_sent_at", "")
    if target == "urgency" and _is_within_cooldown(last_sent_at, cooldown_minutes, now):
        return "info"

    return target  # type: ignore[return-value]


def classify_cta_type(cta: str) -> str:
    lowered = cta.lower()
    if "restore trust" in lowered or "recovery campaign" in lowered:
        return "recover_trust"
    if "push" in lowered:
        return "push_now"
    if "recover" in lowered or "boost" in lowered:
        return "recover_drop"
    if "activate" in lowered:
        return "activate_offer"
    if "try" in lowered:
        return "soft_nudge"
    return "soft_nudge"
