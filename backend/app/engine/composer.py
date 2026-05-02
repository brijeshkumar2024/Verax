from __future__ import annotations

from app.engine.decision_engine import decide
from app.engine.normalizer import normalize_context
from app.engine.persona import route_persona
from app.engine.rationale import build_rationale
from app.engine.scoring_engine import score_variants
from app.engine.signal_fusion import fuse_signals
from app.engine.strategy_engine import classify_cta_type, decide_strategy
from app.engine.suppression import build_suppression_key
from app.engine.trigger_intelligence import infer_trigger
from app.engine.variant_generator import enforce_currency, enforce_message_rules, generate_variants
from app.schemas import ComposeRequest, ComposeResponse, RuleTrace
from app.store.memory_store import state


def compose(payload: ComposeRequest) -> ComposeResponse:
    """
    Deterministic compose orchestration.
    
    DETERMINISM CONTRACT:
    - Same input (merchant, trigger, customer context) ALWAYS produces same output
    - Suppression is tracked but does NOT change the decision message
    - Suppression state is returned as metadata for upstream business logic
    
    This ensures the decision engine itself is deterministic, while suppression
    can be applied by the calling layer (API endpoint, system) if needed.
    """
    ctx = normalize_context(payload)
    trig = infer_trigger(ctx.trigger_type)

    # Compute signals and strategy BEFORE suppression key (strategy needed for key)
    fused = fuse_signals(ctx)
    plan = decide(ctx, fused, trig)
    memory_signals = state.get_memory_signals(ctx.merchant_id)
    strategy = decide_strategy(
        memory_signals,
        {
            "trigger_type": ctx.trigger_type,
            "cooldown_minutes": str(ctx.trigger_window_minutes),
            "rating": str(ctx.rating),
        },
    )

    suppression_key = build_suppression_key(
        merchant_id=ctx.merchant_id,
        trigger_type=ctx.trigger_type,
        timestamp_utc=ctx.timestamp_utc,
        strategy=strategy,
    )
    suppressed = state.is_suppressed(suppression_key, window_minutes=ctx.trigger_window_minutes)

    # Pass recent interaction count for personalization fatigue guard
    recent_interactions = state.get_recent_interactions(ctx.merchant_id, minutes=1440)
    send_as = route_persona(fused, ctx.trigger_type, ctx.customer_id)

    # Generate and score variants (deterministically)
    variants = generate_variants(ctx, fused, trig, plan, send_as, strategy_type=strategy, recent_interaction_count=len(recent_interactions))
    scored = score_variants(variants, ctx, fused)
    best = scored[0]
    cta_type = classify_cta_type(best.variant.cta)

    # Apply soft tone if merchant prefers it
    memory = state.get_context(ctx.merchant_id)
    if memory.get("preferred_tone") == "soft":
        softened = best.variant.message.replace("act now", "act today").replace("execution speed matters", "timing matters")
        best_variant_message = softened
    else:
        best_variant_message = best.variant.message
    best_variant_message = enforce_message_rules(enforce_currency(best_variant_message))
    if best_variant_message.split("\n")[-1].strip() != best.variant.cta.strip():
        best_variant_message = best_variant_message.split("\n")[0] + "\n" + best.variant.cta

    rationale_list = build_rationale(
        ctx, trig, fused, plan, strategy, cta_type, best.total_score,
        winner_score=best.total_score,
        rejected_scores=[s.total_score for s in scored[1:]],
    )
    rationale = " | ".join(r.lstrip("🎯⚡⚠️👤💡📊 ") for r in rationale_list)

    # Final strict 2-line enforcement: line1 clean, line2 = CTA exactly, no trailing whitespace
    lines = [l.strip() for l in best_variant_message.split("\n") if l.strip()]
    line1 = lines[0] if lines else "Demand signal detected in your area."
    best_variant_message = line1 + "\n" + best.variant.cta.strip()
    deviation_pct = round((ctx.trigger_ratio - 1.0) * 100, 1)
    rule_trace = RuleTrace(
        trigger_type=ctx.trigger_type,
        dominant_signal=fused.dominant_signal,
        priority=plan.priority,
        strategy=strategy,
        deviation_pct=deviation_pct,
        intent_score=fused.intent_score,
        urgency_score=fused.urgency_score,
    )

    # Record interaction for memory/analytics
    state.add_interaction(
        merchant_id=ctx.merchant_id,
        trigger=ctx.trigger_type,
        cta=best.variant.cta,
        message=best_variant_message,
        customer_id=ctx.customer_id,
        message_type=strategy,
        cta_type=cta_type,
        response=memory_signals.get("last_response", "ignored"),
    )

    # Return deterministic decision + suppression metadata
    return ComposeResponse(
        message=best_variant_message,
        cta=best.variant.cta,
        send_as=best.variant.send_as,
        suppression_key=suppression_key,
        suppressed=(suppressed or fused.fatigue_suppressed),  # Metadata: clients can choose to honor this
        rationale=rationale,
        decision_score=best.total_score,
        score_components=best.score_components,
        rule_trace=rule_trace,
    )
