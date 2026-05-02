from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToneSpec:
    voice: str
    urgency_word: str
    cta_style: str


TONE_BY_CATEGORY: dict[str, ToneSpec] = {
    "restaurant": ToneSpec("sharp-growth", "today", "table-turn"),
    "gym": ToneSpec("coach-driven", "now", "session-book"),
    "salon": ToneSpec("premium-friendly", "today", "slot-fill"),
    "dentist": ToneSpec("clinical-trust", "today", "appointment-lock"),
    "pharmacy": ToneSpec("care-urgent", "now", "refill-activate"),
}


def get_tone(category: str) -> ToneSpec:
    return TONE_BY_CATEGORY[category]
