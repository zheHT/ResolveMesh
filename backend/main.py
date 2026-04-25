from fastapi import FastAPI, HTTPException
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import bcrypt 
import json
from pydantic import BaseModel
from shield import redact_pii
from database import supabase
from datetime import datetime, timezone
from pdf_service import create_verdict_pdf
from typing import List, Optional

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
    attachment_content: str = None  # Optional field for attachment content

class EvidenceReference(BaseModel):
    transaction_id: str
    details: str

class VerdictPDFRequest(BaseModel):
    """Request to generate a verdict PDF"""
    dispute_id: str
    agent: str  # e.g., "The Judge", "Ledger Auditor"
    confidence_score: int  # 0-100
    reasoning: str
    evidence: List[EvidenceReference]
    summary_tldr: str
    created_at: str
    template: str  # 'police', 'internal', or 'verdict'



def parse_customer_info(raw_customer_info):
    if isinstance(raw_customer_info, dict):
        return raw_customer_info

    if isinstance(raw_customer_info, str):
        try:
            parsed_customer_info = json.loads(raw_customer_info)
        except json.JSONDecodeError:
            return {}

        if isinstance(parsed_customer_info, dict):
            return parsed_customer_info

    return {}


def parse_agent_reports(raw_agent_reports):
    if isinstance(raw_agent_reports, dict):
        return raw_agent_reports

    if isinstance(raw_agent_reports, str):
        try:
            parsed_agent_reports = json.loads(raw_agent_reports)
        except json.JSONDecodeError:
            return {}

        if isinstance(parsed_agent_reports, dict):
            return parsed_agent_reports

    return {}


def get_dispute_timestamp(row, agent_reports):
    created_at = row.get("created_at") if isinstance(row, dict) else None
    if created_at:
        return created_at

    guardian_report = agent_reports.get("guardian") if isinstance(agent_reports, dict) else None
    if isinstance(guardian_report, dict):
        redacted_at = guardian_report.get("redacted_at")
        if redacted_at:
            return redacted_at

    return None


