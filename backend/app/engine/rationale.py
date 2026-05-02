from __future__ import annotations

from app.engine.decision_engine import DecisionPlan
from app.engine.types import FusedSignals, NormalizedContext, TriggerMeaning


def build_rationale(
    ctx: NormalizedContext,
    trig: TriggerMeaning,
    fused: FusedSignals,
    plan: DecisionPlan,
    strategy: str,
    cta_type: str,
    decision_score: int,
) -> list[str]:
    if decision_score > 75:
        confidence = "strong alignment across trigger, merchant, and demand"
    elif decision_score > 50:
        confidence = "moderate alignment with growth opportunity"
    else:
        confidence = "weak alignment, consider alternative action"

    return [
        f"🎯 Trigger: {ctx.trigger_type} ({trig.semantic_label})",
        f"⚠️ Impact: potential loss of {plan.estimated_customers} buyers in {ctx.city}" if ctx.trigger_type == "rating_dip" else f"⚡ Opportunity: {plan.estimated_customers} local buyers in {ctx.city}",
        f"👤 Merchant: rating {ctx.rating:.1f} with {plan.promo_pct}% offer relevance",
        f"💡 Strategy: {strategy} → {cta_type}",
        f"📊 Confidence: {confidence}",
    ]
