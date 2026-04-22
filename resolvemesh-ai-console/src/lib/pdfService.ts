// pdfService.ts
// Utility to call the FastAPI PDF generation endpoint from the React/TS app

import axios from 'axios';

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

export async function generatePDF(summary: InvestigationSummary, apiUrl = 'http://localhost:8000/generate-pdf') {
  const response = await axios.post(apiUrl, summary);
  return response.data.pdf_url as string;
}
