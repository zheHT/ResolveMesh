"""
IMPLEMENTATION GUIDE: Agent Supabase Query System

This guide explains how the legal agents interact with Supabase to gather evidence
and build evidence-based legal arguments.

Implementation: April 24, 2026
Status: ✅ Complete - Ready for integration with n8n workflow
"""

# ============================================================================
# ARCHITECTURE OVERVIEW
# ============================================================================

"""
Four-Layer Query System:

┌─────────────────────────────────────────────────────────────┐
│ Layer 1: QUERY HELPERS (supabase_queries.py)               │
│ - Low-level Supabase queries                               │
│ - Returns citation-ready data (table, row_id, json_path)   │
│ - Functions: get_dispute_record(), get_dispute_logs(), etc.│
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: EVIDENCE GATHERING (evidence_gatherer.py)         │
│ - Agent-specific evidence bundles                          │
│ - Each agent gets tailored evidence                        │
│ - Functions: gather_evidence_for_customer_lawyer(), etc.   │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: PROMPT BUILDING (zai_prompt_builder.py)           │
│ - Format evidence as JSON context                          │
│ - Embed in Z.ai prompts                                    │
│ - Add citation examples and guidelines                     │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: VALIDATION (evidence_validator.py)                │
│ - Verify agent citations reference real rows               │
│ - Store audit trail for compliance                         │
│ - Zero-tolerance for hallucinations                        │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│ NEW API ENDPOINTS (main.py)                                │
│ - POST /api/agents/analyze                                 │
│ - GET /api/disputes/{id}/evidence                          │
│ - GET /api/disputes/{id}/agent-prompt-preview              │
└─────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# FILE STRUCTURE
# ============================================================================

"""
backend/
├── supabase_queries.py        ← Low-level query helpers
├── evidence_gatherer.py       ← Agent-specific evidence gathering
├── zai_prompt_builder.py      ← Prompt formatting with evidence
├── evidence_validator.py      ← Citation validation & audit trail
├── main.py                    ← (UPDATED) New /agents/analyze endpoints
└── agent_router.py            ← (Can integrate with evidence gathering)
"""


# ============================================================================
# KEY FUNCTIONS BY LAYER
# ============================================================================

"""
LAYER 1: supabase_queries.py
───────────────────────────────────────────────────────────────

1. get_dispute_record(dispute_id) → dict
   Returns full dispute with customer_info, status, amount

2. get_dispute_logs(dispute_id, limit=50) → list[dict]
   Returns system logs for dispute (ordered by timestamp)
   Each log includes: event_name, payload, timestamp, row_id

3. get_transaction_by_id(transaction_id) → dict
   Returns transaction with ledger_data (hashes, status)

4. get_transaction_hashes(transaction_id) → list[dict]
   Extracts all hash values from ledger_data

5. search_logs_by_event(dispute_id, pattern) → list[dict]
   Search logs by event type (e.g., "DELIVERY", "REFUND")

6. get_timeline(dispute_id) → list[dict]
   Chronological timeline of all events across tables

7. find_matching_hashes(dispute_id) → dict[str, list]
   Cross-references hashes found in logs and transactions
   Returns: {hash_value: [{table, row_id, json_path}]}

8. verify_row_exists(table, row_id) → bool
   Check if a row actually exists (for validation)

9. verify_json_path(table, row_id, json_path) → bool
   Check if a JSONB path exists


LAYER 2: evidence_gatherer.py
───────────────────────────────────────────────────────────────

1. gather_evidence_for_customer_lawyer(dispute_id) → EvidenceBundle
   Evidence focused on: customer's claim strength
   - Photos/evidence URLs in logs
   - Delivery failures
   - Transaction proof
   - Customer history (fraud detection)

2. gather_evidence_for_company_lawyer(dispute_id) → EvidenceBundle
   Evidence focused on: company's defense strength
   - Delivery completion proofs
   - Transaction settlement status
   - Merchant status logs
   - Hash matches across systems

3. gather_evidence_for_judge(dispute_id) → EvidenceBundle
   Evidence: Complete, neutral picture
   - ALL logs (up to 200)
   - All transactions
   - Full timeline
   - All hash cross-references

4. gather_evidence_for_independent_lawyer(dispute_id) → EvidenceBundle
   Evidence: Summary + settlement focus
   - Key events (50 logs)
   - Customer history (10 past disputes)
   - Critical evidence for settlement

5. gather_evidence(dispute_id, agent_type) → EvidenceBundle
   Router function - calls appropriate gatherer above


LAYER 3: zai_prompt_builder.py
───────────────────────────────────────────────────────────────

1. format_dispute_context(bundle) → str
   JSON block with dispute_id, amount, status, etc.

