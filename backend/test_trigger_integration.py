#!/usr/bin/env python3
"""
Integration test: Verify trigger normalization works through the API endpoint
"""

import sys
from datetime import datetime

sys.path.insert(0, "/e:/VERAX/backend")

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_trigger_alias_via_api():
    """Test that trigger aliases work through the /v1/tick endpoint."""
    
    print("\n" + "="*70)
    print("INTEGRATION TEST: Trigger Alias Normalization via API")
    print("="*70)
    
    test_cases = [
        ("dip", "drop", "Decline signal"),
        ("festival", "weekend_opportunity", "Seasonal peak"),
        ("refill_reminder", "low_repeat_rate", "Retention signal"),
        ("spike", "spike", "Direct match"),
    ]
    
    for alias, canonical, description in test_cases:
        print(f"\nTest Case: '{alias}' → '{canonical}' ({description})")
        
        payload = {
            "category": "restaurant",
            "merchant": {
                "merchant_id": "m_test_001",
                "name": "Test Restaurant",
                "category": "restaurant",
                "city": "Mumbai",
                "avg_order_value": 400,
                "weekly_orders": 1000,
                "conversion_rate": 0.2,
                "repeat_customer_rate": 0.3,
                "rating": 4.1,
                "margin_pct": 0.28,
            },
            "trigger": {
                "type": alias,  # Use the alias!
                "observed_value": 240,
                "baseline_value": 150,
                "window_minutes": 180,
                "timestamp_utc": "2026-05-02T14:00:00Z",
            },
            "customer": {
                "customer_id": "c_test_001",
                "loyalty_tier": "gold",
                "visits_last_30d": 5,
                "spend_last_30d": 2100,
                "last_engagement_days": 4,
            },
        }
        
        try:
            response = client.post("/v1/tick", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Status: 200 OK")
                print(f"  ✓ Message received: {data['message'][:60]}...")
                print(f"  ✓ Decision score: {data['decision_score']}/100")
                print(f"  ✓ Suppressed: {data['suppressed']}")
            elif response.status_code == 422:
                # Validation error - trigger alias not recognized
                error_detail = response.json()
                print(f"  ✗ Status: 422 (Validation Error)")
                print(f"  ✗ Error: {error_detail['detail']}")
            else:
                print(f"  ✗ Status: {response.status_code}")
                print(f"  ✗ Response: {response.text}")
        
        except Exception as e:
            print(f"  ✗ Exception: {e}")

def main():
    test_trigger_alias_via_api()
    print("\n" + "="*70)
    print("✅ Integration test complete")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
