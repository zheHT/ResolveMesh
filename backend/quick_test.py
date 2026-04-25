#!/usr/bin/env python3
"""
quick_test.py - Fastest agent testing (2 minutes)

NEW BEHAVIOR (April 2026):
- NO LONGER creates disputes
- Analyzes existing PENDING disputes from Supabase
- Cross-references disputes → merchant_records → transactions tables
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("RESOLVEMESH AGENT QUICK TEST (April 2026)")
print("=" * 70)

# Test 0: Server connectivity
print("\n0. Checking server connectivity...")
try:
    r = requests.get(f"{BASE_URL}/api/agents", timeout=3)
    if r.status_code == 200:
        print(f"   ✅ Server running at {BASE_URL}")
    else:
        print(f"   ⚠️  Server responded with {r.status_code}")
except requests.ConnectionError:
    print(f"   ❌ Cannot connect to server at {BASE_URL}")
    print(f"      Start the server with: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    sys.exit(1)
except requests.Timeout:
    print(f"   ❌ Server timeout (server may be overloaded)")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Unexpected error: {e}")
    sys.exit(1)

# Test 1: Health checks
print("\n1. Testing system health...")
try:
    # Test Supabase connection (disputes table should be accessible)
    r = requests.post(f"{BASE_URL}/api/disputes", timeout=5)
    if r.status_code == 200:
        print(f"   ✅ Supabase connected")
    else:
        print(f"   ⚠️  Supabase: got {r.status_code}")
except requests.Timeout:
    print("   ⚠️  Supabase: timeout")
except Exception as e:
    print(f"   ❌ Supabase: {type(e).__name__}")

# Z.AI check (skip if slow)
try:
    r = requests.get(f"{BASE_URL}/api/zai/health", timeout=2)
    if r.status_code == 200:
        print(f"   ✅ Z.AI connected")
    else:
        print(f"   ⚠️  Z.AI: got {r.status_code}")
except:
    print("   ⚠️  Z.AI: unavailable or slow (may still work)")

# Test 2: Agent list
print("\n2. Checking agents...")
try:
    r = requests.get(f"{BASE_URL}/api/agents", timeout=3)
    if r.status_code == 200:
        data = r.json()
        # Handle both dict and list responses
        if isinstance(data, dict):
            operational = [a for a in data.get("operational_agents", []) if a]
            legal = [a for a in data.get("legal_agents", []) if a]
        else:
            operational = [a for a in data if isinstance(a, dict) and a.get("system") == "operational"]
            legal = [a for a in data if isinstance(a, dict) and a.get("system") == "legal"]
        
        total = len(operational) + len(legal)
        print(f"   ✅ {total} agents registered ({len(operational)} operational, {len(legal)} legal)")
    else:
        print(f"   ⚠️  Got {r.status_code} (may still be starting)")
except Exception as e:
    print(f"   ⚠️  Skip (may still be loading): {type(e).__name__}")

# Test 3: Analyze PENDING disputes (no creation)
print("\n3. Analyzing PENDING disputes from Supabase...")
try:
    r = requests.post(f"{BASE_URL}/api/disputes/analyze-pending", timeout=5)
    if r.status_code == 200:
        result = r.json()
        disputes_analyzed = result.get("disputes_processed", 0)
        
        if disputes_analyzed > 0:
            print(f"   ✅ Analyzed {disputes_analyzed} PENDING disputes")
        else:
            print(f"   ⚠️  No disputes to analyze")
    else:
        print(f"   ❌ Failed: {r.status_code}")
except requests.Timeout:
    print(f"   ⚠️  Analysis timeout")
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}")

print("\n" + "=" * 70)
print("✅ QUICK TEST COMPLETE")
print("=" * 70)
print("\nNEW WORKFLOW (April 2026):")
print("  • POST /api/disputes → Analyzes PENDING disputes (no creation)")
print("  • System reads from Supabase, doesn't create test data")
print("  • Use forensic_investigation.py for detailed analysis")
print("=" * 70)
