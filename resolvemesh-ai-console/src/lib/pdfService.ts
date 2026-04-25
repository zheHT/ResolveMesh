// pdfService.ts
// Utility to call the FastAPI PDF generation endpoint from the React/TS app

export interface EvidenceReference {
  transaction_id: string;
  hash: string;
  details: string;
}

export interface InvestigationSummary {
  dispute_id: string;
  agent: string;
  confidence_score: number;
  reasoning: string;
  evidence: EvidenceReference[];
  summary_tldr: string;
  pdf_url?: string;
  created_at: string;
  template: 'police' | 'internal' | 'verdict';
}

function joinUrl(base: string, path: string) {
  const normalizedBase = base.endsWith('/') ? base.slice(0, -1) : base;
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

const DEFAULT_PDF_SERVICE_BASE_URL =
  (import.meta as unknown as { env?: Record<string, string | undefined> }).env?.VITE_PDF_SERVICE_URL ||
  'http://localhost:8000';

export async function generatePDF(
  summary: InvestigationSummary,
  apiUrl = joinUrl(DEFAULT_PDF_SERVICE_BASE_URL, '/generate-pdf'),
) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 60_000);

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(summary),
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new Error(`PDF service error (${response.status}): ${text || response.statusText}`);
    }

    const data = (await response.json()) as { pdf_url?: string };
    if (!data.pdf_url) throw new Error('PDF service did not return pdf_url');
    return data.pdf_url;
  } finally {
    window.clearTimeout(timeoutId);
  }
}
