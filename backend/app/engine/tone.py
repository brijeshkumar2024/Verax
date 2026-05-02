from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToneSpec:
    voice: str
    urgency_word: str
    cta_style: str
    category_noun: str        # contextual noun, never raw category label
    category_action: str      # what users do in this category


TONE_BY_CATEGORY: dict[str, ToneSpec] = {
    "restaurant": ToneSpec("sharp-growth",     "today", "table-turn",        "dinner deals",       "order food"),
    "gym":        ToneSpec("coach-driven",      "now",   "session-book",      "fitness sessions",   "book a session"),
    "salon":      ToneSpec("premium-friendly",  "today", "slot-fill",         "beauty slots",       "book a slot"),
    "dentist":    ToneSpec("clinical-trust",    "today", "appointment-lock",  "checkup appointments", "book a checkup"),
    "pharmacy":   ToneSpec("care-urgent",       "now",   "refill-activate",   "medicine refills",   "place a refill"),
}

DEFAULT_TONE = ToneSpec("neutral", "today", "action", "offers", "take action")


def get_tone(category: str) -> ToneSpec:
    return TONE_BY_CATEGORY.get(category, DEFAULT_TONE)
