from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


CategoryType = Literal["restaurant", "gym", "salon", "dentist", "pharmacy"]
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


class MerchantInput(BaseModel):
    merchant_id: str
    name: str
    category: CategoryType
    city: str
    avg_order_value: float = Field(gt=0, le=100_000, description="Average order value in Rs. Must be > 0.")
    weekly_orders: int = Field(gt=0, le=500_000, description="Weekly order volume. Must be > 0.")
    conversion_rate: float = Field(ge=0.0, le=1.0)
    repeat_customer_rate: float = Field(ge=0.0, le=1.0)
    rating: float = Field(ge=1.0, le=5.0)
    margin_pct: float = Field(ge=0.0, le=0.9)


class TriggerInput(BaseModel):
    type: str
    observed_value: float = Field(ge=0, description="Observed metric value. Must be >= 0.")
    baseline_value: float = Field(gt=0, description="Baseline metric value. Must be > 0.")
    window_minutes: int = Field(default=180, ge=15, le=1440)
    timestamp_utc: str


class CustomerInput(BaseModel):
    customer_id: str
    loyalty_tier: Literal["new", "silver", "gold", "platinum"] = "new"
    visits_last_30d: int = Field(ge=0, le=500)
    spend_last_30d: float = Field(ge=0, le=100000)
    last_engagement_days: int = Field(ge=0, le=365)


class ComposeRequest(BaseModel):
    category: CategoryType
    merchant: MerchantInput
    trigger: TriggerInput
    customer: Optional[CustomerInput] = None


class RuleTrace(BaseModel):
    trigger_type: str
    dominant_signal: str
    priority: str
    strategy: str
    deviation_pct: float
    intent_score: int
    urgency_score: int


class ComposeResponse(BaseModel):
    message: str
    cta: str
    send_as: Literal["vera", "system", "merchant"]
    suppression_key: str
    suppressed: bool = False
    rationale: List[str]
    decision_score: int = Field(ge=0, le=100)
    score_components: Dict[str, int] = Field(default_factory=dict)
    rule_trace: RuleTrace


class ContextRequest(BaseModel):
    merchant_id: str
    memory: Dict[str, str] = Field(default_factory=dict)


class TickRequest(BaseModel):
    merchant_id: str
    trigger: TriggerType


class ReplyRequest(BaseModel):
    merchant_id: str
    customer_id: Optional[str] = None
    reply_text: str


class MetadataResponse(BaseModel):
    name: str
    version: str
    deterministic: bool
    latency_target_ms: int
    supported_categories: List[CategoryType]
    supported_triggers: List[TriggerType]
    trigger_priority_order: List[str]
    tone_engine: Dict[str, Any]
    determinism_guarantee: str
    suppression: str
    fatigue_model: str
