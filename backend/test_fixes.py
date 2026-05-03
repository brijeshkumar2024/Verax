#!/usr/bin/env python3
"""
VERAX Production Validation Suite
Tests all critical fixes: CORS, Determinism, Currency, Trigger Normalization, Suppression
"""

import json
import sys
from datetime import datetime, timedelta, timezone
import time
from typing import Any

# Add project to path
sys.path.insert(0, "/e:/VERAX/backend")

from app.main import app
from app.engine.trigger_normalizer import normalize_trigger, select_dominant_trigger, get_trigger_priority
from app.schemas import ComposeRequest, MerchantInput, TriggerInput, CustomerInput
from fastapi.testclient import TestClient

client = TestClient(app)

def test_header(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"✓ {title}")
    print(f"{'='*70}")

def test_cors_headers() -> bool:
    """Verify CORS middleware is configured."""
    test_header("TEST 1: CORS MIDDLEWARE")
    
    response = client.options("/v1/tick")
    
    required_headers = {
        "access-control-allow-origin": "http://localhost:3000",
        "access-control-allow-methods": "GET, POST, PUT, DELETE, OPTIONS",
        "access-control-allow-headers": "content-type",
    }
    
    for header, _ in required_headers.items():
        if header in response.headers:
            print(f"  ✓ {header}: {response.headers[header]}")
        else:
            print(f"  ✗ Missing header: {header}")
            return False
    
    print("  ✅ CORS correctly configured")
    return True

