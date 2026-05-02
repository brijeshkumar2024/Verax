from __future__ import annotations

from app.engine.fatigue import fatigue_penalty, fatigue_score
from app.engine.types import FusedSignals, NormalizedContext


def _dominant_signal(ctx: NormalizedContext) -> str:
    if ctx.trigger_type in {"spike", "drop", "high_cart_abandon"}:
        return "demand"
    if ctx.trigger_type == "low_repeat_rate":
        return "retention"
    if ctx.trigger_type == "rating_dip":
        return "quality"
    if ctx.trigger_type == "inventory_expiry":
        return "operations"
    if ctx.trigger_type == "new_competitor":
        return "competition"
    return "seasonality"


def fuse_signals(ctx: NormalizedContext) -> FusedSignals:
    ratio_delta = abs(ctx.trigger_ratio - 1.0)
    intent = min(100, int(35 + ratio_delta * 40 + ctx.conversion_rate * 25))
    urgency = min(100, int(30 + ratio_delta * 50 + (1 - ctx.repeat_rate) * 20))
    fit = min(100, int(40 + (ctx.margin_pct * 30) + ((5 - ctx.rating) * 8) + (ctx.weekly_orders / 2500 * 20)))

    score = fatigue_score(ctx.merchant_id)
    penalty = fatigue_penalty(ctx.merchant_id)
    intent = max(0, intent - penalty)
    urgency = max(0, urgency - int(penalty / 2))

    return FusedSignals(
        intent_score=intent,
        urgency_score=urgency,
        merchant_fit=fit,
        fatigue_penalty=penalty,
        fatigue_score=score,
        fatigue_suppressed=score > 0.9,
        dominant_signal=_dominant_signal(ctx),
    )
