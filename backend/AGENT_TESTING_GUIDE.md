# Complete Agent Testing Guide

## Quick Start

### 1️⃣ **Test Everything at Once** (2 minutes)
```bash
cd backend
python -m pytest integration_tests.py -v
```

### 2️⃣ **Test Backend Server**
```bash
cd backend
python main.py
# Verify: http://localhost:8000/docs (FastAPI Swagger)
```

---

## Testing Strategy

### Level 1: System Health ✅
**What**: Verify backend can reach dependencies
```bash
curl http://localhost:8000/api/supabase/health
curl http://localhost:8000/api/zai/health
```

### Level 2: Individual Agent Testing
**What**: Test each agent independently with sample data

#### Test Customer Lawyer (Evidence for customer)
```bash
POST http://localhost:8000/api/agents/analyze
{
  "dispute_id": "test-dispute-1",
  "agents": ["customerLawyer"]
}
```

#### Test Company Lawyer (Evidence for company)
```bash
POST http://localhost:8000/api/agents/analyze
{
  "dispute_id": "test-dispute-1",
  "agents": ["companyLawyer"]
}
```

#### Test Judge (Neutral)
```bash
POST http://localhost:8000/api/agents/analyze
{
  "dispute_id": "test-dispute-1",
  "agents": ["judge"]
}
```

#### Test Independent Lawyer (Settlement)
```bash
POST http://localhost:8000/api/agents/analyze
{
  "dispute_id": "test-dispute-1",
  "agents": ["independentLawyer"]
}
```

#### Test Operational Agents
```bash
POST http://localhost:8000/api/agents/analyze
{
  "dispute_id": "test-dispute-1",
  "agents": ["advocate", "auditor", "summarizer"]
}
```

### Level 3: Evidence Bundle Testing
**What**: Verify all agents get complete evidence (disputes + transactions + merchant records)

```bash
# Get evidence for Customer Lawyer
GET http://localhost:8000/api/disputes/{dispute_id}/evidence?agent_type=customerLawyer

# Check response includes:
# ✅ dispute_record (from disputes table)
# ✅ transactions (from transactions table)
# ✅ merchant_record (from merchant_records table)
# ✅ system_logs
# ✅ customer_info
```

### Level 4: Agent Report Validation
**What**: Check agent reports are stored in Supabase

```bash
GET http://localhost:8000/api/disputes/{dispute_id}

# Response should include in data.agent_reports:
{
  "guardian": {...},          # PII redaction
  "sleuth": {...},             # Investigation findings
  "legal_agent_analysis": {
    "customerLawyer": {...},
    "companyLawyer": {...},
    "judge": {...},
    "independentLawyer": {...}
  },
  "auditor": {
    "fraud_risk_score": 45,
    "findings": [...]
  }
}
```

### Level 5: Full End-to-End Testing
**What**: Complete dispute workflow

1. Create dispute (N8n webhook simulation)
2. Retrieve evidence
3. Run all agents
4. Generate PDF
5. Verify verdict

---

## Testing Scripts

### Script 1: Quick Smoke Test (2 minutes)

```python
# test_smoke.py
import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Health checks
print("1. Testing health endpoints...")
r1 = requests.get(f"{BASE_URL}/api/disputes")
r2 = requests.get(f"{BASE_URL}/api/zai/health")
print(f"   Disputes: {r1.status_code}")
print(f"   Z.AI: {r2.status_code}")

# Test 2: List agents
print("\n2. Testing agent list...")
r = requests.get(f"{BASE_URL}/api/agents")
agents = r.json()
print(f"   Operational agents: {len([a for a in agents if a['system'] == 'operational'])}")
print(f"   Legal agents: {len([a for a in agents if a['system'] == 'legal'])}")

# Test 3: Z.AI connection
print("\n3. Testing Z.AI...")
r = requests.post(
    f"{BASE_URL}/api/zai/chat",
    json={"message": "Say 'hello'"}
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   Reply: {r.json().get('reply', '')[:50]}...")

print("\n✅ Smoke test complete")
```

### Script 2: Individual Agent Tester

```python
# test_agents_individual.py
import requests
import json

BASE_URL = "http://localhost:8000"

AGENTS = [
    "customerLawyer",
    "companyLawyer", 
    "judge",
    "independentLawyer"
]

def test_agent(agent_type, dispute_id):
    print(f"\n🧪 Testing {agent_type}...")
    
    payload = {
        "dispute_id": dispute_id,
        "agents": [agent_type]
    }
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/agents/analyze",
            json=payload,
            timeout=60
        )
        
        if r.status_code == 200:
            data = r.json()
            status = data.get("status")
            validation = data.get("validation_report", {})
            
            print(f"✅ {agent_type}: {status}")
            print(f"   Valid: {validation.get('all_responses_valid')}")
            print(f"   Errors: {validation.get('summary', 'None')}")
            return True
        else:
            print(f"❌ {agent_type}: {r.status_code}")
            print(f"   Error: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {agent_type}: {str(e)}")
        return False

# Usage
if __name__ == "__main__":
    dispute_id = input("Enter dispute ID to test: ")
    
    results = {}
    for agent in AGENTS:
        results[agent] = test_agent(agent, dispute_id)
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for agent, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{agent}: {status}")
```

### Script 3: Evidence Bundle Verification

