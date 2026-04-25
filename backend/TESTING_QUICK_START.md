# 🧪 Testing All Agents - Quick Commands

## ⚡ Fastest Test (2 minutes)

**Terminal 1 - Start Backend:**
```bash
cd backend
python main.py
# Verify: http://localhost:8000/docs
```

**Terminal 2 - Run Quick Test:**
```bash
cd backend
python quick_test.py
```

Output shows:
- ✅/❌ Supabase connection
- ✅/❌ Z.AI connection
- ✅/❌ All agents operational
- ✅/❌ Evidence from 3 tables (disputes, transactions, merchant records)
- ✅/❌ Judge agent working

---

## 🧬 Test Individual Agents (5-10 minutes)

**After starting backend, in Terminal 2:**

### Get a Dispute ID First
```bash
# Create a new test dispute and get ID
python quick_test.py
# Copy the dispute_id from output
```

### Test One Agent at a Time
```bash
# Test Customer Lawyer (customer's perspective)
python test_agents_comprehensive.py --individual --dispute-id <paste-id-here>
```

This tests all 7 agents:
- ✅ customerLawyer (defends customer)
- ✅ companyLawyer (defends company)
- ✅ judge (neutral)
- ✅ independentLawyer (settlement)
- ✅ advocate (policy compliance)
- ✅ auditor (fraud detection)
- ✅ summarizer (staff summary)

---

## 📦 Test Evidence Bundles (5 minutes)

Verify all agents receive data from 3 tables:

```bash
python test_agents_comprehensive.py --evidence --dispute-id <id>
```

Output for each agent shows:
```
✅ Disputes table: YES
✅ Transactions table: YES  
✅ Merchant records: YES
```

---

## 🔄 Test Full Workflow (10-15 minutes)

Creates a dispute, retrieves evidence, runs all agents:

```bash
python test_agents_comprehensive.py --workflow
```

Tests:
1. Create dispute ✅
2. Get evidence ✅
3. Run judge ✅
4. Run all legal agents ✅

---

## 🚀 Test EVERYTHING (20 minutes)

```bash
python test_agents_comprehensive.py --all
```

Runs:
- Smoke tests (2 min)
- Individual agent tests (8 min)
- Evidence bundle tests (5 min)
- Full workflow (5 min)

---

## 📊 Using N8n to Test (After Backend Ready)

1. Go to: https://unemployed.app.n8n.cloud
2. Create workflow with:
   - Webhook (POST trigger)
   - HTTP call to `http://localhost:8000/api/disputes`
   - HTTP call to `http://localhost:8000/api/agents/analyze`
   - HTTP call to `http://localhost:8000/generate-pdf`
3. Test with:
```bash
curl -X POST https://unemployed.app.n8n.cloud/webhook-test/userComplaint \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "test@example.com",
    "platform": "GrabFood",
    "amount": 45.50,
    "order_id": "TEST-001",
    "issue_type": "Not Delivered",
    "raw_text": "Never received my order"
  }'
```

---

## 🎯 What Each Test Checks

| Test | Checks |
|------|--------|
| **smoke** | Backend alive, Z.AI up, agents registered |
| **individual** | Each agent produces valid JSON output |
| **evidence** | All agents get disputes + transactions + merchant data |
| **workflow** | Create → Evidence → Analyze → PDF pipeline |

---

## ⚠️ Troubleshooting

### Backend won't start
```bash
# Check port 8000 is free
netstat -ano | findstr :8000

# Or change port in .env
echo "PORT=8001" >> backend/.env
```

### Z.AI returns errors
- Check `ZAI_API_KEY` in `.env`
- Verify API key is valid at https://api.ilmu.ai

### No evidence in bundles
- Check merchant_records table has data
- Verify order_id matches between disputes and merchant_records

### Agent analysis timeout
- Normal for first run (model loading)
- Increase timeout: `TIMEOUT = 120`

---

## 📝 Expected Output

### Quick Test ✅
```
RESOLVEMESH AGENT QUICK TEST
============================================================

1. Testing system health...
   Supabase: ✅
   Z.AI: ✅

2. Checking agents...
   Operational agents: 3
      - advocate
      - auditor
      - summarizer
   Legal agents: 4
      - customerLawyer
      - companyLawyer
      - judge
      - independentLawyer

3. Creating test dispute...
   ✅ Created: disp-abc123def456

4. Testing evidence retrieval...
   Disputes table: ✅
   Transactions table: ✅
   Merchant records: ✅

5. Testing judge agent...
   Status: success
   Valid: ✅
```

### Individual Agent Test ✅
```
INDIVIDUAL AGENT TESTS
============================================================

Testing Legal Agents
→ [1/4] Testing customerLawyer
✅ customerLawyer: success

→ [2/4] Testing companyLawyer
✅ companyLawyer: success

→ [3/4] Testing judge
✅ judge: success

→ [4/4] Testing independentLawyer
✅ independentLawyer: success

Testing Operational Agents
→ [1/3] Testing advocate
✅ advocate: success

→ [2/3] Testing auditor
✅ auditor: success

→ [3/3] Testing summarizer
✅ summarizer: success
```

---

## 🎓 Understanding Agent Roles

### Legal Agents (Defense Arguments)
- **Customer Lawyer**: "Merchant didn't deliver!" (Uses disputes + transactions + merchant records)
- **Company Lawyer**: "We DID deliver, merchant logs prove it" (Uses same 3 tables)
- **Judge**: "Here's the objective truth based on evidence" (Neutral comparison of 3 tables)
- **Independent Lawyer**: "Here's a fair settlement" (Uses 3 tables + settlement analysis)

### Operational Agents (Backend Operations)
- **Advocate**: Validates policy compliance
- **Auditor**: Detects fraud patterns (6 rules: rapid disputes, duplicate emails, etc.)
- **Summarizer**: Creates staff dashboard summary (<30 words)

---

## 🔗 Quick Links

- Backend Swagger Docs: http://localhost:8000/docs
- Backend Health: http://localhost:8000/api/disputes
- Z.AI API: https://api.ilmu.ai
- Supabase Dashboard: https://app.supabase.com
- N8n Automation: https://unemployed.app.n8n.cloud

