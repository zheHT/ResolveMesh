"""PDF Service - Generate and upload verdict PDFs to Supabase"""
from datetime import datetime
import os
from pdf_templates import generate_pdf_by_template
from database import supabase

def create_verdict_pdf(summary: dict) -> dict:
    """
    Generate a verdict PDF, upload to Supabase Storage, then delete local file
    
    Args:
        summary: Dict with keys:
            - dispute_id (str)
            - agent (str)
            - confidence_score (int 0-100)
            - reasoning (str)
            - evidence (list of dicts with transaction_id, details)
            - summary_tldr (str)
            - created_at (str)
            - template (str): 'police', 'internal', or 'verdict'
    
    Returns:
        dict with:
            - status: 'success' or 'error'
            - pdf_url: Public URL to the PDF in Supabase
            - dispute_id: The dispute ID
            - template: Template used
            - error (if status is error)
    """
    local_file_path = None
    try:
        template = summary.get('template', 'verdict').lower()
        dispute_id = summary.get('dispute_id')
        
        if not dispute_id:
            return {"status": "error", "error": "Missing dispute_id in summary"}
        
        # 1. Generate PDF and save to local file
        local_file_path = generate_pdf_by_template(summary, None)
        print(f"[PDF] Generated local PDF: {local_file_path}")
        
        # 2. Verify file was created
        if not os.path.exists(local_file_path):
            return {"status": "error", "error": f"Failed to create local PDF file: {local_file_path}"}
        
        # 3. Upload to Supabase
        temp_filename = f"{template}.pdf"
        bucket_path = f"{dispute_id}/{temp_filename}"
        
        with open(local_file_path, 'rb') as pdf_file:
            response = supabase.storage.from_('investigation-reports').upload(
                path=bucket_path,
                file=pdf_file,
                file_options={"content_type": "application/pdf", "upsert": "true"}
            )
        print(f"[PDF] Upload response: {response}")
        
        # 4. Get public URL
        pdf_url = supabase.storage.from_('investigation-reports').get_public_url(bucket_path)
        print(f"[PDF] Public URL: {pdf_url}")
        
        return {
            "status": "success",
            "pdf_url": pdf_url,
            "dispute_id": dispute_id,
            "template": template
        }
    
    except Exception as e:
        import traceback
        print(f"[ERROR] PDF Generation/Upload Error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "error": str(e),
            "dispute_id": summary.get('dispute_id'),
            "template": summary.get('template', 'verdict')
        }
    
    finally:
        # 5. Delete local file
        if local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
                print(f"[PDF] Deleted local file: {local_file_path}")
            except Exception as e:
                print(f"[WARNING] Failed to delete local file {local_file_path}: {e}")

def get_local_pdf(dispute_id: str, filename: str):
    """Retrieve a locally stored PDF file"""
    file_path = f"pdfs/{dispute_id}/{filename}"
    if os.path.exists(file_path):
        return file_path
    return None
