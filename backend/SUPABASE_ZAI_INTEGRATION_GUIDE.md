# ResolveMesh Supabase + Z.AI Integration Guide

## 📋 Quick Start

### 1. Backend Environment Setup

Your `.env` file is already configured with:
- **Supabase URL**: `https://ztamcvkqxjucvaiziwqs.supabase.co`
- **Supabase Service Role Key**: ✅ Set (gives backend access to all tables)
- **Z.AI API Key**: ✅ Set (`sk-a3d1c498...`)
- **Z.AI Base URL**: `https://api.ilmu.ai/anthropic/v1/messages`

### 2. Database Connection Status

**Connected Tables**:
- ✅ `disputes` - Main dispute records (id, customer_info, agent_reports, status)
- ✅ `system_logs` - Event audit trail (event_name, payload, visibility)
- ✅ `transactions` - Ledger entries (ledger_data JSONB)
- ✅ `merchant_records` - Order fulfillment data (order_id, prep_status, items_prepared)
- ✅ `profiles` - User accounts (email, password_hash)

### 3. Available Endpoints

#### A. Dispute Management
```bash
# Create a dispute (from N8n webhook)
POST /api/disputes
Content-Type: application/json

{
  "customer_email": "user@example.com",
  "platform": "GrabFood",
  "amount": 45.50,
  "order_id": "GRB-999-MYS",
  "issue_type": "Quality Issue",
  "raw_text": "Moldy bread received",
  "evidence_url": "https://...",
  "account_id": "ACC-7788"
}
```

#### B. Agent Analysis
```bash
# Trigger legal agent analysis
POST /api/agents/analyze
Content-Type: application/json

{
  "dispute_id": "ae02d1fe-5a27-4702-b5ab-ef7b7f1b61fd",
  "agents": ["customerLawyer", "companyLawyer", "judge", "independentLawyer", "merchant"]
}
```

#### C. Evidence Retrieval
```bash
# Get evidence bundle for a dispute
GET /api/disputes/{dispute_id}/evidence?agent_type=judge

# Preview agent prompt (for debugging)
GET /api/disputes/{dispute_id}/agent-prompt-preview?agent_type=judge
```

#### D. PDF Generation
```bash
# Generate verdict PDF
POST /generate-pdf
Content-Type: application/json

{
  "dispute_id": "ae02d1fe-5a27-4702-b5ab-ef7b7f1b61fd",
  "template": "verdict",
  "summary": { ... investigation_summary ... }
}
```

#### E. Authentication
```bash
# Sign in or create account
POST /api/auth
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

---

## 🔄 End-to-End Data Flow

### Flow 1: Complaint → Dispute → Analysis

```
1. Customer submits complaint via ComplaintUI
   ↓
2. N8n receives via webhook: https://unemployed.app.n8n.cloud/webhook-test/userComplaint
   ↓
3. N8n makes HTTP POST to: /api/disputes (create dispute)
   ↓
4. Backend redacts PII using shield.redact_pii()
   ↓
5. Dispute inserted into Supabase disputes table
   ↓
6. System log created: GUARDIAN_REDACTION_COMPLETE
   ↓
7. (Optional) N8n triggers: /api/agents/analyze
   ↓
8. Backend runs 5 legal agents in parallel (5 sec each)
   ↓
9. Z.AI invokes agents with evidence context
   ↓
10. Results stored in disputes.agent_reports
    ↓
11. System log: LEGAL_AGENT_ANALYSIS_COMPLETE
```

### Flow 2: Analysis → PDF Generation

```
1. Agent analysis complete
   ↓
2. N8n calls: /generate-pdf
   ↓
3. Backend builds PDF using pdf_service.py (FPDF2)
   ↓
4. PDF uploaded to Supabase Storage
   ↓
5. Public URL returned to N8n
   ↓
