from fastapi import FastAPI, HTTPException
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from shield import redact_pii
from database import supabase
from zai_client import chat_once, verify_connection, generate_staff_tldr
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
    # Metadata (For Vendor Portals/Grab/Banks)
    api_key: str = "INTERNAL_PORTAL" 
    platform: str = "General"
    
    # User/Account Data
    customer_email: str
    account_id: str = "UNKNOWN"
    
    # The Meat of the Dispute
    order_id: str = "N/A"
    amount: float = 0.0
    issue_type: str = "General" # e.g., "Moldy Bread", "Double Charge"
    raw_text: str  # This is where the Email body or Form Description goes
    
    # Evidence
    evidence_url: str = None

# --- UTILITY FUNCTIONS ---
async def is_duplicate_claim(order_id: str, customer_email: str):
    """
    Anti-Fraud Logic: Checks if an active or finished dispute 
    already exists for this specific order and customer.
    """
    # If it's a messy email without an Order ID, we can't reliably check for duplicates yet.
    if order_id == "N/A" or not order_id:
        return False 
        
    # Query Supabase using JSONB arrow operators (->>) to peek inside 'customer_info'
    res = supabase.table("disputes") \
        .select("id") \
        .eq("customer_info->>order_id", order_id) \
        .eq("customer_info->>email", customer_email) \
        .execute()
        
    # Returns True if any rows are found, False otherwise
    return len(res.data) > 0

def require_supabase():
    if supabase is None:
        raise HTTPException(
            status_code=500,
            detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env",
        )
    return supabase

@app.post("/redact")
async def process_dispute(request: DisputeRequest): # Use the new Unified class
    try:
        # 1. ANTI-FRAUD CHECK 
        # We check if this specific Order ID has been disputed before
        is_duplicate = await is_duplicate_claim(request.order_id, request.customer_email)
        
        # Determine initial status
        initial_status = "SUSPECTED_FRAUD" if is_duplicate else "PENDING"

        # 2. REDACTION (The Guardian's Job)
        clean_text = redact_pii(
            request.raw_text,
            allow_list=[request.order_id, request.platform]
        )
        
        # 3. STRUCTURE DATA (Capture everything from the Unified Request)
        customer_data = {
            "email": request.customer_email,
            "platform": request.platform,
            "account_id": request.account_id,
            "order_id": request.order_id,
            "amount": request.amount,
            "issue_type": request.issue_type,
            "evidence_url": request.evidence_url
        }
        
        reports_data = {
            "guardian": {
                "summary": clean_text,
                "redacted_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # 4. DATABASE INSERT
        response = require_supabase().table("disputes").insert({
            "status": initial_status,
            "customer_info": customer_data,
            "agent_reports": reports_data
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Database insertion failed.")

        case_id = response.data[0]['id']

        # 5. LOGGING (Using your new 'visibility' column!)
        # This is a PUBLIC log so the frontend user knows the case is created
        require_supabase().table("system_logs").insert({
            "event_name": "GUARDIAN_REDACTION_COMPLETE",
            "visibility": "PUBLIC", 
            "payload": {
                "dispute_id": case_id,
                "message": f"PII secured. Case initialized as {initial_status}."
            }
        }).execute()
        
        return {
            "status": "success",
            "case_id": case_id,
            "redacted_text": clean_text,
            "initial_status": initial_status
        }
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class LogRequest(BaseModel):
    dispute_id: str
    agent_nickname: str # e.g., "The Sleuth", "The Judge"
    event: str
    visibility: str = "INTERNAL" # Defaults to INTERNAL if not provided
    details: dict = {}

class ZaiChatRequest(BaseModel):
    message: str


class StaffTldrRequest(BaseModel):
    case_text: str

@app.post("/log")
async def add_system_log(request: LogRequest):
    try:
        # Pack everything into the 'payload' column to match your SQL schema
        log_entry = {
            "event_name": f"{request.agent_nickname}_{request.event}",
            "visibility": request.visibility,
            "payload": {
                "dispute_id": request.dispute_id,
                "actor": request.agent_nickname,
                "message": request.event,
                "extra_details": request.details
            }
        }
        require_supabase().table("system_logs").insert(log_entry).execute()
        return {"status": "Logged"}
    except Exception as e:
        print(f"Log Error: {e}")
        return {"status": "Log failed", "error": str(e)}

@app.post("/api/zai/chat")
async def zai_chat(request: ZaiChatRequest):
    try:
        reply = chat_once(request.message)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/zai/health")
async def zai_health():
    try:
        return verify_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/zai/staff-tldr")
async def zai_staff_tldr(request: StaffTldrRequest):
    try:
        tldr = generate_staff_tldr(request.case_text)
        return {"summary_tldr": tldr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ledger/{transaction_id}")
async def get_ledger_entry(transaction_id: str):
    # This searches your NoSQL 'ledger_data' for the ID
    res = require_supabase().table("transactions") \
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
    res = require_supabase().table("transactions") \
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
    res = require_supabase().storage.from_('investigation-reports').create_signed_url(file_path, 900)
    return res

@app.get("/api/customer-brief/{dispute_id}")
async def get_customer_brief(dispute_id: str):
    # Only select specific, non-sensitive keys from customer_info and the guardian summary
    res = require_supabase().table("disputes").select("customer_info, agent_reports->guardian->summary, status").eq("id", dispute_id).execute()
    
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
        require_supabase().storage.from_('investigation-reports').upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type, "upsert": "true"}
        )
        
        # Update the dispute status to 'BRIEF_SENT'
        require_supabase().table("disputes").update({"status": "BRIEF_SENT"}).eq("id", dispute_id).execute()
        
        require_supabase().table("system_logs").insert({
            "event_name": "REPORT_UPLOADED",
            "visibility": "INTERNAL",
            "payload": {"dispute_id": dispute_id, "file_path": file_path}
        }).execute()
        
        return {"status": "Report Uploaded", "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")