from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.engine.composer import compose
from app.engine.trigger_normalizer import normalize_trigger, select_dominant_trigger
from app.schemas import (
    ComposeRequest,
    ComposeResponse,
    ContextRequest,
    MetadataResponse,
    ReplyRequest,
    RuleTrace,
    TickRequest,
)
from app.store.memory_store import state

_START_TIME = time.time()

app = FastAPI(
    title="VERAX Deterministic Decision Engine",
    version="1.0.0",
    description="Production-grade, deterministic, explainable AI decision system for merchant growth.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/healthz")
def healthz() -> dict:
    return {
        "status": "ok",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "deterministic": True,
    }


@app.get("/v1/metadata")
def metadata() -> MetadataResponse:
    return MetadataResponse(
        name="VERAX Deterministic Decision Engine",
        version="1.0.0",
        deterministic=True,
        latency_target_ms=300,
        supported_categories=["restaurant", "gym", "salon", "dentist", "pharmacy"],
        supported_triggers=[
            "spike",
            "drop",
            "high_cart_abandon",
            "low_repeat_rate",
            "new_competitor",
            "rating_dip",
            "inventory_expiry",
            "weekend_opportunity",
        ],
        trigger_priority_order=[
            "spike", "drop", "new_competitor", "rating_dip",
            "high_cart_abandon", "low_repeat_rate", "inventory_expiry", "weekend_opportunity",
        ],
        tone_engine={
            "restaurant": {"voice": "sharp-growth", "urgency": "today", "cta_style": "table-turn"},
            "gym":        {"voice": "coach-driven",  "urgency": "now",   "cta_style": "session-book"},
            "salon":      {"voice": "premium-friendly", "urgency": "today", "cta_style": "slot-fill"},
            "dentist":    {"voice": "clinical-trust", "urgency": "today", "cta_style": "appointment-lock"},
            "pharmacy":   {"voice": "care-urgent",   "urgency": "now",   "cta_style": "refill-activate"},
        },
        determinism_guarantee=(
            "Same merchant + trigger + customer context always produces identical output. "
            "No randomness, no temperature, no probabilistic sampling. "
            "Pure rule-and-score path with stable tie-break ordering."
        ),
        suppression="Per merchant+trigger+time-slot key. Window configurable via trigger.window_minutes.",
        fatigue_model="Interaction history tracked per merchant. Penalty applied after repeated sends.",
    )


@app.post("/v1/context")
def set_context(payload: ContextRequest) -> dict:
    state.set_context(payload.merchant_id, payload.memory)
    return {
        "status": "context_updated",
        "merchant_id": payload.merchant_id,
        "keys_set": list(payload.memory.keys()),
    }


@app.post("/v1/tick")
def tick(payload: ComposeRequest) -> ComposeResponse:
    """
    Main compose decision endpoint.

    DETERMINISM GUARANTEE:
    - Same merchant + trigger + customer context always produces same decision.
    - Suppression returned as metadata only — does not alter the decision.
    - Trigger aliases accepted (e.g. 'dip', 'festival', 'refill_reminder').
    """
    try:
        normalized_trigger = normalize_trigger(payload.trigger.type)
        normalized_payload = ComposeRequest(
            category=payload.category,
            merchant=payload.merchant,
            trigger=payload.trigger,
            customer=payload.customer,
        )
        normalized_payload.trigger.type = normalized_trigger  # type: ignore
        return compose(normalized_payload)
    except ValueError as e:
        # Unknown trigger — fall back to spike (highest priority) and note in trace
        normalized_payload = ComposeRequest(
            category=payload.category,
            merchant=payload.merchant,
            trigger=payload.trigger,
            customer=payload.customer,
        )
        normalized_payload.trigger.type = "spike"  # type: ignore
        result = compose(normalized_payload)
        # Annotate rule trace to show fallback was applied
        fallback_trace = RuleTrace(
            trigger_type=f"unknown({payload.trigger.type})→spike",
            dominant_signal=result.rule_trace.dominant_signal,
            priority=result.rule_trace.priority,
            strategy=result.rule_trace.strategy,
            deviation_pct=result.rule_trace.deviation_pct,
            intent_score=result.rule_trace.intent_score,
            urgency_score=result.rule_trace.urgency_score,
        )
        return result.model_copy(update={"rule_trace": fallback_trace})
    except Exception as e:
        print(f"VERAX TICK ERROR: {e}")
        return ComposeResponse(
            message="High demand detected. A targeted offer can capture this window today.",
            cta="Want me to send them a quick offer now?",
            send_as="system",
            suppression_key="fallback",
            suppressed=False,
            rationale="Fallback decision triggered | Edge case input detected | Safe default applied",
            decision_score=50,
            score_components={"decision_quality": 5, "specificity": 5, "category_fit": 5, "merchant_fit": 5, "engagement": 5},
            rule_trace=RuleTrace(
                trigger_type="fallback",
                dominant_signal="demand",
                priority="capture-demand-now",
                strategy="urgency",
                deviation_pct=0.0,
                intent_score=50,
                urgency_score=50,
            ),
        )


@app.post("/v1/reply")
def reply(payload: ReplyRequest) -> dict:
    """Record merchant reply to update tone preference and response memory."""
    lowered = payload.reply_text.lower()
    tone = "soft" if any(k in lowered for k in ["later", "not now", "stop"]) else "direct"
    if any(k in lowered for k in ["yes", "ok", "do it", "go ahead", "approved", "sure"]):
        response = "accepted"
    elif any(k in lowered for k in ["stop", "no", "don't", "reject", "never"]):
        response = "rejected"
    elif any(k in lowered for k in ["later", "not now", "maybe", "confused", "what", "?"]):
        response = "deferred"
    else:
        response = "ignored"

    state.set_context(payload.merchant_id, {"preferred_tone": tone})
    state.set_last_response(payload.merchant_id, response)

    next_action_map = {
        "accepted":  "Interaction recorded. Next decision will reinforce with follow-up offer.",
        "rejected":  "Suppression extended. Next decision will use softer tone and longer cooldown.",
        "deferred":  "Cooldown applied. Next decision will use softer messaging after delay.",
        "ignored":   "Strategy will rotate to social_proof on next tick to improve engagement.",
    }

    return {
        "status": "reply_recorded",
        "merchant_id": payload.merchant_id,
        "interpreted_response": response,
        "tone_updated": tone,
        "next_action": next_action_map[response],
    }
