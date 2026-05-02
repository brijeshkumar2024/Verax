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


# Urgency closers — rotated deterministically to avoid "now?" overuse
_CLOSERS = ["now?", "right away?", "today?"]

# Demand phrase pool — keyed by merchant_id hash for natural variation without randomness
_DEMAND_PHRASES = ["high-intent buyers", "nearby customers", "ready-to-order users"]


def _demand_phrase(merchant_id: str) -> str:
    return _DEMAND_PHRASES[hash(merchant_id) % len(_DEMAND_PHRASES)]

# Category-specific action verbs for CTA precision
_CTA_VERB: dict[str, str] = {
    "sharp-growth":     "send them a ₹{p} off deal",
    "coach-driven":     "launch a ₹{p} off plan for them",
    "premium-friendly": "promote a ₹{p} off deal to them",
    "clinical-trust":   "offer them a ₹{p} off checkup",
    "care-urgent":      "send them a ₹{p} off refill deal",
    "neutral":          "send them a ₹{p} off deal",
}


def _discount_amount(aov: float, promo_pct: int, strategy_type: str = "info") -> int:
    """Rupee discount = AOV × strategy-aware rate, rounded to nearest ₹5."""
    if strategy_type in {"urgency", "social_proof"}:   # capture-demand: lighter touch
        rate = max(promo_pct, 8) / 100
    elif strategy_type in {"discount", "trust_recovery", "info"}:  # recovery: stronger pull
        rate = max(promo_pct, 12) / 100
    else:
        rate = max(promo_pct, 15) / 100
    raw = aov * rate
    return max(5, int(round(raw / 5) * 5))


