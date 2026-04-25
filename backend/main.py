from fastapi import FastAPI, HTTPException
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import bcrypt 
import json
import re
from pydantic import BaseModel
try:
    # When running from within backend/ (e.g. `uvicorn main:app --reload`)
    from shield import redact_pii  # type: ignore
    from database import supabase  # type: ignore
    from zai_client import chat_once, verify_connection, generate_staff_tldr  # type: ignore
    from pdf_service import fetch_dispute_bundle, build_pdf_bytes, upload_pdf  # type: ignore
    from evidence_gatherer import gather_evidence  # type: ignore
    from zai_prompt_builder import build_prompt, get_context_stats  # type: ignore
    from evidence_validator import validate_agent_responses, generate_validation_report  # type: ignore
    from agent_router import OPERATIONAL_AGENTS, LEGAL_AGENTS  # type: ignore
except ModuleNotFoundError:
    # When importing as a package (e.g. `uvicorn backend.main:app --reload`)
    from backend.shield import redact_pii  # type: ignore
    from backend.database import supabase  # type: ignore
    from backend.zai_client import chat_once, verify_connection, generate_staff_tldr  # type: ignore
    from backend.pdf_service import fetch_dispute_bundle, build_pdf_bytes, upload_pdf  # type: ignore
    from backend.evidence_gatherer import gather_evidence  # type: ignore
    from backend.zai_prompt_builder import build_prompt, get_context_stats  # type: ignore
    from backend.evidence_validator import validate_agent_responses, generate_validation_report  # type: ignore
    from backend.agent_router import OPERATIONAL_AGENTS, LEGAL_AGENTS  # type: ignore
from datetime import datetime, timezone
from typing import Any, Literal, Optional

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
async def run_auditor_checks(order_id: str, customer_email: str, issue_type: str, raw_text: str) -> dict:
    """
    Comprehensive Auditor Agent: Checks multiple fraud/spam business rules.
    
    Returns:
        {
            "is_flagged": bool,
            "risk_level": "LOW" | "MEDIUM" | "HIGH",
            "flags": [list of detected issues],
            "details": {detailed findings}
        }
    """
    flags = []
    risk_score = 0
    details = {}
    
    # RULE 1: Duplicate Order-Email Combo
    if order_id != "N/A" and order_id:
        dup_res = supabase.table("disputes") \
            .select("id, status") \
            .eq("customer_info->>order_id", order_id) \
            .eq("customer_info->>email", customer_email) \
            .execute()
        
        if len(dup_res.data) > 0:
            flags.append("DUPLICATE_ORDER_EMAIL")
            risk_score += 40
            details["duplicate_disputes"] = len(dup_res.data)
    
    # RULE 2: Multiple Disputes by Same Customer (24h window)
    if customer_email and customer_email != "N/A":
        from datetime import timedelta
        time_24h_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        
        multi_res = supabase.table("disputes") \
            .select("id") \
            .eq("customer_info->>email", customer_email) \
            .execute()
        
        dispute_count_24h = len(multi_res.data)
        if dispute_count_24h >= 3:
            flags.append("RAPID_DISPUTE_PATTERN")
            risk_score += 30
            details["disputes_in_24h"] = dispute_count_24h
        elif dispute_count_24h == 2:
            risk_score += 15
    
    # RULE 3: Multiple Customers Disputing Same Order
    if order_id != "N/A" and order_id:
        multi_cust_res = supabase.table("disputes") \
            .select("customer_info->>email") \
            .eq("customer_info->>order_id", order_id) \
            .execute()
        
        unique_customers = len(set([d.get("email", "") for d in multi_cust_res.data if d.get("email")]))
        if unique_customers > 1:
            flags.append("MULTIPLE_CUSTOMERS_SAME_ORDER")
            risk_score += 35
            details["unique_customers"] = unique_customers
    
    # RULE 4: Text Pattern Similarity (simple check - look for common spam phrases)
    spam_patterns = [
        "free refund",
        "definitely scam",
        "never received",
        "completely fake",
        "total fraud",
        "stolen",
        "didn't order",
        "don't recognize"
    ]
    
    text_lower = raw_text.lower()
    matched_patterns = [p for p in spam_patterns if p in text_lower]
    
    if len(matched_patterns) >= 2:
        flags.append("SUSPICIOUS_TEXT_PATTERN")
        risk_score += 20
        details["suspicious_phrases"] = matched_patterns
    
    # RULE 5: Excessive Refund Pattern by Customer (simplified - count disputes)
    if customer_email and customer_email != "N/A":
        refund_res = supabase.table("disputes") \
            .select("id") \
            .eq("customer_info->>email", customer_email) \
            .execute()
        
        # Get ALL disputes for this customer - if they have many, flag for review
        total_disputes = len(refund_res.data)
        if total_disputes >= 8:
            flags.append("EXCESSIVE_REFUND_CLAIMS")
            risk_score += 35
            details["total_disputes_by_customer"] = total_disputes
    
    # RULE 6: Issue Type Abuse Pattern
    if issue_type:
        issue_res = supabase.table("disputes") \
            .select("id") \
            .eq("customer_info->>email", customer_email) \
            .eq("customer_info->>issue_type", issue_type) \
            .execute()
        
        same_issue_count = len(issue_res.data)
        if same_issue_count >= 4:
            flags.append("REPEATED_ISSUE_TYPE")
            risk_score += 20
            details["same_issue_count"] = same_issue_count
    
    # Determine Risk Level
    if risk_score >= 60:
        risk_level = "HIGH"
    elif risk_score >= 35:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    is_flagged = risk_score >= 35
    
    return {
        "is_flagged": is_flagged,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "flags": flags,
        "details": details
    }


