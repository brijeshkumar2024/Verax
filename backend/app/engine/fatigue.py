from __future__ import annotations

from datetime import datetime, timezone

from app.config import DETERMINISTIC_MODE
from app.store.memory_store import state


def fatigue_score(merchant_id: str) -> float:
    if DETERMINISTIC_MODE:
        return 0.3
    recent = state.get_recent_interactions(merchant_id, minutes=1440)
    if not recent:
        return 0.0
    now = datetime.now(timezone.utc)
    score = 0.0
    for interaction in recent:
        hours_ago = max(0.0, (now - interaction.timestamp).total_seconds() / 3600.0)
        score += max(0.0, 0.3 - (0.1 * hours_ago))
    return min(1.0, max(0.0, score))


def fatigue_penalty(merchant_id: str) -> int:
    score = fatigue_score(merchant_id)
    if score < 0.4:
        return 0
    if score < 0.7:
        return 4
    if score < 0.9:
        return 8
    return 12