def _cta_for(
    trigger_type: str,
    discount: int,
    fatigue_score: float,
    has_strong_offer: bool,
    estimated_customers: int,
    cta_variant: int = 0,
    strategy_type: str = "info",
    intent_score: int = 50,
    tone_voice: str = "neutral",
    merchant_id: str = "m_default",
) -> tuple[str, str]:
    closer = _CLOSERS[cta_variant % 3]
    verb_tpl = _CTA_VERB.get(tone_voice, "send them a ₹{p} off deal")
    verb = verb_tpl.replace("{p}", str(discount))
    # CTA phrase pool — deterministic pick by strategy + merchant_id
    _cta_pool_idx = hash(strategy_type + merchant_id) % 3

    if trigger_type == "rating_dip":
        _pool = [
            f"Want me to run a ₹{discount} off trust-recovery campaign {closer}",
            f"Should I activate a ₹{discount} off recovery offer to rebuild trust {closer}",
            f"Want me to push a ₹{discount} off deal to win back confidence {closer}",
        ]
        return "recover_trust", _pool[_cta_pool_idx]

    if fatigue_score > 0.6:
        _pool = [
            f"Want me to run a ₹{discount} off recovery offer today?",
            f"Should I send a ₹{discount} off deal to re-engage them today?",
            f"Want me to activate a ₹{discount} off offer to bring them back?",
        ]
        return "soft_nudge", _pool[_cta_pool_idx]

    if trigger_type == "spike":
        _variants = [
            f"Want me to {verb} {closer}",
            f"Want me to push a ₹{discount} off deal before the window closes?",
            f"Want me to capture them with a ₹{discount} off deal {closer}",
        ]
        return "push_now", _variants[cta_variant % 3]

    if trigger_type == "drop":
        _variants = [
            f"Want me to {verb} to recover orders {closer}",
            f"Want me to activate a ₹{discount} off recovery offer today?",
            f"Want me to win back orders with a ₹{discount} off boost {closer}",
        ]
        return "recover_drop", _variants[cta_variant % 3]

    if trigger_type == "low_repeat_rate":
        _pool = [
            f"Want me to remind them with a ₹{discount} off offer today?",
            f"Should I send a ₹{discount} off loyalty deal to bring them back?",
            f"Want me to re-engage them with a ₹{discount} off offer {closer}",
        ]
        return "recall", _pool[_cta_pool_idx]

    if has_strong_offer:
        return "activate_offer", f"Want me to activate a ₹{discount} off deal {closer}"

    return "soft_nudge", f"Want me to run a ₹{discount} off recovery test today?"


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
    # Compute meaningful rupee discount: strategy-aware AOV × rate, rounded to nearest ₹5
    discount = _discount_amount(ctx.aov, plan.promo_pct, strategy_type)
    demand_phrase = _demand_phrase(ctx.merchant_id)

    # Customer personalization: only when low fatigue (< 3 recent interactions)
    customer_prefix = ""
    if recent_interaction_count < 3:
        if ctx.customer_loyalty and ctx.customer_loyalty in {"gold", "platinum"}:
            customer_prefix = f"As a {ctx.customer_loyalty} member — "
        elif ctx.visits_last_30d > 3:
            customer_prefix = f"You've visited {ctx.visits_last_30d}x this month — "

    def _cta(idx: int) -> tuple[str, str]:
        return _cta_for(
            ctx.trigger_type, discount, fused.fatigue_score,
            has_strong_offer, plan.estimated_customers,
            cta_variant=idx,
            strategy_type=strategy_type,
            intent_score=fused.intent_score,
            tone_voice=tone.voice,
            merchant_id=ctx.merchant_id,
        )

    cta_type, cta0 = _cta(0)
    _,         cta1 = _cta(1)
    _,         cta2 = _cta(2)

    # 4 deterministic intro structures rotated by (estimated_customers % 4)
    # Prevents lexical monotony across repeated ticks with same tone
    _INTROS: dict[str, list[str]] = {
        "sharp-growth": [
            f"{plan.estimated_customers} people in {ctx.city} are actively searching for {tone.category_noun} right now.",
            f"Right now, {plan.estimated_customers} buyers in {ctx.city} are looking for {tone.category_noun}.",
            f"Demand for {tone.category_noun} is live — {plan.estimated_customers} people in {ctx.city} are searching.",
            f"There are {plan.estimated_customers} active buyers in {ctx.city} looking for {tone.category_noun} today.",
        ],
        "coach-driven": [
            f"{plan.estimated_customers} people in {ctx.city} are actively looking to {tone.category_action} right now.",
            f"Right now, {plan.estimated_customers} people in {ctx.city} want to {tone.category_action}.",
            f"{plan.estimated_customers} motivated members in {ctx.city} are ready to {tone.category_action}.",
            f"There are {plan.estimated_customers} people in {ctx.city} looking to {tone.category_action} today.",
        ],
        "premium-friendly": [
            f"{plan.estimated_customers} style-seekers in {ctx.city} are actively browsing {tone.category_noun} right now.",
            f"Right now, {plan.estimated_customers} people in {ctx.city} are browsing {tone.category_noun}.",
            f"{plan.estimated_customers} potential clients in {ctx.city} are exploring {tone.category_noun} today.",
            f"There are {plan.estimated_customers} style-seekers in {ctx.city} looking for {tone.category_noun}.",
        ],
        "clinical-trust": [
            f"{plan.estimated_customers} people in {ctx.city} are actively seeking {tone.category_noun} today.",
            f"Right now, {plan.estimated_customers} patients in {ctx.city} need {tone.category_noun}.",
            f"{plan.estimated_customers} people in {ctx.city} are looking to book {tone.category_noun}.",
            f"There are {plan.estimated_customers} patients in {ctx.city} searching for {tone.category_noun} today.",
        ],
        "care-urgent": [
            f"{plan.estimated_customers} customers in {ctx.city} need to {tone.category_action} right now.",
            f"Right now, {plan.estimated_customers} customers in {ctx.city} need {tone.category_noun}.",
            f"{plan.estimated_customers} people in {ctx.city} are due for {tone.category_noun}.",
            f"There are {plan.estimated_customers} customers in {ctx.city} who need to {tone.category_action} today.",
        ],
        "neutral": [
            f"{plan.estimated_customers} potential customers in {ctx.city} are actively looking for {tone.category_noun} right now.",
            f"Right now, {plan.estimated_customers} people in {ctx.city} are searching for {tone.category_noun}.",
            f"{plan.estimated_customers} buyers in {ctx.city} are looking for {tone.category_noun} today.",
            f"There are {plan.estimated_customers} active buyers in {ctx.city} interested in {tone.category_noun}.",
        ],
    }
    _intro_idx = plan.estimated_customers % 4
    TONE_LINE1: dict[str, str] = {k: v[_intro_idx] for k, v in _INTROS.items()}

    if ctx.trigger_type == "rating_dip":
        line1_variants = [
            f"{customer_prefix}Recent rating drop is pushing customers to competitors.".strip(),
            "Customer trust is slipping — each hour costs repeat revenue.",
            f"{plan.estimated_customers} customers in {ctx.city} may switch due to rating drop.",
        ]
    elif strategy_type == "social_proof":
        line1_variants = [
            f"{plan.estimated_customers} {demand_phrase} are actively ordering {tone.category_noun} nearby right now.",
            f"{plan.estimated_customers} {demand_phrase} acted on this signal today — window is closing.",
            f"{customer_prefix}{plan.estimated_customers} {demand_phrase} already moved on this.".strip(),
        ]
    else:
        base_line = TONE_LINE1.get(tone.voice, f"{plan.estimated_customers} {demand_phrase} in {ctx.city} are actively searching right now.")
        personalized_line = (customer_prefix + base_line[0].lower() + base_line[1:]).strip() if customer_prefix else base_line
        line1_variants = [
            personalized_line,
            f"{plan.estimated_customers} {demand_phrase} searched for {tone.category_noun} in {ctx.city} today — window is live.",
            f"{plan.estimated_customers} {demand_phrase} can generate ₹{estimated_value} if you act now.",
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
