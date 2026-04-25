#!/usr/bin/env python3
"""
quick_test.py - Fastest agent testing (2 minutes)

Run this to verify all agents are operational.
"""

import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("RESOLVEMESH AGENT QUICK TEST")
print("=" * 60)

# Test 1: Health checks
print("\n1. Testing system health...")
try:
    r = requests.get(f"{BASE_URL}/api/disputes", timeout=5)
    print(f"   Supabase: {'✅' if r.status_code == 200 else '❌'}")
except:
    print("   Supabase: ❌")

try:
    r = requests.get(f"{BASE_URL}/api/zai/health", timeout=5)
    print(f"   Z.AI: {'✅' if r.status_code == 200 else '❌'}")
except:
    print("   Z.AI: ❌")

# Test 2: Agent list
print("\n2. Checking agents...")
try:
    r = requests.get(f"{BASE_URL}/api/agents", timeout=5)
    agents = r.json()
    operational = [a for a in agents if a.get("system") == "operational"]
    legal = [a for a in agents if a.get("system") == "legal"]
    
    print(f"   Operational agents: {len(operational)}")
    for a in operational:
        print(f"      - {a['agent_type']}")
    
    print(f"   Legal agents: {len(legal)}")
    for a in legal:
        print(f"      - {a['agent_type']}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Create a test dispute
print("\n3. Creating test dispute...")
payload = {
    "customer_email": f"test+{int(time.time())}@example.com",
    "platform": "GrabFood",
    "amount": 45.50,
    "order_id": f"TEST-{int(time.time())}",
    "issue_type": "Not Delivered",
    "raw_text": "Never received my order",
    "evidence_url": "https://example.com/photo.jpg",
    "account_id": "ACC-TEST",
    "api_key": "INTERNAL_PORTAL"
}

try:
    r = requests.post(f"{BASE_URL}/api/disputes", json=payload, timeout=10)
    if r.status_code == 200:
        dispute_id = r.json()["case_id"]
        print(f"   ✅ Created: {dispute_id}")
        
        # Test 4: Get evidence
        print("\n4. Testing evidence retrieval...")
        r = requests.get(f"{BASE_URL}/api/disputes/{dispute_id}/evidence?agent_type=judge", timeout=10)
        if r.status_code == 200:
            bundle = r.json().get("bundle", {})
            has_disputes = bool(bundle.get("dispute_record"))
            has_transactions = bool(bundle.get("transactions"))
            has_merchant = bool(bundle.get("merchant_record"))
            
            print(f"   Disputes table: {'✅' if has_disputes else '❌'}")
            print(f"   Transactions table: {'✅' if has_transactions else '❌'}")
            print(f"   Merchant records: {'✅' if has_merchant else '❌'}")
        else:
            print(f"   ❌ Failed: {r.status_code}")
        
        # Test 5: Run judge
        print("\n5. Testing judge agent...")
        r = requests.post(
            f"{BASE_URL}/api/agents/analyze",
            json={"dispute_id": dispute_id, "agents": ["judge"]},
            timeout=60
        )
        if r.status_code == 200:
            status = r.json().get("status")
            valid = r.json().get("validation_report", {}).get("all_responses_valid")
            print(f"   Status: {status}")
            print(f"   Valid: {'✅' if valid else '❌'}")
        else:
            print(f"   ❌ Failed: {r.status_code}")
    else:
        print(f"   ❌ Failed: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ QUICK TEST COMPLETE")
print("=" * 60)
print("\nFor detailed testing, run:")
print("   python test_agents_comprehensive.py --all")
print("   python test_agents_comprehensive.py --individual --dispute-id <id>")
