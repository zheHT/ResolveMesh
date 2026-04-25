"""PDF Template Generation for Dispute Verdicts"""
from fpdf import FPDF
from datetime import datetime
import os

class BasePDF(FPDF):
    """Base PDF class with header and footer"""
    def __init__(self, title="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        # Enable UTF-8 encoding to support special characters (em dashes, etc.)
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 15, self.title, border=1, ln=True, align='C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Page {self.page_no()}", align='C')

class PoliceKitPDF(BasePDF):
    """Police evidence kit - Transaction hashes and evidence for authorities"""
    def __init__(self):
        super().__init__(title="Police Evidence Kit")
    
    def body(self, summary):
        self.set_font('Arial', '', 11)
        self.cell(0, 8, f"Dispute ID: {summary.get('dispute_id')}", ln=True)
        self.cell(0, 8, f"Agent: {summary.get('agent')}", ln=True)
        self.cell(0, 8, f"Confidence Score: {summary.get('confidence_score')}%", ln=True)
        self.ln(3)
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, "Transaction Hashes & Evidence:", ln=True)
        
        self.set_font('Arial', '', 10)
        for ev in summary.get('evidence', []):
            self.set_font('Arial', 'B', 10)
            self.cell(0, 6, f"Transaction ID: {ev.get('transaction_id')}", ln=True)
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 6, f"Details: {ev.get('details')}")
            self.ln(2)

class InternalBriefPDF(BasePDF):
    """Internal investigation brief for staff review"""
    def __init__(self):
        super().__init__(title="Internal Investigation Brief")
    
    def body(self, summary):
        self.set_font('Arial', '', 11)
        self.cell(0, 8, f"Dispute ID: {summary.get('dispute_id')}", ln=True)
        self.cell(0, 8, f"Agent: {summary.get('agent')}", ln=True)
        self.cell(0, 8, f"Confidence Score: {summary.get('confidence_score')}%", ln=True)
        self.ln(5)
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, "Reasoning:", ln=True)
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, summary.get('reasoning', ''))
        self.ln(5)
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, "Evidence Summary:", ln=True)
        self.set_font('Arial', '', 10)
        for i, ev in enumerate(summary.get('evidence', []), 1):
            self.multi_cell(0, 6, f"{i}. {ev.get('transaction_id')}: {ev.get('details')}")
        self.ln(5)
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, "TL;DR:", ln=True)
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, summary.get('summary_tldr', ''))

class FinalVerdictPDF(BasePDF):
    """Customer-facing final verdict letter"""
    def __init__(self):
        super().__init__(title="FINAL VERDICT LETTER")
    
    def body(self, summary):
        self.set_font('Arial', '', 11)
        self.cell(0, 8, f"Dispute ID: {summary.get('dispute_id')}", ln=True)
        self.cell(0, 8, f"Issued by: {summary.get('agent')}", ln=True)
        self.cell(0, 8, f"Date: {summary.get('created_at')}", ln=True)
        self.ln(8)
        
        self.set_font('Arial', 'B', 13)
        self.cell(0, 10, "RESOLUTION DECISION", ln=True)
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, 
            "This dispute has been thoroughly reviewed by our AI arbitration system. "
            "All evidence, transaction records, and merchant communications have been analyzed. "
            "A binding judgment has been rendered below."
        )
        self.ln(5)
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, "VERDICT SUMMARY:", ln=True)
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, summary.get('summary_tldr', ''))
        self.ln(5)
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, "DETAILED REASONING:", ln=True)
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, summary.get('reasoning', ''))
        self.ln(5)
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, "KEY EVIDENCE:", ln=True)
        self.set_font('Arial', '', 10)
        for ev in summary.get('evidence', []):
            self.multi_cell(0, 6, f"- {ev.get('details')} (ID: {ev.get('transaction_id')})")
        self.ln(5)
        
        self.set_font('Arial', 'B', 11)
        self.cell(0, 8, f"Confidence Level: {summary.get('confidence_score')}%", ln=True)

def generate_pdf_by_template(summary: dict, output: any) -> str:
    """
    Factory function to generate PDF based on template type
    Saves PDF to local file and returns the file path
    
    Args:
        summary: Dictionary with dispute summary data
        output: Ignored (kept for backward compatibility)
    
    Returns:
        str: Path to the generated PDF file
    """
    # Clean Unicode characters that latin-1 can't encode
    def sanitize_text(text):
        if not isinstance(text, str):
            return text
        # Replace problematic Unicode characters with ASCII equivalents
        replacements = {
            '\u2014': '-',   # em dash → hyphen
            '\u2013': '-',   # en dash → hyphen
            '\u201c': '"',   # left double quote → quote
            '\u201d': '"',   # right double quote → quote
            '\u2018': "'",   # left single quote → apostrophe
            '\u2019': "'",   # right single quote → apostrophe
            '\u2026': '...',  # ellipsis → three dots
        }
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)
        return text
    
    # Sanitize all string values in summary
    summary_clean = {}
    for key, value in summary.items():
        if key == 'evidence' and isinstance(value, list):
            summary_clean[key] = [
                {k: sanitize_text(v) if isinstance(v, str) else v for k, v in ev.items()}
                for ev in value
            ]
        else:
            summary_clean[key] = sanitize_text(value) if isinstance(value, str) else value
    
    template = summary_clean.get('template', 'verdict').lower()
    dispute_id = summary_clean.get('dispute_id')
    
    # Create directory if it doesn't exist
    pdf_dir = f"pdfs/{dispute_id}"
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Create filename - simple, just use template name
    filename = f"{template}.pdf"
    file_path = f"{pdf_dir}/{filename}"
    
    if template == 'police':
        pdf = PoliceKitPDF()
    elif template == 'internal':
        pdf = InternalBriefPDF()
    else:  # default to verdict
        pdf = FinalVerdictPDF()
    
    pdf.add_page()
    pdf.body(summary_clean)
    
    # Save PDF to local file
    pdf.output(file_path)
    
    return file_path
