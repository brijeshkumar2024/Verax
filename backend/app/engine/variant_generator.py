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
    "sharp-growth":     "send them a ₹{p} discount",
    "coach-driven":     "launch a ₹{p} plan for them",
    "premium-friendly": "promote a ₹{p} offer to them",
    "clinical-trust":   "offer them a ₹{p} off checkup",
    "care-urgent":      "send them a ₹{p} refill offer",
    "neutral":          "send them a ₹{p} discount",
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


# ---------------------------------------------------------------------------
# Category × trigger template library
# 3 natural line1 strings per (category, trigger_type)
# Picked by hash(merchant_id + trigger_type) % 3 — fully deterministic
# Rules: opens with number/fact, no greeting, category-specific language
# ---------------------------------------------------------------------------
_TEMPLATES: dict[tuple[str, str], list[str]] = {
    # ── RESTAURANT ──────────────────────────────────────────────────────────
    ("restaurant", "spike"): [
        "{n} people in {city} are actively searching for dinner deals right now.",
        "Dinner demand is surging — {n} hungry buyers in {city} are ready to order.",
        "{n} food orders are waiting in {city} — this window closes fast.",
    ],
    ("restaurant", "drop"): [
        "Order volume in {city} has dropped — {n} potential diners are going elsewhere.",
        "{n} dinner orders were lost today — a targeted deal can win them back.",
        "Food demand in {city} is slipping — {n} buyers need a reason to order now.",
    ],
    ("restaurant", "rating_dip"): [
        "Your rating drop is costing you dinner orders — {n} customers may switch.",
        "{n} diners in {city} are reconsidering after your recent rating dip.",
        "A lower rating is pushing {n} food orders to competitors in {city}.",
    ],
    ("restaurant", "new_competitor"): [
        "A new restaurant opened in {city} — {n} of your regulars are at risk.",
        "{n} loyal diners in {city} are being targeted by a new competitor.",
        "Competition just entered {city} — {n} dinner orders could shift away.",
    ],
    ("restaurant", "low_repeat_rate"): [
        "{n} past diners in {city} haven't reordered in over 2 weeks.",
        "Repeat order rate is falling — {n} customers in {city} need a nudge.",
        "{n} one-time diners in {city} are slipping away without a follow-up.",
    ],
    ("restaurant", "festival"): [
        "Festival demand is live — {n} people in {city} are searching for food deals.",
        "{n} diners in {city} are looking for a festive meal offer right now.",
        "Peak dining window is open — {n} buyers in {city} are ready to order.",
    ],
    ("restaurant", "weekend_opportunity"): [
        "Weekend dinner demand is up — {n} buyers in {city} are searching right now.",
        "{n} people in {city} are planning their weekend meal — window is live.",
        "Weekend food orders are peaking — {n} hungry buyers in {city} are ready.",
    ],
    ("restaurant", "refill_reminder"): [
        "{n} regular diners in {city} haven't ordered in 2 weeks — reach them now.",
        "Repeat order window is open — {n} past customers in {city} need a nudge.",
        "{n} loyal diners in {city} are due for their next order today.",
    ],
    # ── GYM ─────────────────────────────────────────────────────────────────
    ("gym", "spike"): [
        "{n} people in {city} are actively looking to book a fitness session today.",
        "Fitness demand is surging — {n} motivated members in {city} want to train.",
        "{n} people in {city} are searching for a gym session right now.",
    ],
    ("gym", "drop"): [
        "Session bookings in {city} have dropped — {n} members are losing their streak.",
        "{n} gym members in {city} haven't booked this week — re-engage them now.",
        "Fitness momentum is slipping — {n} members in {city} need a push today.",
    ],
    ("gym", "rating_dip"): [
        "Your gym rating dropped — {n} members in {city} may cancel their plan.",
        "{n} fitness members in {city} are reconsidering after your recent reviews.",
        "A rating dip is putting {n} active memberships in {city} at risk.",
    ],
    ("gym", "new_competitor"): [
        "A new gym opened in {city} — {n} of your members are being targeted.",
        "{n} fitness members in {city} are at risk of switching to a new competitor.",
        "Competition just entered {city} — {n} gym sessions could shift away.",
    ],
    ("gym", "low_repeat_rate"): [
        "{n} members in {city} haven't booked a session in over 2 weeks.",
        "Repeat session rate is falling — {n} members in {city} are going inactive.",
        "{n} gym members in {city} are losing their fitness streak — act now.",
    ],
    ("gym", "festival"): [
        "Festival fitness demand is live — {n} people in {city} want to train today.",
        "{n} motivated members in {city} are looking for a festive fitness deal.",
        "Peak fitness window is open — {n} people in {city} are ready to book.",
    ],
    ("gym", "weekend_opportunity"): [
        "Weekend training demand is up — {n} members in {city} want to book today.",
        "{n} people in {city} are planning a weekend workout — window is live.",
        "Weekend fitness sessions are filling up — {n} buyers in {city} are ready.",
    ],
    ("gym", "refill_reminder"): [
        "{n} members in {city} haven't renewed their plan this month — act now.",
        "Plan renewal window is open — {n} gym members in {city} need a reminder.",
        "{n} fitness members in {city} are due for a plan renewal today.",
    ],
    # ── SALON ────────────────────────────────────────────────────────────────
    ("salon", "spike"): [
        "{n} style-seekers in {city} are actively browsing beauty slots right now.",
        "Beauty demand is surging — {n} clients in {city} are looking for a slot.",
        "{n} people in {city} are searching for a salon appointment today.",
    ],
    ("salon", "drop"): [
        "Salon bookings in {city} have dropped — {n} potential clients are going elsewhere.",
        "{n} beauty appointments were missed this week — a deal can bring them back.",
        "Slot demand in {city} is slipping — {n} style-seekers need a reason to book.",
    ],
    ("salon", "rating_dip"): [
        "Your salon rating dropped — {n} clients in {city} may book elsewhere.",
        "{n} beauty clients in {city} are reconsidering after your recent reviews.",
        "A rating dip is putting {n} loyal salon clients in {city} at risk.",
    ],
    ("salon", "new_competitor"): [
        "A new salon opened in {city} — {n} of your regulars are being targeted.",
        "{n} beauty clients in {city} are at risk of switching to a new competitor.",
        "Competition just entered {city} — {n} salon bookings could shift away.",
    ],
    ("salon", "low_repeat_rate"): [
        "{n} past clients in {city} haven't rebooked in over 3 weeks.",
        "Repeat booking rate is falling — {n} beauty clients in {city} need a nudge.",
        "{n} salon clients in {city} are slipping away without a follow-up offer.",
    ],
    ("salon", "festival"): [
        "Festival beauty demand is live — {n} style-seekers in {city} want a slot.",
        "{n} clients in {city} are looking for a festive beauty deal right now.",
        "Peak styling window is open — {n} people in {city} are ready to book.",
    ],
    ("salon", "weekend_opportunity"): [
        "Weekend beauty demand is up — {n} style-seekers in {city} want a slot today.",
        "{n} people in {city} are planning a weekend beauty appointment — act now.",
        "Weekend salon slots are filling up — {n} clients in {city} are ready.",
    ],
    ("salon", "refill_reminder"): [
        "{n} regular clients in {city} haven't rebooked their beauty slot this month.",
        "Rebooking window is open — {n} salon clients in {city} need a reminder.",
        "{n} loyal clients in {city} are due for their next beauty appointment.",
    ],
    # ── DENTIST ──────────────────────────────────────────────────────────────
    ("dentist", "spike"): [
        "{n} patients in {city} are actively seeking a dental checkup today.",
        "Appointment demand is up — {n} people in {city} need a dental visit.",
        "{n} people in {city} are searching for a trusted dentist right now.",
    ],
    ("dentist", "drop"): [
        "Appointment bookings in {city} have dropped — {n} patients need a reminder.",
        "{n} dental patients in {city} are overdue — a timely offer can bring them in.",
        "Checkup demand in {city} is slipping — {n} patients haven't rebooked.",
    ],
    ("dentist", "rating_dip"): [
        "Your clinic rating dropped — {n} patients in {city} may seek care elsewhere.",
        "{n} dental patients in {city} are reconsidering after your recent reviews.",
        "A trust dip is putting {n} patient relationships in {city} at risk.",
    ],
    ("dentist", "new_competitor"): [
        "A new dental clinic opened in {city} — {n} of your patients are at risk.",
        "{n} patients in {city} are being targeted by a new dental competitor.",
        "Competition just entered {city} — {n} checkup appointments could shift away.",
    ],
    ("dentist", "low_repeat_rate"): [
        "{n} patients in {city} haven't booked a follow-up checkup in 6 months.",
        "Recall rate is falling — {n} dental patients in {city} are overdue.",
        "{n} patients in {city} are missing their routine checkup — reach them now.",
    ],
    ("dentist", "refill_reminder"): [
        "{n} patients in {city} are due for their next dental checkup this month.",
        "Checkup reminders are overdue — {n} patients in {city} haven't rebooked.",
        "{n} dental patients in {city} need a recall reminder today.",
    ],
    ("dentist", "weekend_opportunity"): [
        "Weekend appointment slots are open — {n} patients in {city} need a checkup.",
        "{n} people in {city} are looking for a weekend dental appointment today.",
        "Weekend dental demand is live — {n} patients in {city} are ready to book.",
    ],
    # ── PHARMACY ─────────────────────────────────────────────────────────────
    ("pharmacy", "spike"): [
        "{n} customers in {city} need medicine refills or care visits right now.",
        "Health demand is up — {n} people in {city} are searching for a pharmacy.",
        "{n} customers in {city} are actively looking for urgent medicine today.",
    ],
    ("pharmacy", "drop"): [
        "Refill orders in {city} have dropped — {n} customers may be going elsewhere.",
        "{n} pharmacy customers in {city} haven't reordered — a reminder can help.",
        "Medicine demand in {city} is slipping — {n} customers need a care nudge.",
    ],
    ("pharmacy", "rating_dip"): [
        "Your pharmacy rating dropped — {n} customers in {city} may switch providers.",
        "{n} care customers in {city} are reconsidering after your recent reviews.",
        "A trust dip is putting {n} loyal pharmacy customers in {city} at risk.",
    ],
    ("pharmacy", "new_competitor"): [
        "A new pharmacy opened in {city} — {n} of your regulars are at risk.",
        "{n} medicine customers in {city} are being targeted by a new competitor.",
        "Competition just entered {city} — {n} refill orders could shift away.",
    ],
    ("pharmacy", "low_repeat_rate"): [
        "{n} customers in {city} haven't refilled their medicine in over 3 weeks.",
        "Repeat refill rate is falling — {n} pharmacy customers in {city} need a nudge.",
        "{n} care customers in {city} are overdue for a refill — reach them now.",
    ],
    ("pharmacy", "refill_reminder"): [
        "{n} customers in {city} are due for a medicine refill this week.",
        "Refill reminders are overdue — {n} customers in {city} need their medicine.",
        "{n} pharmacy customers in {city} haven't refilled in 30 days — act now.",
    ],
    ("pharmacy", "festival"): [
        "Festival health demand is live — {n} customers in {city} need care supplies.",
        "{n} people in {city} are stocking up on medicine for the festive season.",
        "Peak health demand is open — {n} customers in {city} need a refill deal.",
    ],
    ("pharmacy", "weekend_opportunity"): [
        "Weekend health demand is up — {n} customers in {city} need refills today.",
        "{n} people in {city} are planning weekend medicine pickups — act now.",
        "Weekend pharmacy demand is live — {n} customers in {city} are ready.",
    ],
}


