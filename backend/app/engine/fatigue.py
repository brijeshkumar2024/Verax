from __future__ import annotations

from datetime import datetime

from app.store.memory_store import state


def fatigue_score(merchant_id: str, reference_time: datetime) -> float:
    recent = state.get_recent_interactions(merchant_id, minutes=1440, reference_time=reference_time)
    if not recent:
        return 0.0
    score = 0.0
    for interaction in recent:
        if interaction.timestamp >= reference_time:
            continue
        hours_ago = max(0.0, (reference_time - interaction.timestamp).total_seconds() / 3600.0)
        score += max(0.0, 0.3 - (0.1 * hours_ago))
    return min(1.0, max(0.0, score))


def fatigue_penalty(merchant_id: str, reference_time: datetime) -> int:
    score = fatigue_score(merchant_id, reference_time)
    if score < 0.4:
        return 0
    if score < 0.7:
        return 4
    if score < 0.9:
        return 8
    return 12
