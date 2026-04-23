// investigationSummary.schema.ts
// Canonical JSON structure for investigation summaries POSTed by n8n into Supabase.
//
// This file is intentionally **runtime-validated** (Zod), not just TypeScript-typed,
// so we can reliably guarantee that all outputs include:
// - `confidence_score` in [0..100]
// - at least one explicit evidence citation to Supabase row(s)

import { z } from "zod";

export const EvidenceSupabaseRefSchema = z.object({
  table: z.string().min(1),
  row_id: z.string().min(1),
  column: z.string().min(1).optional(),
  json_path: z.string().min(1).optional(),
});

export const EvidenceReferenceSchema = z
  .object({
    // Required: explicit citation to the row used as evidence
    supabase: EvidenceSupabaseRefSchema,

    // Optional compatibility fields: many workflows still talk in "transaction_id/hash"
    transaction_id: z.string().min(1).optional(),
    hash: z.string().min(1).optional(),

    // Required: human-readable explanation of why this row matters
    details: z.string().min(1),
  })
  .superRefine((v, ctx) => {
    // We require *some* identifier humans can cross-check quickly.
    if (!v.transaction_id && !v.hash) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["transaction_id"],
        message: "Provide at least one of transaction_id or hash.",
      });
    }
  });

const maxWords = (s: string) => s.trim().split(/\s+/).filter(Boolean).length;

export const InvestigationSummarySchema = z.object({
  dispute_id: z.string().min(1),
  agent: z.string().min(1), // e.g. "Negotiator"
  confidence_score: z.number().min(0).max(100),
  reasoning: z.string().min(1),
  evidence: z.array(EvidenceReferenceSchema).min(1),
  summary_tldr: z
    .string()
    .min(1)
    .refine((s) => maxWords(s) <= 30, "summary_tldr must be <= 30 words."),
  pdf_url: z.string().url().optional(),
  created_at: z.string().datetime({ offset: true }),
});

export type EvidenceSupabaseRef = z.infer<typeof EvidenceSupabaseRefSchema>;
export type EvidenceReference = z.infer<typeof EvidenceReferenceSchema>;
export type InvestigationSummary = z.infer<typeof InvestigationSummarySchema>;

export type InvestigationSummaryValidationResult =
  | { ok: true; value: InvestigationSummary }
  | { ok: false; errors: string[] };

export function validateInvestigationSummary(input: unknown): InvestigationSummaryValidationResult {
  const parsed = InvestigationSummarySchema.safeParse(input);
  if (parsed.success) return { ok: true, value: parsed.data };
  return { ok: false, errors: parsed.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`) };
}

export function assertInvestigationSummaryComplete(input: unknown): InvestigationSummary {
  // Throws with a readable message when confidence/evidence are missing or invalid.
  return InvestigationSummarySchema.parse(input);
}
