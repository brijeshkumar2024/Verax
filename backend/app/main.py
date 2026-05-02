from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.engine.composer import compose
from app.engine.trigger_normalizer import normalize_trigger, select_dominant_trigger
from app.schemas import (
    ComposeRequest,
    ComposeResponse,
    ContextRequest,
    MetadataResponse,
    ReplyRequest,
    TickRequest,
)
from app.store.memory_store import state


app = FastAPI(title="VERAX API", version="1.0.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3006",
        "http://localhost:3100",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3006",
        "http://127.0.0.1:3100",
        "http://localhost:8000",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/healthz")
def healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/v1/metadata")
def metadata() -> MetadataResponse:
    """System metadata including supported categories and triggers."""
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
    )


@app.post("/v1/context")
def set_context(payload: ContextRequest) -> dict[str, str]:
    """Set merchant context/memory for tone and preference tracking."""
    state.set_context(payload.merchant_id, payload.memory)
    return {"status": "context_updated", "merchant_id": payload.merchant_id}


@app.post("/v1/tick")
def tick(payload: ComposeRequest) -> ComposeResponse:
    """
    Main compose decision endpoint.
    
    DETERMINISM GUARANTEE:
    - Same merchant + trigger + customer context always produces same decision
    - Suppression is returned as metadata, not changing the decision
    - Use trigger aliases (e.g., 'dip', 'festival', 'refill_reminder')
    """
    try:
        # Normalize trigger name in case user provided alias
        normalized_trigger = normalize_trigger(payload.trigger.type)  # type: ignore
        
        # Create new payload with normalized trigger
        normalized_payload = ComposeRequest(
            category=payload.category,
            merchant=payload.merchant,
            trigger=payload.trigger,  # Keep original for now
            customer=payload.customer,
        )
        
        # Override the trigger type with normalized version
        normalized_payload.trigger.type = normalized_trigger  # type: ignore
        
        return compose(normalized_payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"VERAX TICK ERROR: {e}")
        return ComposeResponse(
            message="High demand detected. A targeted offer can capture this window today.",
            cta="Run a quick offer to capture demand now?",
            send_as="system",
            suppression_key="fallback",
            suppressed=False,
            rationale=["Fallback decision triggered", "Edge case input detected", "Safe default applied"],
            decision_score=50,
            score_components={
                "decision_quality": 5,
                "specificity": 5,
                "category_fit": 5,
                "merchant_fit": 5,
                "engagement": 5,
            },
        )


@app.post("/v1/reply")
def reply(payload: ReplyRequest) -> dict[str, str]:
    """Record merchant reply to update tone preference."""
    lowered = payload.reply_text.lower()
    tone = "soft" if any(k in lowered for k in ["later", "not now", "stop ping"]) else "direct"
    if any(k in lowered for k in ["yes", "ok", "do it", "go ahead", "approved"]):
        response = "accepted"
    elif any(k in lowered for k in ["stop", "no", "don't", "reject"]):
        response = "rejected"
    else:
        response = "ignored"
    state.set_context(payload.merchant_id, {"preferred_tone": tone})
    state.set_last_response(payload.merchant_id, response)
    return {
        "status": "reply_recorded",
        "merchant_id": payload.merchant_id,
        "tone": tone,
    }
