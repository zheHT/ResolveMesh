# API Contract: n8n → PDF Service & Supabase

## 1. PDF Generation Service (FastAPI)

### Endpoint
POST /generate-pdf

### Request Body (JSON)
```
{
  "dispute_id": "string",
  "agent": "string", // e.g., "Negotiator"
  "confidence_score": 0-100,
  "reasoning": "string",
  "evidence": [
    {
      "transaction_id": "string",
      "hash": "string",
      "details": "string"
    }
  ],
  "summary_tldr": "string", // 30-word summary
  "pdf_url": "string (optional)",
  "created_at": "ISO timestamp",
  "template": "police" | "internal" | "verdict"
}
```

### Response
```
{
  "pdf_url": "string" // Public or local path to PDF
}
```

---

## 2. Supabase Disputes Table (n8n → Supabase)

### Table: disputes
- id: string (PK)
- ...other fields...
- ai_evidence: JSONB (InvestigationSummary structure)
- pdf_url: string
- status: string (e.g., "AWAITING_STAFF_ACTION")

### Example n8n Upsert/Update
- Upsert or update the row with the new ai_evidence and pdf_url after PDF generation.

---

## 3. System Logs Table (for audit trail)
- Log every POST to /generate-pdf and every update to disputes.
- Include timestamp, user, action, and payload.

---

## Notes
- All timestamps must be ISO 8601.
- Evidence array must cite transaction_id and hash.
- summary_tldr is required for staff dashboard.
- template field determines PDF format.