6. N8n sends email to customer with PDF
```

---

## 🎯 Agent Evidence Configuration

Each legal agent sees different evidence based on role:

### Customer Lawyer (~50 events)
- ✅ Customer complaint details
- ✅ Transaction status
- ✅ Order fulfillment (delivery confirmation)
- ✅ Merchant response (if accepted)
- ❌ Merchant internal notes
- ❌ Payment reconciliation details

**Query**: 
```python
from evidence_config import get_agent_events
events = get_agent_events("customerLawyer")  # Returns 50 event types
```

### Company Lawyer (~100 events)
- ✅ All customer events
- ✅ Internal analysis (The Sleuth)
- ✅ Transaction reconciliation
- ✅ Chargeback details
- ✅ Refund tracking
- ❌ Regulatory reports

### Judge (~200 events)
- ✅ **COMPLETE ACCESS** - All events, all fields
- Sees everything for full context

### Independent Lawyer (~50 events)
- ✅ Objective evidence only
- ✅ Transaction facts
- ✅ Merchant response
- ✅ Customer claim
- ❌ Internal analysis
- ❌ Company notes

### Merchant (~100 events)
- ✅ Order preparation timeline
- ✅ Delivery confirmation
- ✅ Customer claim
- ✅ Transaction status
- ❌ Internal customer notes
- ❌ Company strategy

---

## 🔐 PII Masking Rules

When disputes are created, PII is automatically masked:

```
BEFORE: "My name is John Smith, IC 123456-78-9012, call me at 01234567890"
AFTER:  "My name is <PERSON>, IC <NRIC>, call me at <PHONE_NUMBER>"
```

**Masked Fields**:
- Person names → `<PERSON>`
- Phone numbers → `<PHONE_NUMBER>`
- Email addresses → `<EMAIL_ADDRESS>`
- Credit cards → `<CREDIT_CARD>`
- Malaysian IC/NRIC → `<NRIC>`
- Locations → `<LOCATION>`

Redaction happens in `shield.py`:
```python
from shield import redact_pii
masked_text = redact_pii("My name is John...")
```

---

## 📊 Data Schema Reference

### Disputes Table
```sql
disputes(
  id: UUID PRIMARY KEY,
  customer_info: JSONB {email, amount, order_id, platform, issue_type, evidence_url, account_id},
  agent_reports: JSONB {
    guardian: {summary, redacted_at},
    legal_agent_analysis: {
      agent_responses: {customerLawyer: {...}, companyLawyer: {...}, ...},
      validation_report: {...},
      analyzed_at: timestamp
    },
    investigation_summary: {agent, confidence_score, evidence, summary_tldr, created_at}
  },
  status: text (PENDING, BRIEF_SENT, SUSPECTED_FRAUD, RESOLVED)
)
```

### System Logs Table
```sql
system_logs(
  id: SERIAL PRIMARY KEY,
  event_name: text (GUARDIAN_REDACTION_COMPLETE, LEGAL_AGENT_ANALYSIS_COMPLETE, ...),
  payload: JSONB {...event-specific data...},
  created_at: timestamp,
  visibility: text (PUBLIC, INTERNAL)
)
```

### Transactions Table
```sql
transactions(
  id: UUID PRIMARY KEY,
  ledger_data: JSONB {
    amount, method, status, order_id, transaction_id,
    merchant_name, bank_status, merchant_status
  }
)
```

---

## 🚀 Starting the Backend

### 1. Activate Virtual Environment
```bash
cd c:\Users\TENG WEN HONG\Documents\ResolveMesh
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Start Backend Server
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test Connection
```bash
curl http://localhost:8000/api/zai/health

# Expected Response:
{
  "status": "connected",
  "message": "Z.AI is reachable"
}
```

---

## 🧪 Integration Testing