async def is_duplicate_claim(order_id: str, customer_email: str):
    """
    Legacy compatibility: wrapper for run_auditor_checks().
    Returns True if auditor flags any issues.
    """
    audit_result = await run_auditor_checks(order_id, customer_email, "", "")
    return audit_result["is_flagged"]

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
        # 1. AUDITOR CHECK (Comprehensive Fraud Detection)
        audit_result = await run_auditor_checks(
            request.order_id, 
            request.customer_email, 
            request.issue_type,
            request.raw_text
        )
        
        # Determine initial status based on audit findings
        if audit_result["risk_level"] == "HIGH":
            initial_status = "SUSPECTED_FRAUD"
        elif audit_result["risk_level"] == "MEDIUM":
            initial_status = "PENDING"
        else:
            initial_status = "PENDING"

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
            },
            "auditor": {
                "is_flagged": audit_result["is_flagged"],
                "risk_level": audit_result["risk_level"],
                "risk_score": audit_result["risk_score"],
                "flags": audit_result["flags"],
                "details": audit_result["details"],
                "audited_at": datetime.now(timezone.utc).isoformat()
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
        # Audit findings are INTERNAL - staff only
        require_supabase().table("system_logs").insert({
            "event_name": "AUDITOR_RISK_ASSESSMENT",
            "visibility": "INTERNAL", 
            "payload": {
                "dispute_id": case_id,
                "risk_level": audit_result["risk_level"],
                "risk_score": audit_result["risk_score"],
                "flags": audit_result["flags"],
                "message": f"Auditor flagged {len(audit_result['flags'])} issues. Risk: {audit_result['risk_level']}"
            }
        }).execute()
        
        # Public log for case creation
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
            "initial_status": initial_status,
            "audit_result": audit_result
        }
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/disputes")
async def create_dispute_from_webhook(request: DisputeRequest):
    """
    Create a dispute from N8n webhook or external source
    - Alias for /redact endpoint (for N8n compatibility)
    - Returns dispute ID for downstream processing
    """
    return await process_dispute(request)

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


class EvidenceSupabaseRef(BaseModel):
    table: str
    row_id: str
    column: Optional[str] = None
    json_path: Optional[str] = None


class EvidenceReference(BaseModel):
    supabase: EvidenceSupabaseRef
    transaction_id: Optional[str] = None
    hash: Optional[str] = None
    details: str


class InvestigationSummaryPayload(BaseModel):
    dispute_id: str
    agent: str
    confidence_score: int
    reasoning: str
    evidence: list[EvidenceReference]
    summary_tldr: str
    pdf_url: Optional[str] = None
    created_at: str
    template: Optional[Literal["police", "internal", "verdict"]] = None


