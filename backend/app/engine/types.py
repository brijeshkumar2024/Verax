from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal


@dataclass(frozen=True)
class NormalizedContext:
    merchant_id: str
    merchant_name: str
    category: str
    city: str
    aov: float
    weekly_orders: int
    conversion_rate: float
    repeat_rate: float
    rating: float
    margin_pct: float
    trigger_type: str
    trigger_ratio: float
    trigger_window_minutes: int
    timestamp_utc: str
    customer_id: str | None
    customer_loyalty: str | None
    visits_last_30d: int
    spend_last_30d: float
    last_engagement_days: int


@dataclass(frozen=True)
class FusedSignals:
    intent_score: int
    urgency_score: int
    merchant_fit: int
    fatigue_penalty: int
    fatigue_score: float
    fatigue_suppressed: bool
    dominant_signal: Literal[
        "demand",
        "retention",
        "quality",
        "operations",
        "competition",
        "seasonality",
    ]


@dataclass(frozen=True)
class TriggerMeaning:
    semantic_label: str
    urgency_phrase: str
    priority_weight: int


@dataclass(frozen=True)
class Variant:
    message: str
    cta: str
    send_as: Literal["vera", "system", "merchant"]
    rationale: List[str]


@dataclass(frozen=True)
class ScoredVariant:
    variant: Variant
    decision_quality: int
    specificity: int
    category_fit: int
    merchant_fit: int
    engagement: int
    anti_pattern_penalty: int
    score_components: Dict[str, int]
    total_score: int
