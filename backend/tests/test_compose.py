from fastapi.testclient import TestClient

from app.engine.decision_engine import decide
from app.engine.normalizer import normalize_context
from app.engine.persona import route_persona
from app.engine.scoring_engine import score_variants
from app.engine.signal_fusion import fuse_signals
from app.engine.strategy_engine import decide_strategy
from app.engine.trigger_intelligence import infer_trigger
from app.engine.variant_generator import generate_variants
from app.main import app
from app.schemas import ComposeRequest


client = TestClient(app)


def _payload() -> dict:
    return {
        "category": "restaurant",
        "merchant": {
            "merchant_id": "m_1021",
            "name": "Biryani House",
            "category": "restaurant",
            "city": "Bengaluru",
            "avg_order_value": 320,
            "weekly_orders": 1400,
            "conversion_rate": 0.19,
            "repeat_customer_rate": 0.27,
            "rating": 4.1,
            "margin_pct": 0.28,
        },
        "trigger": {
            "type": "spike",
            "observed_value": 240,
            "baseline_value": 150,
            "window_minutes": 180,
            "timestamp_utc": "2026-05-02T14:00:00Z",
        },
        "customer": {
            "customer_id": "c_991",
            "loyalty_tier": "gold",
            "visits_last_30d": 5,
            "spend_last_30d": 2100,
            "last_engagement_days": 4,
        },
    }


def _rating_dip_payload() -> dict:
    payload = _payload()
    payload["trigger"] = {
        "type": "rating_dip",
        "observed_value": 3.6,
        "baseline_value": 4.2,
        "window_minutes": 180,
        "timestamp_utc": "2026-05-02T14:00:00Z",
    }
    return payload


def _pipeline(payload: dict):
    normalized = normalize_context(ComposeRequest.model_validate(payload))
    trigger = infer_trigger(normalized.trigger_type)
    fused = fuse_signals(normalized)
    plan = decide(normalized, fused, trigger)
    strategy = decide_strategy(
        {
            "last_message_type": "info",
            "last_response": "ignored",
            "last_sent_at": "",
        },
        {"trigger_type": normalized.trigger_type, "cooldown_minutes": str(normalized.trigger_window_minutes)},
    )
    send_as = route_persona(fused, normalized.trigger_type, normalized.customer_id)
    variants = generate_variants(normalized, fused, trigger, plan, send_as, strategy_type=strategy)
    scored = score_variants(variants, normalized, fused)
    return normalized, fused, plan, variants, scored


def test_healthz() -> None:
    res = client.get("/v1/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_compose_deterministic_for_same_input() -> None:
    payload = _payload()

    a = client.post("/v1/tick", json=payload)
    b = client.post("/v1/tick", json=payload)

    assert a.status_code == 200
    assert b.status_code == 200

    assert a.json() == b.json()


def test_variants_are_distinct_and_cta_stable() -> None:
    _, _, _, variants, _ = _pipeline(_payload())

    assert len({variant.message for variant in variants}) == 3
    assert len({variant.cta for variant in variants}) == 1
    for variant in variants:
        assert variant.message.split("\n")[1] == variant.cta


def test_scoring_integrity_applies_penalty() -> None:
    _, _, _, variants, scored = _pipeline(_payload())

    best = scored[0]
    base = int(sum(best.score_components.values()) * 2)
    expected = max(0, min(100, base - best.anti_pattern_penalty))

    assert best.total_score == expected
    assert best.variant in variants


def test_rating_dip_message_and_cta_quality() -> None:
    _, _, _, variants, _ = _pipeline(_rating_dip_payload())

    best = variants[0]
    assert best.message.split("\n")[0] == "Recent rating drop detected impacting customer trust."
    assert best.cta.startswith("Run ₹")
    assert "trust-recovery campaign to improve reviews now?" in best.cta
    assert "Try this" not in best.cta


def test_context_and_reply_update_memory() -> None:
    context_res = client.post("/v1/context", json={"merchant_id": "m_1021", "memory": {"preferred_tone": "soft"}})
    assert context_res.status_code == 200

    reply_res = client.post(
        "/v1/reply",
        json={"merchant_id": "m_1021", "customer_id": "c_991", "reply_text": "Stop pinging now"},
    )
    assert reply_res.status_code == 200
    assert reply_res.json()["tone"] == "soft"
