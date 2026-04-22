# pdf_templates.py
from fpdf import FPDF
from main import InvestigationSummary

class PoliceKitPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Police Kit', ln=True, align='C')

    def body(self, summary: InvestigationSummary):
        self.set_font('Arial', '', 12)
        self.cell(0, 10, f"Dispute ID: {summary.dispute_id}", ln=True)
        self.cell(0, 10, f"Timestamps & Hashes:", ln=True)
        for ev in summary.evidence:
            self.cell(0, 10, f"- {ev.transaction_id}: {ev.hash}", ln=True)

class InternalBriefPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Internal Brief', ln=True, align='C')

    def body(self, summary: InvestigationSummary):
        self.set_font('Arial', '', 12)
        self.cell(0, 10, f"Dispute ID: {summary.dispute_id}", ln=True)
        self.multi_cell(0, 10, f"Reasoning: {summary.reasoning}")
        self.cell(0, 10, f"Evidence:", ln=True)
        for ev in summary.evidence:
            self.cell(0, 10, f"- {ev.transaction_id}: {ev.details}", ln=True)

class FinalVerdictPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Final Verdict', ln=True, align='C')

    def body(self, summary: InvestigationSummary):
        self.set_font('Arial', '', 12)
        self.cell(0, 10, f"Dispute ID: {summary.dispute_id}", ln=True)
        self.multi_cell(0, 10, f"Resolution Letter: This dispute has been reviewed and resolved. Please see attached evidence.")
        self.cell(0, 10, f"Staff TL;DR: {summary.summary_tldr}", ln=True)

# Factory function

def generate_pdf_by_template(summary: InvestigationSummary, filename: str):
    if summary.template == 'police':
        pdf = PoliceKitPDF()
        pdf.add_page()
        pdf.body(summary)
    elif summary.template == 'internal':
        pdf = InternalBriefPDF()
        pdf.add_page()
        pdf.body(summary)
    else:
        pdf = FinalVerdictPDF()
        pdf.add_page()
        pdf.body(summary)
    pdf.output(filename)