2. format_timeline(bundle, max_events=30) → str
   Chronological timeline with timestamps and citations

3. format_system_logs(bundle, max_logs=30) → str
   Readable log format with citation examples

4. format_transactions(bundle) → str
   Transaction ledger with status and hashes

5. format_hash_cross_reference(bundle) → str
   Hash matching analysis

6. build_prompt(bundle, agent_type) → str
   Complete prompt with:
   - Base legal agent instructions
   - Evidence context (dispute, logs, transactions, timeline)
   - Citation guidelines with examples
   - Output format requirements


LAYER 4: evidence_validator.py
───────────────────────────────────────────────────────────────

1. validate_supabase_reference(evidence_item) → ValidationResult
   Verify single citation (table, row_id, json_path exist)

2. validate_all_evidence(evidence_items) → ValidationResult
   Validate all evidence in agent output
   Returns: valid, errors, warnings, hallucination_risk

3. validate_agent_output(output) → ValidationResult
   Complete validation:
   - Required fields present
   - confidence_score in [0, 100]
   - summary_tldr <= 30 words
   - All citations valid

4. store_evidence_audit_trail(dispute_id, agent, evidence, ...) → bool
   Create compliance audit record for each citation

5. generate_validation_report(dispute_id, responses) → dict
   Report on all agents with summary and recommendations

6. check_citation_quality(evidence_items) → dict
   Metrics: specificity, cross-referencing, detail level
   Returns: quality_score, recommendation
"""


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
EXAMPLE 1: Gather Evidence for Customer Lawyer
──────────────────────────────────────────────

from evidence_gatherer import gather_evidence

bundle = gather_evidence("disp-123", "customerLawyer")

bundle contains:
{
    "dispute_id": "disp-123",
    "dispute_record": {...},
    "customer_info": {...},
    "system_logs": [50 most relevant logs],
    "transactions": [related transactions],
    "timeline": [chronological events],
    "hash_cross_ref": {hash_value: [locations]},
    "customer_history": [past disputes],
    "metadata": {...}
}


EXAMPLE 2: Build Prompt with Evidence Context
──────────────────────────────────────────────

from evidence_gatherer import gather_evidence
from zai_prompt_builder import build_prompt

bundle = gather_evidence("disp-123", "judge")
prompt = build_prompt(bundle, "judge")

prompt structure:
1. Base legal agent instructions
2. Dispute context (JSON)
3. Chronological timeline
4. System logs (30 most relevant)
5. Transaction ledger
6. Hash cross-references
7. Citation guidelines with examples
8. Output format requirements


EXAMPLE 3: Invoke Agent and Validate
─────────────────────────────────────

from zai_client import chat_once
from evidence_validator import validate_agent_output, store_evidence_audit_trail

# Get prompt with evidence
prompt = build_prompt(bundle, "judge")

# Invoke agent
response_text = chat_once(prompt)
agent_output = json.loads(response_text)

# Validate
validation = validate_agent_output(agent_output)

if validation["valid"]:
    # Store audit trail
    store_evidence_audit_trail(
        "disp-123",
        "judge",
        agent_output["evidence"],
        validation,
        agent_output["confidence_score"]
    )
    print("✅ Agent output valid - citations verified")
else:
    print(f"❌ Invalid citations: {validation['errors']}")
    if validation["hallucination_risk"]:
        print("⚠️ ALERT: Possible hallucinated rows detected!")


EXAMPLE 4: Full Flow - API Endpoint
────────────────────────────────────

# Client makes request
POST /api/agents/analyze
{
    "dispute_id": "disp-123",
    "agents": ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
}

# Backend (in main.py):
1. gather_evidence("disp-123", "customerLawyer")
2. gather_evidence("disp-123", "companyLawyer")
3. gather_evidence("disp-123", "judge")
4. gather_evidence("disp-123", "independentLawyer")

5. build_prompt(bundle_1, "customerLawyer")
6. build_prompt(bundle_2, "companyLawyer")
7. build_prompt(bundle_3, "judge")
8. build_prompt(bundle_4, "independentLawyer")

9. chat_once(prompt_1) → customerLawyer response
10. chat_once(prompt_2) → companyLawyer response
11. chat_once(prompt_3) → judge response
12. chat_once(prompt_4) → independentLawyer response

13. validate_agent_responses("disp-123", {responses})
    → Verify all 4 agents' citations

14. Store in disputes.agent_reports.legal_agent_analysis
    → Include responses + validation report

# Response to client
{
    "status": "success",
    "dispute_id": "disp-123",
    "agents_analyzed": ["customerLawyer", "companyLawyer", "judge", "independentLawyer"],
    "validation_report": {
        "all_responses_valid": true,
        "hallucination_detected": false,
        "total_errors": 0,
        "agent_results": {...}
    },
    "responses": { 4 agent outputs with validated citations }
}
"""


