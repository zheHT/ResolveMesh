# Legal Agent System - Deployment Checklist

**Status**: Implementation Complete ✅  
**Last Updated**: April 24, 2026  
**Maintainer**: AI Development Team

---

## Phase 1: Pre-Deployment Verification

### Layer 1: Supabase Query Helpers ✅
- [x] `supabase_queries.py` created with 9 query functions
- [x] Syntax verified - no errors
- [x] Citation format: `{table, row_id, json_path}`
- [x] All functions return citation-ready data

**To Test Before Deployment:**
- [ ] Run `get_dispute_record("real-dispute-id")` - verify returns valid dispute
- [ ] Run `get_dispute_logs("real-dispute-id")` - verify logs have row_ids
- [ ] Run `get_transaction_by_id("real-transaction-id")` - verify ledger_data
- [ ] Run `find_matching_hashes("real-dispute-id")` - verify hash cross-references
- [ ] Run `verify_row_exists()` with valid and invalid row_ids - must handle both

**Expected Results:**
- All queries return within 200ms
- No NULL rows, no missing json_paths
- Citation format consistent across all functions

---

### Layer 2: Evidence Gathering ✅
- [x] `evidence_gatherer.py` created with 5 agent-specific gatherers
- [x] Syntax verified - no errors
- [x] Each agent receives tailored evidence (customer vs company vs judge vs independent)

**To Test Before Deployment:**
- [ ] Run `gather_evidence("real-dispute-id", "customerLawyer")` - verify bundle has 8+ fields
- [ ] Run `gather_evidence("real-dispute-id", "companyLawyer")` - verify different evidence than customer
- [ ] Run `gather_evidence("real-dispute-id", "judge")` - verify complete evidence (max logs)
- [ ] Run `gather_evidence("real-dispute-id", "independentLawyer")` - verify summary + history
- [ ] Verify `EvidenceBundle` type has: dispute_record, customer_info, system_logs, transactions, timeline, hash_cross_ref, customer_history, metadata

**Expected Results:**
- No two agents get identical evidence
- Judge gets most logs (~200), customer/independent get filtered (~50)
- All bundles complete without errors
- Customer history populated for independent lawyer

---

### Layer 3: Prompt Building ✅
- [x] `zai_prompt_builder.py` created with 4 prompt builders
- [x] Syntax verified - no errors
- [x] LEGAL_AGENT_BASE_PROMPTS defined in Python

**To Test Before Deployment:**
- [ ] Run `build_prompt(bundle, "customerLawyer")` - verify includes customer-focused role
- [ ] Run `build_prompt(bundle, "companyLawyer")` - verify includes company-focused role
- [ ] Run `build_prompt(bundle, "judge")` - verify neutral language
- [ ] Run `build_prompt(bundle, "independentLawyer")` - verify settlement focus
- [ ] Check prompt includes:
  - [ ] Dispute context (JSON with amount, status)
  - [ ] Timeline (chronological events)
  - [ ] System logs (30 most relevant)
  - [ ] Transactions (with ledger_data)
  - [ ] Hash cross-references
  - [ ] Citation examples: `table='system_logs', row_id='log-457', json_path='payload.field'`
  - [ ] Output format requirements

**Expected Results:**
- Prompts are 3000-5000 characters
- Token estimate 1500-3000 tokens (manageable for Z.ai)
- Citation examples present
- All 4 agents have distinct role instructions

---

### Layer 4: Validation ✅
- [x] `evidence_validator.py` created with validation + audit trail
- [x] Syntax verified - no errors
- [x] Zero-tolerance hallucination policy

**To Test Before Deployment:**
- [ ] Run `validate_supabase_reference()` with valid citation - must return valid=True
- [ ] Run `validate_supabase_reference()` with invalid row_id - must return valid=False, errors populated
- [ ] Run `validate_all_evidence()` with all valid citations - must return valid=True
- [ ] Run `validate_all_evidence()` with ONE invalid citation - must return valid=False (zero-tolerance)
- [ ] Run `validate_agent_output()` with proper format - must return valid=True
- [ ] Run `validate_agent_output()` with confidence_score > 100 - must return error
- [ ] Run `validate_agent_output()` with summary_tldr > 30 words - must return error
- [ ] Run `generate_validation_report()` - verify report summary

