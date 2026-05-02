from __future__ import annotations

from dataclasses import dataclass

from app.engine.types import FusedSignals, NormalizedContext, TriggerMeaning


@dataclass(frozen=True)
class DecisionPlan:
    priority: str
    promo_pct: int
    estimated_customers: int
    estimated_revenue: int


def decide(ctx: NormalizedContext, fused: FusedSignals, trig: TriggerMeaning) -> DecisionPlan:
    if fused.dominant_signal == "demand":
        priority = "capture-demand-now"
    elif fused.dominant_signal == "retention":
        priority = "recover-repeat-demand"
    elif fused.dominant_signal == "quality":
        priority = "repair-trust-and-convert"
    elif fused.dominant_signal == "operations":
        priority = "protect-wasting-inventory"
    elif fused.dominant_signal == "competition":
        priority = "defend-market-share"
    else:
        priority = "maximize-peak-window"

    base_promo = 8 + int((fused.urgency_score + trig.priority_weight) / 20)
    promo_pct = min(25, max(8, base_promo))

    estimated_customers = min(2000, max(int(ctx.weekly_orders * 0.05), int(ctx.weekly_orders * 0.008 + fused.intent_score * 1.3)))
    estimated_revenue = int(estimated_customers * ctx.aov * (1 - (promo_pct / 100)))

    return DecisionPlan(
        priority=priority,
        promo_pct=promo_pct,
        estimated_customers=estimated_customers,
        estimated_revenue=estimated_revenue,
    )
