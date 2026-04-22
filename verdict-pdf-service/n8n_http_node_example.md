# n8n HTTP Node Example: Call PDF Service

## Purpose
This example demonstrates how to configure an n8n HTTP Request node to call the PDF generation FastAPI service.

---

### HTTP Request Node Configuration
- **HTTP Method:** POST
- **URL:** http://localhost:8000/generate-pdf
- **Content Type:** JSON
- **Body Parameters:**
  - dispute_id: string
  - agent: string
  - confidence_score: number
  - reasoning: string
  - evidence: array of objects (transaction_id, hash, details)
  - summary_tldr: string
  - created_at: ISO timestamp
  - template: police | internal | verdict

#### Example JSON Body
```
{
  "dispute_id": "RM-48201",
  "agent": "Negotiator",
  "confidence_score": 92,
  "reasoning": "Transaction hash abc123 matches the disputed charge.",
  "evidence": [
    {"transaction_id": "tx123", "hash": "abc123", "details": "Charge on 2026-04-19"}
  ],
  "summary_tldr": "Dispute over recurring charge. Transaction hash matches. High confidence.",
  "created_at": "2026-04-22T10:00:00Z",
  "template": "police"
}
```

---

### Response
- **pdf_url:** Path or public URL to the generated PDF.

---

### Usage
1. Add an HTTP Request node in your n8n workflow.
2. Set the method, URL, and body as above.
3. Use the returned pdf_url in subsequent workflow steps (e.g., update Supabase, email customer, etc).

---

### Note
- Ensure the FastAPI service is running and accessible from n8n.
- Adjust the URL if deploying to a different host or port.