### Test 1: Create a Dispute
```bash
curl -X POST http://localhost:8000/api/disputes \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "test@example.com",
    "platform": "GrabFood",
    "amount": 45.50,
    "order_id": "GRB-999-MYS",
    "issue_type": "Quality Issue",
    "raw_text": "My name is John Smith. The food had mold. My phone is 01234567890",
    "account_id": "ACC-7788"
  }'
```

**Expected Response**:
```json
{
  "id": "ae02d1fe-5a27-4702-b5ab-ef7b7f1b61fd",
  "customer_info": {...},
  "agent_reports": {
    "guardian": {
      "summary": "My name is <PERSON>. The food had mold. My phone is <PHONE_NUMBER>",
      "redacted_at": "2026-04-24T12:00:00Z"
    }
  },
  "status": "PENDING"
}
```

### Test 2: Trigger Agent Analysis
```bash
curl -X POST http://localhost:8000/api/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_id": "ae02d1fe-5a27-4702-b5ab-ef7b7f1b61fd",
    "agents": ["judge"]
  }'
```

**Expected Response**:
```json
{
  "status": "success",
  "dispute_id": "ae02d1fe-5a27-4702-b5ab-ef7b7f1b61fd",
  "agents_analyzed": ["judge"],
  "validation_report": {
    "all_responses_valid": true,
    "hallucination_detected": false
  },
  "responses": {
    "judge": {
      "investigation_summary": "...",
      "confidence_score": 0.87,
      "evidence_array": [...],
      "summary_tldr": "..."
    }
  }
}
```

### Test 3: Get Evidence Bundle
```bash
curl http://localhost:8000/api/disputes/ae02d1fe-5a27-4702-b5ab-ef7b7f1b61fd/evidence?agent_type=judge

# Expected: Returns all system logs, transactions, timeline for dispute
```

---

## ⚡ Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Create Dispute | <1s | PII masking + Supabase insert |
| Evidence Gathering | <5s | Per agent, parallel OK |
| Agent Invocation | <5s | Z.AI API call |
| PDF Generation | <3s | FPDF2 rendering |
| **Total E2E** | **<15-20s** | Create → Analyze (5 agents) → PDF |

---

## 🔧 Troubleshooting

### Issue: "SUPABASE_SERVICE_ROLE_KEY missing"
**Solution**: Check `.env` file in backend/ directory. Key should start with `eyJ...`

### Issue: "Z.AI connection failed"
**Solution**: 
1. Verify `ZAI_API_KEY` in `.env`
2. Test: `curl http://localhost:8000/api/zai/health`

### Issue: "Evidence gathering timeout"
**Solution**: Increase `EVIDENCE_TIMEOUT` in `.env` (default: 15s)

### Issue: "PDF generation failed"
**Solution**: Check `SUPABASE_VERDICT_BUCKET` exists in Supabase Storage

---

## 📝 N8n Webhook Setup

### Configure N8n to Receive Complaints

1. **Create N8n Webhook Trigger**
   - Workflow: "User Complaint Intake"
   - Trigger: HTTP GET/POST
   - Webhook URL: (N8n auto-generates)

2. **Configure HTTP Node to Call Backend**
   ```
   Method: POST
   URL: http://localhost:8000/api/disputes
   Body: {customer_email, platform, amount, order_id, issue_type, raw_text, evidence_url}
   ```

3. **Optional: Trigger Analysis via N8n**
   ```
   Method: POST
   URL: http://localhost:8000/api/agents/analyze
   Body: {dispute_id: "{{ $json.id }}", agents: [...]}
   ```

4. **Generate PDF via N8n**
   ```
   Method: POST
   URL: http://localhost:8000/generate-pdf
   Body: {dispute_id, template: "verdict", summary: "{{ $json.agent_reports.investigation_summary }}"}
   ```

---

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Z.AI / Ilmu API Docs](https://api.ilmu.ai/docs)
- [FastAPI Docs](http://localhost:8000/docs) - Available when backend is running
- [N8n Webhook Setup](https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-trigger-webhook/)
