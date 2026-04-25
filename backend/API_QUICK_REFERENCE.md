# Legal Agent Analysis API - Quick Reference

## Overview
Three new endpoints for legal agent analysis with evidence gathering and validation.

---

## 1. POST /api/agents/analyze
**Invoke all legal agents with evidence context**

### Request
```json
{
  "dispute_id": "disp-123",
  "agents": ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
}
```

### Response (Success - 200)
```json
{
  "status": "success",
  "dispute_id": "disp-123",
  "agents_analyzed": ["customerLawyer", "companyLawyer", "judge", "independentLawyer"],
  "validation_report": {
    "all_responses_valid": true,
    "hallucination_detected": false,
    "total_errors": 0,
    "summary": "All 4 agent responses validated successfully",
    "agent_results": {
      "customerLawyer": {"valid": true, "evidence_count": 12},
      "companyLawyer": {"valid": true, "evidence_count": 15},
      "judge": {"valid": true, "evidence_count": 18},
      "independentLawyer": {"valid": true, "evidence_count": 10}
    }
  },
  "responses": {
    "customerLawyer": { "confidence_score": 85, "summary_tldr": "Customer claim valid...", "evidence": [...] },
    "companyLawyer": { "confidence_score": 72, "summary_tldr": "Company has defense...", "evidence": [...] },
    "judge": { "confidence_score": 78, "summary_tldr": "Evidence supports...", "evidence": [...] },
    "independentLawyer": { "confidence_score": 80, "summary_tldr": "Settlement likely at...", "evidence": [...] }
  }
}
```

### Response (Invalid Citations - 400)
```json
{
  "status": "error",
  "detail": "Validation failed: CompanyLawyer cited non-existent row_id in system_logs"
}
```

### Flow
1. **Gather Evidence** (agent-specific) → ~1-2 seconds
2. **Build Prompts** (with citation examples) → ~400 ms
3. **Invoke Z.ai** (4 agents, parallel) → ~5 seconds
4. **Validate Citations** (zero-tolerance) → ~400 ms
5. **Store Results** (disputes.agent_reports) → ~200 ms

**Total: ~8-9 seconds**

---

## 2. GET /api/disputes/{dispute_id}/evidence
**Preview evidence bundle for a dispute**

### Request
```
GET /api/disputes/disp-123/evidence?agent_type=judge
```

### Parameters
- `dispute_id` (path, required): Dispute ID
- `agent_type` (query, optional): "customerLawyer", "companyLawyer", "judge", "independentLawyer"
  - Default: "judge" (complete evidence set)

### Response (200)
```json
{
  "dispute_id": "disp-123",
  "agent_type": "judge",
  "stats": {
    "dispute_amount": 450.50,
    "logs_count": 200,
    "transactions_count": 3,
    "estimated_prompt_tokens": 2850
  },
  "dispute_record": {
    "id": "disp-123",
    "customer_id": "cust-456",
    "amount": 450.50,
    "status": "UNDER_REVIEW"
  },
  "customer_info": {
    "email": "customer@example.com",
    "dispute_count": 1
  },
  "system_logs_count": 200,
  "transactions_count": 3,
  "timeline_count": 42,
  "hash_matches": 5,
  "customer_history_count": 1
}
```

### Use Cases
- **Debugging**: See what evidence agents will receive
- **Optimization**: Check log counts and token estimates
- **Transparency**: Preview evidence before running analysis
- **Development**: Verify gather_evidence() is working

---

## 3. GET /api/disputes/{dispute_id}/agent-prompt-preview
**Preview the full prompt sent to Z.ai**

### Request
```
GET /api/disputes/disp-123/agent-prompt-preview?agent_type=judge
```

### Parameters
- `dispute_id` (path, required): Dispute ID
- `agent_type` (query, optional): Agent type (default: "judge")

### Response (200)
```json
{
  "dispute_id": "disp-123",
  "agent_type": "judge",
  "prompt_preview": "You are a legal Judge evaluating a GrabFood dispute.\n\n[DISPUTE CONTEXT]\n...",
  "prompt_length_chars": 4250,
  "context_stats": {
    "dispute_amount": 450.50,
    "logs_count": 200,
    "transactions_count": 3,
    "estimated_prompt_tokens": 2850
  }
}
```

