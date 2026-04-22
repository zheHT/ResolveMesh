# Validation Checklist: Confidence Score & Evidence

## Purpose
Ensure all outputs (PDF, investigation summary, Supabase row) include:
- Confidence score (0-100)
- Explicit evidence references (transaction_id, hash)
- Staff TL;DR summary

---

## Checklist
- [x] InvestigationSummary schema includes confidence_score and evidence array
- [x] PDF templates display confidence score and evidence
- [x] Example n8n payload includes confidence_score and evidence
- [x] API contract requires confidence_score and evidence
- [x] Staff summary (TL;DR) present in all outputs

---

## Test Cases
1. Submit a sample investigation summary to /generate-pdf with evidence and confidence_score
2. Verify generated PDF contains:
   - Dispute ID
   - Confidence Score
   - Evidence (transaction_id, hash)
   - Staff TL;DR
3. Confirm returned pdf_url is valid
4. Upsert the returned pdf_url and investigation summary to Supabase disputes table
5. Review staff dashboard for correct display

---

## Notes
- All evidence must cite transaction_id and hash
- Confidence score must be present and between 0-100
- Staff summary must be concise (≤ 30 words)
