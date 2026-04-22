// investigationSummary.schema.ts
// JSON structure for investigation summaries to be POSTed to Supabase disputes table

export interface EvidenceReference {
  transaction_id: string;
  hash: string;
  details: string;
}

export interface InvestigationSummary {
  dispute_id: string;
  agent: string; // e.g., "Negotiator"
  confidence_score: number; // 0-100
  reasoning: string;
  evidence: EvidenceReference[];
  summary_tldr: string; // 30-word staff summary
  pdf_url?: string; // Link to generated PDF
  created_at: string; // ISO timestamp
}

// Example usage:
// const summary: InvestigationSummary = { ... };
