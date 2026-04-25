# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pdf_templates import generate_pdf_by_template
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class EvidenceReference(BaseModel):
    transaction_id: str
    hash: str
    details: str

class InvestigationSummary(BaseModel):
    dispute_id: str
    agent: str
    confidence_score: int
    reasoning: str
    evidence: List[EvidenceReference]
    summary_tldr: str
    pdf_url: Optional[str] = None
    created_at: str
    template: str  # 'police', 'internal', 'verdict'

# --- PDF Generation ---


# --- API Endpoint ---
@app.post("/generate-pdf")
def create_pdf(summary: InvestigationSummary):
    # Choose template (expand as needed)
    template = summary.template.lower()
    filename = f"pdfs/{summary.dispute_id}_{template}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    os.makedirs("pdfs", exist_ok=True)
    generate_pdf_by_template(summary, filename)
    # TODO: Upload to Supabase Storage and return public URL
    # For now, return local path
    return {"pdf_url": filename}
