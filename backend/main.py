from fastapi import FastAPI, HTTPException
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from shield import redact_pii
from database import supabase
from datetime import datetime, timezone

app = FastAPI(title="Resolve Mesh Security Shield")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # During hackathons, "*" allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DisputeRequest(BaseModel):
    customer_email: str
    raw_text: str

@app.post("/redact")
async def process_dispute(request: DisputeRequest):
    try:
        # 1. Run the Redaction Logic
        clean_text = redact_pii(request.raw_text)
        
        # 2. Structure the data for our NoSQL-style columns
        # We store the email in customer_info
        customer_data = {
            "email": request.customer_email
        }
        
        # We store the Guardian's work in agent_reports
        # We use a key like 'guardian' so other agents can add their reports later!
        reports_data = {
            "guardian": {
                "summary": clean_text,
                "redacted_at": datetime.now(timezone.utc).isoformat() # Mock timestamp for now
            }
        }
        
        # 3. Perform the Insert
        response = supabase.table("disputes").insert({
            "status": "PENDING",
            "customer_info": customer_data,
            "agent_reports": reports_data
        }).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="Dispute created but no data returned from database.")
        
        supabase.table("system_logs").insert({
            "event_name": "GUARDIAN_REDACTION_COMPLETE",
            "payload": {"dispute_id": response.data[0]['id'], "status": "PENDING"}
        }).execute()
        
        return {
            "status": "success",
            "case_id": response.data[0]['id'],
            "redacted_text": clean_text
        }
    
    except Exception as e:
        # If something goes wrong (e.g. Supabase is down), we show the error
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Database insertion failed.")

class LogRequest(BaseModel):
    dispute_id: str
    agent_nickname: str # e.g., "The Sleuth", "The Judge"
    event: str
    details: dict = {}

@app.post("/log")
async def add_system_log(request: LogRequest):
    try:
        # Pack everything into the 'payload' column to match your SQL schema
        log_entry = {
            "event_name": f"{request.agent_nickname}_{request.event}",
            "payload": {
                "dispute_id": request.dispute_id,
                "actor": request.agent_nickname,
                "message": request.event,
                "extra_details": request.details
            }
        }
        supabase.table("system_logs").insert(log_entry).execute()
        return {"status": "Logged"}
    except Exception as e:
        print(f"Log Error: {e}")
        return {"status": "Log failed", "error": str(e)}

@app.get("/api/ledger/{transaction_id}")
async def get_ledger_entry(transaction_id: str):
    # This searches your NoSQL 'ledger_data' for the ID
    res = supabase.table("transactions") \
        .select("*") \
        .eq("ledger_data->>transaction_id", transaction_id) \
        .execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Transaction not found in Digital Twin.")
    
    return res.data[0]

@app.post("/api/merchant-sim/{txn_id}") # Added /{txn_id}
async def merchant_handshake(txn_id: str):
    # This simulates a B2B call to a merchant like 'Tealive' or 'Shopee'
    # In a real app, this would hit their API. For the hackathon, we fetch our 'merchant_status'
    res = supabase.table("transactions") \
        .select("ledger_data->>merchant_status") \
        .eq("ledger_data->>transaction_id", txn_id) \
        .execute()
    
    # Explicitly check for data presence
    if not res.data:
        return {"merchant_response": "NOT_FOUND", "status": "warning"}
    
    return {"merchant_response": res.data[0], "status": "success"}

# helper function that generates temporary signed url for frontend to show files in investigation-reports
@app.get("/api/reports/sign-url/{file_path:path}")
async def get_signed_url(file_path: str):
    print(f"DEBUG: Requesting URL for path: {file_path}")
    # Generates a temporary URL valid for 15 minutes (900 seconds)
    res = supabase.storage.from_('investigation-reports').create_signed_url(file_path, 900)
    return res

@app.get("/api/customer-brief/{dispute_id}")
async def get_customer_brief(dispute_id: str):
    # Only select specific, non-sensitive keys from customer_info and the guardian summary
    res = supabase.table("disputes").select("customer_info, agent_reports->guardian->summary, status").eq("id", dispute_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Dispute brief not found.")
        
    case = res.data[0]
    return {
        "report_type": "OFFICIAL_DISPUTE_BRIEF",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customer_email": case['customer_info'].get('email'),
        "incident_summary": case['agent_reports']['guardian']['summary'],
        "current_status": case['status']
    }

@app.post("/api/reports/upload/{dispute_id}")
async def upload_investigation_report(dispute_id: str, file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        file_path = f"{dispute_id}/{file.filename}"
        
        # Upload to Supabase Storage
        supabase.storage.from_('investigation-reports').upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type, "upsert": "true"}
        )
        
        # Update the dispute status to 'BRIEF_SENT'
        supabase.table("disputes").update({"status": "BRIEF_SENT"}).eq("id", dispute_id).execute()
        
        supabase.table("system_logs").insert({
            "event_name": "REPORT_UPLOADED",
            "payload": {"dispute_id": dispute_id, "file_path": file_path}
        }).execute()
        
        return {"status": "Report Uploaded", "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")