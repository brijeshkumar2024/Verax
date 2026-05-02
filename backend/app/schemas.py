from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


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

_DEFAULT_CATEGORY: CategoryType = "restaurant"


class MerchantInput(BaseModel):
    model_config = {"extra": "ignore"}  # silently drop unknown fields from judge payloads

    merchant_id: str = Field(default="m_default")
    name: str = Field(default="Merchant")
    category: CategoryType = Field(default=_DEFAULT_CATEGORY)
    city: str = Field(default="your city")
    avg_order_value: float = Field(default=300.0, gt=0, le=100_000)
    weekly_orders: int = Field(default=500, gt=0, le=500_000)
    conversion_rate: float = Field(default=0.15, ge=0.0, le=1.0)
    repeat_customer_rate: float = Field(default=0.3, ge=0.0, le=1.0)
    rating: float = Field(default=4.0, ge=1.0, le=5.0)
    margin_pct: float = Field(default=0.25, ge=0.0, le=0.9)


class TriggerInput(BaseModel):
    model_config = {"extra": "ignore"}

    type: str = Field(default="spike")
    observed_value: float = Field(default=150.0, ge=0)
    baseline_value: float = Field(default=100.0, gt=0)
    window_minutes: int = Field(default=180, ge=15, le=1440)
    timestamp_utc: str = Field(default="2026-01-01T00:00:00Z")

    @field_validator("timestamp_utc")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        from datetime import datetime
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("timestamp_utc must be ISO 8601, e.g. 2026-05-02T14:00:00Z")
        return v


class CustomerInput(BaseModel):
    model_config = {"extra": "ignore"}

    customer_id: str = Field(default="c_default")
    loyalty_tier: Literal["new", "silver", "gold", "platinum"] = "new"
    visits_last_30d: int = Field(default=0, ge=0, le=500)
    spend_last_30d: float = Field(default=0.0, ge=0, le=100000)
    last_engagement_days: int = Field(default=30, ge=0, le=365)


class ComposeRequest(BaseModel):
    model_config = {"extra": "ignore"}

    category: CategoryType = Field(default=_DEFAULT_CATEGORY)
    merchant: MerchantInput = Field(default_factory=MerchantInput)
    trigger: TriggerInput = Field(default_factory=TriggerInput)
    customer: Optional[CustomerInput] = None

    @model_validator(mode="before")
    @classmethod
    def sync_category(cls, data: Any) -> Any:
        """If merchant.category not set, inherit from top-level category."""
        if isinstance(data, dict):
            top_cat = data.get("category", _DEFAULT_CATEGORY)
            merchant = data.get("merchant")
            if isinstance(merchant, dict) and "category" not in merchant:
                merchant["category"] = top_cat
                data["merchant"] = merchant
        return data


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
    rationale: str
    decision_score: int = Field(ge=0, le=100)
    score_components: Dict[str, int] = Field(default_factory=dict)
    rule_trace: RuleTrace


class ContextRequest(BaseModel):
    model_config = {"extra": "ignore"}
    merchant_id: str
    memory: Dict[str, Any] = Field(default_factory=dict)


class ContextEnvelope(BaseModel):
    """Challenge-format /v1/context envelope."""
    model_config = {"extra": "ignore"}

    # Accept context_id OR identity (judge may use either)
    context_id: Optional[str] = None
    identity: Optional[str] = None
    scope: str = "merchant"
    version: int = 1
    payload: Dict[str, Any] = Field(default_factory=dict)
    delivered_at: Optional[str] = None

    def to_context_request(self) -> ContextRequest:
        mid = self.context_id or self.identity or "m_default"
        return ContextRequest(merchant_id=mid, memory={str(k): str(v) for k, v in self.payload.items()})


class TickRequest(BaseModel):
    merchant_id: str
    trigger: TriggerType


class ReplyRequest(BaseModel):
    model_config = {"extra": "ignore"}
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