### Notes
- Full prompt preview: first 500 chars + "..."
- Useful for debugging prompt building
- Check token count before Z.ai invocation
- Verify citation examples are present

---

## Agent Types & Evidence Focus

### customerLawyer
**Goal**: Build strongest case for customer

Evidence:
- Claims & evidence URLs (photos, proofs)
- Delivery failures & refund requests
- Transaction payment proof
- Customer fraud history (to rule out disputes)
- **Max logs**: 50 (high-relevance filtered)

Example output:
```json
{
  "confidence_score": 85,
  "summary_tldr": "Customer's claim valid - delivery never completed, refund justified",
  "evidence": [
    {
      "type": "delivery_failure",
      "citation": {"table": "system_logs", "row_id": "log-457", "json_path": "payload.delivery_timestamp"},
      "detail": "No delivery confirmation on 2024-04-22"
    }
  ]
}
```

### companyLawyer
**Goal**: Build strongest defense for company

Evidence:
- Delivery completion proofs
- Transaction settlement status
- Merchant order confirmations
- Payment processor confirmations
- **Max logs**: 100 (all relevant)

Example output:
```json
{
  "confidence_score": 72,
  "summary_tldr": "Company has documented delivery proof, customer may be disputing legitimately settled order",
  "evidence": [...]
}
```

### judge
**Goal**: Neutral evaluation of both positions

Evidence:
- Complete dispute record
- All logs (chronological, no filtering)
- All transactions with ledger data
- Full timeline of events
- Hash cross-references
- **Max logs**: 200 (everything)

Example output:
```json
{
  "confidence_score": 78,
  "summary_tldr": "Evidence suggests delivery incomplete, company should issue refund",
  "evidence": [...]
}
```

### independentLawyer
**Goal**: Objective advisor for settlement

Evidence:
- Key events (summary logs)
- Customer dispute history
- Similar past disputes
- Settlement recommendations
- **Max logs**: 50 (summarized)

Example output:
```json
{
  "confidence_score": 80,
  "summary_tldr": "Settlement recommended at 80% refund - customer likely to accept",
  "evidence": [...]
}
```

---

## Error Handling

### 404 Not Found
```json
{
  "detail": "Dispute disp-999 not found"
}
```

### 500 Internal Error
```json
{
  "detail": "Analysis failed: Could not gather evidence - Supabase connection error"
}
```

### 400 Bad Request
```json
{
  "detail": "Validation failed: CustomerLawyer cited non-existent row_id 'log-99999' in system_logs"
}
```

---

## Citation Format Reference

All agent evidence must cite real Supabase data:

```json
{
  "citation": {
    "supabase": {
      "table": "system_logs",
      "row_id": "log-457",
      "json_path": "payload.delivery_timestamp"
    }
  },
  "detail": "Delivery timestamp confirms..."
}
```

**Valid Tables**: 
- `disputes`
- `system_logs`
- `transactions`

**Validation**: Every citation is verified:
1. Row exists in table
2. JSONB path exists at json_path
3. Zero hallucinated rows allowed (fails entire analysis if found)

---

## Integration with n8n

```json
HTTP Request Node:
{
  "method": "POST",
  "url": "http://localhost:8000/api/agents/analyze",
  "headers": {"Content-Type": "application/json"},
  "body": {
    "dispute_id": "{{ $json.dispute_id }}",
    "agents": ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
  }
}

Process Response:
{
  "condition": "response.validation_report.all_responses_valid === true",
  "ifTrue": "Generate PDF with 4-agent analysis",
  "ifFalse": "Alert staff - citation validation failed"
}
```

---

## Performance Benchmarks

| Operation | Time |
|-----------|------|
| Gather evidence (1 agent) | 500 ms |
| Build prompt | 100 ms |
| Z.ai invocation (1 agent) | 2-5 seconds |
| Validation (all agents) | 400 ms |
| **Total (4 agents, parallel Z.ai)** | **~8-9 seconds** |

---

## Next Steps

1. **Test**: Use `/evidence` endpoint to preview data
2. **Review**: Check `/agent-prompt-preview` to verify evidence context
3. **Analyze**: Run `/agents/analyze` to invoke all agents
4. **Verify**: Check `validation_report.all_responses_valid`
5. **Generate**: Use responses in PDF service or other workflows
