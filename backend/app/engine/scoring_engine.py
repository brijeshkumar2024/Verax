from __future__ import annotations

from typing import List

from app.engine.anti_pattern import anti_pattern_check
from app.engine.types import FusedSignals, NormalizedContext, ScoredVariant, Variant


CATEGORY_KEYWORDS = {
    "restaurant": ["dinner", "table", "menu"],
    "gym": ["session", "trial", "fitness"],
    "salon": ["slot", "beauty", "styling"],
    "dentist": ["checkup", "hygiene", "dental"],
    "pharmacy": ["refill", "care", "medicine"],
}


def _specificity(message: str) -> int:
    """Calculate message specificity (higher = more concrete numbers and urgency)."""
    score = 20
    
    # Count numeric sequences (higher precision = more points)
    import re
    numbers = re.findall(r'\d+', message)
    if numbers:
        score += 25 + min(10, len(numbers) * 2)  # Bonus for multiple numbers
    
    # Currency symbol (high specificity signal)
    if "₹" in message or "Rs" in message:
        score += 20
    
    # Urgency markers
    urgency_markers = ["today", "now", "immediate", "act", "urgent", "speed"]
    urgency_count = sum(1 for m in urgency_markers if m in message.lower())
    score += urgency_count * 8
    
    # Multi-line message (better structure)
    if "\n" in message:
        score += 10
    
    # Strategic keywords
    if any(w in message.lower() for w in ["value", "impact", "roi", "capture", "demand"]):
        score += 5
    
    return min(100, score)


def _category_fit(category: str, message: str, cta: str) -> int:
    """Calculate how well message matches category expectations."""
    joined = f"{message.lower()} {cta.lower()}"
    hits = sum(1 for k in CATEGORY_KEYWORDS[category] if k in joined)
    base_fit = 65 + hits * 12
    
    # Bonus for category-specific pricing/positioning language
    if category == "restaurant" and any(w in joined for w in ["dining", "cuisine", "reservation"]):
        base_fit += 5
    if category == "gym" and any(w in joined for w in ["membership", "workout", "training"]):
        base_fit += 5
    if category == "salon" and any(w in joined for w in ["appointment", "consultation"]):
        base_fit += 5
    
    return min(100, base_fit)


def _engagement(cta: str, fatigue_penalty: int) -> int:
    """Calculate engagement strength based on CTA quality and fatigue state."""
    base = 80 if cta.endswith("?") else 65
    
    # Bonus for action verbs
    action_verbs = ["enable", "activate", "launch", "open", "trigger", "run"]
    if any(verb in cta.lower() for verb in action_verbs):
        base += 5
    
    # Reduce by fatigue
    return max(0, min(100, base - fatigue_penalty))


def _to_component_10(value_100: int) -> int:
    return max(0, min(10, round(value_100 / 10)))


def score_variants(
    variants: List[Variant],
    ctx: NormalizedContext,
    fused: FusedSignals,
) -> List[ScoredVariant]:
    """
    Score variants with improved differentiation to avoid score clustering.
    
    Weighting strategy:
    - Decision quality (signal fusion): 32% (primary driver)
    - Specificity (numbers, urgency): 24% (concrete over vague)
    - Category fit (domain relevance): 16% (business context)
    - Merchant fit (customer profile): 16% (personalization)
    - Engagement (CTA strength): 12% (call-to-action quality)
    """
    scored: List[ScoredVariant] = []
    
    for variant in variants:
        anti = anti_pattern_check(variant.message, variant.cta)
        penalty = int(anti["penalty_score"])
        specificity = _specificity(variant.message)
        cat_fit = _category_fit(ctx.category, variant.message, variant.cta)
        
        # Merchant fit with quality adjustment
        m_fit = min(100, int(fused.merchant_fit * 0.75 + (100 - penalty) * 0.25))
        
        # Decision quality: how well fused signals align
        quality = min(100, int(
            (fused.intent_score * 0.40) +
            (fused.urgency_score * 0.40) +
            (specificity * 0.20)
        ))
        
        # Engagement: CTA effectiveness adjusted for fatigue
        engage = _engagement(variant.cta, fused.fatigue_penalty)
        score_components = {
            "decision_quality": _to_component_10(quality),
            "specificity": _to_component_10(specificity),
            "category_fit": _to_component_10(cat_fit),
            "merchant_fit": _to_component_10(m_fit),
            "engagement": _to_component_10(engage),
        }

        component_sum = (
            score_components["decision_quality"]
            + score_components["specificity"]
            + score_components["category_fit"]
            + score_components["merchant_fit"]
            + score_components["engagement"]
        )
        # Scale penalty proportionally: raw penalty is 0–100 range, scale to component space
        scaled_penalty = round(penalty * 0.3)
        final_score = max(0, min(100, (component_sum * 2) - scaled_penalty))

        scored.append(
            ScoredVariant(
                variant=variant,
                decision_quality=quality,
                specificity=specificity,
                category_fit=cat_fit,
                merchant_fit=m_fit,
                engagement=engage,
                anti_pattern_penalty=penalty,
                score_components=score_components,
                total_score=final_score,
            )
        )

    # Deterministic sorting: score DESC → quality DESC → specificity DESC → message lexicographically
    scored.sort(key=lambda x: (-x.total_score, -x.decision_quality, -x.specificity, x.variant.message))
    return scored