```python
# test_evidence_bundles.py
import requests
import json

BASE_URL = "http://localhost:8000"

def verify_evidence_bundle(dispute_id, agent_type):
    print(f"\n📦 Verifying evidence for {agent_type}...")
    
    r = requests.get(
        f"{BASE_URL}/api/disputes/{dispute_id}/evidence",
        params={"agent_type": agent_type}
    )
    
    if r.status_code != 200:
        print(f"❌ Failed to get evidence: {r.status_code}")
        return False
    
    data = r.json()
    stats = data.get("stats", {})
    bundle = data.get("bundle", {})
    
    # Check all three tables are present
    checks = {
        "disputes_table": bool(bundle.get("dispute_record")),
        "transactions_table": len(bundle.get("transactions", [])) > 0,
        "merchant_records_table": bool(bundle.get("merchant_record"))
    }
    
    print(f"✅ Evidence retrieved for {agent_type}")
    print(f"   Disputes: {checks['disputes_table']}")
    print(f"   Transactions: {checks['transactions_table']} ({stats.get('transactions_count', 0)} items)")
    print(f"   Merchant Records: {checks['merchant_records_table']}")
    print(f"   Total logs: {stats.get('system_logs_count', 0)}")
    
    return all(checks.values())

# Usage
if __name__ == "__main__":
    dispute_id = input("Enter dispute ID: ")
    
    agents = ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
    
    results = {}
    for agent in agents:
        results[agent] = verify_evidence_bundle(dispute_id, agent)
    
    print("\n" + "="*50)
    print("EVIDENCE BUNDLE SUMMARY")
    print("="*50)
    for agent, passed in results.items():
        status = "✅ COMPLETE" if passed else "❌ INCOMPLETE"
        print(f"{agent}: {status}")
```

### Script 4: Full Workflow Test

```python
# test_full_workflow.py
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_full_workflow():
    """Test complete workflow: Create → Analyze → PDF"""
    
    # Step 1: Create dispute
    print("\n[1/5] Creating dispute...")
    payload = {
        "customer_email": "test@example.com",
        "platform": "GrabFood",
        "amount": 45.50,
        "order_id": f"TEST-{int(time.time())}",
        "issue_type": "Not Delivered",
        "raw_text": "Never received my order",
        "evidence_url": "https://example.com/photo.jpg",
        "account_id": "ACC-TEST",
        "api_key": "INTERNAL_PORTAL"
    }
    
    r = requests.post(f"{BASE_URL}/api/disputes", json=payload)
    if r.status_code != 200:
        print(f"❌ Failed to create: {r.status_code}")
        return False
    
    dispute_id = r.json()["case_id"]
    print(f"✅ Dispute created: {dispute_id}")
    
    # Step 2: Get evidence
    print("\n[2/5] Retrieving evidence...")
    r = requests.get(f"{BASE_URL}/api/disputes/{dispute_id}/evidence?agent_type=judge")
    if r.status_code != 200:
        print(f"❌ Failed to get evidence: {r.status_code}")
        return False
    print(f"✅ Evidence retrieved")
    
    # Step 3: Run judge
    print("\n[3/5] Running judge analysis...")
    r = requests.post(
        f"{BASE_URL}/api/agents/analyze",
        json={"dispute_id": dispute_id, "agents": ["judge"]},
        timeout=60
    )
    if r.status_code != 200:
        print(f"❌ Analysis failed: {r.status_code}")
        return False
    print(f"✅ Judge analysis complete")
    
    # Step 4: Run all agents
    print("\n[4/5] Running all legal agents...")
    agents = ["customerLawyer", "companyLawyer", "independentLawyer"]
    for agent in agents:
        r = requests.post(
            f"{BASE_URL}/api/agents/analyze",
            json={"dispute_id": dispute_id, "agents": [agent]},
            timeout=60
        )
        if r.status_code == 200:
            print(f"   ✅ {agent}")
        else:
            print(f"   ❌ {agent}: {r.status_code}")
    
    # Step 5: Generate PDF
    print("\n[5/5] Generating verdict PDF...")
    r = requests.post(
        f"{BASE_URL}/generate-pdf",
        json={"dispute_id": dispute_id}
    )
    if r.status_code != 200:
        print(f"❌ PDF generation failed: {r.status_code}")
        return False
    
    pdf_url = r.json().get("pdf_url")
    print(f"✅ PDF generated: {pdf_url}")
    
    # Summary
    print("\n" + "="*60)
    print("✅ FULL WORKFLOW SUCCESSFUL")
    print("="*60)
    print(f"Dispute ID: {dispute_id}")
    print(f"PDF URL: {pdf_url}")
    
    return True

if __name__ == "__main__":
    test_full_workflow()
```

---

## Testing Checklist

### ✅ Agent Functionality
- [ ] Customer Lawyer gets customer-focused evidence
- [ ] Company Lawyer gets company-focused evidence
- [ ] Judge gets complete evidence
- [ ] Independent Lawyer gets settlement analysis data
- [ ] Auditor detects fraud patterns
- [ ] Guardian redacts PII
- [ ] Summarizer creates staff summary

### ✅ Evidence Quality
- [ ] Disputes table data included
- [ ] Transactions table data included
- [ ] Merchant records table data included
- [ ] Timestamps cross-referenced
- [ ] PII properly masked
- [ ] Logs contain relevant events

### ✅ Agent Reports
- [ ] Each agent stores JSON report
- [ ] Reports include confidence scores
- [ ] Reports cite evidence sources
- [ ] Reports are validation-passed JSON
- [ ] Fraud score populated in auditor report

### ✅ End-to-End
- [ ] Dispute creation works
- [ ] Evidence retrieval works
- [ ] Agent analysis works
- [ ] PDF generation works
- [ ] All agents produce valid output

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Z.AI returns markdown instead of JSON | Backend auto-extracts JSON from markdown code blocks |
| Evidence is incomplete | Check merchant_records table has data for order_id |
| Agent analysis timeout | Increase timeout, may be cold start |
| PII not masked | Guardian agent may be skipped, check logs |
| PDF generation fails | Ensure all agent reports are complete first |