# ============================================================================
# TESTING CHECKLIST
# ============================================================================

"""
PRE-DEPLOYMENT VERIFICATION:

[ ] 1. Query Functions Work
    - Test get_dispute_record() with real dispute_id
    - Test get_dispute_logs() returns logs with row_ids
    - Test get_transaction_by_id() with transaction data
    - Test find_matching_hashes() finds cross-references

[ ] 2. Evidence Gathering Works
    - Gather evidence for all 4 agent types
    - Verify each bundle has required fields
    - Check evidence counts are reasonable
    - Verify no empty bundles

[ ] 3. Prompt Building Works
    - Build prompts for all 4 agents
    - Verify prompts include dispute context
    - Check citation examples are present
    - Validate prompt length (~3000-5000 chars)

[ ] 4. Validation Works
    - Mock agent outputs with valid citations
    - Mock agent outputs with invalid row_ids
    - Verify invalid citations detected
    - Check hallucination detection triggers

[ ] 5. API Endpoints Work
    - Test POST /api/agents/analyze with dispute_id
    - Test GET /api/disputes/{id}/evidence
    - Test GET /api/disputes/{id}/agent-prompt-preview
    - Verify responses include validation reports

[ ] 6. Audit Trail Works
    - Run analysis, check system_logs for evidence citations
    - Verify agent_evidence_citations table populated
    - Check row_ids in audit table match actual Supabase rows
    - Verify timestamp and agent names recorded

[ ] 7. Citation Accuracy
    - Spot-check 3 agent outputs
    - Manually verify each cited row_id exists in Supabase
    - Verify json_paths point to actual data
    - Zero hallucinated rows allowed

[ ] 8. Performance
    - Time evidence gathering for large disputes (100+ logs)
    - Target: < 2 seconds per agent
    - Measure prompt length impact on Z.ai latency
    - Profile memory usage
"""


# ============================================================================
# DEBUGGING TIPS
# ============================================================================

"""
1. Agent citations missing or wrong?
   → Check zai_prompt_builder.py format_system_logs()
   → Verify row_ids in bundle match Supabase
   → Test get_dispute_logs() directly

2. Evidence context too large?
   → Adjust max_logs in evidence_gatherer.py (default 50, 100, 200 by agent)
   → Use filter_logs_by_relevance() to reduce size
   → Check token estimate in get_context_stats()

3. Validation failing?
   → Check verify_row_exists() can reach Supabase
   → Verify json_path syntax (use dots: payload.field)
   → Check agent output JSON format is valid

4. Hallucination detected?
   → Agent referenced non-existent row_id
   → Check if log was deleted between evidence gathering and validation
   → Re-run evidence gathering to get fresh data

5. Prompt building slow?
   → Optimize max_events in get_timeline()
   → Cache evidence bundles if analyzing same dispute multiple times
   → Consider lazy-loading transactions if not needed
"""


# ============================================================================
# INTEGRATION WITH n8n
# ============================================================================

"""
To integrate with n8n workflow:

1. n8n HTTP Node Configuration
   Method: POST
   URL: http://localhost:8000/api/agents/analyze
   Headers: {"Content-Type": "application/json"}
   Body:
   {
       "dispute_id": "{{ $json.dispute_id }}",
       "agents": ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
   }

2. Process Response
   - Check response.validation_report.all_responses_valid
   - If valid: use response.responses for PDF generation
   - If invalid: log errors and alert staff

3. Store Results
   Update Supabase disputes table:
   disputes
   ├─ id: dispute_id
   └─ agent_reports:
      └─ legal_agent_analysis:
         ├─ agent_responses
         ├─ validation_report
         └─ analyzed_at

4. Optional: Generate PDFs
   Use response.responses (4 agent analyses) as input to
   verdict-pdf-service for multi-perspective PDF generation
"""


# ============================================================================
# PERFORMANCE TARGETS
# ============================================================================

"""
Query Performance (per agent):
- Gather evidence:     < 500 ms
- Build prompt:        < 100 ms
- Total before Z.ai:   < 600 ms

Z.ai Invocation:
- Per agent:           ~2-5 seconds (depends on model)
- 4 agents parallel:   ~5 seconds (not sequential)

Validation:
- Per agent output:    < 100 ms
- 4 agents:            < 400 ms

Total end-to-end (4 agents):
- Evidence gathering:  ~2 seconds
- Prompt building:     ~400 ms
- Z.ai invocation:     ~5 seconds
- Validation:          ~400 ms
- Storage:             ~200 ms
────────────────────────────────
Total: ~8-9 seconds target
"""
