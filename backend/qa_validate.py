from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Tuple

import httpx

BASE = "http://127.0.0.1:8000"


def timed_request(client: httpx.Client, method: str, path: str, payload: Dict[str, Any] | None = None) -> Tuple[httpx.Response, float]:
    start = time.perf_counter()
    res = client.request(method, f"{BASE}{path}", json=payload)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return res, elapsed_ms


def build_payload(category: str, trigger_type: str, merchant_id: str, ts: str, city: str = "Bengaluru") -> Dict[str, Any]:
    return {
        "category": category,
        "merchant": {
            "merchant_id": merchant_id,
            "name": f"{category.title()} Prime",
            "category": category,
            "city": city,
            "avg_order_value": 320 if category != "gym" else 450,
            "weekly_orders": 1400 if category != "dentist" else 550,
            "conversion_rate": 0.19,
            "repeat_customer_rate": 0.27,
            "rating": 4.1,
            "margin_pct": 0.28,
        },
        "trigger": {
            "type": trigger_type,
            "observed_value": 240,
            "baseline_value": 150,
            "window_minutes": 180,
            "timestamp_utc": ts,
        },
        "customer": {
            "customer_id": "c_991",
            "loyalty_tier": "gold",
            "visits_last_30d": 5,
            "spend_last_30d": 2100,
            "last_engagement_days": 4,
        },
    }


def validate_message_rules(data: Dict[str, Any]) -> Dict[str, bool]:
    msg = data.get("message", "")
    cta = data.get("cta", "")
    return {
        "has_number": any(ch.isdigit() for ch in msg),
        "has_rupee_symbol": "₹" in msg,
        "has_urgency": any(k in msg.lower() for k in ["today", "now", "right now"]),
        "single_cta_field": isinstance(cta, str) and len(cta.strip()) > 0,
        "max_2_lines": msg.count("\n") <= 1,
    }


def validate_structure(data: Dict[str, Any]) -> Dict[str, bool]:
    required = ["message", "cta", "send_as", "suppression_key", "rationale", "decision_score"]
    return {k: (k in data) for k in required}


def main() -> None:
    report: Dict[str, Any] = {
        "endpoint_tests": {},
        "functional_cases": [],
        "edge_cases": {},
        "quality_notes": [],
    }

    with httpx.Client(timeout=10.0) as client:
        # Endpoint tests
        h, h_ms = timed_request(client, "GET", "/v1/healthz")
        m, m_ms = timed_request(client, "GET", "/v1/metadata")
        c, c_ms = timed_request(
            client,
            "POST",
            "/v1/context",
            {"merchant_id": "m_ctx", "memory": {"preferred_tone": "soft"}},
        )
        r, r_ms = timed_request(
            client,
            "POST",
            "/v1/reply",
            {"merchant_id": "m_ctx", "customer_id": "c_1", "reply_text": "stop ping now"},
        )

        report["endpoint_tests"] = {
            "GET /v1/healthz": {"status_code": h.status_code, "latency_ms": round(h_ms, 2)},
            "GET /v1/metadata": {"status_code": m.status_code, "latency_ms": round(m_ms, 2)},
            "POST /v1/context": {"status_code": c.status_code, "latency_ms": round(c_ms, 2)},
            "POST /v1/reply": {"status_code": r.status_code, "latency_ms": round(r_ms, 2)},
        }

        cases: List[Tuple[str, Dict[str, Any]]] = [
            ("case_1_restaurant_spike", build_payload("restaurant", "spike", "m_r1", "2026-05-02T14:00:00Z")),
            ("case_2_gym_dip", build_payload("gym", "drop", "m_g1", "2026-05-02T15:00:00Z", city="Pune")),
            ("case_3_salon_festival", build_payload("salon", "weekend_opportunity", "m_s1", "2026-05-02T16:00:00Z", city="Delhi")),
            ("case_4_pharmacy_refill_reminder", build_payload("pharmacy", "low_repeat_rate", "m_p1", "2026-05-02T17:00:00Z", city="Mumbai")),
        ]

        for case_name, payload in cases:
            res, t_ms = timed_request(client, "POST", "/v1/tick", payload)
            data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
            report["functional_cases"].append(
                {
                    "name": case_name,
                    "status_code": res.status_code,
                    "latency_ms": round(t_ms, 2),
                    "structure": validate_structure(data),
                    "message_rules": validate_message_rules(data),
                    "send_as": data.get("send_as"),
                    "decision_score": data.get("decision_score"),
                    "message": data.get("message"),
                    "cta": data.get("cta"),
                }
            )

        # Determinism check on same input
        payload_det = build_payload("restaurant", "spike", "m_det", "2026-05-02T18:00:00Z")
        d1, _ = timed_request(client, "POST", "/v1/tick", payload_det)
        d2, _ = timed_request(client, "POST", "/v1/tick", payload_det)
        report["edge_cases"]["determinism_same_input"] = {
            "equal_outputs": d1.json() == d2.json(),
            "first_score": d1.json().get("decision_score"),
            "second_score": d2.json().get("decision_score"),
            "first_message": d1.json().get("message"),
            "second_message": d2.json().get("message"),
        }

        # Suppression check
        payload_sup = build_payload("gym", "drop", "m_sup", "2026-05-02T19:00:00Z")
        s1, _ = timed_request(client, "POST", "/v1/tick", payload_sup)
        s2, _ = timed_request(client, "POST", "/v1/tick", payload_sup)
        report["edge_cases"]["suppression"] = {
            "first_status": s1.status_code,
            "second_status": s2.status_code,
            "second_mentions_suppression": "suppression" in " ".join(s2.json().get("rationale", [])).lower(),
            "same_suppression_key": s1.json().get("suppression_key") == s2.json().get("suppression_key"),
        }

        # High fatigue behavior on pharmacy (vary timestamps to avoid suppression collision)
        fatigue_payloads = [
            build_payload("pharmacy", "low_repeat_rate", "m_fat", f"2026-05-02T0{h}:00:00Z") for h in [1, 2, 3, 4]
        ]
        for p in fatigue_payloads:
            timed_request(client, "POST", "/v1/tick", p)
        fat5, _ = timed_request(client, "POST", "/v1/tick", build_payload("pharmacy", "low_repeat_rate", "m_fat", "2026-05-02T09:00:00Z"))
        fat_data = fat5.json()
        report["edge_cases"]["high_fatigue_tone"] = {
            "cta": fat_data.get("cta"),
            "softened_cta": "soft" in fat_data.get("cta", "").lower(),
        }

        # Invalid input behavior
        inv, inv_ms = timed_request(client, "POST", "/v1/tick", build_payload("salon", "festival", "m_inv", "2026-05-02T10:00:00Z"))
        report["edge_cases"]["invalid_input"] = {
            "status_code": inv.status_code,
            "latency_ms": round(inv_ms, 2),
            "graceful_422": inv.status_code == 422,
        }

        # Performance summary for /v1/tick from functional cases
        tick_latencies = [case["latency_ms"] for case in report["functional_cases"]]
        report["edge_cases"]["performance"] = {
            "all_under_300ms": all(v < 300 for v in tick_latencies),
            "latencies_ms": tick_latencies,
            "max_ms": max(tick_latencies) if tick_latencies else None,
        }

        # Conflicting triggers capability note
        report["edge_cases"]["conflicting_triggers"] = {
            "supported": False,
            "note": "API accepts one trigger only, so direct conflict arbitration is not implemented.",
        }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