def normalize_dispute_row(row):
    if not isinstance(row, dict):
        return {
            "id": "unknown",
            "status": "PENDING",
            "customer_info": {},
            "agent_reports": {},
            "created_at": None,
        }

    customer_info = parse_customer_info(row.get("customer_info"))
    agent_reports = parse_agent_reports(row.get("agent_reports"))
    timestamp = get_dispute_timestamp(row, agent_reports)
    normalized_customer_info = {
        **customer_info,
        "email": customer_info.get("email"),
        "amount": customer_info.get("amount"),
        "order_id": customer_info.get("order_id"),
        "platform": customer_info.get("platform"),
        "issue_type": customer_info.get("issue_type"),
        "evidence_url": customer_info.get("evidence_url"),
        "account_id": customer_info.get("account_id"),
    }

    return {
        **row,
        "customer_info": normalized_customer_info,
        "agent_reports": agent_reports,
        "created_at": timestamp,
    }

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
                "redacted_at": datetime.now(timezone.utc).isoformat(),
                "attachment_content": request.attachment_content or ""
            }
        }
        
        # 4. DATABASE INSERT
        response = supabase.table("disputes").insert({
            "status": initial_status,
            "customer_info": customer_data,
            "agent_reports": reports_data
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Database insertion failed.")

        case_id = response.data[0]['id']

        # 5. LOGGING (Using your new 'visibility' column!)
        # This is a PUBLIC log so the frontend user knows the case is created
        supabase.table("system_logs").insert({
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
        supabase.table("system_logs").insert(log_entry).execute()
        return {"status": "Logged"}
    except Exception as e:
        print(f"Log Error: {e}")
        return {"status": "Log failed", "error": str(e)}

class AppendAgentReportRequest(BaseModel):
    dispute_id: str
    agent_name: str  # e.g., "sleuth", "judge", "investigator"
    report_data: dict  # Flexible object to append

@app.post("/api/agent-reports/append")
async def append_agent_report(request: AppendAgentReportRequest):
    """
    Appends a new agent report object to the agent_reports column for a dispute.
    """
    try:
        # 1. Fetch current dispute with agent_reports
        res = supabase.table("disputes") \
            .select("agent_reports") \
            .eq("id", request.dispute_id) \
            .execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Dispute not found.")
        
        current_reports = parse_agent_reports(res.data[0].get("agent_reports", {}))
        
        # 2. Append the new report under the agent_name key
        current_reports[request.agent_name] = request.report_data
        
        # 3. Update the disputes table
        update_res = supabase.table("disputes") \
            .update({"agent_reports": current_reports}) \
            .eq("id", request.dispute_id) \
            .execute()
        
        if not update_res.data:
            raise HTTPException(status_code=500, detail="Failed to update agent reports.")
        
        return {
            "status": "success",
            "message": f"Agent report '{request.agent_name}' appended successfully.",
            "dispute_id": request.dispute_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error appending agent report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class UpdateDisputeStatusRequest(BaseModel):
    dispute_id: str
    status: str  # e.g., "PENDING", "APPROVED", "REJECTED", "RESOLVED", "PARTIAL_REFUND"
    reason: str = ""  # Optional reason for status change

@app.patch("/api/disputes/{dispute_id}/status")
async def update_dispute_status(dispute_id: str, request: UpdateDisputeStatusRequest):
    """
    Updates the status of a dispute. Used by AI agents to mark cases as APPROVED, REJECTED, etc.
    """
    try:
        # 1. Verify dispute exists
        res = supabase.table("disputes") \
            .select("id") \
            .eq("id", dispute_id) \
            .execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Dispute not found.")
        
        # 2. Update status
        update_res = supabase.table("disputes") \
            .update({"status": request.status}) \
            .eq("id", dispute_id) \
            .execute()
        
        if not update_res.data:
            raise HTTPException(status_code=500, detail="Failed to update dispute status.")
        
        # 3. Log the status change (internal visibility)
        supabase.table("system_logs").insert({
            "event_name": "DISPUTE_STATUS_UPDATED",
            "visibility": "INTERNAL",
            "payload": {
                "dispute_id": dispute_id,
                "new_status": request.status,
                "reason": request.reason
            }
        }).execute()
        
        return {
            "status": "success",
            "message": f"Dispute {dispute_id} status updated to {request.status}",
            "dispute_id": dispute_id,
            "new_status": request.status
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating dispute status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ledger/{transaction_id}")
async def get_ledger_entry(transaction_id: str):
    # Supports both transaction_id and order_id lookups.
    res = supabase.table("transactions") \
        .select("*") \
        .eq("ledger_data->>transaction_id", transaction_id) \
        .execute()

    if not res.data:
        res = supabase.table("transactions") \
            .select("*") \
            .eq("ledger_data->>order_id", transaction_id) \
            .execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Transaction not found in Digital Twin.")
    
    return res.data[0]


@app.get("/api/disputes/{case_id}")
async def get_dispute_by_case_id(case_id: str):
    """
    Fetches a single dispute row by dispute id for the detail page.
    """
    try:
        try:
            res = (
                supabase.table("disputes")
                .select("id, status, customer_info, agent_reports, created_at")
                .eq("id", case_id)
                .limit(1)
                .execute()
            )
            rows = res.data or []
        except Exception:
            fallback_res = (
                supabase.table("disputes")
                .select("id, status, customer_info, agent_reports")
                .eq("id", case_id)
                .limit(1)
                .execute()
            )
            rows = [
                {**row, "created_at": None}
                for row in (fallback_res.data or [])
                if isinstance(row, dict)
            ]

        if not rows:
            raise HTTPException(status_code=404, detail="Dispute not found.")

        return normalize_dispute_row(rows[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching dispute {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not load dispute detail.")

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
    customer_info = parse_customer_info(case.get("customer_info"))
    return {
        "report_type": "OFFICIAL_DISPUTE_BRIEF",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customer_email": customer_info.get("email"),
        "order_id": customer_info.get("order_id"),
        "platform": customer_info.get("platform"),
        "amount": customer_info.get("amount"),
        "issue_type": customer_info.get("issue_type"),
        "evidence_url": customer_info.get("evidence_url"),
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
            "visibility": "INTERNAL",
            "payload": {"dispute_id": dispute_id, "file_path": file_path}
        }).execute()
        
        return {"status": "Report Uploaded", "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# MERCHANT ADAPTER (The 3rd Party Plugin)
@app.get("/api/merchant/{order_id}")
async def get_merchant_record(order_id: str):
    try:
        # We query by order_id because the Merchant doesn't know our internal dispute_id
        # Querying a specific transaction by looking inside the JSONB column
        res = (
            supabase.table("transactions")
            .select("*")
            .filter("ledger_data->>order_id", "eq", order_id)
            .execute()
        )
        
        if not res.data:
            # If no record, we return a 404 so the AI knows the merchant has no data
            raise HTTPException(status_code=404, detail="No merchant record found for this order.")
            
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Setup password hashing with bcrypt directly
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

class AuthRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth")
async def authenticate_user(request: AuthRequest):
    # 1. Search for the user by email
    res = supabase.table("profiles").select("*").eq("email", request.email).execute()
    
    # 2. Case: USER EXISTS (Sign In)
    if res.data:
        user = res.data[0]
        is_valid = verify_password(request.password, user["password_hash"])
        
        if not is_valid:
            raise HTTPException(status_code=401, detail="Incorrect password for existing account.")
        
        return {
            "status": "login",
            "message": "Welcome back!",
            "user": {"id": user["account_id"], "email": user["email"]}
        }

    # 3. Case: USER DOES NOT EXIST (Auto Sign Up)
    else:
        hashed_password = hash_password(request.password)
        
        new_user = {
            "email": request.email,
            "password_hash": hashed_password
        }
        
        insert_res = supabase.table("profiles").insert(new_user).execute()
        
        if not insert_res.data:
            raise HTTPException(status_code=500, detail="Failed to create account.")
            
        created_user = insert_res.data[0]
        
        return {
            "status": "signup",
            "message": "Account created successfully!",
            "user": {"id": created_user["account_id"], "email": created_user["email"]}
        }
    
@app.get("/api/disputes")
async def get_all_disputes():
    try:
        # Fetch active disputes only; the dashboard hides resolved cases.
        # Some schemas may not have created_at, so we retry without it.
        try:
            res = (
                supabase.table("disputes")
                .select("id, status, customer_info, agent_reports, created_at")
                .neq("status", "RESOLVED")
                .execute()
            )
            rows = res.data or []
        except Exception:
            fallback_res = (
                supabase.table("disputes")
                .select("id, status, customer_info, agent_reports")
                .neq("status", "RESOLVED")
                .execute()
            )
            rows = [
                {**row, "created_at": None}
                for row in (fallback_res.data or [])
                if isinstance(row, dict)
            ]

        return [normalize_dispute_row(row) for row in rows]
    except Exception as e:
        print(f"Error fetching disputes: {e}")
        raise HTTPException(status_code=500, detail="Could not load disputes list.")

@app.get("/api/logs/{case_id}")
async def get_case_logs(case_id: str):
    try:
        response = (
            supabase.table("system_logs")
            .select("*")
            .eq("payload->>dispute_id", case_id)
            .eq("visibility", "PUBLIC")
            .order("created_at", descending=False) # Oldest first to show the timeline
            .execute()
        )

        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=str(response.error))

        return response.data

    except Exception as e:
        print(f"[ERROR] Log Fetch Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching logs")

@app.post("/api/pdf/generate/{dispute_id}")
async def generate_verdict_pdf(dispute_id: str, request: VerdictPDFRequest):
    """
    Generate a verdict PDF and upload directly to Supabase Storage
    
    Used by n8n AI agents (Judge, Auditor, etc.) to create official case documents.
    Templates: 'verdict' (customer-facing), 'internal' (staff review), 'police' (authorities)
    
    Path parameter dispute_id must match request.dispute_id
    """
    try:
        # Verify dispute_id matches
        if dispute_id != request.dispute_id:
            raise HTTPException(status_code=400, detail="dispute_id in path does not match request body")
        
        # Convert Pydantic model to dict for pdf_service
        summary = {
            "dispute_id": request.dispute_id,
            "agent": request.agent,
            "confidence_score": request.confidence_score,
            "reasoning": request.reasoning,
            "evidence": [ev.dict() for ev in request.evidence],
            "summary_tldr": request.summary_tldr,
            "created_at": request.created_at,
            "template": request.template
        }
        
        # Generate and upload PDF
        result = create_verdict_pdf(summary)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        # Log PDF generation
        supabase.table("system_logs").insert({
            "event_name": "PDF_GENERATED",
            "visibility": "INTERNAL",
            "payload": {
                "dispute_id": request.dispute_id,
                "template": request.template,
                "agent": request.agent,
                "pdf_url": result.get("pdf_url")
            }
        }).execute()
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] PDF Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")