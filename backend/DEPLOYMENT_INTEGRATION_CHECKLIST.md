# ResolveMesh Deployment Checklist - Supabase + Z.AI Integration

## ✅ Pre-Deployment Verification

### A. Environment Configuration
- [ ] `.env` file exists in `backend/` directory
- [ ] `SUPABASE_URL` = `https://ztamcvkqxjucvaiziwqs.supabase.co`
- [ ] `SUPABASE_SERVICE_ROLE_KEY` is set (not empty)
- [ ] `ZAI_API_KEY` is set (starts with `sk-`)
- [ ] `PORT` = 8000 (or desired port)

### B. Database Schema Verification

Run these queries in Supabase to verify table structure:

```sql
-- Check disputes table
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'disputes' ORDER BY ordinal_position;

-- Expected columns:
-- - id (uuid)
-- - customer_info (jsonb)
-- - agent_reports (jsonb)
-- - status (text)
-- - created_at (timestamptz)

-- Check system_logs table
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'system_logs' ORDER BY ordinal_position;

-- Expected columns:
-- - id (bigint/serial)
-- - event_name (text)
-- - payload (jsonb)
-- - created_at (timestamptz)
-- - visibility (text)

-- Check transactions table
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'transactions' ORDER BY ordinal_position;

-- Expected columns:
-- - id (uuid)
-- - ledger_data (jsonb)
```

### C. Python Dependencies

```bash
# Verify all required packages installed
cd backend
pip list | grep -E "fastapi|supabase|requests|python-dotenv|pydantic|fpdf2"

# Required packages:
# - fastapi >= 0.95.0
# - python-supabase >= 2.0.0
# - requests >= 2.31.0
# - python-dotenv >= 1.0.0
# - pydantic >= 2.0.0
# - fpdf2 >= 2.7.0
```

### D. Test Connectivity

```bash
# 1. Start backend
cd backend
uvicorn main:app --reload --port 8000

# 2. Run integration tests (in new terminal)
cd backend
python integration_tests.py http://localhost:8000

# 3. Verify all 7 tests pass:
# ✅ Supabase Connection
# ✅ Z.AI Connection
# ✅ Create Dispute
# ✅ Get Evidence
# ✅ Agent Analysis
# ✅ Z.AI Chat
# ✅ Authentication
```

---

## 🚀 Deployment Steps

### Step 1: Backend Deployment (FastAPI)

**Option A: Local Development**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option B: Production (Gunicorn)**
```bash
pip install gunicorn
cd backend
gunicorn main:app -w 4 -b 0.0.0.0:8000 --timeout 60
```

**Option C: Cloud (Railway, Heroku, AWS Lambda)**
- Push code to GitHub
- Connect to deployment platform
- Set environment variables (same `.env` values)
- Deploy

### Step 2: N8n Webhook Configuration

**On N8n instance:**

1. **Create workflow: "Dispute Intake"**
   - Add Webhook Trigger node
   - Set to POST `/webhook-test/userComplaint`
   - Copy webhook URL: `https://unemployed.app.n8n.cloud/webhook-test/userComplaint`

2. **Add HTTP Request node to create dispute**
   ```
   Method: POST
   URL: http://YOUR_BACKEND:8000/api/disputes
   
   Body (JSON):
   {
     "customer_email": "{{ $json.email }}",
     "platform": "{{ $json.platform }}",
     "amount": "{{ $json.amount }}",
     "order_id": "{{ $json.order_id }}",
     "issue_type": "{{ $json.issue_type }}",
     "raw_text": "{{ $json.raw_complaint_text }}",
     "evidence_url": "{{ $json.evidence_url }}"
   }
   ```

3. **Optional: Add HTTP Request node to trigger analysis**
   ```
   Method: POST
   URL: http://YOUR_BACKEND:8000/api/agents/analyze
   
   Body (JSON):
   {
     "dispute_id": "{{ $json.case_id }}",
     "agents": ["judge", "independentLawyer"]
   }
   ```

4. **Optional: Add HTTP Request node to generate PDF**
   ```
   Method: POST
   URL: http://YOUR_BACKEND:8000/generate-pdf
   
   Body (JSON):
   {
     "dispute_id": "{{ $json.case_id }}",
     "template": "verdict"
   }
   ```

### Step 3: Frontend Deployment

```bash
# Frontend TypeScript project
cd frontend
npm install
npm run build
npm run preview  # or deploy to Vercel, Netlify, etc.

# Update API endpoints in frontend/src/lib/disputes.ts
# Point to your deployed backend URL
```

### Step 4: Verify End-to-End Flow

1. **Submit test complaint** via ComplaintUI
2. **Check N8n logs** - should show webhook received
3. **Check Supabase** - dispute should appear in table
4. **Check backend logs** - should show PII masking completed
5. **Trigger analysis** - via N8n or manual curl
6. **Verify agent results** - in disputes.agent_reports

---

## 🔍 Post-Deployment Monitoring

### A. Health Checks (Hourly)
```bash
curl http://YOUR_BACKEND:8000/api/zai/health
curl http://YOUR_BACKEND:8000/api/disputes
```

### B. Log Monitoring
- [ ] Backend logs for errors
- [ ] Supabase activity logs
- [ ] N8n workflow execution logs
- [ ] PDF generation logs

