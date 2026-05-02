from __future__ import annotations

from typing import List

from app.engine.decision_engine import DecisionPlan
from app.engine.tone import get_tone
from app.engine.trigger_intelligence import TriggerMeaning
from app.engine.types import FusedSignals, NormalizedContext, Variant


def _message_type_for(strategy: str) -> str:
    if strategy == "trust_recovery":
        return "problem_fix"
    if strategy in {"urgency", "discount", "social_proof"}:
        return strategy
    return "info"


def enforce_currency(msg: str) -> str:
    return msg.replace("Rs", "").replace("INR", "").replace("()", "").replace("  ", " ").strip()


def enforce_message_rules(msg: str) -> str:
    lines = [line.strip() for line in msg.strip().split("\n") if line.strip()]
    return "\n".join(lines[:2])


def _cta_for(
    trigger_type: str,
    promo_pct: int,
    fatigue_score: float,
    has_strong_offer: bool,
    estimated_customers: int,
) -> tuple[str, str]:
    if trigger_type == "rating_dip":
        return "recover_trust", f"Run {promo_pct}% trust-recovery campaign to improve reviews now?"
    if fatigue_score > 0.6:
        return "soft_nudge", f"Run a low-pressure {promo_pct}% recovery test today?"
    if trigger_type == "spike":
        return "push_now", f"Push {promo_pct}% offer to {estimated_customers} users now?"
    if trigger_type == "drop":
        return "recover_drop", f"Run {promo_pct}% boost to recover orders now?"
    if has_strong_offer:
        return "activate_offer", f"Activate {promo_pct}% offer for today?"
    return "soft_nudge", f"Run a low-pressure {promo_pct}% recovery test today?"


def _line2(priority: str, city: str, trigger_label: str) -> str:
    if priority == "capture-demand-now":
        return f"Demand signal: {trigger_label} in {city}; act now to secure top intent."
    if priority == "recover-repeat-demand":
        return f"Retention risk in {city}: {trigger_label}; recover repeat demand today."
    if priority == "repair-trust-and-convert":
        return f"Trust risk in {city}: {trigger_label}; steady conversion today."
    if priority == "protect-wasting-inventory":
        return f"Inventory pressure in {city}: {trigger_label}; protect margin now."
    if priority == "defend-market-share":
        return f"Competition rise in {city}: {trigger_label}; defend share today."
    return f"Peak window in {city}: {trigger_label}; convert attention now."


def generate_variants(
    ctx: NormalizedContext,
    fused: FusedSignals,
    trig: TriggerMeaning,
    plan: DecisionPlan,
    send_as: str,
    strategy_type: str = "info",
) -> List[Variant]:
    tone = get_tone(ctx.category)
    has_strong_offer = plan.promo_pct >= 14
    estimated_value = plan.estimated_revenue
    cta_type, cta = _cta_for(
        ctx.trigger_type,
        plan.promo_pct,
        fused.fatigue_score,
        has_strong_offer,
        plan.estimated_customers,
    )
    message_type = _message_type_for(strategy_type)

    if ctx.trigger_type == "rating_dip":
        line1_variants = [
            "Recent rating drop detected impacting customer trust.",
            "Customer trust is slipping after a recent rating drop.",
            "Protect revenue before more customers lose confidence today.",
        ]
    elif strategy_type == "social_proof":
        line1_variants = [
            f"{plan.estimated_customers} people ordered from {ctx.category} nearby today.",
            f"{plan.estimated_customers} others ordered today — join them before the window closes.",
            f"{plan.estimated_customers} local buyers acted on this signal today.",
        ]
    else:
        line1_variants = [
            f"{plan.estimated_customers} nearby buyers are ready today.",
            f"{plan.estimated_customers} people searched for {ctx.category} nearby today.",
            f"{plan.estimated_customers} nearby users can generate ₹{estimated_value} today.",
        ]
    line2 = cta

    v1 = Variant(
        message=enforce_message_rules(enforce_currency(f"{line1_variants[0]}\n{line2}")),
        cta=cta,
        send_as=send_as,
        rationale=[
            f"Dominant signal selected: {fused.dominant_signal}",
            f"Trigger interpreted as {trig.semantic_label}",
            f"Category voice applied: {tone.voice}",
            f"Strategy selected: {strategy_type}",
            f"CTA type selected: {cta_type}",
            f"Message type selected: {message_type}",
        ],
    )

    v2 = Variant(
        message=enforce_message_rules(
            enforce_currency(
                f"{line1_variants[1]}\n"
                f"{line2}"
            )
        ),
        cta=cta,
        send_as=send_as,
        rationale=[
            f"Merchant fit score considered: {fused.merchant_fit}",
            f"Urgency calibrated to {fused.urgency_score}",
            f"Priority plan: {plan.priority}",
            f"Strategy selected: {strategy_type}",
            f"CTA type selected: {cta_type}",
            f"Message type selected: {message_type}",
        ],
    )

    v3 = Variant(
        message=enforce_message_rules(
            enforce_currency(
                f"{line1_variants[2]}\n"
                f"{line2}"
            )
        ),
        cta=cta,
        send_as=send_as,
        rationale=[
            f"Intent score from fused signals: {fused.intent_score}",
            f"Fatigue penalty applied: {fused.fatigue_penalty}",
            "Deterministic variant template index: 3",
            f"Strategy selected: {strategy_type}",
            f"CTA type selected: {cta_type}",
            f"Message type selected: {message_type}",
        ],
    )

    return [v1, v2, v3]
