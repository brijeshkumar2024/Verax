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
    cta_variant: int = 0,  # 0,1,2 — deterministic variation by variant index
) -> tuple[str, str]:
    if trigger_type == "rating_dip":
        return "recover_trust", f"Run ₹{promo_pct} trust-recovery campaign to improve reviews now?"
    if fatigue_score > 0.6:
        return "soft_nudge", f"Should I run a ₹{promo_pct} recovery offer today?"
    if trigger_type == "spike":
        _variants = [
            f"Push ₹{promo_pct} offer to {estimated_customers} users now?",
            f"Should I send ₹{promo_pct} offer to {estimated_customers} users?",
            f"Want me to push ₹{promo_pct} offer to capture them now?",
        ]
        return "push_now", _variants[cta_variant % 3]
    if trigger_type == "drop":
        _variants = [
            f"Run ₹{promo_pct} boost to recover orders now?",
            f"Should I activate ₹{promo_pct} recovery offer today?",
            f"Want me to run ₹{promo_pct} boost to win back orders?",
        ]
        return "recover_drop", _variants[cta_variant % 3]
    if has_strong_offer:
        return "activate_offer", f"Activate ₹{promo_pct} offer for today?"
    return "soft_nudge", f"Run a ₹{promo_pct} recovery test today?"


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
    recent_interaction_count: int = 0,
) -> List[Variant]:
    tone = get_tone(ctx.category)
    has_strong_offer = plan.promo_pct >= 14
    estimated_value = plan.estimated_revenue
    message_type = _message_type_for(strategy_type)

    # Customer personalization: only when low fatigue (< 3 recent interactions)
    customer_prefix = ""
    if recent_interaction_count < 3:
        if ctx.customer_loyalty and ctx.customer_loyalty in {"gold", "platinum"}:
            customer_prefix = f"As a {ctx.customer_loyalty} member — "
        elif ctx.visits_last_30d > 3:
            customer_prefix = f"You've visited {ctx.visits_last_30d}x this month — "

    # Build 3 CTAs with deterministic variation per variant index
    cta_type, cta0 = _cta_for(ctx.trigger_type, plan.promo_pct, fused.fatigue_score, has_strong_offer, plan.estimated_customers, 0)
    _,         cta1 = _cta_for(ctx.trigger_type, plan.promo_pct, fused.fatigue_score, has_strong_offer, plan.estimated_customers, 1)
    _,         cta2 = _cta_for(ctx.trigger_type, plan.promo_pct, fused.fatigue_score, has_strong_offer, plan.estimated_customers, 2)

    # Line1 uses category_noun/category_action — never raw category label
    TONE_LINE1: dict[str, str] = {
        "sharp-growth":     f"{plan.estimated_customers} people in {ctx.city} are actively searching for {tone.category_noun} right now.",
        "coach-driven":     f"{plan.estimated_customers} people in {ctx.city} are actively looking to {tone.category_action} right now.",
        "premium-friendly": f"{plan.estimated_customers} style-seekers in {ctx.city} are actively browsing {tone.category_noun} right now.",
        "clinical-trust":   f"{plan.estimated_customers} people in {ctx.city} are actively seeking {tone.category_noun} today.",
        "care-urgent":      f"{plan.estimated_customers} customers in {ctx.city} need to {tone.category_action} right now.",
        "neutral":          f"{plan.estimated_customers} potential customers in {ctx.city} are actively looking for {tone.category_noun} right now.",
    }

    if ctx.trigger_type == "rating_dip":
        line1_variants = [
            f"{customer_prefix}Recent rating drop is pushing customers to competitors.".strip(),
            "Customer trust is slipping — each hour costs repeat revenue.",
            f"{plan.estimated_customers} customers in {ctx.city} may switch due to rating drop.",
        ]
    elif strategy_type == "social_proof":
        line1_variants = [
            f"{plan.estimated_customers} people are actively ordering {tone.category_noun} nearby right now.",
            f"{plan.estimated_customers} others acted on this signal today — window is closing.",
            f"{customer_prefix}{plan.estimated_customers} local buyers already moved on this.".strip(),
        ]
    else:
        base_line = TONE_LINE1.get(tone.voice, f"{plan.estimated_customers} potential customers in {ctx.city} are actively searching right now.")
        personalized_line = (customer_prefix + base_line[0].lower() + base_line[1:]).strip() if customer_prefix else base_line
        line1_variants = [
            personalized_line,
            f"{plan.estimated_customers} people searched for {tone.category_noun} in {ctx.city} today — window is live.",
            f"{plan.estimated_customers} nearby users can generate ₹{estimated_value} if you act now.",
        ]

    def _make_variant(line1: str, cta: str, rationale_items: list[str]) -> Variant:
        msg = line1.strip() + "\n" + cta.strip()
        return Variant(message=msg, cta=cta.strip(), send_as=send_as, rationale=rationale_items)

    v1 = _make_variant(line1_variants[0], cta0, [
        f"Dominant signal: {fused.dominant_signal}",
        f"Trigger: {trig.semantic_label}",
        f"Tone: {tone.voice}",
        f"Strategy: {strategy_type} | CTA: {cta_type}",
    ])
    v2 = _make_variant(line1_variants[1], cta1, [
        f"Merchant fit: {fused.merchant_fit} | Urgency: {fused.urgency_score}",
        f"Priority: {plan.priority}",
        f"Strategy: {strategy_type} | CTA: {cta_type}",
    ])
    v3 = _make_variant(line1_variants[2], cta2, [
        f"Intent: {fused.intent_score} | Fatigue penalty: {fused.fatigue_penalty}",
        f"Strategy: {strategy_type} | CTA: {cta_type}",
    ])

    return [v1, v2, v3]
