from __future__ import annotations

import re

def anti_pattern_check(message: str, cta: str) -> dict[str, object]:
    penalty = 0
    flags: list[str] = []
    lowered = message.lower()
    urgency_terms = ["now", "limited", "hurry"]
    urgency_hits = sum(1 for t in urgency_terms if t in lowered)
    if urgency_hits >= 2:
        penalty += 8
        flags.append("double_urgency")

    if "₹" not in message:
        penalty += 30
        flags.append("missing_currency_symbol")

    if not re.search(r"\d+", message):
        penalty += 30
        flags.append("missing_number")

    if message.count("\n") > 1:
        penalty += 6
        flags.append("too_many_lines")

    if any(w in cta.lower() for w in ["check", "explore"]):
        penalty += 5
        flags.append("weak_cta")

    if "?" not in cta:
        penalty += 15
        flags.append("non_binary_cta")

    return {"penalty_score": penalty, "flags": flags}


def anti_pattern_penalty(message: str, cta: str) -> int:
    return int(anti_pattern_check(message, cta)["penalty_score"])