def test_currency_formatting() -> bool:
    """Verify ₹ symbol is used in all messages."""
    test_header("TEST 2: CURRENCY FORMATTING")
    
    payload = {
        "category": "restaurant",
        "merchant": {
            "merchant_id": "m_1021",
            "name": "Test Restaurant",
            "category": "restaurant",
            "city": "Mumbai",
            "avg_order_value": 500,
            "weekly_orders": 1000,
            "conversion_rate": 0.2,
            "repeat_customer_rate": 0.3,
            "rating": 4.2,
            "margin_pct": 0.25,
        },
        "trigger": {
            "type": "spike",
            "observed_value": 250,
            "baseline_value": 150,
            "window_minutes": 180,
            "timestamp_utc": datetime.fromtimestamp(time.time(), timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        "customer": {
            "customer_id": "c_001",
            "loyalty_tier": "gold",
            "visits_last_30d": 5,
            "spend_last_30d": 2500,
            "last_engagement_days": 2,
        },
    }
    
    response = client.post("/v1/tick", json=payload)
    data = response.json()
    
    if "₹" in data["message"]:
        print(f"  ✓ Found ₹ symbol in message")
        print(f"  Message preview: {data['message'][:80]}...")
    else:
        print(f"  ✗ No ₹ symbol found in message")
        print(f"  Message: {data['message']}")
        return False
    
    if "Rs" in data["message"]:
        print(f"  ✗ Old Rs format still present")
        return False
    else:
        print(f"  ✓ No old 'Rs' format found")
    
    print("  ✅ Currency formatting correct")
    return True

def test_determinism() -> bool:
    """Verify same input produces same output."""
    test_header("TEST 3: DETERMINISM GUARANTEE")
    
    payload = {
        "category": "gym",
        "merchant": {
            "merchant_id": "m_2022",
            "name": "FitPlex",
            "category": "gym",
            "city": "Bangalore",
            "avg_order_value": 2000,
            "weekly_orders": 80,
            "conversion_rate": 0.15,
            "repeat_customer_rate": 0.4,
            "rating": 4.5,
            "margin_pct": 0.5,
        },
        "trigger": {
            "type": "drop",
            "observed_value": 40,
            "baseline_value": 80,
            "window_minutes": 180,
            "timestamp_utc": "2026-05-02T14:30:00Z",
        },
    }
    
    # Call 1
    response1 = client.post("/v1/tick", json=payload)
    data1 = response1.json()
    
    # Call 2 with identical payload
    response2 = client.post("/v1/tick", json=payload)
    data2 = response2.json()
    
    # Check critical fields are identical
    fields_to_check = ["message", "cta", "send_as", "decision_score"]
    all_match = True
    
    for field in fields_to_check:
        if data1[field] == data2[field]:
            print(f"  ✓ {field}: matches between calls")
        else:
            print(f"  ✗ {field}: DIFFERS")
            print(f"    Call 1: {data1[field]}")
            print(f"    Call 2: {data2[field]}")
            all_match = False
    
    if all_match:
        print("  ✅ DETERMINISM CONTRACT VERIFIED")
        return True
    else:
        print("  ✗ DETERMINISM BROKEN")
        return False

def test_suppression_metadata() -> bool:
    """Verify suppression is returned as metadata, not changing message."""
    test_header("TEST 4: SUPPRESSION AS METADATA")
    
    payload = {
        "category": "pharmacy",
        "merchant": {
            "merchant_id": "m_3030",
            "name": "MedCare",
            "category": "pharmacy",
            "city": "Delhi",
            "avg_order_value": 300,
            "weekly_orders": 500,
            "conversion_rate": 0.18,
            "repeat_customer_rate": 0.35,
            "rating": 4.0,
            "margin_pct": 0.3,
        },
        "trigger": {
            "type": "low_repeat_rate",
            "observed_value": 45,
            "baseline_value": 100,
            "window_minutes": 180,
            "timestamp_utc": "2026-05-02T15:00:00Z",
        },
    }
    
    # First call - should not be suppressed
    response1 = client.post("/v1/tick", json=payload)
    data1 = response1.json()
    
    print(f"  Call 1:")
    print(f"    - suppressed: {data1['suppressed']}")
    print(f"    - decision_score: {data1['decision_score']}")
    
    # Second call - might be suppressed but message should be similar
    response2 = client.post("/v1/tick", json=payload)
    data2 = response2.json()
    
    print(f"  Call 2:")
    print(f"    - suppressed: {data2['suppressed']}")
    print(f"    - decision_score: {data2['decision_score']}")
    
    # Check that suppressed field exists
    if "suppressed" in data1:
        print(f"  ✓ suppressed field present in response")
    else:
        print(f"  ✗ suppressed field missing")
        return False
    
    # Even if suppressed, message should be real (not fallback)
    if "suppression active" not in data1["message"].lower():
        print(f"  ✓ Message is real decision (not suppression fallback)")
    else:
        print(f"  ✗ Message is suppression fallback (old behavior)")
        return False
    
    print("  ✅ SUPPRESSION AS METADATA VERIFIED")
    return True

def test_trigger_normalization() -> bool:
    """Verify trigger alias normalization works."""
    test_header("TEST 5: TRIGGER NORMALIZATION")
    
    test_cases = [
        ("dip", "drop"),
        ("festival", "weekend_opportunity"),
        ("refill_reminder", "low_repeat_rate"),
        ("spike", "spike"),
        ("drop", "drop"),
    ]
    
    for alias, expected in test_cases:
        try:
            result = normalize_trigger(alias)
            if result == expected:
                print(f"  ✓ '{alias}' → '{result}'")
            else:
                print(f"  ✗ '{alias}' mapped to '{result}' (expected '{expected}')")
                return False
        except ValueError as e:
            print(f"  ✗ Failed to normalize '{alias}': {e}")
            return False
    
    print("  ✅ TRIGGER NORMALIZATION VERIFIED")
    return True

def test_trigger_priority() -> bool:
    """Verify trigger priority triage works."""
    test_header("TEST 6: TRIGGER PRIORITY TRIAGE")
    
    # Test priority scoring
    triggers = ["spike", "drop", "new_competitor", "low_repeat_rate"]
    priorities = [(t, get_trigger_priority(t)) for t in triggers]
    
    print(f"  Trigger priorities (lower = higher priority):")
    for trigger, priority in sorted(priorities, key=lambda x: x[1]):
        print(f"    - {trigger}: {priority}")
    
    # Select dominant trigger
    selected = select_dominant_trigger(triggers)
    print(f"  Selected dominant trigger: {selected}")
    
    if selected == "spike":
        print(f"  ✓ Correctly selected highest priority trigger")
    else:
        print(f"  ✗ Did not select highest priority trigger")
        return False
    
    print("  ✅ TRIGGER PRIORITY TRIAGE VERIFIED")
    return True

def test_health_endpoint() -> bool:
    """Verify health endpoint works."""
    test_header("TEST 7: HEALTH ENDPOINT")
    
    response = client.get("/v1/healthz")
    if response.status_code == 200 and response.json()["status"] == "ok":
        print(f"  ✓ Health check passed")
        print("  ✅ HEALTH ENDPOINT VERIFIED")
        return True
    else:
        print(f"  ✗ Health check failed")
        return False

def main() -> None:
    """Run all tests."""
    print("\n" + "="*70)
    print("VERAX PRODUCTION VALIDATION SUITE")
    print(f"Timestamp: {datetime.fromtimestamp(time.time(), timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print("="*70)
    
    tests = [
        test_health_endpoint,
        test_cors_headers,
        test_currency_formatting,
        test_determinism,
        test_suppression_metadata,
        test_trigger_normalization,
        test_trigger_priority,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - SYSTEM READY FOR SUBMISSION")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
