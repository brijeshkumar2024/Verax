from __future__ import annotations

from app.engine.types import NormalizedContext
from app.schemas import ComposeRequest


def normalize_context(payload: ComposeRequest) -> NormalizedContext:
    trigger_ratio = payload.trigger.observed_value / payload.trigger.baseline_value
    customer = payload.customer

    return NormalizedContext(
        merchant_id=payload.merchant.merchant_id.strip(),
        merchant_name=payload.merchant.name.strip(),
        category=payload.category,
        city=payload.merchant.city.strip(),
        aov=round(payload.merchant.avg_order_value, 2),
        weekly_orders=payload.merchant.weekly_orders,
        conversion_rate=payload.merchant.conversion_rate,
        repeat_rate=payload.merchant.repeat_customer_rate,
        rating=payload.merchant.rating,
        margin_pct=payload.merchant.margin_pct,
        trigger_type=payload.trigger.type,
        trigger_ratio=round(trigger_ratio, 4),
        trigger_window_minutes=payload.trigger.window_minutes,
        timestamp_utc=payload.trigger.timestamp_utc,
        customer_id=customer.customer_id if customer else None,
        customer_loyalty=customer.loyalty_tier if customer else None,
        visits_last_30d=customer.visits_last_30d if customer else 0,
        spend_last_30d=round(customer.spend_last_30d, 2) if customer else 0.0,
        last_engagement_days=customer.last_engagement_days if customer else 999,
    )