def _get_line1(
    category: str,
    trigger_type: str,
    merchant_id: str,
    n: int,
    city: str,
    customer_prefix: str = "",
) -> str:
    """Pick a category+trigger-specific line1 deterministically."""
    _alias_map = {"festival": "festival", "refill_reminder": "refill_reminder"}
    tkey = _alias_map.get(trigger_type, trigger_type)
    templates = _TEMPLATES.get((category, tkey)) or _TEMPLATES.get((category, "spike"))
    if not templates:
        templates = [
            f"{n} potential customers in {city} are actively searching right now.",
            f"Right now, {n} buyers in {city} are looking for a deal.",
            f"{n} active buyers in {city} are ready to convert today.",
        ]
    idx = hash(merchant_id + tkey) % 3
    line = templates[idx].format(n=n, city=city)
    if customer_prefix:
        line = customer_prefix + line[0].lower() + line[1:]
    return line.strip()


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

    # 3 deterministic line1 variants — category+trigger specific, picked by hash
    line1_variants = [
        _get_line1(ctx.category, ctx.trigger_type, ctx.merchant_id, plan.estimated_customers, ctx.city, customer_prefix),
        _get_line1(ctx.category, ctx.trigger_type, ctx.merchant_id + "_v2", plan.estimated_customers, ctx.city, ""),
        _get_line1(ctx.category, ctx.trigger_type, ctx.merchant_id + "_v3", plan.estimated_customers, ctx.city, ""),
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
