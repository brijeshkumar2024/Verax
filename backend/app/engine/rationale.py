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
    selection_note = f"Winner {winner_score}/100" + (f" vs {', '.join(str(s) for s in rejected)}" if rejected else "")

    return [
        f"Trigger: {ctx.trigger_type} | Signal: {trig.semantic_label}",
        f"Impact: {plan.estimated_customers} buyers at risk in {ctx.city}" if ctx.trigger_type == "rating_dip" else f"Opportunity: {plan.estimated_customers} buyers in {ctx.city}",
        f"Offer: ₹{plan.estimated_revenue} potential | {plan.promo_pct}% promo | rating {ctx.rating:.1f}",
        f"Strategy: {strategy} → {cta_type} | {selection_note} | {confidence[:20]}",
    ]
