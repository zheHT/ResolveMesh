import { ingestInvestigationSummary } from "@/lib/investigationSummary.ingest";
import {
  INVALID_INVESTIGATION_SUMMARY_MISSING_FIELDS,
  VALID_INVESTIGATION_SUMMARY,
} from "@/lib/investigationSummary.fixtures";

export function selfCheckInvestigationSummaryValidation() {
  const ok = ingestInvestigationSummary(VALID_INVESTIGATION_SUMMARY);
  const bad = ingestInvestigationSummary(INVALID_INVESTIGATION_SUMMARY_MISSING_FIELDS);

  return {
    valid_ok: ok.ok,
    invalid_ok: bad.ok,
    invalid_errors: bad.ok ? [] : bad.error.errors,
  };
}