**Expected Results:**
- Invalid citations are caught before Z.ai invocation
- Hallucination detection works (row doesn't exist)
- All agents' outputs validated
- Zero hallucinated rows allowed in final result

---

### Layer 5: API Endpoints ✅
- [x] `main.py` updated with 3 new endpoints
- [x] POST /api/agents/analyze endpoint
- [x] GET /api/disputes/{id}/evidence endpoint  
- [x] GET /api/disputes/{id}/agent-prompt-preview endpoint

**To Test Before Deployment:**
- [ ] POST /api/agents/analyze with valid dispute_id - verify returns analysis
- [ ] POST /api/agents/analyze with invalid dispute_id - verify returns 404
- [ ] POST /api/agents/analyze - check response time (target: 8-9 seconds)
- [ ] GET /api/disputes/{id}/evidence - verify returns stats and evidence count
- [ ] GET /api/disputes/{id}/agent-prompt-preview - verify shows sample prompt
- [ ] Verify disputes table updated with agent_reports after analysis
- [ ] Check system_logs table has EVIDENCE_GATHERED and LEGAL_AGENT_ANALYSIS_COMPLETE events

**Expected Results:**
- Analysis completes in ~8-9 seconds
- Response includes validation_report
- All 4 agents run and return responses
- audit_trail stored in system_logs

---

## Phase 2: Integration Testing

### End-to-End Flow
**Test with Real Dispute Data** (Pick a GrabFood or Banking dispute)

1. [ ] **Evidence Gathering**
   - Run gather_evidence() for all 4 agent types
   - Verify evidence varies by agent type
   - Check log counts: customer 50, company 100, judge 200, independent 50
   - Verify no data loss in bundling

2. [ ] **Prompt Building**
   - Build prompts from bundles
   - Verify context is properly embedded
   - Check citation examples are clear
   - Estimate tokens (should be < 3000)

3. [ ] **Agent Invocation**
   - Invoke chat_once() with prompts
   - Verify Z.ai returns valid JSON
   - Check all 4 responses returned
   - Monitor response times (2-5 seconds per agent)

4. [ ] **Validation**
   - Run validate_agent_output() on all 4 responses
   - Verify all citations check against Supabase
   - Confirm zero hallucinations
   - Check validation_report generated

5. [ ] **Storage**
   - Verify disputes table updated with agent_reports
   - Check system_logs has audit trail entries
   - Confirm timestamps are correct
   - Validate audit entries reference correct agents

---

### n8n Workflow Integration
- [ ] Create n8n HTTP node calling POST /api/agents/analyze
- [ ] Add error handling for non-200 responses
- [ ] Add conditional logic based on validation_report.all_responses_valid
- [ ] If valid: pass responses to PDF generation
- [ ] If invalid: log error and alert staff
- [ ] Test full workflow end-to-end

---

### Frontend Integration (resolvemesh-ai-console)
- [ ] Create DisputeAnalysis component consuming /api/agents/analyze
- [ ] Display 4-agent analysis results
- [ ] Show validation_report status
- [ ] Add evidence preview button (calls /evidence endpoint)
- [ ] Add prompt preview button (calls /agent-prompt-preview endpoint)
- [ ] Error handling for failed analyses

---

## Phase 3: Performance & Load Testing

### Single Dispute Analysis
- [ ] Time complete /api/agents/analyze flow
  - Target: 8-9 seconds
  - Acceptable: 8-12 seconds
  - Slow: > 12 seconds
- [ ] Measure evidence gathering time per agent
- [ ] Measure prompt building time
- [ ] Measure validation time
- [ ] Identify bottleneck if > 12 seconds

### Concurrent Analysis
- [ ] Run 5 analyses simultaneously
- [ ] Monitor CPU and memory usage
- [ ] Verify no race conditions in Supabase updates
- [ ] Check response times remain acceptable

### Large Dispute Handling
- [ ] Test with dispute having 500+ logs
- [ ] Verify log filtering works
- [ ] Check max_logs limits enforced
- [ ] Monitor memory with large bundles

---

## Phase 4: Security & Compliance

### Data Validation
- [ ] All Supabase row_ids verified before use
- [ ] No SQL injection possible (queries use table().eq() API)
- [ ] No JSON path traversal attacks possible
- [ ] All user inputs (dispute_id, agent_type) validated

### Audit Trail
- [ ] All agent analyses logged in system_logs
- [ ] Timestamps recorded for compliance
- [ ] Evidence citations stored in audit table
- [ ] Validation results preserved

### Privacy
- [ ] Customer data only seen by relevant agents
- [ ] Customer lawyer sees customer-favorable evidence
- [ ] Company lawyer sees company-favorable evidence
- [ ] Judge/independent see balanced evidence
- [ ] No cross-contamination of evidence

---

## Phase 5: Deployment

### Database Migrations
- [ ] Create agent_evidence_citations table:
  ```sql
  CREATE TABLE agent_evidence_citations (
    id UUID PRIMARY KEY,
    dispute_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    evidence_index INT,
    supabase_table TEXT,
    row_id TEXT,
    json_path TEXT,
    transaction_id TEXT,
    hash TEXT,
    details TEXT,
    confidence_used INT,
    validation_passed BOOLEAN,
    validation_errors JSONB,
    hallucination_risk BOOLEAN,
    created_at TIMESTAMP
  );
  ```
- [ ] Add index on dispute_id for fast lookups
- [ ] Add index on agent_name for reporting

### Code Deployment
- [ ] Copy all 4 Python modules to production backend
- [ ] Update main.py with new endpoints
- [ ] Test imports work in production environment
- [ ] Verify Supabase connection string is configured
- [ ] Verify Z.ai credentials are configured

### Monitoring Setup
- [ ] Log all /api/agents/analyze calls
- [ ] Alert on validation failures (hallucinations)
- [ ] Monitor endpoint response times
- [ ] Track error rates
- [ ] Dashboard for agent analysis metrics

---

## Phase 6: Documentation & Handoff

### Documentation Created ✅
- [x] IMPLEMENTATION_GUIDE.py (this guide)
- [x] API_QUICK_REFERENCE.md (API documentation)
- [x] DEPLOYMENT_CHECKLIST.md (this file)
- [x] Code comments in all Python modules
- [x] Type hints on all functions

### Training Materials Needed
- [ ] Brief for operations team on new endpoints
- [ ] Troubleshooting guide for common errors
- [ ] How to interpret validation_report
- [ ] How to investigate hallucinations

### Maintenance Plan
- [ ] Owner: [assign person]
- [ ] On-call: [assign person]
- [ ] Runbook for common issues
- [ ] SLA for agent analysis (< 15 seconds)

---

## Known Limitations & Future Work

### Current Limitations
1. **No agent_evidence_citations table yet**
   - Audit trail stored in system_logs instead
   - Migration needed for compliance

2. **Evidence fetching limited by max_logs**
   - Judge sees max 200 logs
   - Performance tradeoff vs completeness
   - Could optimize with pagination

3. **No caching of evidence bundles**
   - Regathering evidence for same dispute is slow
   - Could cache with TTL (5 minutes)

4. **Serial agent invocation**
   - Could parallelize chat_once() calls
   - Would reduce total time from 8-9s to 5-7s

5. **No streaming of agent responses**
   - Frontend waits for all 4 agents
   - Could stream responses as they arrive

### Future Enhancements
- [ ] Implement agent_evidence_citations table
- [ ] Add evidence caching layer
- [ ] Parallelize agent invocation
- [ ] Stream agent responses to frontend
- [ ] Add graphical evidence timeline
- [ ] Implement confidence score reasoning
- [ ] Add citation explanation UI
- [ ] Support for more agent types (mediator, arbitrator)
- [ ] Multi-language support
- [ ] Custom evidence filters by jurisdiction

---

## Rollback Plan

If issues found in production:

1. **Critical Issues (> 10% failure rate)**
   - Disable /api/agents/analyze endpoint
   - Revert main.py imports
   - Restore previous version
   - Investigate in staging

2. **Non-Critical Issues (< 10% failure rate)**
   - Deploy fixes to production
   - Monitor for resolution
   - Document in runbook

3. **Data Issues (hallucinated citations)**
   - Stop agent invocations immediately
   - Quarantine affected disputes
   - Revalidate all citations
   - Determine root cause before resuming

---

## Sign-Off

- [ ] Tech Lead: ________________ Date: _____
- [ ] QA Lead: __________________ Date: _____
- [ ] Operations: _______________ Date: _____
- [ ] Product: __________________ Date: _____

---

## Version History

| Version | Date | Author | Status |
|---------|------|--------|--------|
| 1.0 | 2026-04-24 | AI Team | Implementation Complete |
| | | | Ready for Testing |