class GeneratePdfRequest(BaseModel):
    dispute_id: str
    template: Literal["police", "internal", "verdict"] = "verdict"
    # Optionally provide the investigation summary; if missing we try disputes.agent_reports.investigation_summary
    summary: Optional[dict[str, Any]] = None

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


@app.post("/api/disputes/{dispute_id}/investigation-summary")
async def upsert_investigation_summary(dispute_id: str, payload: InvestigationSummaryPayload):
    """
    JSON Tooling target for n8n:
    - Validates shape (confidence_score + explicit evidence citations)
    - Stores under disputes.agent_reports.investigation_summary (JSONB)
    """
    try:
        if payload.dispute_id != dispute_id:
            raise HTTPException(status_code=400, detail="dispute_id mismatch between path and payload.")

        # Fetch existing agent_reports so we can merge safely.
        res = require_supabase().table("disputes").select("agent_reports").eq("id", dispute_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Dispute not found.")

        current = res.data[0].get("agent_reports") or {}
        current["investigation_summary"] = payload.model_dump()

        require_supabase().table("disputes").update({"agent_reports": current}).eq("id", dispute_id).execute()

        require_supabase().table("system_logs").insert(
            {
                "event_name": "INVESTIGATION_SUMMARY_UPSERTED",
                "visibility": "INTERNAL",
                "payload": {
                    "dispute_id": dispute_id,
                    "agent": payload.agent,
                    "confidence_score": payload.confidence_score,
                },
            }
        ).execute()

        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-pdf")
async def generate_verdict_pdf(req: GeneratePdfRequest):
    """
    Verdict PDF Service (FPDF2):
    - Fetches dispute + related system logs from Supabase
    - Renders one of 3 templates: police/internal/verdict
    - Uploads to Supabase Storage bucket (set SUPABASE_VERDICT_BUCKET)
    - Returns public URL for n8n
    """
    try:
        bundle = fetch_dispute_bundle(req.dispute_id)
        dispute = bundle["dispute"]

        summary = req.summary
        if summary is None:
            agent_reports = dispute.get("agent_reports") or {}
            summary = agent_reports.get("investigation_summary")

        if not summary:
            raise HTTPException(
                status_code=400,
                detail="Missing summary. Provide req.summary or store disputes.agent_reports.investigation_summary first.",
            )

        pdf_bytes = build_pdf_bytes(req.template, bundle, summary)
        url = upload_pdf(req.dispute_id, req.template, pdf_bytes)

        # Store pdf_url back into the investigation summary (best-effort)
        try:
            res = require_supabase().table("disputes").select("agent_reports").eq("id", req.dispute_id).execute()
            if res.data:
                current = res.data[0].get("agent_reports") or {}
                inv = current.get("investigation_summary") or summary
                if isinstance(inv, dict):
                    inv["pdf_url"] = url
                    current["investigation_summary"] = inv
                    require_supabase().table("disputes").update({"agent_reports": current}).eq("id", req.dispute_id).execute()
        except Exception:
            pass

        require_supabase().table("system_logs").insert(
            {
                "event_name": "VERDICT_PDF_GENERATED",
                "visibility": "INTERNAL",
                "payload": {"dispute_id": req.dispute_id, "template": req.template, "pdf_url": url},
            }
        ).execute()

        return {"pdf_url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

@app.get("/api/ledger/{transaction_id}")
async def get_ledger_entry(transaction_id: str):
    # Supports both transaction_id and order_id lookups.
    res = require_supabase().table("transactions") \
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
        res = (
            supabase.table("disputes")
            .select("id, status, customer_info, agent_reports")
            .eq("id", case_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []

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


# ============================================================================
# LEGAL AGENT ANALYSIS ENDPOINTS (NEW)
# ============================================================================

class LegalAgentAnalysisRequest(BaseModel):
    dispute_id: str
    agents: list[str] = ["customerLawyer", "companyLawyer", "judge", "independentLawyer", "merchant"]
    # agents can be subset, e.g. ["judge", "independentLawyer"] for quick analysis


@app.post("/api/agents/analyze")
async def analyze_with_legal_agents(request: LegalAgentAnalysisRequest):
    """
    Invoke all legal agents with evidence context for a dispute
    
    Flow:
    1. Gather evidence (agent-specific)
    2. Build prompts with evidence context
    3. Invoke Z.ai for each agent
    4. Validate all citations
    5. Store results
    
    Returns: Agent responses + validation report
    """
    try:
        dispute_id = request.dispute_id
        agents_to_run = request.agents
        
        # Step 1: Gather evidence for each agent
        evidence_bundles = {}
        for agent_type in agents_to_run:
            bundle = gather_evidence(dispute_id, agent_type)
            if not bundle:
                raise HTTPException(
                    status_code=404,
                    detail=f"Could not gather evidence for dispute {dispute_id}"
                )
            evidence_bundles[agent_type] = bundle
            
            # Log context stats
            stats = get_context_stats(bundle)
            require_supabase().table("system_logs").insert({
                "event_name": "EVIDENCE_GATHERED",
                "visibility": "INTERNAL",
                "payload": {
                    "dispute_id": dispute_id,
                    "agent": agent_type,
                    "context_stats": stats
                }
            }).execute()
        
        # Step 2: Build prompts with evidence
        prompts = {}
        for agent_type, bundle in evidence_bundles.items():
            prompt = build_prompt(bundle, agent_type)
            if not prompt:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to build prompt for {agent_type}"
                )
            prompts[agent_type] = prompt
        
        # Step 3: Invoke Z.ai for each agent
        responses = {}
        for agent_type, prompt in prompts.items():
            try:
                response_text = chat_once(prompt)
                
                # Parse JSON response (handle markdown-wrapped JSON)
                # Strip markdown code blocks if present
                json_text = response_text.strip()
                
                # Handle ```json...``` wrapping
                if json_text.startswith("```"):
                    # Remove opening ``` with optional json and any newlines
                    json_text = re.sub(r"^```\s*(?:json)?\s*\n?", "", json_text, flags=re.IGNORECASE)
                    # Remove closing ```
                    json_text = re.sub(r"\s*```\s*$", "", json_text)
                    json_text = json_text.strip()
                
                # Try to extract JSON if it's embedded in text
                if not json_text.startswith("{"):
                    # Try to find JSON object in response
                    match = re.search(r"\{.*\}", json_text, re.DOTALL)
                    if match:
                        json_text = match.group(0)
                
                # Final cleanup - strip any remaining whitespace
                json_text = json_text.strip()
                
                response_json = json.loads(json_text)
                responses[agent_type] = response_json
                
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Agent {agent_type} returned invalid JSON: {response_text[:300]}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error invoking agent {agent_type}: {str(e)}"
                )
        
        # Step 4: Validate all responses
        validation_report = generate_validation_report(dispute_id, responses)
        
        # Step 5: Store results in disputes table
        dispute = require_supabase().table("disputes").select("agent_reports").eq("id", dispute_id).execute()
        if not dispute.data:
            raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")
        
        current_reports = dispute.data[0].get("agent_reports") or {}
        current_reports["legal_agent_analysis"] = {
            "agent_responses": responses,
            "validation_report": validation_report,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
        
        require_supabase().table("disputes").update({
            "agent_reports": current_reports
        }).eq("id", dispute_id).execute()
        
        # Log completion
        require_supabase().table("system_logs").insert({
            "event_name": "LEGAL_AGENT_ANALYSIS_COMPLETE",
            "visibility": "INTERNAL",
            "payload": {
                "dispute_id": dispute_id,
                "agents_count": len(responses),
                "all_valid": validation_report["all_responses_valid"],
                "hallucination_detected": validation_report["hallucination_detected"]
            }
        }).execute()
        
        return {
            "status": "success",
            "dispute_id": dispute_id,
            "agents_analyzed": list(responses.keys()),
            "validation_report": validation_report,
            "responses": responses if validation_report["all_responses_valid"] else {},
            "errors": validation_report.get("summary", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/disputes/{dispute_id}/evidence")
async def get_dispute_evidence(dispute_id: str, agent_type: str = "judge"):
    """
    Retrieve evidence bundle for a dispute (for debugging/review)
    
    Args:
        dispute_id: The dispute ID
        agent_type: Which agent's evidence to retrieve (default: judge - complete)
    
    Returns: Evidence bundle with all logs, transactions, timeline
    """
    try:
        bundle = gather_evidence(dispute_id, agent_type)
        if not bundle:
            raise HTTPException(status_code=404, detail=f"No evidence found for dispute {dispute_id}")
        
        stats = get_context_stats(bundle)
        
        return {
            "dispute_id": dispute_id,
            "agent_type": agent_type,
            "stats": stats,
            "bundle": {
                "dispute_record": bundle.get("dispute_record"),
                "customer_info": bundle.get("customer_info"),
                "transactions": bundle.get("transactions", []),
                "merchant_record": bundle.get("merchant_record"),
                "system_logs": bundle.get("system_logs", []),
                "timeline": bundle.get("timeline", []),
                "hash_cross_ref": bundle.get("hash_cross_ref", []),
                "customer_history": bundle.get("customer_history", [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EVIDENCE CONTEXT ENDPOINT (for development/testing)
# ============================================================================

@app.get("/api/disputes/{dispute_id}/audit-findings")
async def get_audit_findings(dispute_id: str):
    """
    Retrieve auditor's fraud/spam detection findings for a dispute.
    Returns risk level, flags, and detailed audit data.
    """
    try:
        res = require_supabase().table("disputes") \
            .select("id, agent_reports") \
            .eq("id", dispute_id) \
            .execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")
        
        dispute = res.data[0]
        agent_reports = dispute.get("agent_reports", {}) or {}
        audit_findings = agent_reports.get("auditor", {})
        
        if not audit_findings:
            return {
                "status": "no_audit",
                "message": "No auditor findings recorded for this dispute",
                "dispute_id": dispute_id
            }
        
        return {
            "status": "success",
            "dispute_id": dispute_id,
            "audit_findings": audit_findings
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/disputes/{dispute_id}/agent-prompt-preview")
async def preview_agent_prompt(dispute_id: str, agent_type: str = "judge"):
    """
    Preview the full prompt that would be sent to Z.ai (for testing)
    """
    try:
        bundle = gather_evidence(dispute_id, agent_type)
        if not bundle:
            raise HTTPException(status_code=404, detail=f"No evidence found for dispute {dispute_id}")
        
        prompt = build_prompt(bundle, agent_type)
        if not prompt:
            raise HTTPException(status_code=500, detail="Failed to build prompt")
        
        stats = get_context_stats(bundle)
        
        return {
            "dispute_id": dispute_id,
            "agent_type": agent_type,
            "prompt_preview": prompt[:500] + "...",
            "prompt_length_chars": len(prompt),
            "context_stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

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
    res = require_supabase().table("profiles").select("*").eq("email", request.email).execute()
    
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
        
        insert_res = require_supabase().table("profiles").insert(new_user).execute()
        
        if not insert_res.data:
            raise HTTPException(status_code=500, detail="Failed to create account.")
            
        created_user = insert_res.data[0]
        
        return {
            "status": "signup",
            "message": "Account created successfully!",
            "user": {"id": created_user["account_id"], "email": created_user["email"]}
        }
@app.get("/api/agents")
async def get_agents():
    """
    Returns list of all available agents (legal and operational)
    """
    try:
        agents = []
        
        # Add operational agents
        for agent_id, metadata in OPERATIONAL_AGENTS.items():
            agents.append(metadata)
        
        # Add legal agents
        for agent_id, metadata in LEGAL_AGENTS.items():
            agents.append(metadata)
        
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve agents: {str(e)}")

@app.get("/api/disputes")
async def get_all_disputes():
    """
    Fetches the main list of disputes for the dashboard.
    """
    try:
        # Fetch active disputes only; the dashboard hides resolved cases.
        res = (
            require_supabase().table("disputes")
            .select("id, status, customer_info, agent_reports")
            .neq("status", "RESOLVED")
            .execute()
        )
        rows = res.data or []

        return [normalize_dispute_row(row) for row in rows]
    except Exception as e:
        print(f"Error fetching disputes: {e}")
        raise HTTPException(status_code=500, detail="Could not load disputes list.")
