import { type InvestigationSummary } from "@/lib/investigationSummary.schema";

export const VALID_INVESTIGATION_SUMMARY: InvestigationSummary = {
  dispute_id: "RM-00000",
  agent: "Negotiator",
  confidence_score: 87,
  reasoning:
    "Transaction hash and device/IP cluster match prior authenticated sessions; no anomaly in merchant descriptors. Recommend deny chargeback and request customer verification.",
  evidence: [
    {
      supabase: { table: "transactions", row_id: "tx_123", column: "audit_log", json_path: "$.hash" },
      transaction_id: "tx_123",
      hash: "0xabc123",
      details: "Hash matches the ledger entry stored in transactions.audit_log for the disputed charge.",
    },
  ],
  summary_tldr: "Hash and session signals match prior activity; no anomaly detected; recommend deny chargeback pending customer verification.",
  pdf_url: "https://example.invalid/bucket/RM-00000/internal-brief.pdf",
  created_at: "2026-04-22T00:00:00Z",
};

// Deliberately invalid: missing evidence + confidence out of range
export const INVALID_INVESTIGATION_SUMMARY_MISSING_FIELDS = {
  dispute_id: "RM-00001",
  agent: "Negotiator",
  confidence_score: 120,
  reasoning: "Insufficient data.",
  evidence: [],
  summary_tldr: "Too long ".repeat(50),
  created_at: "not-a-date",
};

