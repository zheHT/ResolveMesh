import {
  type InvestigationSummary,
  validateInvestigationSummary,
} from "@/lib/investigationSummary.schema";

export type InvestigationSummaryIngestResult =
  | { ok: true; summary: InvestigationSummary }
  | { ok: false; error: { message: string; errors: string[] } };

/**
 * Use this at the "golden thread" boundary (n8n → app/backend → Supabase).
 * It guarantees every stored summary has:
 * - confidence_score (0..100)
 * - >= 1 evidence citation with explicit Supabase row reference
 */
export function ingestInvestigationSummary(payload: unknown): InvestigationSummaryIngestResult {
  const validated = validateInvestigationSummary(payload);
  if (validated.ok) return { ok: true, summary: validated.value };
  return {
    ok: false,
    error: {
      message: "Invalid investigation summary payload (missing confidence/evidence or malformed fields).",
      errors: validated.errors,
    },
  };
}

