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
    winner_score: int = 0,
    rejected_scores: list[int] | None = None,
) -> list[str]:
    if decision_score > 75:
        confidence = "strong alignment across trigger, merchant, and demand"
    elif decision_score > 50:
        confidence = "moderate alignment with growth opportunity"
    else:
        confidence = "weak alignment, consider alternative action"

    rejected = rejected_scores or []
    selection_note = (
        f"Winner scored {winner_score}/100"
        + (f"; rejected variants scored {', '.join(str(s) for s in rejected)}" if rejected else "")
    )

    return [
        f"Trigger: {ctx.trigger_type} ({trig.semantic_label})",
        f"Impact: potential loss of {plan.estimated_customers} buyers in {ctx.city}" if ctx.trigger_type == "rating_dip" else f"Opportunity: {plan.estimated_customers} active buyers in {ctx.city}",
        f"Merchant: rating {ctx.rating:.1f}, {plan.promo_pct}% offer, ₹{plan.estimated_revenue} revenue potential",
        f"Strategy: {strategy} → {cta_type}",
        f"Selection: {selection_note}",
        f"Confidence: {confidence}",
    ]
