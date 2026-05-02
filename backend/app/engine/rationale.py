from __future__ import annotations

from app.engine.decision_engine import DecisionPlan
from app.engine.types import FusedSignals, NormalizedContext, TriggerMeaning


def _fmt_revenue(amount: int) -> str:
    """Format revenue to clean readable amount: round to nearest 100, use K for thousands."""
    rounded = int(round(amount / 100) * 100)
    if rounded >= 1000:
        return f"₹{rounded / 1000:.1f}K"
    return f"₹{rounded}"


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

    _STRATEGY_LABELS: dict[str, str] = {
        "urgency":        "Demand Capture",
        "social_proof":   "Social Proof",
        "discount":       "Discount Push",
        "trust_recovery": "Trust Recovery",
        "info":           "Awareness",
    }
    strategy_label = _STRATEGY_LABELS.get(strategy, strategy.replace("_", " ").title())

    return [
        f"Trigger: {ctx.trigger_type} | Signal: {trig.semantic_label}",
        f"Impact: {plan.estimated_customers} buyers at risk in {ctx.city}" if ctx.trigger_type == "rating_dip" else f"Opportunity: {plan.estimated_customers} buyers in {ctx.city}",
        f"Offer: {_fmt_revenue(plan.estimated_revenue)} ({plan.estimated_customers} buyers × AOV × conv × {100 - plan.promo_pct}%) | rating {ctx.rating:.1f}",
        f"Strategy: {strategy_label} | {selection_note} | {confidence}",
    ]