### C. Performance Metrics
Monitor these in Supabase dashboard:
- [ ] Query performance (system_logs, disputes)
- [ ] Storage usage (PDFs)
- [ ] API request count
- [ ] Error rates

### D. Alert Thresholds
Set up alerts if:
- [ ] Z.AI response time > 10 seconds
- [ ] Dispute creation failing > 1% of requests
- [ ] Agent analysis timeout > 30 seconds
- [ ] PDF generation failure > 5%

---

## 🛡️ Security Checklist

### A. API Security
- [ ] CORS configured correctly (check `allowed_origins` in main.py)
- [ ] Rate limiting enabled (if using API gateway)
- [ ] API keys not exposed in logs
- [ ] JWT tokens implemented for frontend auth

### B. Data Security
- [ ] PII masking enabled for all disputes
- [ ] Supabase RLS policies enforced
- [ ] Service role key only for backend
- [ ] Encryption at rest enabled (Supabase default)

### C. Network Security
- [ ] HTTPS enforced for all endpoints
- [ ] Firewall rules configured (if on VPN)
- [ ] VPN access to database (if not on public internet)
- [ ] CORS headers validated

---

## 📊 Performance Optimization

### A. Database Optimization
```sql
-- Add indexes for frequent queries
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_system_logs_event_name ON system_logs(event_name);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX idx_transactions_order_id ON transactions USING gin(ledger_data);
```

### B. Query Optimization
- [ ] Agent analysis filters correct events (use `evidence_config.py`)
- [ ] Pagination implemented for large result sets
- [ ] Caching enabled for repeated queries

### C. Agent Analysis Optimization
- [ ] Run agents in parallel (5 concurrent max)
- [ ] Use appropriate agent for query (judge sees all, customer_lawyer sees less)
- [ ] Confidence threshold set correctly
- [ ] Timeout limits configured

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] `shield.py` - PII masking tests
- [ ] `database.py` - Supabase connection tests
- [ ] `zai_client.py` - Z.AI API tests
- [ ] `evidence_gatherer.py` - Evidence filtering tests

### Integration Tests
Run: `python backend/integration_tests.py`
- [ ] All 7 tests pass
- [ ] No timeout errors
- [ ] Validation reports all green

### E2E Tests
- [ ] Submit complaint → System logs created
- [ ] Dispute created → PII masked
- [ ] Analysis triggered → Agents respond
- [ ] Results stored → Visible in dashboard
- [ ] PDF generated → Stored in Supabase

---

## 📝 Rollback Plan

If something goes wrong in production:

### A. Backend Rollback
```bash
# 1. Stop current backend
pkill -f uvicorn

# 2. Revert to previous version
git checkout main  # or previous tag
git pull

# 3. Restart with previous env
python -m uvicorn main:app --port 8000
```

### B. Database Rollback
```sql
-- If corrupted, restore from Supabase backup
-- Supabase has automatic daily backups (go to settings)
```

### C. Frontend Rollback
```bash
# If using Vercel/Netlify, simply rollback to previous deploy
# Or manually:
git checkout main
npm run build
npm run deploy
```

---

## 🎯 Success Criteria

✅ **Deployment is successful when:**

1. All 7 integration tests pass
2. Z.AI health check returns `connected`
3. Supabase contains at least one test dispute
4. Agent analysis returns valid responses
5. PDF generation works and uploads to Storage
6. N8n webhook successfully receives complaints
7. No errors in backend logs for 30 minutes

✅ **Performance targets met:**
- Dispute creation: < 1 second
- Evidence gathering: < 5 seconds per agent
- Agent analysis: < 5 seconds per agent
- PDF generation: < 3 seconds
- Total E2E time: < 20 seconds

---

## 📞 Support & Troubleshooting

### Issue: "SUPABASE_SERVICE_ROLE_KEY not found"
**Solution**: 
1. Check `.env` file exists in `backend/` directory
2. Verify key format: `eyJ...` (JWT format)
3. Re-copy key from Supabase dashboard → Settings → API

### Issue: "Z.AI connection timeout"
**Solution**:
1. Check API key is correct in `.env`
2. Verify internet connectivity
3. Check Z.AI API status at `https://api.ilmu.ai/status`

### Issue: "PII masking not working"
**Solution**:
1. Verify `shield.py` is imported correctly
2. Check `ENABLE_PII_MASKING=true` in `.env`
3. Review masking rules in `shield.py`

### Issue: "Agent analysis returns empty results"
**Solution**:
1. Verify evidence is being gathered (check system_logs)
2. Check Z.AI response format matches expected structure
3. Review `evidence_validator.py` for validation errors

### Issue: "N8n webhook not receiving complaints"
**Solution**:
1. Verify webhook URL is accessible from external network
2. Check N8n workflow is in "Active" state
3. Test webhook with curl:
   ```bash
   curl -X POST https://unemployed.app.n8n.cloud/webhook-test/userComplaint \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","platform":"GrabFood",...}'
   ```

---

## 📅 Maintenance Schedule

### Daily
- [ ] Check backend logs for errors
- [ ] Monitor Z.AI response times

### Weekly
- [ ] Review dispute statistics
- [ ] Check Supabase storage usage
- [ ] Verify agent analysis quality scores

### Monthly
- [ ] Performance review
- [ ] Security audit
- [ ] Database optimization
- [ ] Backup verification

---

**Last Updated**: 2026-04-24
**Integration Status**: ✅ COMPLETE
**Deployment Ready**: ✅ YES
